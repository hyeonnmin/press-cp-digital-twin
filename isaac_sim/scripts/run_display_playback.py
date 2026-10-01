"""Standalone 연속 표시 진입점. GUI Script Editor에서는 display_playback.start()."""
import argparse
parser=argparse.ArgumentParser()
parser.add_argument("--headless",action="store_true")
parser.add_argument("--verify",action="store_true")
parser.add_argument("--verify-timeline",action="store_true")
parser.add_argument("--interval",type=float)
parser.add_argument("--updates",type=int)
parser.add_argument("--start-index",type=int,default=0)
args=parser.parse_args()
if args.updates is not None and args.updates<=0: parser.error("--updates는 양수여야 합니다")
from isaacsim import SimulationApp
app=SimulationApp({"headless":args.headless,"width":1920,"height":1080})
code=0
try:
    import display_playback
    if args.verify_timeline:
        from verify_timeline_playback import verify
        app.run_coroutine(verify())
    else:
        app.run_coroutine(display_playback.verify() if args.verify else display_playback.run(args.interval,args.updates,args.start_index,protect_current=False))
except KeyboardInterrupt:
    pass
except Exception:
    import traceback
    traceback.print_exc();code=1
finally:
    app.close(exit_code=code)
