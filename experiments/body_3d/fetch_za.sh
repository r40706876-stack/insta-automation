#!/bin/bash
# Downloads only the 5 Z-Anatomy FBX files we use, from a pinned commit (same files every time).
set -e
DEST=${1:-za}; COMMIT=6c7f9016bd5899ac8edafd31b9900c151df42ed6
rm -rf "$DEST"; git init -q "$DEST"; cd "$DEST"
git remote add origin https://github.com/LluisV/Z-Anatomy
git sparse-checkout set --no-cone "Resources/Models/License.txt" "Resources/Models/FBX/VisceralSystem100.fbx" \
  "Resources/Models/FBX/CardioVascular41.fbx" "Resources/Models/FBX/NervousSystem100.fbx" \
  "Resources/Models/FBX/SkeletalSystem100.fbx" "Resources/Models/FBX/Regions of human body100.fbx"
git fetch -q --depth 1 --filter=blob:none origin $COMMIT
git checkout -q FETCH_HEAD
ls -la Resources/Models/FBX
