import bpy
from ..utils.collections import ensure_collection, move_to_collection
from .empties import TRACK_CONSTRAINT_NAME

CAMERAS_COLLECTION = "Vizable Cameras"


class VIZABLE_OT_camera_new(bpy.types.Operator):
    """Add a new camera and place it in the Vizable Cameras collection"""
    bl_idname = "vizable.camera_new"
    bl_label = "New Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.camera_add()
        cam_obj = context.active_object
        col = ensure_collection(CAMERAS_COLLECTION)
        move_to_collection(cam_obj, col)
        context.scene.camera = cam_obj
        return {'FINISHED'}


class VIZABLE_OT_camera_set_active(bpy.types.Operator):
    """Set this camera as the active scene camera"""
    bl_idname = "vizable.camera_set_active"
    bl_label = "Set Active Camera"
    bl_options = {'REGISTER', 'UNDO'}

    camera_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.camera_name)
        if obj and obj.type == 'CAMERA':
            context.scene.camera = obj
        return {'FINISHED'}


class VIZABLE_OT_camera_delete(bpy.types.Operator):
    """Delete this camera from the scene"""
    bl_idname = "vizable.camera_delete"
    bl_label = "Delete Camera"
    bl_options = {'REGISTER', 'UNDO'}

    camera_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        obj = bpy.data.objects.get(self.camera_name)
        if obj and obj.type == 'CAMERA':
            if context.scene.camera == obj:
                # Hand active camera to another camera if one exists
                others = [o for o in context.scene.objects
                          if o.type == 'CAMERA' and o != obj]
                context.scene.camera = others[0] if others else None
            bpy.data.objects.remove(obj, do_unlink=True)
        return {'FINISHED'}


class VIZABLE_OT_save_view_as_camera(bpy.types.Operator):
    """Create a camera that matches the current viewport view"""
    bl_idname = "vizable.save_view_as_camera"
    bl_label = "Save View as Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.camera_add()
        cam_obj = context.active_object
        context.scene.camera = cam_obj
        bpy.ops.view3d.camera_to_view()
        col = ensure_collection(CAMERAS_COLLECTION)
        move_to_collection(cam_obj, col)
        return {'FINISHED'}


class VIZABLE_OT_camera_toggle_tracking(bpy.types.Operator):
    """Toggle the camera's Track To constraint on or off"""
    bl_idname = "vizable.camera_toggle_tracking"
    bl_label = "Toggle Tracking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam_obj = context.scene.camera
        if cam_obj is None:
            return {'CANCELLED'}
        con = cam_obj.constraints.get(TRACK_CONSTRAINT_NAME)
        if con is None:
            self.report({'INFO'}, "Set a tracking target first")
            return {'CANCELLED'}
        con.mute = not con.mute
        return {'FINISHED'}


class VIZABLE_OT_camera_clear_tracking(bpy.types.Operator):
    """Remove the tracking constraint from this camera"""
    bl_idname = "vizable.camera_clear_tracking"
    bl_label = "Clear Tracking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam_obj = context.scene.camera
        if cam_obj is None:
            return {'CANCELLED'}
        con = cam_obj.constraints.get(TRACK_CONSTRAINT_NAME)
        if con:
            cam_obj.constraints.remove(con)
        return {'FINISHED'}


class VIZABLE_OT_camera_clear_dof(bpy.types.Operator):
    """Clear the depth of field focus object"""
    bl_idname = "vizable.camera_clear_dof"
    bl_label = "Clear DOF Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam_obj = context.scene.camera
        if cam_obj is None:
            return {'CANCELLED'}
        cam_obj.data.dof.focus_object = None
        cam_obj.data.dof.use_dof = False
        return {'FINISHED'}


classes = [
    VIZABLE_OT_camera_new,
    VIZABLE_OT_camera_set_active,
    VIZABLE_OT_camera_delete,
    VIZABLE_OT_save_view_as_camera,
    VIZABLE_OT_camera_toggle_tracking,
    VIZABLE_OT_camera_clear_tracking,
    VIZABLE_OT_camera_clear_dof,
]
