# Group Maker (Classical Grouping)

Blender addon that creates a null (Empty) as a group parent for selected objects with Keep Transform functionality. Provides classical grouping workflow with flexible pivot placement.

## Features

- **Empty as Group Parent**: Creates an Empty object to act as a group container
- **Keep Transform**: Parents objects while preserving their world transforms (no visual movement)
- **Multiple Pivot Options**: Choose where to place the group pivot point
  - **Bounds Center**: Places pivot at the center of selection's bounding box
  - **Bounds Bottom**: Places pivot at bottom-center (useful for furniture, props)
  - **Active Object**: Uses active object's location and rotation
- **Rotation Alignment**: Option to align group rotation to active object even in bounds modes
- **Hidden Object Support**: Choose whether to include hidden objects in selection
- **Custom Group Names**: Name your groups on creation
- **Safe Parenting**: Data API with operator fallback for reliable transform preservation

## Installation

1. Download the addon folder
2. In Blender, go to Edit → Preferences → Add-ons
3. Click "Install..." and select the folder or zip file
4. Enable "Group Maker (Classical Grouping)" addon

## Usage

1. Select objects you want to group
2. Open the 3D Viewport sidebar (N key)
3. Go to the "Groups" tab
4. Configure group settings:
   - **Name**: Enter a name for the group
   - **Pivot**: Choose pivot placement mode
   - **Align Rotation to Active**: Copy active object's rotation (bounds modes)
   - **Include Hidden**: Whether to include hidden objects
5. Click "Create Group"

### Pivot Modes:

**Bounds Center**
- Group pivot placed at geometric center of all selected objects
- Ideal for symmetric objects or general grouping

**Bounds Bottom**
- Group pivot placed at bottom-center of bounding box
- Perfect for props that sit on ground (furniture, cabinets, etc.)
- Makes it easy to place objects on surfaces

**Active Object**
- Group pivot placed at active object's location
- Group rotation matches active object's rotation
- Useful when you want precise control over group orientation

### Workflow Examples:

**Grouping Furniture:**
1. Select all parts (legs, top, drawers)
2. Set pivot to "Bounds Bottom"
3. Create group
4. Result: Pivot at base, easy to place on floor

**Grouping Character Parts:**
1. Select all body parts
2. Make pelvis/root active object
3. Set pivot to "Active Object"
4. Create group
5. Result: Pivot matches character's root bone location

**Complex Mechanical Assembly:**
1. Select all parts
2. Set pivot to "Bounds Center"
3. Enable "Align Rotation to Active" if needed
4. Create group
5. Result: Centered pivot, optional alignment

## Technical Details

- Uses `matrix_parent_inverse` to preserve world transforms
- Handles objects with or without bounding boxes
- Fallback to operator-based parenting if data API fails
- Respects viewport visibility settings
- Final selection: group only (easy to move/rotate as unit)

## Requirements

- Blender 4.0+

## Author

Viktor Kom

## License

GPL-2.0-or-later

