import bpy
import os
from ..props import ASPECT_VALUES

# Resolution presets: (id, label, long_axis_px)
# The "long axis" is applied to whichever dimension is larger given the
# camera's aspect ratio, so a 1920 preset renders 1920×1080 for 16:9
# landscape but 1080×1920 for 9:16 portrait.
RESOLUTION_PRESETS = [
    ("720p",  "720p  — 1280 px",  "", 0),
    ("1080p", "1080p — 1920 px",  "", 1),
    ("1440p", "1440p — 2560 px",  "", 2),
    ("4K",    "4K    — 3840 px",  "", 3),
]

RESOLUTION_LONG_AXIS = {
    "720p":  1280,
    "1080p": 1920,
    "1440p": 2560,
    "4K":    3840,
}


def _apply_resolution(scene, camera_name, resolution_id):
    """Set scene render resolution from a camera's aspect + a resolution preset."""
    cam_obj = bpy.data.objects.get(camera_name)
    if cam_obj is None or cam_obj.type != 'CAMERA':
        return

    aspect_key = cam_obj.data.vizable.aspect_preset
    w_ratio, h_ratio = ASPECT_VALUES.get(aspect_key, (16, 9))
    long_px = RESOLUTION_LONG_AXIS.get(resolution_id, 1920)

    if w_ratio >= h_ratio:
        scene.render.resolution_x = long_px
        scene.render.resolution_y = round(long_px * h_ratio / w_ratio)
    else:
        scene.render.resolution_y = long_px
        scene.render.resolution_x = round(long_px * w_ratio / h_ratio)


def _safe_filename(name: str) -> str:
    """Strip characters that are unsafe in filenames."""
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789-_.()")
    return "".join(c if c in keep else "_" for c in name)


# ── Add job ────────────────────────────────────────────────────────────────

class VIZABLE_OT_render_job_add(bpy.types.Operator):
    """Add a new render job to the queue"""
    bl_idname = "vizable.render_job_add"
    bl_label = "Add Render Job"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        jobs = context.scene.vizable.render_jobs
        job = jobs.add()
        # Sensible defaults
        cam = context.scene.camera
        job.camera_name = cam.name if cam else ""
        job.resolution   = "1080p"
        job.output_name  = f"render_{len(jobs):02d}"
        context.scene.vizable.active_render_job = len(jobs) - 1
        return {'FINISHED'}


# ── Remove job ─────────────────────────────────────────────────────────────

class VIZABLE_OT_render_job_remove(bpy.types.Operator):
    """Remove this render job from the queue"""
    bl_idname = "vizable.render_job_remove"
    bl_label = "Remove Render Job"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        jobs = context.scene.vizable.render_jobs
        if 0 <= self.index < len(jobs):
            jobs.remove(self.index)
            idx = context.scene.vizable.active_render_job
            context.scene.vizable.active_render_job = max(0, min(idx, len(jobs) - 1))
        return {'FINISHED'}


# ── Move job ───────────────────────────────────────────────────────────────

class VIZABLE_OT_render_job_move(bpy.types.Operator):
    """Move a render job up or down in the queue"""
    bl_idname = "vizable.render_job_move"
    bl_label = "Move Render Job"
    bl_options = {'REGISTER', 'UNDO'}

    index:     bpy.props.IntProperty()
    direction: bpy.props.EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])

    def execute(self, context):
        jobs = context.scene.vizable.render_jobs
        n = len(jobs)
        i = self.index
        if self.direction == 'UP' and i > 0:
            jobs.move(i, i - 1)
            context.scene.vizable.active_render_job = i - 1
        elif self.direction == 'DOWN' and i < n - 1:
            jobs.move(i, i + 1)
            context.scene.vizable.active_render_job = i + 1
        return {'FINISHED'}


# ── Render queue ───────────────────────────────────────────────────────────

class VIZABLE_OT_render_queue(bpy.types.Operator):
    """Render all enabled jobs in the queue sequentially"""
    bl_idname = "vizable.render_queue"
    bl_label = "Render Queue"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        jobs  = scene.vizable.render_jobs

        enabled = [j for j in jobs if j.enabled and j.camera_name]
        if not enabled:
            self.report({'WARNING'}, "No enabled jobs with a camera set")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(scene.vizable.render_output_dir)
        if not output_dir:
            output_dir = bpy.path.abspath("//renders/")
        os.makedirs(output_dir, exist_ok=True)

        # Save state we'll restore afterwards
        orig_camera     = scene.camera
        orig_res_x      = scene.render.resolution_x
        orig_res_y      = scene.render.resolution_y
        orig_filepath   = scene.render.filepath
        orig_file_format = scene.render.image_settings.file_format

        scene.render.image_settings.file_format = 'PNG'
        errors = []

        for job in enabled:
            cam_obj = bpy.data.objects.get(job.camera_name)
            if cam_obj is None or cam_obj.type != 'CAMERA':
                errors.append(f"'{job.camera_name}' not found — skipped")
                continue

            scene.camera = cam_obj
            _apply_resolution(scene, job.camera_name, job.resolution)

            safe_name = _safe_filename(job.output_name) or "render"
            scene.render.filepath = os.path.join(output_dir, safe_name)

            bpy.ops.render.render(write_still=True)

        # Restore state
        scene.camera                          = orig_camera
        scene.render.resolution_x             = orig_res_x
        scene.render.resolution_y             = orig_res_y
        scene.render.filepath                 = orig_filepath
        scene.render.image_settings.file_format = orig_file_format

        if errors:
            self.report({'WARNING'}, "Queue done with warnings: " + "; ".join(errors))
        else:
            n = len(enabled)
            self.report({'INFO'}, f"Queue done — {n} render{'s' if n != 1 else ''} written to {output_dir}")

        return {'FINISHED'}


# ── Render single job ──────────────────────────────────────────────────────

class VIZABLE_OT_render_job_single(bpy.types.Operator):
    """Render just this one job"""
    bl_idname = "vizable.render_job_single"
    bl_label = "Render This Job"
    bl_options = {'REGISTER'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        jobs  = scene.vizable.render_jobs
        if not (0 <= self.index < len(jobs)):
            return {'CANCELLED'}

        job = jobs[self.index]
        if not job.camera_name:
            self.report({'WARNING'}, "No camera set for this job")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(scene.vizable.render_output_dir)
        if not output_dir:
            output_dir = bpy.path.abspath("//renders/")
        os.makedirs(output_dir, exist_ok=True)

        orig_camera      = scene.camera
        orig_res_x       = scene.render.resolution_x
        orig_res_y       = scene.render.resolution_y
        orig_filepath    = scene.render.filepath
        orig_file_format = scene.render.image_settings.file_format

        scene.render.image_settings.file_format = 'PNG'
        scene.camera = bpy.data.objects.get(job.camera_name)
        _apply_resolution(scene, job.camera_name, job.resolution)

        safe_name = _safe_filename(job.output_name) or "render"
        scene.render.filepath = os.path.join(output_dir, safe_name)
        bpy.ops.render.render(write_still=True)

        scene.camera                          = orig_camera
        scene.render.resolution_x             = orig_res_x
        scene.render.resolution_y             = orig_res_y
        scene.render.filepath                 = orig_filepath
        scene.render.image_settings.file_format = orig_file_format

        self.report({'INFO'}, f"Rendered to {output_dir}{safe_name}.png")
        return {'FINISHED'}


class VIZABLE_OT_render_job_select(bpy.types.Operator):
    """Expand or collapse a render job in the panel"""
    bl_idname = "vizable.render_job_select"
    bl_label = "Select Render Job"
    bl_options = {'INTERNAL'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        current = context.scene.vizable.active_render_job
        # Toggle: clicking the active job collapses it (use -1 as "none")
        if current == self.index:
            context.scene.vizable.active_render_job = -1
        else:
            context.scene.vizable.active_render_job = self.index
        return {'FINISHED'}


classes = [
    VIZABLE_OT_render_job_add,
    VIZABLE_OT_render_job_remove,
    VIZABLE_OT_render_job_move,
    VIZABLE_OT_render_queue,
    VIZABLE_OT_render_job_single,
    VIZABLE_OT_render_job_select,
]
