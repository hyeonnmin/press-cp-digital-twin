"""기존 Isaac Sim 설치본으로 전체 CP Scene을 검증한다."""
import argparse
from pathlib import Path
import sys
import traceback

parser=argparse.ArgumentParser()
parser.add_argument("--reopen-only",action="store_true")
args,_=parser.parse_known_args()

from isaacsim import SimulationApp
app=SimulationApp({"headless":True,"width":1920,"height":1080})
exit_code=0
try:
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import full_scene_setup
    app.run_coroutine(full_scene_setup.run(rebuild=not args.reopen_only,protect_current=False,mode="standalone_headless"))
except Exception:
    traceback.print_exc();exit_code=1
finally:
    app.close(exit_code=exit_code)
