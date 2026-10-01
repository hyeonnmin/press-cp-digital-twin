"""Standalone 학습 데이터 생성 진입점."""
import argparse

parser=argparse.ArgumentParser()
parser.add_argument("--frames",type=int)
parser.add_argument("--seed",type=int)
parser.add_argument("--config")
parser.add_argument("--output-root",help="Run 저장 상위 폴더 (기본: datasets/synthetic/cp_training)")
parser.add_argument("--gui",action="store_true")
parser.add_argument("--export-yolo",action="store_true",help="생성 후 Panel 이미지와 YOLO Slot 라벨도 출력 (최소 2 프레임)")
args=parser.parse_args()
if args.export_yolo:
    import training_capture
    if training_capture.read_config(args.config,args.frames,args.seed)["frame_count"]<2:
        parser.error("--export-yolo의 Train/Val 분할에는 최소 2 프레임이 필요합니다")
from isaacsim import SimulationApp
app=SimulationApp({"headless":not args.gui,"width":1280,"height":720,
                   "extra_args":["--/exts/isaacsim.core.throttling/enable_async=false"]})
code=0
try:
    import training_capture
    output=app.run_coroutine(training_capture.run(args.config,args.frames,args.seed,protect_current=False,output_root=args.output_root))
    if args.export_yolo:
        from src.dataset.panel_yolo import export_run
        export_run(output)
except BaseException:
    import traceback
    traceback.print_exc();code=1
finally:
    app.close(exit_code=code)
