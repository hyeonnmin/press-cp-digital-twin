import platform
import sys

import omni.usd
from pxr import UsdGeom


def check_environment():
    stage = omni.usd.get_context().get_stage()

    if stage is None:
        raise RuntimeError("Stage가 없습니다. Stage를 연 뒤 다시 실행하세요.")

    print("[CP-DT] Environment check")
    print(f"OS: {platform.platform()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Stage: {stage.GetRootLayer().identifier}")
    print(f"Up-axis: {UsdGeom.GetStageUpAxis(stage)}")
    print(f"Meters per unit: {UsdGeom.GetStageMetersPerUnit(stage)}")
    print("[CP-DT] CHECK_OK")


check_environment()