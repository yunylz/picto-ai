#!/bin/bash
# Usage: ./process_dancer.sh dancer_image.png

# Extract pose data
python _extract_pose.py "$1" pose_data.json

# Define blender path and check if it exists
BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"

if [ ! -x "$BLENDER_PATH" ]; then
    echo "Blender not found at specified path, searching in Applications..."
    
    # First try default Blender.app location
    if [ -d "/Applications/Blender.app" ]; then
        BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"
    else
        # Try to find any Blender application in Applications folder
        BLENDER_APP=$(find /Applications -maxdepth 2 -name "Blender*.app" -print -quit 2>/dev/null)
        
        if [ -n "$BLENDER_APP" ]; then
            BLENDER_PATH="$BLENDER_APP/Contents/MacOS/Blender"
        else
            echo "Error: Could not find Blender application. Please install Blender or provide the correct path."
            exit 1
        fi
    fi
fi

# Verify Blender exists and is executable
if [ ! -x "$BLENDER_PATH" ]; then
    echo "Error: Blender was found but is not executable at path: $BLENDER_PATH"
    exit 1
fi

echo "Using Blender at: $BLENDER_PATH"

# Apply to Blender and render
"$BLENDER_PATH" -b ./model/picto.blend --python _pose_to_blender.py -- pose_data.json rendered_output.png

echo "Process completed. Check the rendered output at: rendered_output.png"
echo "Skeleton visualization saved at: pose_data_skeleton.png"