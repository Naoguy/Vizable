import bpy
import os
from ..props import ASPECT_VALUES

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


# ── Helpers ────────────────────────────────────────────────────────────────

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
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789-_.()")
    return "".join(c if c in keep else "_" for c in name)


# ── Module-level queue state ───────────────────────────────────────────────
# Handlers and timers can't hold operator references, so state lives here.

_Q = {
    'jobs':       [],   # list of dicts: {camera_name, resolution, output_name}
    'index':      0,
    'output_dir': '',
    'scene_name': '',
    'errors':     [],
    'orig':       {},   # scene state to restore when done
    'running':    False,
}


def _q_setup(scene, jobs, output_dir):
    _Q['jobs']       = jobs
    _Q['index']      = 0
    _Q['output_dir'] = output_dir
    _Q['scene_name'] = scene.name
    _Q['errors']     = []
    _Q['running']    = True
    _Q['orig']       = {
        'camera':      scene.camera,
        'res_x':       scene.render.resolution_x,
        'res_y':       scene.render.resolution_y,
        'filepath':    scene.render.filepath,
        'file_format': scene.render.image_settings.file_format,
    }
    scene.render.image_settings.file_format = 'PNG'


def _q_restore():
    scene = bpy.data.scenes.get(_Q['scene_name'])
    if scene is None:
        return
    orig = _Q['orig']
    scene.camera                          = orig['camera']
    scene.render.resolution_x             = orig['res_x']
    scene.render.resolution_y             = orig['res_y']
    scene.render.filepath                 = orig['filepath']
    scene.render.image_settings.file_format = orig['file_format']
    _Q['running'] = False


def _q_remove_handlers():
    if _on_render_complete in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(_on_render_complete)
    if _on_render_cancel in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(_on_render_cancel)


def _q_start_next():
    """Timer callback — sets up the next job and fires the render window."""
    scene = bpy.data.scenes.get(_Q['scene_name'])
    if scene is None:
        _q_remove_handlers()
        _q_restore()
        return

    # Skip any jobs whose camera is gone
    while _Q['index'] < len(_Q['jobs']):
        job = _Q['jobs'][_Q['index']]
        cam_obj = bpy.data.objects.get(job['camera_name'])
        if cam_obj and cam_obj.type == 'CAMERA':
            break
        _Q['errors'].append(f"'{job['camera_name']}' not found — skipped")
        _Q['index'] += 1

    if _Q['index'] >= len(_Q['jobs']):
        # All jobs done
        _q_remove_handlers()
        _q_restore()
        n    = len(_Q['jobs'])
        errs = _Q['errors']
        if errs:
            print(f"Vizable Render Queue: done with warnings — " + "; ".join(errs))
        else:
            print(f"Vizable Render Queue: {n} render(s) complete → {_Q['output_dir']}")
        return

    job = _Q['jobs'][_Q['index']]
    scene.camera = bpy.data.objects.get(job['camera_name'])
    _apply_resolution(scene, job['camera_name'], job['resolution'])
    safe_name = _safe_filename(job['output_name']) or 'render'
    scene.render.filepath = os.path.join(_Q['output_dir'], safe_name)

    # Open the normal render window — non-blocking, handler fires when done
    bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)


@bpy.app.handlers.persistent
def _on_render_complete(scene, depsgraph=None):
    if not _Q['running']:
        return
    _Q['index'] += 1
    # Use a timer so we're not inside a render callback when we start the next one
    bpy.app.timers.register(_q_start_next, first_interval=0.2)


@bpy.app.handlers.persistent
def _on_render_cancel(scene, depsgraph=None):
    if not _Q['running']:
        return
    _q_remove_handlers()
    _q_restore()
    print("Vizable Render Queue: cancelled by user")


# ── Add job ────────────────────────────────────────────────────────────────

class VIZABLE_OT_render_job_add(bpy.types.Operator):
    """Add a new render job to the queue"""
    bl_idname = "vizable.render_job_add"
    bl_label = "Add Render Job"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        jobs = context.scene.vizable.render_jobs
        job  = jobs.add()
        cam  = context.scene.camera
        job.camera_name = cam.name if cam else ""
        job.resolution  = "1080p"
        job.output_name = f"render_{len(jobs):02d}"
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
    """Render all enabled jobs sequentially, opening the render window for each"""
    bl_idname = "vizable.render_queue"
    bl_label = "Render Queue"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if _Q['running']:
            self.report({'WARNING'}, "A render queue is already running")
            return {'CANCELLED'}

        scene = context.scene
        jobs  = scene.vizable.render_jobs

        enabled = [
            {'camera_name': j.camera_name,
             'resolution':  j.resolution,
             'output_name': j.output_name}
            for j in jobs if j.enabled and j.camera_name
        ]
        if not enabled:
            self.report({'WARNING'}, "No enabled jobs with a camera set")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(scene.vizable.render_output_dir) or bpy.path.abspath("//renders/")
        os.makedirs(output_dir, exist_ok=True)

        _q_setup(scene, enabled, output_dir)

        # Register handlers to chain jobs
        _q_remove_handlers()  # safety: clear any stale ones
        bpy.app.handlers.render_complete.append(_on_render_complete)
        bpy.app.handlers.render_cancel.append(_on_render_cancel)

        # Kick off the first job via a timer so the operator returns cleanly first
        bpy.app.timers.register(_q_start_next, first_interval=0.1)

        self.report({'INFO'}, f"Starting queue — {len(enabled)} job(s)")
        return {'FINISHED'}


# ── Render single job ──────────────────────────────────────────────────────

class VIZABLE_OT_render_job_single(bpy.types.Operator):
    """Render just this one job, opening the normal render window"""
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

        cam_obj = bpy.data.objects.get(job.camera_name)
        if cam_obj is None or cam_obj.type != 'CAMERA':
            self.report({'WARNING'}, f"Camera '{job.camera_name}' not found")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(scene.vizable.render_output_dir) or bpy.path.abspath("//renders/")
        os.makedirs(output_dir, exist_ok=True)

        # Apply settings
        scene.camera = cam_obj
        _apply_resolution(scene, job.camera_name, job.resolution)
        safe_name = _safe_filename(job.output_name) or "render"
        scene.render.filepath = os.path.join(output_dir, safe_name)
        scene.render.image_settings.file_format = 'PNG'

        # Open the normal render window
        bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
        return {'FINISHED'}


# ── Expand/collapse job ────────────────────────────────────────────────────

class VIZABLE_OT_render_job_select(bpy.types.Operator):
    """Expand or collapse a render job in the panel"""
    bl_idname = "vizable.render_job_select"
    bl_label = "Select Render Job"
    bl_options = {'INTERNAL'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        current = context.scene.vizable.active_render_job
        context.scene.vizable.active_render_job = -1 if current == self.index else self.index
        return {'FINISHED'}


classes = [
    VIZABLE_OT_render_job_add,
    VIZABLE_OT_render_job_remove,
    VIZABLE_OT_render_job_move,
    VIZABLE_OT_render_queue,
    VIZABLE_OT_render_job_single,
    VIZABLE_OT_render_job_select,
]
