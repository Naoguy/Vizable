import bpy
import math

ASPECT_PRESETS = [
    ("16:9",  "16:9",          "", 0),
    ("4:3",   "4:3",           "", 1),
    ("3:2",   "3:2",           "", 2),
    ("1:1",   "1:1 Square",    "", 3),
    ("9:16",  "9:16 Portrait", "", 4),
    ("3:4",   "3:4 Portrait",  "", 5),
]

ASPECT_VALUES = {
    "16:9": (16, 9),
    "4:3":  (4,  3),
    "3:2":  (3,  2),
    "1:1":  (1,  1),
    "9:16": (9,  16),
    "3:4":  (3,  4),
}

# ---------------------------------------------------------------------------
# Kelvin ↔ colour helpers  (Tanner Helland approximation)
# ---------------------------------------------------------------------------

def kelvin_to_rgb(kelvin: float) -> tuple:
    """Return a linear (r, g, b) tuple for a colour temperature in Kelvin."""
    temp = max(1000.0, min(10000.0, kelvin)) / 100.0

    # Red
    if temp <= 66.0:
        r = 1.0
    else:
        r = 329.698727446 * ((temp - 60.0) ** -0.1332047592) / 255.0
        r = max(0.0, min(1.0, r))

    # Green
    if temp <= 66.0:
        g = (99.4708025861 * math.log(temp) - 161.1195681661) / 255.0
    else:
        g = 288.1221695283 * ((temp - 60.0) ** -0.0755148492) / 255.0
    g = max(0.0, min(1.0, g))

    # Blue
    if temp >= 66.0:
        b = 1.0
    elif temp <= 19.0:
        b = 0.0
    else:
        b = (138.5177312231 * math.log(temp - 10.0) - 305.0447927307) / 255.0
        b = max(0.0, min(1.0, b))

    return (r, g, b)


# ---------------------------------------------------------------------------
# Internal helpers for update callbacks
# ---------------------------------------------------------------------------

def _find_camera_obj(cam_settings):
    """Return the Object that owns the given VizableCameraSettings instance."""
    for cam in bpy.data.cameras:
        try:
            if cam.vizable == cam_settings:
                for obj in bpy.data.objects:
                    if obj.type == 'CAMERA' and obj.data == cam:
                        return obj
        except Exception:
            pass
    return None


def _update_aspect(self, context):
    """Apply the selected aspect preset to the scene render resolution.

    Only fires for the active scene camera so switching to a different camera
    automatically updates the viewport frame to match that camera's aspect.
    Keeps the longer axis at 1920 px; the render panel will later add
    resolution-budget presets on top of this.
    """
    if context is None:
        return
    obj = _find_camera_obj(self)
    if obj is None or context.scene.camera != obj:
        return
    w, h = ASPECT_VALUES[self.aspect_preset]
    if w >= h:
        context.scene.render.resolution_x = 1920
        context.scene.render.resolution_y = round(1920 * h / w)
    else:
        context.scene.render.resolution_y = 1920
        context.scene.render.resolution_x = round(1920 * w / h)


def _find_light_obj(light_settings):
    """Return the Object that owns the given VizableLightSettings instance."""
    for lamp in bpy.data.lights:
        try:
            if lamp.vizable == light_settings:
                for obj in bpy.data.objects:
                    if obj.type == 'LIGHT' and obj.data == lamp:
                        return obj
        except Exception:
            pass
    return None


def _update_kelvin(self, context):
    if not self.use_kelvin:
        return
    obj = _find_light_obj(self)
    if obj is None:
        return
    obj.data.color = kelvin_to_rgb(self.kelvin)


def _update_spherical(self, context):
    if not self.use_spherical:
        return
    obj = _find_light_obj(self)
    if obj is None:
        return

    el = math.radians(self.elevation)
    az = math.radians(self.azimuth)
    d  = self.distance

    try:
        subject = context.scene.vizable.subject
        cx, cy, cz = (subject.location.x, subject.location.y, subject.location.z) \
                     if subject else (0.0, 0.0, 0.0)
    except Exception:
        cx, cy, cz = 0.0, 0.0, 0.0

    obj.location = (
        cx + d * math.cos(el) * math.cos(az),
        cy + d * math.cos(el) * math.sin(az),
        cz + d * math.sin(el),
    )


# ---------------------------------------------------------------------------
# Property groups
# ---------------------------------------------------------------------------

class VizableCameraSettings(bpy.types.PropertyGroup):
    aspect_preset: bpy.props.EnumProperty(
        name="Aspect Ratio",
        items=ASPECT_PRESETS,
        default="16:9",
        update=_update_aspect,
    )


class VizableLightSettings(bpy.types.PropertyGroup):
    # Colour temperature
    use_kelvin: bpy.props.BoolProperty(
        name="Color Temperature",
        description="Drive the light colour from a Kelvin temperature value",
        default=False,
        update=_update_kelvin,
    )
    kelvin: bpy.props.FloatProperty(
        name="Temperature",
        description="Colour temperature in Kelvin (1 000 – 10 000 K)",
        min=1000.0, max=10000.0, default=5600.0, step=100,
        update=_update_kelvin,
    )

    # Spherical positioning
    use_spherical: bpy.props.BoolProperty(
        name="Position by Angle",
        description="Position the light using elevation / azimuth / distance around the subject",
        default=False,
        update=_update_spherical,
    )
    elevation: bpy.props.FloatProperty(
        name="Elevation",
        description="Angle above the horizon (degrees)",
        min=-90.0, max=90.0, default=45.0,
        update=_update_spherical,
    )
    azimuth: bpy.props.FloatProperty(
        name="Azimuth",
        description="Orbit angle around the subject (degrees, 0 = +X axis)",
        min=0.0, max=360.0, default=0.0,
        update=_update_spherical,
    )
    distance: bpy.props.FloatProperty(
        name="Distance",
        description="Distance from the subject centre",
        min=0.01, default=5.0, soft_max=50.0,
        update=_update_spherical,
    )


class VizableRenderJob(bpy.types.PropertyGroup):
    """One entry in the render queue."""
    enabled: bpy.props.BoolProperty(
        name="Enabled",
        description="Include this job when rendering the full queue",
        default=True,
    )
    output_name: bpy.props.StringProperty(
        name="Output Name",
        description="Filename (without extension) written into the output folder",
        default="render",
    )
    camera_name: bpy.props.StringProperty(
        name="Camera",
        description="Name of the camera object to render from",
        default="",
    )
    resolution: bpy.props.EnumProperty(
        name="Resolution",
        description="Pixel budget; actual width/height is resolved from the camera's aspect ratio",
        items=[
            ("720p",  "720p  — 1280 px",  "", 0),
            ("1080p", "1080p — 1920 px",  "", 1),
            ("1440p", "1440p — 2560 px",  "", 2),
            ("4K",    "4K    — 3840 px",  "", 3),
        ],
        default="1080p",
    )


class VizableSceneProps(bpy.types.PropertyGroup):
    camera_list_index: bpy.props.IntProperty(default=0)
    active_light_name: bpy.props.StringProperty(
        name="Active Light",
        description="Name of the light currently expanded in the Lights panel",
        default="",
    )
    subject: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Subject",
        description="Object at the centre of the scene; used as the origin for spherical light positioning",
    )

    # ── Render queue ───────────────────────────────────────────────────
    render_jobs: bpy.props.CollectionProperty(type=VizableRenderJob)
    active_render_job: bpy.props.IntProperty(
        name="Active Render Job",
        description="Index of the job currently expanded in the Render panel",
        default=0,
    )
    render_output_dir: bpy.props.StringProperty(
        name="Output Folder",
        description="Directory where rendered images are saved "
                    "(use // for a path relative to the .blend file)",
        default="//renders/",
        subtype='DIR_PATH',
    )


classes = [VizableCameraSettings, VizableLightSettings, VizableRenderJob, VizableSceneProps]
