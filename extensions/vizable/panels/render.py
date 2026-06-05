import bpy
from ..operators.render import RESOLUTION_PRESETS, RESOLUTION_LONG_AXIS
from ..props import ASPECT_VALUES


class VIZABLE_PT_render(bpy.types.Panel):
    bl_label = "Render"
    bl_idname = "VIZABLE_PT_render"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vizable"

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        viz    = scene.vizable
        jobs   = viz.render_jobs

        # ── Output directory ────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Output Folder")
        col.prop(viz, "render_output_dir", text="")

        layout.separator(factor=0.5)

        # ── Queue header ────────────────────────────────────────────────
        row = layout.row()
        row.label(text="Render Queue", icon='RENDER_STILL')
        row.operator("vizable.render_job_add", text="", icon='ADD')

        if not jobs:
            layout.label(text="No jobs — press + to add one", icon='INFO')
        else:
            for i, job in enumerate(jobs):
                self._draw_job(layout, context, job, i)

        layout.separator(factor=0.5)

        # ── Render all button ───────────────────────────────────────────
        enabled_count = sum(1 for j in jobs if j.enabled and j.camera_name)
        row = layout.row()
        row.scale_y = 1.4
        sub = row.row()
        sub.enabled = enabled_count > 0
        sub.operator(
            "vizable.render_queue",
            text=f"Render All  ({enabled_count} job{'s' if enabled_count != 1 else ''})",
            icon='RENDER_ANIMATION',
        )

    def _draw_job(self, layout, context, job, index):
        scene = context.scene
        viz   = scene.vizable

        box = layout.box()
        is_active = (viz.active_render_job == index)

        # ── Row 1: enable toggle + name + move + remove ─────────────────
        header = box.row(align=True)
        header.prop(job, "enabled", text="")

        # Click the output name to expand/collapse
        op = header.operator(
            "vizable.render_job_select",
            text=job.output_name or f"Job {index + 1}",
            icon='TRIA_DOWN' if is_active else 'TRIA_RIGHT',
            emboss=False,
        )
        op.index = index

        # Move up/down
        sub = header.row(align=True)
        sub.scale_x = 0.8
        op_up = sub.operator("vizable.render_job_move", text="", icon='TRIA_UP', emboss=False)
        op_up.index     = index
        op_up.direction = 'UP'
        op_dn = sub.operator("vizable.render_job_move", text="", icon='TRIA_DOWN', emboss=False)
        op_dn.index     = index
        op_dn.direction = 'DOWN'

        # Remove
        op_rm = header.operator("vizable.render_job_remove", text="", icon='X', emboss=False)
        op_rm.index = index

        if not is_active:
            # Collapsed: show a one-line summary
            if job.camera_name or job.resolution:
                summary = box.row()
                summary.enabled = False  # read-only appearance
                cam_label = job.camera_name or "—"
                res_label = job.resolution
                w, h = _resolve_dims(job.camera_name, job.resolution)
                summary.label(text=f"{cam_label}  ·  {res_label}  ({w}×{h})", icon='INFO')
            return

        # ── Expanded settings ────────────────────────────────────────────
        col = box.column(align=True)

        # Output name
        col.prop(job, "output_name", text="Name")

        col.separator(factor=0.4)

        # Camera picker
        row = col.row(align=True)
        row.label(text="Camera", icon='CAMERA_DATA')
        # Build a list of camera names for display; use a string prop + manual
        # operator so we don't need a pointer (pointers can't live in CollectionProperty)
        cameras = [o for o in context.scene.objects if o.type == 'CAMERA']
        if cameras:
            row2 = col.row(align=True)
            row2.prop_search(job, "camera_name", context.scene, "objects",
                             text="", icon='OUTLINER_OB_CAMERA')
        else:
            col.label(text="No cameras in scene", icon='ERROR')

        col.separator(factor=0.4)

        # Resolution
        col.label(text="Resolution", icon='IMAGE_DATA')
        col.prop(job, "resolution", text="")

        # Show resolved pixel dimensions
        w, h = _resolve_dims(job.camera_name, job.resolution)
        col.label(text=f"{w} × {h} px", icon='INFO')

        col.separator(factor=0.4)

        # Render this job alone
        op_single = col.operator("vizable.render_job_single", text="Render This Job", icon='RENDER_STILL')
        op_single.index = index


def _resolve_dims(camera_name, resolution_id):
    """Return (w, h) pixel dimensions for a camera + resolution combination."""
    cam_obj = bpy.data.objects.get(camera_name) if camera_name else None
    if cam_obj and cam_obj.type == 'CAMERA':
        aspect_key = cam_obj.data.vizable.aspect_preset
        w_r, h_r   = ASPECT_VALUES.get(aspect_key, (16, 9))
    else:
        w_r, h_r = 16, 9  # fallback

    long_px = RESOLUTION_LONG_AXIS.get(resolution_id, 1920)
    if w_r >= h_r:
        return long_px, round(long_px * h_r / w_r)
    else:
        return round(long_px * w_r / h_r), long_px


classes = [VIZABLE_PT_render]
