import bpy
import math
from ..utils.collections import ensure_collection, move_to_collection
from ..utils.constraints import bake_and_remove_constraint
from .empties import TRACK_CONSTRAINT_NAME

LIGHTS_COLLECTION = "Vizable Lights"

# Sensible defaults applied when a light is created via Vizable
_LIGHT_DEFAULTS = {
    'AREA':  {'energy': 100.0,  'size': 1.0},
    'POINT': {'energy': 100.0,  'shadow_soft_size': 0.1},
    'SPOT':  {'energy': 200.0,  'shadow_soft_size': 0.1,
               'spot_size': math.radians(45), 'spot_blend': 0.15},
    'SUN':   {'energy': 5.0,    'angle': math.radians(0.53)},  # ~solar diameter
}


class VIZABLE_OT_light_add(bpy.types.Operator):
    """Add a new light with sensible defaults and place it in the Vizable Lights collection"""
    bl_idname = "vizable.light_add"
    bl_label = "Add Light"
    bl_options = {'REGISTER', 'UNDO'}

    light_type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('AREA',  'Area',  'Soft rectangular / disc light',   'LIGHT_AREA',  0),
            ('POINT', 'Point', 'Omnidirectional point light',     'LIGHT_POINT', 1),
            ('SPOT',  'Spot',  'Directional cone light',          'LIGHT_SPOT',  2),
            ('SUN',   'Sun',   'Distant parallel light',          'LIGHT_SUN',   3),
        ],
        default='AREA',
    )

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.light_add(type=self.light_type)
        light_obj = context.active_object

        defaults = _LIGHT_DEFAULTS.get(self.light_type, {})
        for attr, val in defaults.items():
            if hasattr(light_obj.data, attr):
                setattr(light_obj.data, attr, val)

        col = ensure_collection(LIGHTS_COLLECTION)
        move_to_collection(light_obj, col)

        context.scene.vizable.active_light_name = light_obj.name
        return {'FINISHED'}


class VIZABLE_OT_light_select(bpy.types.Operator):
    """Expand this light's settings in the panel"""
    bl_idname = "vizable.light_select"
    bl_label = "Select Light"
    bl_options = {'INTERNAL'}

    light_name: bpy.props.StringProperty()

    def execute(self, context):
        current = context.scene.vizable.active_light_name
        # Toggle: clicking the active light collapses it
        if current == self.light_name:
            context.scene.vizable.active_light_name = ""
        else:
            context.scene.vizable.active_light_name = self.light_name
        return {'FINISHED'}


class VIZABLE_OT_light_delete(bpy.types.Operator):
    """Delete this light from the scene"""
    bl_idname = "vizable.light_delete"
    bl_label = "Delete Light"
    bl_options = {'REGISTER', 'UNDO'}

    light_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        obj = bpy.data.objects.get(self.light_name)
        if obj and obj.type == 'LIGHT':
            if context.scene.vizable.active_light_name == self.light_name:
                context.scene.vizable.active_light_name = ""
            bpy.data.objects.remove(obj, do_unlink=True)
        return {'FINISHED'}


class VIZABLE_OT_light_toggle_tracking(bpy.types.Operator):
    """Toggle the light's Track To constraint on or off"""
    bl_idname = "vizable.light_toggle_tracking"
    bl_label = "Toggle Light Tracking"
    bl_options = {'REGISTER', 'UNDO'}

    light_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.light_name)
        if obj is None or obj.type != 'LIGHT':
            return {'CANCELLED'}
        con = obj.constraints.get(TRACK_CONSTRAINT_NAME)
        if con is None:
            self.report({'INFO'}, "Set a tracking target first")
            return {'CANCELLED'}
        con.mute = not con.mute
        return {'FINISHED'}


class VIZABLE_OT_light_clear_tracking(bpy.types.Operator):
    """Remove the tracking constraint from this light"""
    bl_idname = "vizable.light_clear_tracking"
    bl_label = "Clear Light Tracking"
    bl_options = {'REGISTER', 'UNDO'}

    light_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.light_name)
        if obj is None or obj.type != 'LIGHT':
            return {'CANCELLED'}
        bake_and_remove_constraint(obj, TRACK_CONSTRAINT_NAME)
        return {'FINISHED'}


class VIZABLE_OT_light_rename(bpy.types.Operator):
    """Rename this light"""
    bl_idname = "vizable.light_rename"
    bl_label = "Rename Light"
    bl_options = {'REGISTER', 'UNDO'}

    light_name: bpy.props.StringProperty()
    new_name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, event):
        obj = bpy.data.objects.get(self.light_name)
        if obj:
            self.new_name = obj.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "new_name", text="Name")

    def execute(self, context):
        obj = bpy.data.objects.get(self.light_name)
        if obj and obj.type == 'LIGHT':
            obj.name = self.new_name
            obj.data.name = self.new_name
        return {'FINISHED'}


classes = [
    VIZABLE_OT_light_rename,
    VIZABLE_OT_light_add,
    VIZABLE_OT_light_select,
    VIZABLE_OT_light_delete,
    VIZABLE_OT_light_toggle_tracking,
    VIZABLE_OT_light_clear_tracking,
]
