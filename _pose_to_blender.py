# pose_to_blender.py - Apply pose data to Blender rig and render
import bpy
import os
import sys
import json
from mathutils import Vector, Quaternion

# Get command line arguments after the "--" 
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # Get args after "--"

# The first argument should be the path to the JSON file with pose data
pose_data_path = argv[0]
output_path = argv[1] if len(argv) > 1 else "//rendered_pose.png"

# Load the pose data
with open(pose_data_path, 'r') as f:
    pose_data = json.load(f)

def apply_pose_to_rig(pose_data):
    """Apply pose landmarks to the Blender rig"""
    # Ensure we're in object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Select the armature
    rig = bpy.data.objects.get("rig")
    if not rig:
        raise Exception("Rig not found in the scene")
    
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    
    # Enter pose mode
    bpy.ops.object.mode_set(mode='POSE')
    
    # First, reset the pose to clear any previous animations
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    
    # Apply rotations to bones
    for bone_name, rotation in pose_data.items():
        if "_location" not in bone_name and bone_name in rig.pose.bones:
            bone = rig.pose.bones[bone_name]
            
            # Set to quaternion rotation mode
            bone.rotation_mode = 'QUATERNION'
            
            # Apply rotation - rotation is a list [w, x, y, z]
            bone.rotation_quaternion = rotation
    
    # Apply IK target locations
    for bone_name, location in pose_data.items():
        if "_location" in bone_name:
            actual_bone_name = bone_name.replace("_location", "")
            if actual_bone_name in rig.pose.bones:
                bone = rig.pose.bones[actual_bone_name]
                
                # Set the location
                bone.location = location
    
    # Update the scene
    bpy.context.view_layer.update()

def setup_camera_and_render(output_path):
    """Set up camera and render the scene"""
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

# Apply the pose and render
apply_pose_to_rig(pose_data)
setup_camera_and_render(output_path)

print(f"Rendered image saved to {output_path}")