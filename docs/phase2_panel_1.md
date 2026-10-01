# Phase 2 — Panel 1 Geometry 검증

작성일: 2026-09-30 (Asia/Seoul).

## 결과와 범위

첫 작업의 완료 기준인 Panel 1의 온도·압력·진공 Module, 여섯 주요 표시 영역, USD 저장·재열기를 실제 Isaac Sim 런타임에서 검증했다. 전체 Phase 2 완료나 영상 유사성 검증 완료는 아니다. 숫자 대신 위·아래 영역을 녹색·황색 사각형으로 표시한다.

## 확인한 자료

- 원본: `C:\Users\rlaek\Downloads\IMG_2631.MOV`.
- SHA-256: `e20d0d72bf3cc8522939055fc053f2edadd9ad0cb6e3022489755ccd9742139b`.
- FFmpeg로 확인: H.264, 1920×1080, 약 20.54초, 약 29.99 fps. 원본 파일은 수정하지 않았다.
- 2·4·10·18초 PNG를 `outputs/phase2_reference/`에 추출했다. 4초·18초 프레임을 직접 시각 확인했으며 배치는 4초 프레임에서 수동으로 읽었다.
- 원본·프레임·도구·렌더·상세 실행 보고서는 Git 제외 경로에 둔다. 디코더는 `outputs/tools/`의 imageio-ffmpeg 0.6.0이다. Isaac Sim 내장 OpenCV에는 FFmpeg 파일 디코딩 기능이 없어 별도 디코더를 사용했다.
- 원본의 기존 Train/Test 구간은 미확인이다. 이 결과는 예비 외형 작업이며 최종 학습·평가용 보정값으로 확정하지 않는다.

## 가정과 임시값

Config: `config/panel_1_geometry.json`. bbox는 `[left, top, right, bottom]`, 이미지 좌상단 원점이며 원근 보정 전 수동 근사값이다. OCR 정답 bbox가 아니다. 실제 크기 자료가 없으므로 1 px를 임의로 0.001 m에 대응시켰다.

| 대상 | 영상상 bbox (px) | 모델 폭×높이 (m, 임시) |
|---|---|---|
| 온도 | [290, 126, 433, 260] | 0.143 × 0.134 |
| 압력 | [462, 125, 602, 259] | 0.140 × 0.134 |
| 진공 | [637, 125, 704, 257] | 0.067 × 0.132 |
| 배경판 일부 | [260, 95, 730, 280] | 0.470 × 0.185 |

모듈 깊이 0.018 m, 배경판 두께 0.012 m, 표시 영역 두께 0.001 m도 구현용 임시값이다. 배경판은 Panel 1 주변의 일부 영역으로, 제어반 전체 크기를 뜻하지 않는다.

좌표: +X는 영상 오른쪽, +Z는 위, 전면은 -Y. 원점은 참조 프레임의 (495, 192) px에 대응한다. 온도·압력의 주요 숫자 영역은 모듈 오른쪽 위에 배치하고, 진공의 밝은 하부 조작부는 간단한 사각형으로 표현했다. PV/SV 의미는 부여하지 않았다.

검토용 정면 직교 카메라, 균일 DomeLight, 임시 표면 색·Roughness는 같은 Config의 `preview`에 둔다. 1200×600 검토 렌더는 1920×1080 실영상과의 전체 프레임 비교나 OCR 입력 해상도가 아니다. 실제 카메라·조명 보정은 다음 작업이다.

## 파일과 실행

| 파일 | 역할 |
|---|---|
| `isaac_sim/assets/cp_panel/panel_1_geometry.usda` | 배경판, 세 모듈, 여섯 표시 영역 및 임시 Material |
| `isaac_sim/stages/panel_1_preview.usda` | Asset 상대 참조, 검토 Camera·Light |
| `isaac_sim/scripts/panel_1_geometry.py` | Config 기반 생성과 구조 검증 |
| `isaac_sim/scripts/scene_setup.py` | 열기→저장→닫기→재열기→렌더→실행 보고서 |
| `isaac_sim/scripts/verify_panel_1_standalone.py` | GUI 제어가 불가능할 때 같은 함수를 별도 앱에서 실행 |

이 두 작은 텍스트 USD는 Git 관리 대상이다. 생성 스크립트를 다시 실행하면 생성기 표식이 있는 같은 출력 파일을 재작성한다. 해당 USD를 수동 수정해 보존하려면 다른 이름으로 저장한다. 생성기 표식이 없는 파일은 덮어쓰지 않는다.

GUI에서 `panel_1_preview.usda`를 열고 Viewport Camera를 `/World/ReviewCamera`로 선택하면 검토할 수 있다. GUI Script Editor에서는 현재 Stage를 먼저 저장하고 다음 코드를 실행한다. GUI에서는 SimulationApp을 새로 생성하지 않는다.

```python
import sys
import asyncio
import importlib

script_dir = r"C:\Projects\press-cp-digital-twin\isaac_sim\scripts"
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
import panel_1_geometry
import scene_setup
importlib.reload(panel_1_geometry)
importlib.reload(scene_setup)
panel1_task = asyncio.ensure_future(scene_setup.run())
```

성공 메시지는 `[CP-DT] PANEL1_GEOMETRY_OK`이다. 저장된 파일만 확인하려면 `scene_setup.run(rebuild=False)`를 사용한다. 작업이 끝난 뒤 `panel1_task.result()`로 비동기 실행 결과 또는 예외를 확인할 수 있다. 실행 중 중복 실행하지 않는다.

이번에 실제 수행한 PowerShell 명령은 다음과 같다. 저장소 루트에서 실행한다.

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/verify_panel_1_standalone.py
& C:\isaacsim\python.bat isaac_sim/scripts/verify_panel_1_standalone.py --reopen-only
```

## 검증 근거

- 실제 설치본: `6.1.0-rc.26+release.49347.2d230af4.gl`. `C:\isaacsim\VERSION`, 앱 Config의 6.1.0과 실제 실행 보고서가 일치했다. 이전 문서의 6.0.1은 사용자 보고 이력이며 이번 검증 버전으로 쓰지 않는다.
- Kit: `110.3.0+feature.371399.00c488ae.gl`, 내부 Python 3.12.13, OpenUSD 0.25.11, RTX 4070 SUPER.
- 최종 생성 실행과 새 프로세스의 `--reopen-only` 실행 모두 종료 코드 0 및 `PANEL1_GEOMETRY_OK` 확인.
- 검사: Z-up, metersPerUnit 1.0, Module 3개, 고유 Slot 6개, 온도→압력→진공 좌우 순서, Slot 1이 Slot 2 위에 있음, 두 Slot이 모듈 전면 및 외곽 안에 있음. 저장 전후·별도 프로세스의 검사 결과가 일치했다.
- PNG의 1200×600 해상도와 파일 디코딩 검증 후 렌더를 직접 확인했다. 작은 진공 모듈, 주요 표시 영역 및 하부 조작부가 예상 배치대로 보인다.
- 상세 보고서: `outputs/phase2_validation/build_report.json`, `reopen_report.json`. Config 전체, 원본 식별 정보, 코드·Config·USD·PNG SHA-256, 실행 모드, 버전, 실행 시각, 기반 Commit `4faf060b5c24be215850faa824b016dbf07144e8`와 미커밋 변경 상태를 기록했다. 랜덤화가 없어 Seed는 null이다.
- 렌더: `outputs/phase2_validation/panel_1_preview.png`, `panel_1_reopened.png`.
- Python 문법 검사와 `git diff --check` 통과.

Windows Computer Use 연결은 `native pipe ... os error 2`로 실패했고 재초기화 후에도 복구되지 않았다. 따라서 실제 검증 방식은 **Standalone headless**이며 GUI Script Editor에서의 직접 실행은 이번에 검증하지 않았다. GUI 실행 코드는 동일 함수를 사용하도록 제공했다.

구현 중 확인한 저장 API 반환값은 3개로, 공개 문서의 2개 설명과 달랐다. 성공값을 명시적으로 검사하도록 처리했다. PNG 캡처 완료와 파일 기록 완료의 시차도 처리했다. 최종 실행에는 이 두 오류가 없다. 앱 시작 시 기존 Omniverse proxy 설정 관련 경고는 남아 있으나 이번 검증은 통과했다.

## 다음 작업 하나

Panel 1의 가상 **투시 Camera**를 설정해 참조 프레임과 모듈·표시 영역의 이미지상 위치·크기·원근을 비교한다. 정면 직교 검토 Camera와 영상 재현 Camera를 구분한다. 이후 조명·Material 조정 및 나머지 Panel 확대를 순차 진행한다. 최종 보정 프레임과 실험 Split은 기존 데이터 사용 이력을 확인한 뒤 고정한다.

## 확인한 공식 API 자료

- [Isaac Sim 6.1 OpenUSD 기초](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/omniverse_usd/open_usd.html)
- [Isaac Sim 6.1 Scene 설정 예제](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/python_scripting/environment_setup.html)
- [Isaac Sim 6.1 SimulationApp](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)
- [Omniverse UsdContext 저장·재열기](https://docs.omniverse.nvidia.com/kit/docs/omni.usd/latest/omni.usd/omni.usd.UsdContext.html)
- [Viewport 파일 캡처](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.utility/latest/omni.kit.viewport.utility/omni.kit.viewport.utility.capture_viewport_to_file.html)

6.1 공식 문서와 설치된 확장 코드·실제 실행 결과를 함께 확인했다. RC 빌드와 공개 문서가 완전히 같다고 가정하지 않는다.
