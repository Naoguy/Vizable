# ─────────────────────────────────────────────────────────────────────────────
#  Morrama: STEP Importer  v1.4.0
#  Blender Extension — Blender 4.2+
#
#  HOW IT WORKS
#  ────────────
#    1. Run the bundled step2glb.exe (OpenCASCADE-based STEP→GLB converter)
#    2. Import the resulting .glb using bpy.ops.import_scene.gltf()
#       — this operator is ALWAYS present in Blender 4.x, no extra add-on needed
#    3. Apply Morrama post-processing:
#         • rename objects to their real part names
#         • guarantee a single root empty named after the file
#         • drop that empty at the base (bottom-centre) of the model
#         • correct source up-axis orientation
#         • place the import in a file-named collection under the active one
#
#  The step2glb.exe + OpenCASCADE DLLs in the bin/ folder are redistributed
#  from the Step2Blend project (Louis Rist, mrrist.com) under its license.
#
#  KNOWN LIMITATIONS (see project notes — addressed by a future signed converter)
#    • Deeply nested sub-assemblies are flattened to a single level.
#    • Multiple bodies inside one sub-assembly may merge into a single mesh.
#  These are properties of step2glb's conversion, not of this add-on.
#
#  Installation
#  ────────────
#  Edit › Preferences › Get Extensions › ▾ › Install from Disk → select zip
#  Then: N-panel in any 3D Viewport › Morrama tab
# ─────────────────────────────────────────────────────────────────────────────

import bpy
import os
import sys
import stat
import math
import tempfile
import subprocess
import mathutils
from bpy.props import (
    StringProperty, FloatProperty, BoolProperty, EnumProperty,
)
from bpy.types import Operator, Panel, PropertyGroup
from bpy_extras.io_utils import ImportHelper


# ─────────────────────────────────────────────────────────────────────────────
#  step2glb binary discovery
# ─────────────────────────────────────────────────────────────────────────────

def _addon_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _step2glb_path():
    """Return path to the bundled step2glb binary, or None."""
    bin_dir = os.path.join(_addon_dir(), "bin")
    exe = "step2glb.exe" if sys.platform == "win32" else "step2glb"
    path = os.path.join(bin_dir, exe)
    if os.path.isfile(path):
        # Ensure executable bit is set on Mac/Linux
        if sys.platform != "win32":
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return path
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  Properties
# ─────────────────────────────────────────────────────────────────────────────

class MorramaImportSettings(PropertyGroup):

    # ── Scale ─────────────────────────────────────────────────────────────────
    # step2glb reads the STEP file's declared unit and outputs metres into the
    # GLB, so Blender receives correctly-scaled geometry automatically.
    # The user can override if a file's declared unit is wrong.
    scale_mode: EnumProperty(
        name="Scale override",
        items=[
            ("AUTO",    "Auto (recommended)",
             "Trust the unit declared in the STEP file — correct for all "
             "modern CAD exports from Fusion 360, SolidWorks, Rhino, Onshape"),
            ("MM_TO_M", "Force mm → m",
             "Override: treat as millimetres regardless of file header"),
            ("CM_TO_M", "Force cm → m",
             "Override: treat as centimetres regardless of file header"),
            ("MANUAL",  "Manual factor",
             "Apply a custom multiplier to the imported scale"),
        ],
        default="AUTO",
    )

    manual_scale: FloatProperty(
        name="Scale factor",
        default=1.0, min=0.000001, max=1000.0, precision=6,
    )

    apply_scale: BoolProperty(
        name="Apply scale transform",
        description="Apply scale so objects read 1.0 in the transform panel",
        default=True,
    )

    # ── Mesh quality ──────────────────────────────────────────────────────────
    quality: EnumProperty(
        name="Mesh quality",
        description="Triangle density for the converted mesh. Higher quality = "
                    "more polygons, slower conversion.",
        items=[
            ("1", "Draft",    "Very coarse — fast preview"),
            ("2", "Low",      "Low poly — good for early-stage layout"),
            ("3", "Medium",   "Balanced — recommended for most work"),
            ("4", "High",     "Fine detail — use for hero shots"),
            ("5", "Maximum",  "Maximum detail — slow, high memory"),
        ],
        default="3",
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

# Quality presets: (linear_deflection_mm, angular_deflection_deg)
_QUALITY_PARAMS = {
    "1": (4.0,   35.0),
    "2": (1.0,   20.0),
    "3": (0.3,   15.0),
    "4": (0.1,   10.0),
    "5": (0.05,   5.0),
}

def _build_conversion_cmd(exe, step_path, glb_path, quality):
    lin, ang = _QUALITY_PARAMS[quality]
    ang_rad = math.radians(ang)
    return [
        exe,
        step_path,
        glb_path,
        "--linear",  str(lin),
        "--angular", str(ang_rad),
    ]


def _scale_factor(s):
    return {"AUTO": 1.0, "MM_TO_M": 0.001,
            "CM_TO_M": 0.01, "MANUAL": s.manual_scale}[s.scale_mode]


def _active_collection():
    """The collection currently active in the outliner (where new data lands)."""
    alc = bpy.context.view_layer.active_layer_collection
    if alc is not None:
        return alc.collection
    return bpy.context.scene.collection


def _link_only_to(obj, collection):
    """Unlink obj from every collection, then link to `collection`."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)


def _rename_to_real_part_names(mesh_objs):
    """step2glb places the assembly-occurrence label (e.g. NAUO1) on the object
    and the real part name (e.g. Fillet3) on the mesh datablock. Promote the
    real name onto the object so downstream tooling (and the user) sees it."""
    for o in mesh_objs:
        if o.data and o.data.name:
            o.name = o.data.name


def _world_bbox_base(objs):
    """Return (centre_x, centre_y, min_z) of the combined world-space bounding
    box of the mesh objects — i.e. the bottom-centre 'base' point."""
    xs, ys, zs = [], [], []
    for o in objs:
        if o.type != "MESH":
            continue
        for corner in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(corner)
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
    if not xs:
        return mathutils.Vector((0.0, 0.0, 0.0))
    return mathutils.Vector((
        (min(xs) + max(xs)) * 0.5,
        (min(ys) + max(ys)) * 0.5,
        min(zs),
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Main import operator
# ─────────────────────────────────────────────────────────────────────────────

class MORRAMA_OT_ImportStep(Operator, ImportHelper):
    """Import a STEP/STP file — converts via step2glb then imports as GLB"""
    bl_idname  = "morrama.import_step"
    bl_label   = "Import STEP / STP"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".step"
    filter_glob: StringProperty(
        default="*.step;*.stp;*.STEP;*.STP", options={"HIDDEN"})

    def execute(self, context):
        s   = context.scene.morrama_import
        exe = _step2glb_path()

        # ── Guard: binary must exist ──────────────────────────────────────────
        if exe is None:
            self.report({"ERROR"},
                "step2glb binary not found in the add-on's bin/ folder.\n"
                "Please reinstall the add-on from the original zip file.")
            return {"CANCELLED"}

        if not os.path.isfile(self.filepath):
            self.report({"ERROR"}, f"File not found: {self.filepath}")
            return {"CANCELLED"}

        base_name = os.path.splitext(os.path.basename(self.filepath))[0]

        # ── Step 1: convert STEP → GLB via step2glb ───────────────────────────
        tmpdir  = tempfile.mkdtemp(prefix="morrama_step_")
        glb_out = os.path.join(tmpdir, "converted.glb")

        cmd = _build_conversion_cmd(exe, self.filepath, glb_out, s.quality)
        print(f"[Morrama] Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,   # 5 min max
            )
        except subprocess.TimeoutExpired:
            self.report({"ERROR"},
                "Conversion timed out after 5 minutes.\n"
                "Try a lower mesh quality setting.")
            return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to run converter: {e}")
            return {"CANCELLED"}

        if result.returncode != 0 or not os.path.isfile(glb_out):
            err = (result.stderr or result.stdout or "no output").strip()[-300:]
            self.report({"ERROR"},
                f"Conversion failed (exit {result.returncode}):\n{err}")
            print(f"[Morrama] step2glb stderr:\n{result.stderr}")
            return {"CANCELLED"}

        print(f"[Morrama] Converted to GLB: {glb_out}")

        # ── Step 2: import GLB — always works, built into Blender 4.x ─────────
        before = set(bpy.data.objects)

        try:
            bpy.ops.import_scene.gltf(filepath=glb_out)
        except Exception as e:
            self.report({"ERROR"}, f"GLB import failed: {e}")
            return {"CANCELLED"}
        finally:
            try:
                os.remove(glb_out)
                os.rmdir(tmpdir)
            except Exception:
                pass

        new_objs   = list(set(bpy.data.objects) - before)
        mesh_objs  = [o for o in new_objs if o.type == "MESH"]

        if not mesh_objs:
            self.report({"WARNING"},
                "Conversion succeeded but no mesh objects were created.\n"
                "The STEP file may contain only assembly structure with no geometry.")
            return {"FINISHED"}

        # ── Step 3: Morrama post-processing ───────────────────────────────────

        # 3a. Promote real part names onto the objects.
        _rename_to_real_part_names(mesh_objs)

        # 3b. Free the meshes from any step2glb parenting (keep world transform)
        #     and discard step2glb's own empties — we build a clean root ourselves.
        for o in mesh_objs:
            if o.parent is not None:
                mw = o.matrix_world.copy()
                o.parent = None
                o.matrix_world = mw
        for o in new_objs:
            if o.type == "EMPTY":
                bpy.data.objects.remove(o, do_unlink=True)
        context.view_layer.update()

        # 3c. Apply the scale override directly to the geometry (about the world
        #     origin), then optionally bake it so the root empty stays a clean
        #     handle. The glTF importer already converts the source up-axis to
        #     Blender's Z-up, so no rotation correction is needed here.
        factor = _scale_factor(s)
        if factor != 1.0:
            S = mathutils.Matrix.Scale(factor, 4)
            for o in mesh_objs:
                o.matrix_world = S @ o.matrix_world
            context.view_layer.update()
            if s.apply_scale:
                bpy.ops.object.select_all(action="DESELECT")
                for o in mesh_objs:
                    o.select_set(True)
                context.view_layer.objects.active = mesh_objs[0]
                bpy.ops.object.transform_apply(
                    location=False, rotation=False, scale=True)
                context.view_layer.update()

        # 3d. Create the single root empty at the model's base (bottom-centre).
        base = _world_bbox_base(mesh_objs)
        root = bpy.data.objects.new(base_name, None)  # None data → EMPTY
        root.empty_display_type = "PLAIN_AXES"
        context.scene.collection.objects.link(root)
        root.location = base
        context.view_layer.update()

        # 3e. Parent every mesh to the root, preserving world transforms.
        root_inv = root.matrix_world.inverted()
        for o in mesh_objs:
            o.parent = root
            o.matrix_parent_inverse = root_inv

        # 3f. Move the whole import into a file-named collection placed under
        #     whatever collection is active in the outliner.
        parent_col = _active_collection()
        file_col   = bpy.data.collections.new(base_name)
        parent_col.children.link(file_col)
        for o in [root] + mesh_objs:
            _link_only_to(o, file_col)

        # 3g. Frame imported geometry in the viewport (best-effort).
        try:
            bpy.ops.object.select_all(action="DESELECT")
            for o in mesh_objs:
                o.select_set(True)
            context.view_layer.objects.active = mesh_objs[0]
            bpy.ops.view3d.view_selected()
        except Exception:
            pass

        self.report({"INFO"},
            f"Morrama: imported {len(mesh_objs)} object(s) from "
            f"'{os.path.basename(self.filepath)}'")

        return {"FINISHED"}


# ─────────────────────────────────────────────────────────────────────────────
#  N-Panel
# ─────────────────────────────────────────────────────────────────────────────

class MORRAMA_PT_ImportPanel(Panel):
    bl_label       = "STEP Import"
    bl_idname      = "MORRAMA_PT_import_panel"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Vizable"

    def draw(self, context):
        layout = self.layout
        s      = context.scene.morrama_import
        exe    = _step2glb_path()

        # ── Status ────────────────────────────────────────────────────────────
        box = layout.box()
        if exe:
            box.label(text="Converter: ready", icon="CHECKMARK")
        else:
            col = box.column(align=True)
            col.label(text="step2glb binary missing", icon="ERROR")
            col.label(text="Reinstall from the original zip.")

        layout.separator()

        # ── Import button ─────────────────────────────────────────────────────
        row = layout.row()
        row.enabled = exe is not None
        row.scale_y = 1.5
        row.operator("morrama.import_step",
                      text="Import STEP / STP", icon="FILE_3D")

        layout.separator()

        # ── Quality ───────────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Mesh quality", icon="MESH_DATA")
        box.prop(s, "quality", text="")

        # ── Scale ─────────────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Scale", icon="OBJECT_ORIGIN")
        box.prop(s, "scale_mode", text="")
        if s.scale_mode == "MANUAL":
            box.prop(s, "manual_scale")
        if s.scale_mode != "AUTO":
            box.prop(s, "apply_scale")

        layout.separator()
        layout.label(text="Imports as: file-named collection +", icon="INFO")
        layout.label(text="root empty at model base.")
        layout.label(text="Converter: step2glb (OpenCASCADE)", icon="INFO")


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

_classes = (
    MorramaImportSettings,
    MORRAMA_OT_ImportStep,
    MORRAMA_PT_ImportPanel,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.morrama_import = bpy.props.PointerProperty(
        type=MorramaImportSettings)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.morrama_import


if __name__ == "__main__":
    register()
