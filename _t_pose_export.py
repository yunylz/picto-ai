import bpy
import json
import os
from mathutils import Vector, Euler, Quaternion

# Output paths
render_output_path = "//t_pose_render.png"
json_output_path = "//rig_data.json"

def collect_rig_data():
    """Collect detailed information about the rig and its bones"""
    
    # Ensure we're in object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get the armature
    rig = bpy.data.objects.get("rig")
    if not rig:
        raise Exception("Rig not found in the scene")
    
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    
    # Enter pose mode
    bpy.ops.object.mode_set(mode='POSE')
    
    # Collect rig data
    rig_data = {
        "name": rig.name,
        "custom_properties": {},
        "bones": {}
    }
    
    # Get custom properties
    for prop_name in rig.keys():
        if prop_name != "_RNA_UI" and not prop_name.startswith('_'):
            rig_data["custom_properties"][prop_name] = rig[prop_name]
    
    # Collect bone data
    for bone in rig.pose.bones:
        bone_data = {
            "name": bone.name,
            "parent": bone.parent.name if bone.parent else None,
            "head": [bone.head[0], bone.head[1], bone.head[2]],
            "tail": [bone.tail[0], bone.tail[1], bone.tail[2]],
            "rotation_mode": bone.rotation_mode,
            "location": [bone.location[0], bone.location[1], bone.location[2]],
            "rotation": [],
            "scale": [bone.scale[0], bone.scale[1], bone.scale[2]],
            "custom_properties": {},
            "constraints": [],
            "full_path": get_bone_path(bone)
        }
        
        # Add rotation data based on the mode
        if bone.rotation_mode == 'QUATERNION':
            bone_data["rotation"] = [bone.rotation_quaternion[0], bone.rotation_quaternion[1], 
                                     bone.rotation_quaternion[2], bone.rotation_quaternion[3]]
        else:  # Euler rotations
            bone_data["rotation"] = [bone.rotation_euler[0], bone.rotation_euler[1], bone.rotation_euler[2]]
        
        # Get custom properties
        for prop_name in bone.keys():
            if prop_name != "_RNA_UI" and not prop_name.startswith('_'):
                bone_data["custom_properties"][prop_name] = bone[prop_name]
        
        # Get constraints
        for constraint in bone.constraints:
            constraint_data = {
                "name": constraint.name,
                "type": constraint.type,
                "influence": constraint.influence,
            }
            bone_data["constraints"].append(constraint_data)
        
        rig_data["bones"][bone.name] = bone_data
    
    return rig_data

def get_bone_path(bone):
    """Get the full path to a bone"""
    path = bone.name
    parent = bone.parent
    
    while parent:
        path = parent.name + "/" + path
        parent = parent.parent
    
    return "/rig/Pose/root/" + path

def render_t_pose(output_path):
    """Render the model in T-pose"""
    # Make sure the rig is in its default pose
    rig = bpy.data.objects.get("rig")
    if rig:
        # Clear any pose transformations
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()
    
    # Set up camera and render settings
    camera = bpy.data.objects.get("camera")
    if not camera:
        raise Exception("Camera not found in the scene")
    
    # Position the camera to frame the character
    camera.location = (0, -5, 1.7)
    camera.rotation_euler = (1.5708, 0, 0)
    
    # Set up rendering parameters
    scene = bpy.context.scene
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = output_path
    
    # Make background transparent
    scene.render.film_transparent = True
    
    # Render the image
    bpy.ops.render.render(write_still=True)

def main():
    # Render T-pose
    render_t_pose(render_output_path)
    print(f"T-pose render saved to {bpy.path.abspath(render_output_path)}")
    
    # Collect and save rig data
    rig_data = collect_rig_data()
    
    # Save rig data to JSON
    with open(bpy.path.abspath(json_output_path), 'w') as f:
        json.dump(rig_data, f, indent=4)
    
    print(f"Rig data saved to {bpy.path.abspath(json_output_path)}")

# Run the script
if __name__ == "__main__":
    main()