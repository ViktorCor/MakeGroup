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

    full_parenting: BoolProperty(
        name="Full Parenting",
        description="If ON, moves objects to group collection (like manual Set Parent To). If OFF, keeps objects in original collections with visual hierarchy only.",
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

        if self.full_parenting:
            # Full parenting mode: move objects to common collection (like manual Set Parent To)
            # Find the common collection where most objects are located
            collection_counts = {}
            for child in to_parent:
                for collection in child.users_collection:
                    collection_counts[collection] = collection_counts.get(collection, 0) + 1
            
            # Use the collection with most objects, or scene collection as fallback
            target_collection = max(collection_counts.items(), key=lambda x: x[1])[0] if collection_counts else context.scene.collection
            
            # Move the group empty to the target collection (no extra collection needed)
            for collection in grp.users_collection:
                collection.objects.unlink(grp)
            target_collection.objects.link(grp)
            
            # Move all objects to target collection and parent them
            bpy.ops.object.select_all(action='DESELECT')
            for child in to_parent:
                # Remove from current collections
                for collection in child.users_collection:
                    collection.objects.unlink(child)
                # Add to target collection
                target_collection.objects.link(child)
                # Select for parenting
                child.select_set(True)
            
            # Set the group as active object (parent)
            context.view_layer.objects.active = grp
            
            # Use Blender's built-in parent_set operator with keep_transform=True
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        else:
            # Visual hierarchy mode: keep objects in original collections, show visual hierarchy only
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
        col.prop(context.scene, "gm_full_parenting")
        op = col.operator("object.make_group_parent", text="Create Group")
        op.group_name = context.scene.gm_group_name
        op.pivot_mode = context.scene.gm_pivot_mode
        op.align_rotation_to_active = context.scene.gm_align_rot
        op.include_hidden = context.scene.gm_include_hidden
        op.full_parenting = context.scene.gm_full_parenting

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
    bpy.types.Scene.gm_full_parenting = BoolProperty(
        name="Full Parenting",
        description="If ON, moves objects to group collection (like manual Set Parent To). If OFF, keeps objects in original collections with visual hierarchy only.",
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
    del bpy.types.Scene.gm_full_parenting

if __name__ == "__main__":
    register()


