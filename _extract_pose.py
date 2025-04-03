# extract_pose.py - Extract pose from image and save skeleton visualization
import cv2
import mediapipe as mp
import numpy as np
import json
import argparse
import math
import os

def extract_pose_from_image(image_path, output_json_path):
    """Extract pose landmarks from the input image using MediaPipe and save skeleton visualization"""
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        raise Exception(f"Could not read image at {image_path}")
    
    # Convert to RGB for MediaPipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process with MediaPipe
    with mp_pose.Pose(static_image_mode=True, model_complexity=2, 
                     min_detection_confidence=0.5) as pose:
        results = pose.process(image_rgb)
    
    if not results.pose_landmarks:
        raise Exception("No pose detected in the image")
    
    # Extract landmarks
    landmarks = [(lm.x, lm.y, lm.z, lm.visibility) for lm in results.pose_landmarks.landmark]
    
    # Create a skeleton visualization (512x512)
    # Instead of a blank image, use a white background
    skeleton_image = np.ones((512, 512, 3), dtype=np.uint8) * 255
    
    # Draw the pose skeleton on the image
    mp_drawing.draw_landmarks(
        skeleton_image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
    )
    
    # Add some text to the image
    cv2.putText(skeleton_image, 'Pose Skeleton', (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Save skeleton visualization
    skeleton_output_path = os.path.splitext(output_json_path)[0] + "_skeleton.png"
    cv2.imwrite(skeleton_output_path, skeleton_image)
    print(f"Skeleton visualization saved to {skeleton_output_path}")
    
    # Convert landmarks to rotations for Blender bones based on your rig structure
    pose_data = {}
    
    # Map MediaPipe landmarks to bone rotations for your specific rig
    bone_mapping = {
        # Main body
        "root": (23, 24, 11),  # hip center
        "pelvis": (23, 24, 12),
        
        # Spine chain
        "spine1": (23, 11, 12),
        "spine2": (11, 12, 0),
        "spine3": (11, 12, 0),
        "spine4": (0, 11, 12),
        
        # Head
        "head": (11, 0, 12),
        
        # Left arm chain (IK)
        "shoulder.L": (11, 13, 15),
        "upperarm.L": (11, 13, 15),
        "arm.L": (13, 15, 17),
        "hand.L": (15, 17, 19),
        
        # Right arm chain (IK)
        "shoulder.R": (12, 14, 16),
        "upperarm.R": (12, 14, 16),
        "arm.R": (14, 16, 18),
        "hand.R": (16, 18, 20),
        
        # Left arm chain (FK)
        "shoulder-fk.L": (11, 13, 15),
        "upperarm-fk.L": (11, 13, 15),
        "arm-fk.L": (13, 15, 17),
        "hand-fk.L": (15, 17, 19),
        
        # Right arm chain (FK)
        "shoulder-fk.R": (12, 14, 16),
        "upperarm-fk.R": (12, 14, 16),
        "arm-fk.R": (14, 16, 18),
        "hand-fk.R": (16, 18, 20),
        
        # Left leg chain (IK)
        "thigh.L": (23, 25, 27),
        "leg.L": (25, 27, 31),
        "foot.L": (27, 31, 29),
        
        # Right leg chain (IK)
        "thigh.R": (24, 26, 28),
        "leg.R": (26, 28, 32),
        "foot.R": (28, 32, 30),
        
        # Left leg chain (FK)
        "thigh-fk.L": (23, 25, 27),
        "leg-fk.L": (25, 27, 31),
        
        # Right leg chain (FK)
        "thigh-fk.R": (24, 26, 28),
        "leg-fk.R": (26, 28, 32),
    }
    
    # Calculate bone rotations from landmarks
    def calculate_bone_quaternion(a, b, c):
        """Calculate quaternion rotation for a bone based on three points"""
        # Vector from joint b to joint a (reversed from standard notation for clarity)
        vec_ba = np.array([a[0] - b[0], a[1] - b[1], a[2] - b[2]])
        
        # Vector from joint b to joint c
        vec_bc = np.array([c[0] - b[0], c[1] - b[1], c[2] - b[2]])
        
        # Normalize vectors
        if np.linalg.norm(vec_ba) > 0:
            vec_ba = vec_ba / np.linalg.norm(vec_ba)
        if np.linalg.norm(vec_bc) > 0:
            vec_bc = vec_bc / np.linalg.norm(vec_bc)
        
        # Create a rotation quaternion (simplified)
        # This is a placeholder - in reality, you'd compute this more robustly
        w = 0.5 + 0.5 * np.dot(vec_ba, vec_bc)
        x = np.cross(vec_ba, vec_bc)[0] * 0.5
        y = np.cross(vec_ba, vec_bc)[1] * 0.5
        z = np.cross(vec_ba, vec_bc)[2] * 0.5
        
        # Normalize quaternion
        magnitude = math.sqrt(w**2 + x**2 + y**2 + z**2)
        if magnitude > 0:
            w /= magnitude
            x /= magnitude
            y /= magnitude
            z /= magnitude
        else:
            w, x, y, z = 1, 0, 0, 0
        
        return [w, x, y, z]
    
    # Process bone rotations
    for bone_name, (idx_a, idx_b, idx_c) in bone_mapping.items():
        if idx_a < len(landmarks) and idx_b < len(landmarks) and idx_c < len(landmarks):
            a = landmarks[idx_a][:3]  # Ignore visibility
            b = landmarks[idx_b][:3]
            c = landmarks[idx_c][:3]
            
            # Skip if visibility is too low
            if len(landmarks[idx_a]) > 3 and landmarks[idx_a][3] < 0.5:
                continue
            if len(landmarks[idx_b]) > 3 and landmarks[idx_b][3] < 0.5:
                continue
            if len(landmarks[idx_c]) > 3 and landmarks[idx_c][3] < 0.5:
                continue
            
            pose_data[bone_name] = calculate_bone_quaternion(a, b, c)
    
    # Add IK targets with locations
    ik_targets = {
        "foot.L": 27,  # Left ankle
        "foot.R": 28,  # Right ankle
        "hand.L": 15,  # Left wrist
        "hand.R": 16   # Right wrist
    }
    
    for bone_name, idx in ik_targets.items():
        if idx < len(landmarks) and landmarks[idx][3] > 0.5:  # Check visibility
            # Scale coordinates to match Blender scale
            x = (landmarks[idx][0] - 0.5) * 4  # Scale from [0,1] to [-2,2]
            y = (0.5 - landmarks[idx][1]) * 4  # Flip Y and scale
            z = landmarks[idx][2] * 2 + 1      # Adjust height
            
            pose_data[f"{bone_name}_location"] = [x, y, z]
    
    # Save to JSON file
    with open(output_json_path, 'w') as f:
        json.dump(pose_data, f, indent=4)
    
    print(f"Pose data saved to {output_json_path}")
    return output_json_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract pose from an image')
    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('output_json', help='Path to save the pose data as JSON')
    
    args = parser.parse_args()
    extract_pose_from_image(args.image_path, args.output_json)