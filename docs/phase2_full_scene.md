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

Scene → 제어반·주변 Asset → PNG의 경로는 모두 상대 참조다. Scene만 따로 복사하지 말고 `isaac_sim/stages`와 `isaac_sim/assets`의 상대 구조를 함께 유지한다. 기존 Panel 1 검증 파일은 그대로 남겨 두었다.

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

이 결과는 **전체 정적 가상환경 구축**이다. 실영상과의 정량 유사성 합격 기준, 반사·노이즈·흔들림·LED 갱신 특성, 동적 문자열 변경, 학습용 데이터 생성·평가 검증은 남아 있다. 기존 Train/Test 구간 미확인 상태이므로 현재 설정을 최종 학습·평가용 보정값으로 고정하지 않는다.

## 사용한 공식 API 근거

- [Isaac Sim 6.1 OpenUSD](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/omniverse_usd/open_usd.html)
- [Isaac Sim 6.1 SimulationApp](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)
- [OpenUSD Preview Surface·UV 텍스처](https://openusd.org/dev/spec_usdpreviewsurface.html)
- [Viewport 캡처](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.utility/latest/omni.kit.viewport.utility/omni.kit.viewport.utility.capture_viewport_to_file.html)
- [Viewport 표시 동작](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.actions/latest/actions_api.html)
- [Viewport 프레임 준비 대기](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.docs/109.0.0/viewport_api.html)

설치된 확장 코드의 API 정의와 실제 실행 결과를 함께 확인했다.
