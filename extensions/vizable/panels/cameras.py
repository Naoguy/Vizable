import bpy
from ..operators.empties import TRACK_CONSTRAINT_NAME


class VIZABLE_PT_cameras(bpy.types.Panel):
    bl_label = "Cameras"
    bl_idname = "VIZABLE_PT_cameras"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vizable"

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        viz    = scene.vizable

        # ── Top action row ───────────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("vizable.camera_new",          text="New Camera",  icon='ADD')
        row.operator("vizable.save_view_as_camera", text="Save View",   icon='VIEW_CAMERA')

        layout.separator(factor=0.5)

        cameras = [obj for obj in scene.objects if obj.type == 'CAMERA']

        if not cameras:
            layout.label(text="No cameras in scene", icon='INFO')
        else:
            for cam_obj in cameras:
                self._draw_camera_row(layout, context, cam_obj)

        # ── Organise footer ──────────────────────────────────────────────
        layout.separator(factor=0.3)
        layout.operator("vizable.organise_scene", text="Sort into Collections", icon='OUTLINER_COLLECTION')

    def _draw_camera_row(self, layout, context, cam_obj):
        scene      = context.scene
        viz        = scene.vizable
        is_active  = (scene.camera == cam_obj)
        is_open    = (viz.active_camera_name == cam_obj.name)

        box = layout.box()

        # ── Header ──────────────────────────────────────────────────────
        header = box.row(align=True)

        # Expand/collapse toggle
        op = header.operator(
            "vizable.camera_select",
            text="",
            icon='TRIA_DOWN' if is_open else 'TRIA_RIGHT',
            emboss=False,
        )
        op.camera_name = cam_obj.name

        # Camera name — click also expands
        op = header.operator(
            "vizable.camera_select",
            text=cam_obj.name,
            emboss=False,
        )
        op.camera_name = cam_obj.name

        # Active scene camera indicator / set-active button
        if is_active:
            header.label(text="", icon='CAMERA_DATA')
        else:
            op = header.operator(
                "vizable.camera_set_active",
                text="",
                icon='OUTLINER_OB_CAMERA',
                emboss=False,
            )
            op.camera_name = cam_obj.name

        # Rename / delete
        op = header.operator("vizable.camera_rename", text="", icon='OUTLINER_DATA_GP_LAYER', emboss=False)
        op.camera_name = cam_obj.name
        op = header.operator("vizable.camera_delete", text="", icon='X', emboss=False)
        op.camera_name = cam_obj.name

        if not is_open:
            return

        # ── Expanded settings ────────────────────────────────────────────
        col = box.column(align=True)
        cam = cam_obj.data

        # Lens
        col.prop(cam, "lens",         text="Focal Length")
        col.prop(cam, "sensor_width", text="Sensor Width")
        row = col.row(align=True)
        row.prop(cam, "clip_start", text="Near")
        row.prop(cam, "clip_end",   text="Far")

        box.separator(factor=0.4)

        # Aspect ratio
        col2 = box.column(align=True)
        col2.label(text="Aspect Ratio")
        col2.prop(cam.vizable, "aspect_preset", text="")
        col2.label(
            text=f"{scene.render.resolution_x} × {scene.render.resolution_y} px"
            if is_active else "",
            icon='INFO' if is_active else 'NONE',
        )

        box.separator(factor=0.4)

        # Depth of field
        self._draw_dof(box, cam_obj)

        box.separator(factor=0.4)

        # Tracking
        self._draw_tracking(box, cam_obj)

    def _draw_dof(self, box, cam_obj):
        cam = cam_obj.data
        dof = cam.dof
        col = box.column(align=True)

        row = col.row(align=True)
        row.prop(dof, "use_dof", text="Depth of Field")

        if not dof.use_dof:
            return

        if dof.focus_object:
            row = col.row(align=True)
            row.prop(dof, "focus_object", text="Focus")
            op = row.operator("vizable.place_empty", text="", icon='EYEDROPPER')
            op.purpose = 'dof'
            row2 = col.row(align=True)
            row2.operator("vizable.camera_clear_dof", text="Clear", icon='X')
        else:
            op = col.operator("vizable.place_empty", text="Set Focus Point", icon='EYEDROPPER')
            op.purpose = 'dof'

        col.prop(dof, "aperture_fstop", text="f-stop")

    def _draw_tracking(self, box, cam_obj):
        col       = box.column(align=True)
        track_con = cam_obj.constraints.get(TRACK_CONSTRAINT_NAME)

        if track_con is None:
            op = col.operator("vizable.place_empty", text="Set Track Target", icon='EYEDROPPER')
            op.purpose = 'track'
            return

        row        = col.row(align=True)
        tracking_on = not track_con.mute
        row.operator(
            "vizable.camera_toggle_tracking",
            text="Tracking",
            icon='TRACKING' if tracking_on else 'TRACKING_CLEAR',
            depress=tracking_on,
        )
        row.prop(track_con, "target", text="")
        op = row.operator("vizable.place_empty", text="", icon='EYEDROPPER')
        op.purpose = 'track'

        col.operator("vizable.camera_clear_tracking", text="Remove Tracking", icon='X')


classes = [VIZABLE_PT_cameras]
