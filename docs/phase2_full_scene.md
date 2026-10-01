# 영상 기반 전체 CP 가상환경

작성일: 2026-09-30. 대상은 `IMG_2631.MOV`의 CP 제어반과 영상에 보이는 주변 구조이다.

## 열어 볼 파일

Isaac Sim의 **File → Open**에서 다음 파일을 연다. 생성 스크립트를 실행하지 않아도 저장된 Scene을 볼 수 있다.

```text
C:\Projects\press-cp-digital-twin\isaac_sim\stages\press_cp_main.usda
```

Viewport의 Camera 목록에서 다음 Camera를 선택한다.

| Camera 경로 | 용도 |
|---|---|
| `/World/Cameras/reference` | 원본 4초 프레임과 비교하는 투시 구도 |
| `/World/Cameras/training` | 전체 Panel을 정면 중앙에서 보는 직교 시점. 학습 생성 기본 카메라, [별도 실행 안내](training_capture.md) |
| `/World/Cameras/overview` | 제어반 두께와 좌우 주변 구조를 보는 사선 전체 구도 |
| `/World/Cameras/detail` | Panel 1 숫자·모듈 근접 확인 |

렌더 파일: `outputs/full_scene/reference.png`, `overview.png`, `detail.png`. 새 프로세스 재열기 렌더는 `reference_reopened.png`이다. 영상 기준 렌더는 원본과 같은 1920×1080이다.

## 구현한 구성

| 구성 | 구현 내용 |
|---|---|
| 제어반 | 외장 본체, 좌우 문, 중앙 틈, 문 두께, 모서리 경사, 경첩, 손잡이, 하부 받침 |
| HP 그룹 | 왼쪽 HP1~HP5의 5단, 오른쪽 HP6·번호 7의 2단 |
| 계측기 | 21개. 온도·압력의 넓은 검정 몸체와 진공의 좁은 세로 몸체·밝은 하부 조작부 |
| 주요 표시줄 | 42개. 위·아래 발광 숫자, 꺼진 세그먼트, 소수점을 Mesh로 구성 |
| 주변 조작부 | 그룹별 빨간 정지 버튼과 회전 표시, 빈 마개, 번호표, 로더 버튼·표시등 |
| 오른쪽 상부 | HMI 테두리·화면 모식도, OPERATION PANEL 라벨, 안전 안내판, 점검표 |
| 기타 | 기계 명판, HP6·7 사이 초록색 반투명 커버, 모듈 명판·간단한 보조 표시 |
| 주변 환경 | 좌측 설비 블록·배관, 우측 배관·플랜지·볼트·밸브 휠, 바닥·배경 벽 |

모델은 서로 분리된 3D Prim으로 구성되어 편집 가능하다. 원본 영상 사진을 제어반 전체에 붙인 평면 모델이 아니다. 숫자는 기하학적 세그먼트로 만들었고 HMI·명판만 절차적 PNG 텍스처를 사용한다. 실제 설비를 작동시키는 물리 시뮬레이션이나 HMI 제어 기능은 구현하지 않았다.

## 근거와 가정

확인한 자료는 원본 영상과 앞서 추출한 프레임이다. 주 배치에는 4초 프레임의 수동 근사 bbox를 사용했다. 원본 SHA-256은 Config와 실행 보고서에 기록했다. HP7 문자 라벨은 확정하지 않아 모델에도 별도의 HP7 명판을 만들지 않고 번호 7을 사용했다.

실제 치수와 렌즈 정보가 없으므로 가상 초점거리 1800 px, 위치 `(0, -2, 1.6)` m, 약 20도 하향 시점을 가정했다. 영상의 모듈 bbox 중심을 제어반 전면 평면에 역투영하여 배치했다. 가상 제어반은 폭 1.77 m, 높이 1.50 m, 깊이 0.30 m이다. **이 수치들은 영상 배치를 재현하기 위한 임시 모델링 값이며 실측값이 아니다.** 단일 영상으로 유일한 실제 치수·촬영 설정을 복원했다는 뜻이 아니다.

Module bbox의 숨겨진 경계와 두께는 근사값이다. 특히 Panel 7 압력 모듈의 위쪽은 초록 커버와 겹쳐 관찰이 제한된다. 커버의 앞면 깊이와 투명도를 조정해 주요 숫자열이 보이도록 했다. 보이지 않는 뒷면·배관 연결·벽·바닥과 주변 설비는 단순화했다.

42개 표시 문자열은 영상에서 읽은 값을 참고한 **초기 화면 예시**다. 전사 검증된 실영상 정답이나 실제 표시 범위로 쓰지 않는다. Config에서 문자열로 보존하고 USD의 각 Slot에 `display_text`를 기록한다. 실제 PV/SV 의미나 단위를 새로 확정하지 않는다. 모듈의 작은 보조 표시·범용 조작부 문자는 외형용 예시다.

HMI와 안전 안내판은 색·선·영역 배치를 참고한 모식도다. 실제 프로그램, 안전 절차 문서 또는 기기 매뉴얼을 정확히 복제한 것이 아니다. 최종 OCR 대상은 기존 원칙대로 주요 42개 Slot으로 구분한다.

## 파일 구조

```text
config/press_cp_scene.json                    # 배치, 문자열, Camera, Light, Material
isaac_sim/stages/press_cp_main.usda            # 최상위 Scene과 Camera·Light
isaac_sim/assets/cp_panel/press_cp_cabinet.usda # 전체 제어반
isaac_sim/assets/cp_panel/textures/*.png       # 작은 명판·HMI 텍스처
isaac_sim/assets/environment/workcell.usda     # 주변 구조
isaac_sim/scripts/press_cp_environment.py      # 3D 모델 생성·구조 검사
isaac_sim/scripts/cp_label_textures.py          # 명판·HMI PNG 생성
isaac_sim/scripts/full_scene_setup.py          # 저장·재열기·렌더·보고서
isaac_sim/scripts/verify_full_scene.py          # Standalone 검증 진입점
```

Scene → 제어반·주변 Asset → PNG의 경로는 모두 상대 참조다. Scene만 따로 복사하지 말고 `isaac_sim/stages`와 `isaac_sim/assets`의 상대 구조를 함께 유지한다. 2026-10-01 단일 Panel 시험 파일을 정리했으며, 현재 실행 경로는 이 전체 환경으로 통일했다.

작은 USD·명판 텍스처는 모델의 소스 Asset으로 Git 관리할 수 있다. 원본 영상, 참조 프레임, 검증 렌더·상세 보고서·캐시는 `outputs/` 아래에 두며 일반 Git에서 제외한다.

## 재생성과 실행

Config를 수정한 뒤 저장소 루트의 PowerShell에서 실행한다.

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/verify_full_scene.py
& C:\isaacsim\python.bat isaac_sim/scripts/verify_full_scene.py --reopen-only
```

첫 명령은 생성기 소유의 전체 Scene·Asset·명판 텍스처를 재작성한다. 수동 USD 수정 내용을 보존하려면 다른 이름으로 저장한다. 두 번째 명령은 모델을 재생성하지 않고 저장된 Scene을 열어 검사한다. 두 명령 모두 `[CP-DT] FULL_SCENE_OK`가 성공 메시지이다.

GUI Script Editor에서는 현재 Stage를 저장한 뒤 다음 코드를 실행할 수 있다.

```python
import sys, asyncio, importlib
script_dir = r"C:\Projects\press-cp-digital-twin\isaac_sim\scripts"
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
import cp_label_textures, press_cp_environment, full_scene_setup
importlib.reload(cp_label_textures)
importlib.reload(press_cp_environment)
importlib.reload(full_scene_setup)
cp_task = asyncio.ensure_future(full_scene_setup.run())
```

실행 종료 후 `cp_task.result()`로 결과나 예외를 확인한다. 저장 파일만 확인하려면 `full_scene_setup.run(rebuild=False)`를 사용한다. GUI에 새 SimulationApp을 생성하지 않는다. 이번 직접 검증은 Standalone headless이며 GUI Script Editor의 직접 조작 검증과 구분한다.

## 검증과 한계

실행 설치본은 `6.1.0-rc.26+release.49347.2d230af4.gl`, Kit `110.3.0+feature.371399.00c488ae.gl`, Python 3.12.13이다. 설치 변경은 하지 않았다.

검사 항목은 Z-up·metersPerUnit 1.0, 7 Panel·21 Module·고유 Slot 42개, 좌우 문 분배, 그룹의 위아래 순서, 각 모듈의 좌우 순서, Slot 위아래 관계, 정확한 표시 문자열, HMI·커버·손잡이·바닥의 존재, 텍스처 참조 해석이다. 저장·닫기·재열기 결과를 비교하고 렌더 파일의 해상도·디코딩과 실제 외형을 확인한다.

보고서는 `outputs/full_scene/build_report.json`과 `reopen_report.json`이다. 적용 Config 전체, 코드·Asset·텍스처·렌더의 SHA-256, 실행 모드·버전·시각, 기반 Commit과 미커밋 변경 여부를 기록한다. 랜덤화는 없어 Seed는 null이다.

최종 실행은 2026-09-30 14:31 KST에 생성·재열기 두 프로세스 모두 `FULL_SCENE_OK`, 종료 코드 0으로 통과했다. 중간 실행에서 Viewport 준비 시간 초과 뒤 Fabric native crash가 1회 발생하여 실제 렌더 프레임 준비 대기를 추가했다. 이후 두 실행은 정상 종료했으나 단일 실패의 근본 원인은 확정하지 않았다.

카메라의 `module_anchor_projection_max_error_px`는 입력 배치점과 USD 투영 규약의 일관성 검사다. 같은 배치점을 사용하므로 독립 영상 유사도나 카메라 보정 정확도로 해석하지 않는다. 실영상 외장 네 영역의 평균 RGB도 살펴 임시 광원을 조정했으나, 한 프레임의 일부 영역 비교이므로 전체 조명·반사 재현을 보증하지 않는다.

이 결과는 **전체 정적 가상환경 구축**이다. 실영상과의 정량 유사성 합격 기준, 반사·노이즈·흔들림·LED 갱신 특성, 동적 문자열 변경, 학습용 데이터 생성·평가 검증은 남아 있다. 2026-10-01 사용자가 Train/Test 구간은 아직 정하지 않았다고 확인했다. 현재 설정을 최종 학습·평가용 보정값으로 고정하지 않는다.

## 2026-10-01 — 42 Slot Crop 비교와 LED 발광

실영상 4초 프레임, 수정 전 렌더, LED 수정 후 렌더를 같은 1920×1080 좌표로 비교했다. `config/slot_crop_comparison.json`은 Module 수동 bbox와 Crop 시각 확인으로 정한 고정 검색창 42개를 저장한다. 정답 숫자 bbox가 아니며 USD의 투영 결과로 실영상을 정렬하지 않는다. 원본 Crop은 크기·색을 변환하지 않으며 비교표만 최근접 보간으로 4배 확대한다.

결과물은 `outputs/led_comparison/comparison/`의 `panel_1.png`~`panel_7.png`, `crops/`의 원본 크기 Crop 126개, `comparison.json`이다. JSON에는 고유 Slot ID·ROI·입력/출력 Hash와 변경 전후 렌더 보고서의 조건을 저장한다. 이전 렌더·보고서는 `outputs/led_comparison/before_*`로 보존했다. 모두 Git 제외 산출물이다.

측정은 검색창의 녹색/주황색 마스크에서 밝기 상위 40% 픽셀을 사용한다. 아래 값은 각 표시줄 21개 Slot에서 얻은 RGB 중앙값의 중앙값이다. 센서 노출과 배경 반사, 글자 형태에 영향을 받는 8-bit 이미지 지표이며 LED의 물리 휘도 측정값이 아니다.

| 표시줄 | 실영상 | 변경 전 DT | LED 수정 후 DT |
|---|---|---|---|
| 위쪽 녹색 | (183, 223, 49) | (239, 246, 28) | (193.5, 231, 75) |
| 아래쪽 주황색 | (195, 154, 85) | (237, 212, 26) | (195, 152, 71.5) |

기존 DT의 지나치게 밝고 노란 색 차이가 줄었다. 반면 색 마스크 중심 거리 중앙값은 수정 후 위쪽 8.19 px, 아래쪽 7.87 px로 남았다. 실제 숫자는 더 넓거나 기울어져 보이고 모듈별 밝기가 다르다. 특히 진공 표시의 아래 숫자는 일부 실영상에서 현재 DT보다 밝다. 반사와 흐림까지 일치했다고 판단하지 않는다. 위치/형상은 이번에 수정하지 않았으며 중심값의 작은 변동은 색 마스크 변화에도 영향을 받는다.

숫자 Mesh는 `UsdPreviewSurface`의 `emissiveColor`로 **자체 발광**한다. `materials.green_led`와 `amber_led`의 `emission_color × emission_intensity`가 발광 입력이며, `rendering.settings`의 FFT Bloom은 렌더러 내부에서 광학 번짐을 만든다. 저장된 PNG에 Glow를 나중에 합성한 결과가 아니다. 발광 색·세기와 Bloom 수치는 영상 관찰에 따른 예비값이며 측정된 LED 광도나 렌즈 설정이 아니다. 별도 점광원은 추가하지 않았다.

Scene의 `customLayerData.renderSettings`에 설정을 기록해 직접 열기에도 사용한다. Kit 저장이 기본값을 생략하는 것을 확인해 저장 후 명시값을 다시 기록하고, 재열기 후 USD와 런타임 적용값을 검사한다. Bloom은 숫자뿐 아니라 HMI 등 화면의 다른 밝은 부분에도 영향을 주므로 Config와 적용값을 함께 기록한다.

```powershell
# 전체 환경 재생성 및 LED 발광 대조 렌더
& C:\isaacsim\python.bat isaac_sim/scripts/verify_full_scene.py --led-checks
# 새 프로세스에서 저장 결과와 LED 검증
& C:\isaacsim\python.bat isaac_sim/scripts/verify_full_scene.py --reopen-only --led-checks
# 실영상 / 보존된 변경 전 렌더 / 수정 후 렌더 비교
& C:\isaacsim\python.bat isaac_sim/scripts/compare_slot_crops.py --after outputs/full_scene/reference.png --before-report outputs/led_comparison/before_build_report.json --after-report outputs/full_scene/build_report.json
```

변경 전 산출물이 없는 새 Checkout에서는 비교할 렌더와 보고서를 `--before`, `--before-report`로 지정한다. 실영상 프레임도 로컬 파일이 필요하며 Config의 SHA-256을 확인한다. 생성·재열기 보고서에 코드·Config·Asset·렌더 Hash와 적용 설정, Seed null을 남긴다.

`--led-checks`는 같은 Scene에서 Bloom 끔, 환경 조명 0에서 LED 발광 켬, 동일 조건에서 발광 끔을 순서대로 캡처한다. 결과는 `outputs/full_scene/led_checks/build/` 또는 `reopen/`의 `led_bloom_off.png`, `led_dark_on.png`, `led_dark_off.png`다. 생성·재열기 산출물을 분리해 이전 보고서의 Hash 연결을 유지한다. 숫자가 켜진 픽셀의 동일 좌표끼리 밝기를 비교해 42개 Slot의 자체 발광을 검사하며, 진단 변경은 복구하고 디스크 Scene에 저장하지 않는다. 이는 발광 구현 검증이며 실제 주변 물체를 비추는 조도·광량의 정확성을 보증하지 않는다.

일부 검색창은 실영상과 DT의 위치 차이 때문에 이웃 표시줄의 가장자리를 포함한다. 측정에는 표시줄별 색 조건을 동일 적용한다. 원본 문자열의 전사 검증, OCR 정답 정확도, 글자별 SSIM 점수는 산출하지 않는다. Train/Validation/Test를 나누기 전에 사용한 4초 프레임과 인접 구간을 보정 이력으로 관리하고 최종 Test 재사용을 피한다.

최종 생성·별도 프로세스 재열기는 모두 `FULL_SCENE_OK`, 종료 코드 0이었다. 보고서의 코드·Asset·렌더 Hash와 현재 파일이 일치하고 Crop 126개도 ID 연결·디코딩·Hash 검사를 통과했다. 발광 픽셀의 중앙값 밝기 차이는 생성 시 최소 155, 재열기 시 최소 160이었다. 최종 색 마스크가 검색창 경계에 닿은 사례는 없었다. Kit의 `restoreMetadataSettings` 경고는 남았으나 저장된 설정과 명시적으로 적용한 런타임 값 검사는 통과했다. GUI에서 파일만 직접 열었을 때의 설정 복원은 이번 Standalone 검증과 구분한다.

## 사용한 공식 API 근거

- [Isaac Sim 6.1 OpenUSD](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/omniverse_usd/open_usd.html)
- [Isaac Sim 6.1 SimulationApp](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)
- [OpenUSD Preview Surface·UV 텍스처](https://openusd.org/dev/spec_usdpreviewsurface.html)
- [Viewport 캡처](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.utility/latest/omni.kit.viewport.utility/omni.kit.viewport.utility.capture_viewport_to_file.html)
- [Viewport 표시 동작](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.actions/latest/actions_api.html)
- [Viewport 프레임 준비 대기](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.docs/109.0.0/viewport_api.html)
- [OpenUSD 발광 재질 입력](https://openusd.org/release/spec_usdpreviewsurface.html)
- [RTX FFT Bloom 설정](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx_post-processing.html#fft-bloom)
- [USD에 렌더 설정 저장 예시](https://docs.omniverse.nvidia.com/workflows/latest/rtx_rt-dh-setup.html)

설치된 확장 코드의 API 정의와 실제 실행 결과를 함께 확인했다. Bloom의 정확한 설정 키는 현재 설치본 `omni.rtx.settings.core-0.7.1+00c488ae/omni/rtx/settings/core/widgets/post_widgets.py`와 대조했다.
