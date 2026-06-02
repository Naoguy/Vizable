import bpy
from ..operators.empties import TRACK_CONSTRAINT_NAME
from ..props import kelvin_to_rgb

# Light type icons used throughout the panel
_TYPE_ICON = {
    'AREA':  'LIGHT_AREA',
    'POINT': 'LIGHT_POINT',
    'SPOT':  'LIGHT_SPOT',
    'SUN':   'LIGHT_SUN',
}


class VIZABLE_PT_lights(bpy.types.Panel):
    bl_label = "Lights"
    bl_idname = "VIZABLE_PT_lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vizable"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ── Quick-add row ────────────────────────────────────────────────
        row = layout.row(align=True)
        for ltype in ('AREA', 'POINT', 'SPOT', 'SUN'):
            op = row.operator(
                "vizable.light_add",
                text=ltype.capitalize(),
                icon=_TYPE_ICON[ltype],
            )
            op.light_type = ltype

        layout.separator(factor=0.5)

        # ── Subject picker (used for spherical positioning) ───────────────
        col = layout.column(align=True)
        col.label(text="Subject")
        col.prop(scene.vizable, "subject", text="")

        layout.separator(factor=0.5)

        # ── Light list ───────────────────────────────────────────────────
        lights = [obj for obj in scene.objects if obj.type == 'LIGHT']

        if not lights:
            layout.label(text="No lights in scene", icon='INFO')
        else:
            active_name = scene.vizable.active_light_name

            for light_obj in lights:
                is_active = (light_obj.name == active_name)
                box = layout.box()
                self._draw_light_header(box, light_obj, is_active)
                if is_active:
                    self._draw_light_settings(box, context, light_obj)

        # ── Organise footer ──────────────────────────────────────────────
        layout.separator(factor=0.3)
        layout.operator("vizable.organise_scene", text="Sort into Collections", icon='OUTLINER_COLLECTION')

    # ── Header row ──────────────────────────────────────────────────────

    def _draw_light_header(self, box, light_obj, is_active):
        row = box.row(align=True)
        icon = _TYPE_ICON.get(light_obj.data.type, 'LIGHT')

        # Expand / collapse toggle
        expand_icon = 'TRIA_DOWN' if is_active else 'TRIA_RIGHT'
        op = row.operator(
            "vizable.light_select",
            text=light_obj.name,
            icon=expand_icon,
            emboss=False,
        )
        op.light_name = light_obj.name

        # Light type badge (read-only icon, no label)
        row.label(text="", icon=icon)

        # Rename
        op = row.operator("vizable.light_rename", text="", icon='OUTLINER_DATA_GP_LAYER', emboss=False)
        op.light_name = light_obj.name

        # Delete
        op = row.operator("vizable.light_delete", text="", icon='X', emboss=False)
        op.light_name = light_obj.name

    # ── Settings (expanded) ─────────────────────────────────────────────

    def _draw_light_settings(self, box, context, light_obj):
        lamp = light_obj.data
        viz  = lamp.vizable

        # Strength
        col = box.column(align=True)
        col.prop(lamp, "energy", text="Strength")

        box.separator(factor=0.5)

        # Colour / temperature
        self._draw_colour(box, lamp, viz)

        box.separator(factor=0.5)

        # Size / softness (type-dependent)
        self._draw_size(box, lamp)

        box.separator(factor=0.5)

        # Spherical positioning
        self._draw_position(box, context, light_obj, viz)

        box.separator(factor=0.5)

        # Tracking
        self._draw_tracking(box, light_obj)

    def _draw_colour(self, box, lamp, viz):
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(viz, "use_kelvin", text="Color Temperature")

        if viz.use_kelvin:
            col.prop(viz, "kelvin", text="K", slider=False)
            # Show a read-only colour swatch so the user can see the result
            col.prop(lamp, "color", text="")
        else:
            col.prop(lamp, "color", text="Color")

    def _draw_size(self, box, lamp):
        col = box.column(align=True)
        ltype = lamp.type

        if ltype == 'AREA':
            col.prop(lamp, "size",   text="Width")
            col.prop(lamp, "size_y", text="Height")
        elif ltype in ('POINT', 'SPOT'):
            col.prop(lamp, "shadow_soft_size", text="Radius")
            if ltype == 'SPOT':
                col.separator(factor=0.3)
                col.prop(lamp, "spot_size",  text="Cone Angle")
                col.prop(lamp, "spot_blend", text="Blend")
        elif ltype == 'SUN':
            col.prop(lamp, "angle", text="Angle")

    def _draw_position(self, box, context, light_obj, viz):
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(viz, "use_spherical", text="Position by Angle")

        if not viz.use_spherical:
            return

        sub = col.column(align=True)
        sub.prop(viz, "elevation", text="Elevation °")
        sub.prop(viz, "azimuth",   text="Azimuth °")
        sub.prop(viz, "distance",  text="Distance")

        # Hint about subject
        subject = context.scene.vizable.subject
        hint = f"Around: {subject.name}" if subject else "Around: world origin"
        col.label(text=hint, icon='INFO')

    def _draw_tracking(self, box, light_obj):
        col = box.column(align=True)
        track_con = light_obj.constraints.get(TRACK_CONSTRAINT_NAME)

        if track_con is None:
            op = col.operator(
                "vizable.place_empty",
                text="Set Track Target",
                icon='EYEDROPPER',
            )
            op.purpose = 'track'
            op.target_object_name = light_obj.name
            return

        tracking_on = not track_con.mute
        row = col.row(align=True)

        op = row.operator(
            "vizable.light_toggle_tracking",
            text="Tracking",
            icon='TRACKING' if tracking_on else 'TRACKING_CLEAR',
            depress=tracking_on,
        )
        op.light_name = light_obj.name

        row.prop(track_con, "target", text="")

        op = row.operator("vizable.place_empty", text="", icon='EYEDROPPER')
        op.purpose = 'track'
        op.target_object_name = light_obj.name

        op = col.operator(
            "vizable.light_clear_tracking",
            text="Remove Tracking",
            icon='X',
        )
        op.light_name = light_obj.name


classes = [VIZABLE_PT_lights]
