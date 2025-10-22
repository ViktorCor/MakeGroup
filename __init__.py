bl_info = {
    "name": "Group Maker (Classical Grouping)",
    "author": "Viktor Kom",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > N-panel > Groups",
    "description": "Creates a null (Empty) as a group parent for selected objects with Keep Transform. Pivot: bounds center / bounds bottom / active object.",
    "category": "Object",
}

from . import group_maker


def register():
    group_maker.register()


def unregister():
    group_maker.unregister()


if __name__ == "__main__":
    register()


