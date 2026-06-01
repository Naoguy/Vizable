import bpy


def bake_and_remove_constraint(obj: bpy.types.Object, constraint_name: str) -> bool:
    """Remove a constraint while preserving the object's current evaluated orientation.

    Captures the fully-evaluated world matrix (with the constraint active), removes
    the constraint, then writes the matrix back so the object stays exactly where it
    was pointing.  Works correctly whether or not the object is parented.

    Returns True if the constraint was found and removed, False otherwise.
    """
    con = obj.constraints.get(constraint_name)
    if con is None:
        return False

    # Capture the constrained orientation before touching anything
    depsgraph = bpy.context.evaluated_depsgraph_get()
    baked_matrix = obj.evaluated_get(depsgraph).matrix_world.copy()

    # Hold a reference to the target empty before the constraint is gone
    target_empty = con.target

    # Remove the constraint
    obj.constraints.remove(con)

    # Restore orientation — matrix_world setter decomposes into local space,
    # correctly accounting for any parent transform
    obj.matrix_world = baked_matrix

    # Delete the tracking empty — it has no purpose without the constraint
    if target_empty and target_empty.type == 'EMPTY':
        bpy.data.objects.remove(target_empty, do_unlink=True)

    return True
