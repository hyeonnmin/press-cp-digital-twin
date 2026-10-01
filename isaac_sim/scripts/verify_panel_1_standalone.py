"""GUI 연결 불가 시 별도 프로세스에서 같은 생성·검증 함수를 실행한다."""

import argparse
import sys
import traceback
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--reopen-only", action="store_true")
args, _ = parser.parse_known_args()

from isaacsim import SimulationApp

app = SimulationApp({"headless": True, "width": 1200, "height": 600})
exit_code = 0
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import scene_setup

    app.run_coroutine(scene_setup.run(execution_mode="standalone_headless", rebuild=not args.reopen_only, protect_current=False))
except Exception:
    traceback.print_exc()
    exit_code = 1
finally:
    # RC 빌드의 fast shutdown은 프로세스를 종료하므로 예외와 종료 코드를 먼저 보존한다.
    app.close(exit_code=exit_code)
