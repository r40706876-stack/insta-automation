#!/bin/bash
# Renders only frames not yet on disk (resumable). Usage: render_missing.sh FIRST LAST
cd "$(dirname "$0")"; export DEMO_ROOT=$PWD
L=$(python3 -c "
import os,sys
a,b=int(sys.argv[1]),int(sys.argv[2])
m=[f for f in range(a,b+1) if not os.path.exists(f'frames/{f:04d}.png')]
print(','.join(map(str,m)))" $1 $2)
[ -z "$L" ] && { echo "nothing to render"; exit 0; }
DEMO_FRAMES="$L" ${BLENDER:-blender} -b -t 0 --python scene.py 2>&1 | grep -E "^Saved|Error|Traceback"
