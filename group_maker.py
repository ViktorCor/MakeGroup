import bpy
from mathutils import Vector, Matrix
from bpy.props import EnumProperty, StringProperty, BoolProperty

def get_world_bounds(objs):
    pts = []
    for o in objs:
        try:
            bb = o.bound_box
        except Exception:
            bb = None
        if bb is None:
            # Fallback: use origin as a point
            pts.append(o.matrix_world.translation.copy())
            continue
        for c in bb:
            v = o.matrix_world @ Vector(c)
            pts.append(v)
    if not pts:
        return None, None
    min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return min_v, max_v


class OBJECT_OT_make_group_parent(bpy.types.Operator):
    bl_idname = "object.make_group_parent"
    bl_label = "Create Group Parent"
    bl_options = {'REGISTER', 'UNDO'}

    pivot_mode: EnumProperty(
        name="Pivot",
        items=[
            ('CENTER', "Bounds Center", "Place group at the center of world bounds of selection"),
            ('BOTTOM', "Bounds Bottom", "Place group at bottom-center of world bounds (useful for cabinets, etc.)"),
            ('ACTIVE', "Active Object", "Place group at active object's location+rotation (scale forced to 1)")
        ],
        default='CENTER'
    )

    group_name: StringProperty(
        name="Group Name",
        description="Name for the new group (Empty)",
        default="Group"
    )

    align_rotation_to_active: BoolProperty(
        name="Align Rotation to Active (for bounds modes)",
        description="If ON and an active object exists, copy its rotation for the group even when using bounds pivot",
        default=False
    )

    include_hidden: BoolProperty(
        name="Include Hidden Selection",
        description="If OFF, ignores objects hidden in viewport (only affects selection pass).",
        default=True
    )

    def execute(self, context):
        sel = [o for o in context.selected_objects]
        if not sel:
            self.report({'WARNING'}, "Нет выделенных объектов.")
            return {'CANCELLED'}

        # Optionally filter out hidden
        if not self.include_hidden:
            sel = [o for o in sel if not o.hide_get()]

        # Remove potential empties we'll create from сел set later
        active = context.view_layer.objects.active

        # Compute transform for new group empty
        grp_loc = Vector((0.0, 0.0, 0.0))
        grp_rot = (0.0, 0.0, 0.0)  # Euler XYZ by default
        grp_scl = (1.0, 1.0, 1.0)

        if self.pivot_mode in {'CENTER', 'BOTTOM'}:
            min_v, max_v = get_world_bounds(sel)
            if min_v is None:
                self.report({'WARNING'}, "Не удалось вычислить баундбокс выделения.")
                return {'CANCELLED'}
            if self.pivot_mode == 'CENTER':
                grp_loc = (min_v + max_v) * 0.5
            else:
                # bottom-center: center X/Y, min Z
                center_xy = (min_v + max_v) * 0.5
                grp_loc = Vector((center_xy.x, center_xy.y, min_v.z))

            if self.align_rotation_to_active and active is not None and active in sel:
                grp_rot = active.rotation_euler.copy()
        else:  # ACTIVE mode
            if active is None or active not in sel:
                self.report({'INFO'}, "Активный объект недоступен — использую Bounds Center.")
                self.pivot_mode = 'CENTER'
                min_v, max_v = get_world_bounds(sel)
                grp_loc = (min_v + max_v) * 0.5
            else:
                grp_loc = active.matrix_world.translation.copy()
                grp_rot = active.rotation_euler.copy()

        # Create the Empty (group)
        grp = bpy.data.objects.new(self.group_name, None)
        grp.empty_display_type = 'PLAIN_AXES'
        grp.location = grp_loc
        grp.rotation_euler = grp_rot
        grp.scale = grp_scl

        context.scene.collection.objects.link(grp)

        # Parent all selected objects to the new group (keep transform)
        # Avoid parenting the new group to itself if it somehow got selected
        to_parent = [o for o in sel if o != grp]

        # Parent all selected objects to the new group using Blender's built-in command
        # This is equivalent to "Set Parent To (Keep Transform)" from the UI
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select all objects to be parented
        for child in to_parent:
            child.select_set(True)
        
        # Set the group as active object (parent)
        context.view_layer.objects.active = grp
        
        # Use Blender's built-in parent_set operator with keep_transform=True
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        # Final selection: select group only, set active to group
        bpy.ops.object.select_all(action='DESELECT')
        grp.select_set(True)
        context.view_layer.objects.active = grp

        self.report({'INFO'}, f"Создана группа '{grp.name}' и привязано объектов: {len(to_parent)}.")
        return {'FINISHED'}

class VIEW3D_PT_group_maker(bpy.types.Panel):
    bl_label = "Group Maker"
    bl_idname = "VIEW3D_PT_group_maker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Groups"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Create Group Parent")
        col.prop(context.scene, "gm_group_name")
        col.prop(context.scene, "gm_pivot_mode", text="Pivot")
        col.prop(context.scene, "gm_align_rot")
        col.prop(context.scene, "gm_include_hidden")
        op = col.operator("object.make_group_parent", text="Create Group")
        op.group_name = context.scene.gm_group_name
        op.pivot_mode = context.scene.gm_pivot_mode
        op.align_rotation_to_active = context.scene.gm_align_rot
        op.include_hidden = context.scene.gm_include_hidden

def register_props():
    bpy.types.Scene.gm_group_name = StringProperty(
        name="Name",
        default="Group"
    )
    bpy.types.Scene.gm_pivot_mode = EnumProperty(
        name="Pivot",
        items=[
            ('CENTER', "Bounds Center", ""),
            ('BOTTOM', "Bounds Bottom", ""),
            ('ACTIVE', "Active Object", ""),
        ],
        default='CENTER'
    )
    bpy.types.Scene.gm_align_rot = BoolProperty(
        name="Align Rotation to Active",
        default=False
    )
    bpy.types.Scene.gm_include_hidden = BoolProperty(
        name="Include Hidden",
        default=True
    )

classes = (
    OBJECT_OT_make_group_parent,
    VIEW3D_PT_group_maker,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    register_props()

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    # Clean up props
    del bpy.types.Scene.gm_group_name
    del bpy.types.Scene.gm_pivot_mode
    del bpy.types.Scene.gm_align_rot
    del bpy.types.Scene.gm_include_hidden

if __name__ == "__main__":
    register()


