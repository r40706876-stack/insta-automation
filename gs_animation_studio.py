"""Manual GS Animation Studio, with bounded automatic recovery."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'gs_animation_studio'))
from recovery import main
if __name__=='__main__':main()
