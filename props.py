import bpy

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


class VizableCameraSettings(bpy.types.PropertyGroup):
    aspect_preset: bpy.props.EnumProperty(
        name="Aspect Ratio",
        items=ASPECT_PRESETS,
        default="16:9",
    )


class VizableSceneProps(bpy.types.PropertyGroup):
    camera_list_index: bpy.props.IntProperty(default=0)


classes = [VizableCameraSettings, VizableSceneProps]
