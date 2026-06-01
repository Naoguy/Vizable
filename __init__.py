import bpy
from . import props
from .operators import cameras as cam_ops
from .operators import empties as empty_ops
from .panels import cameras as cam_panel

_classes = (
    props.classes
    + cam_ops.classes
    + empty_ops.classes
    + cam_panel.classes
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Camera.vizable = bpy.props.PointerProperty(type=props.VizableCameraSettings)
    bpy.types.Scene.vizable = bpy.props.PointerProperty(type=props.VizableSceneProps)


def unregister():
    del bpy.types.Scene.vizable
    del bpy.types.Camera.vizable

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
