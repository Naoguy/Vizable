import bpy


def ensure_collection(name: str, parent: bpy.types.Collection = None) -> bpy.types.Collection:
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)

    parent = parent or bpy.context.scene.collection
    if col.name not in parent.children:
        parent.children.link(col)

    return col


def move_to_collection(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
