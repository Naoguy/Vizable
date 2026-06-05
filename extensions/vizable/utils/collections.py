import bpy

# Blender collection color tags (bl_idname strings used by the color_tag property)
COL_COLOR_CAMERAS = 'COLOR_04'   # blue
COL_COLOR_LIGHTS  = 'COLOR_05'   # yellow
COL_COLOR_TARGETS = 'COLOR_03'   # green


def ensure_collection(
    name: str,
    parent: bpy.types.Collection = None,
    color_tag: str = 'NONE',
) -> bpy.types.Collection:
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)

    # Apply / re-apply color so it's always correct even if someone changed it
    if color_tag != 'NONE':
        col.color_tag = color_tag

    parent = parent or bpy.context.scene.collection
    if col.name not in parent.children:
        parent.children.link(col)

    return col


def move_to_collection(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
