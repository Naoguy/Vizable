import bpy
from bpy_extras import view3d_utils

TRACK_CONSTRAINT_NAME = "Vizable Track"


class VIZABLE_OT_place_empty(bpy.types.Operator):
    """Click in the viewport to place a target empty for tracking or depth of field"""
    bl_idname = "vizable.place_empty"
    bl_label = "Place Target"
    bl_options = {'REGISTER', 'UNDO'}

    purpose: bpy.props.StringProperty(default='track')  # 'track' or 'dof'

    # Optional: name of the object to attach to.
    # If empty, falls back to context.scene.camera (camera panel behaviour).
    target_object_name: bpy.props.StringProperty(default='')

    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'ERROR'}, "Must be used from the 3D viewport")
            return {'CANCELLED'}

        if self.target_object_name:
            self._target_obj = bpy.data.objects.get(self.target_object_name)
            if self._target_obj is None:
                self.report({'ERROR'}, f"Object '{self.target_object_name}' not found")
                return {'CANCELLED'}
        else:
            self._target_obj = context.scene.camera
            if self._target_obj is None:
                self.report({'ERROR'}, "No active camera in scene")
                return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        context.area.header_text_set("Click to place target  |  Esc to cancel")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            context.area.header_text_set(None)
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            context.area.header_text_set(None)
            location = self._raycast(context, event)
            empty = self._create_empty(context, location)
            self._assign(empty)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def _raycast(self, context, event):
        region = context.region
        rv3d = context.region_data
        coord = (event.mouse_region_x, event.mouse_region_y)
        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)

        depsgraph = context.evaluated_depsgraph_get()
        hit, location, *_ = context.scene.ray_cast(depsgraph, origin, direction)
        return location if hit else origin + direction * 2.0

    def _create_empty(self, context, location):
        target_name = self._target_obj.name
        label = "DOF" if self.purpose == 'dof' else "Track"
        empty_name = f"Vizable {label} — {target_name}"

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='SPHERE', radius=0.05, location=location)
        empty = context.active_object
        empty.name = empty_name
        return empty

    def _assign(self, empty):
        target = self._target_obj

        if self.purpose == 'dof' and target.type == 'CAMERA':
            target.data.dof.focus_object = empty
            target.data.dof.use_dof = True

        elif self.purpose == 'track':
            con = target.constraints.get(TRACK_CONSTRAINT_NAME)
            if con is None:
                con = target.constraints.new('TRACK_TO')
                con.name = TRACK_CONSTRAINT_NAME
            con.target = empty
            con.track_axis = 'TRACK_NEGATIVE_Z'
            con.up_axis = 'UP_Y'
            con.mute = False


classes = [VIZABLE_OT_place_empty]
