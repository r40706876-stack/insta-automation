#!/bin/bash
# Render frames A..B that are not on disk yet (resumable). Needs BLENDER, TOPIC, OUT.
cd "$(dirname "$0")"; export BODY_ROOT=$PWD
L=$(python3 -c "
import os,sys
a,b=int(sys.argv[1]),int(sys.argv[2]); o=os.environ['OUT']
print(','.join(str(f) for f in range(a,b+1) if not os.path.exists(f'{o}/frames/{f:04d}.png')))" $1 $2)
[ -z "$L" ] && { echo "nothing to render"; exit 0; }
DEMO_FRAMES="$L" ${BLENDER:-blender} -b -t 0 --python body_scene.py 2>&1 | grep -E "^Saved|Error|Traceback|DONE"
