import bpy
from . import props
from .operators import cameras as cam_ops
from .operators import empties as empty_ops
from .operators import lights as light_ops
from .operators import render as render_ops
from .panels import cameras as cam_panel
from .panels import lights as light_panel
from .panels import render as render_panel

_classes = (
    props.classes
    + cam_ops.classes
    + empty_ops.classes
    + light_ops.classes
    + render_ops.classes
    + cam_panel.classes
    + light_panel.classes
    + render_panel.classes
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Camera.vizable = bpy.props.PointerProperty(type=props.VizableCameraSettings)
    bpy.types.Light.vizable  = bpy.props.PointerProperty(type=props.VizableLightSettings)
    bpy.types.Scene.vizable  = bpy.props.PointerProperty(type=props.VizableSceneProps)


def unregister():
    del bpy.types.Scene.vizable
    del bpy.types.Light.vizable
    del bpy.types.Camera.vizable

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
