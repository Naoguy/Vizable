import bpy
from ..utils.collections import (
    ensure_collection, move_to_collection,
    COL_COLOR_CAMERAS, COL_COLOR_LIGHTS, COL_COLOR_TARGETS,
)
from .cameras import CAMERAS_COLLECTION
from .lights  import LIGHTS_COLLECTION
from .empties import TARGETS_COLLECTION


class VIZABLE_OT_organise_scene(bpy.types.Operator):
    """Move all cameras, lights, and Vizable target empties into their Vizable collections"""
    bl_idname = "vizable.organise_scene"
    bl_label = "Sort into Collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam_col    = ensure_collection(CAMERAS_COLLECTION, color_tag=COL_COLOR_CAMERAS)
        light_col  = ensure_collection(LIGHTS_COLLECTION,  color_tag=COL_COLOR_LIGHTS)
        target_col = ensure_collection(TARGETS_COLLECTION, color_tag=COL_COLOR_TARGETS)

        moved = {'cameras': 0, 'lights': 0, 'targets': 0}

        for obj in context.scene.objects:
            if obj.type == 'CAMERA':
                if cam_col.name not in [c.name for c in obj.users_collection]:
                    move_to_collection(obj, cam_col)
                    moved['cameras'] += 1

            elif obj.type == 'LIGHT':
                if light_col.name not in [c.name for c in obj.users_collection]:
                    move_to_collection(obj, light_col)
                    moved['lights'] += 1

            elif obj.type == 'EMPTY' and obj.name.startswith("Vizable "):
                if target_col.name not in [c.name for c in obj.users_collection]:
                    move_to_collection(obj, target_col)
                    moved['targets'] += 1

        parts = []
        if moved['cameras']:
            parts.append(f"{moved['cameras']} camera{'s' if moved['cameras'] != 1 else ''}")
        if moved['lights']:
            parts.append(f"{moved['lights']} light{'s' if moved['lights'] != 1 else ''}")
        if moved['targets']:
            parts.append(f"{moved['targets']} target{'s' if moved['targets'] != 1 else ''}")

        if parts:
            self.report({'INFO'}, "Sorted: " + ", ".join(parts))
        else:
            self.report({'INFO'}, "Everything is already organised")

        return {'FINISHED'}


classes = [VIZABLE_OT_organise_scene]
