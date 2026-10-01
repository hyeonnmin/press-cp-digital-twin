# 학습 데이터 생성 모드

작성일: 2026-10-01. 설치된 Isaac Sim `6.1.0-rc.26+release.49347.2d230af4.gl`, Replicator `1.13.36`의 Standalone 실행으로 검증한다.

## 실행

저장소 루트 PowerShell에서 실행한다. 기본값은 Seed 42, 전체 이미지 10장, 42개 Slot의 Crop 420개다. 사전 잔상 검증 이미지 3장은 학습 샘플과 별도 저장한다.

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/generate_training_data.py

# 개수·Seed 변경
& C:\isaacsim\python.bat isaac_sim/scripts/generate_training_data.py --frames 100 --seed 123

# 창을 보면서 같은 생성 루프 실행
& C:\isaacsim\python.bat isaac_sim/scripts/generate_training_data.py --gui --frames 10
```

설정은 `config/training_capture.json`이다. `--config`로 다른 JSON도 지정할 수 있다. 이번에 검증한 실행 경로는 headless다. 기존 GUI에서 실행하려면 미저장 작업을 보관한 뒤 Script Editor에서 다음을 실행한다. 생성용 Stage로 전환되며 Timeline의 자동 숫자 Behavior는 비활성화한다.

```python
import sys
script_dir = r"C:\Projects\press-cp-digital-twin\isaac_sim\scripts"
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
import training_capture
task = training_capture.start(frames=10, seed=42)
# 완료 후 task.result()로 저장 폴더 확인. 예외 발생 시 원인도 조회 가능.
```

메인 Scene의 Play는 여전히 순차 변화 확인용이다. 학습 데이터 저장은 위 생성 명령으로 실행한다.

온도·압력·진공 표시기 3개가 들어간 Panel 이미지와 YOLO Slot 라벨도 필요하면 `--export-yolo`를 추가한다. 기존 Run만 변환하는 코드도 제공한다. [Panel 검출 데이터 실행 안내](panel_detection.md)를 참고한다.

검토용 소량 렌더는 `--output-root outputs/bloom_check/runs`처럼 저장 상위 폴더를 지정할 수 있다. 상대 경로는 저장소 루트 기준이며 기본 저장 위치는 바뀌지 않는다. 각 실행은 별도 UTC Run 폴더를 만든다.

2026-10-01 정리 요청으로 기존 `datasets/synthetic`의 Run은 모두 삭제했다. 아래 과거 Run ID와 수치는 당시 검증 이력이다. 이후 사용자 요청으로 현재 빛번짐 설정의 `datasets/synthetic/cp_training/20261001T064808_756110Z`를 새로 생성했다: 전체 프레임 2장, Crop 84개, YOLO Panel 14장·박스 84개, Seed 42, 생성·독립 검증 PASS.

## 숫자 빛번짐 설정

공통 렌더 설정은 `config/press_cp_scene.json`의 `rendering.settings`에서 관리한다. 2026-10-01 사용자 요청으로 `/rtx/post/lensFlares/flareScale`을 `0.1`에서 `0.4`로 높였다. 전체 배경까지 밝아지는 현상을 줄이기 위해 `cutoffPoint=[0.5,0.5,0.5]`, `isotropicFlareFalloff=[5,5,5]`으로 조정했다. 실제 측정값이 아닌 Crop 관찰에 따른 임시 시각 설정이다. LED 색·발광 재질과 숫자 Mesh는 유지한다.

학습 생성기는 매번 Config를 적용한다. 저장된 `press_cp_main.usda`의 렌더 설정도 맞췄으므로 기존 GUI에서는 Scene을 다시 열어 확인한다. 생성기를 재실행해도 Config를 통해 유지된다. 이미지 파일에 사후 Blur를 덧씌우는 처리는 없다.

설정 의미는 NVIDIA [FFT Bloom 문서](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx_post-processing.html#fft-bloom), 캡처 방식은 [Isaac Sim 6.1 Replicator 문서](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)를 확인했다. 설치된 6.1.0 RC에서 실제 렌더로 별도 검증한다.

## 숫자 선택과 저장 순서

1. Seed와 프레임 번호로 재현 가능한 무작위 문자열을 42개 Slot에 선택한다.
2. 숫자 Mesh의 Fabric Transform과 `display_text`를 갱신한다.
3. 누적 이력을 한 번 초기화한 뒤, 같은 숫자를 유지하며 `rep.orchestrator.step_async(delta_time=0.0, rt_subframes=..., wait_for_render=True)`를 호출한다.
4. 최초 32 subframe, 이후 8 subframe씩 추가 렌더한다. 모든 Slot ROI의 이전 이미지 대비 평균 RGB 차이가 3/255 이하인 검사가 두 번 연속 통과하면 저장한다. 최대 160 subframe에서 미통과하면 Run을 FAILED로 종료한다.
5. RGB Annotator가 반환한 완료 이미지를 복사해 PNG로 저장한다. 그 이미지에서 Crop을 추출하고 같은 적용 문자열로 정답을 기록한 뒤 다음 숫자로 넘어간다.

이 기준은 초기 수치 안정화 검사이며 OCR 품질의 절대 합격 기준은 아니다. 대기한 앱 업데이트 수를 subframe 수로 간주하지 않는다. DLSS Quality, RTX Real-Time 2.0, 모션 블러 끄기를 적용한다. 숫자 변경 직후 한 번만 전체 누적을 초기화하고 안정화 중에는 초기화하지 않는다.

범위는 `0.0~999.0`, 소수점 한 자리다. 정수부 1·2·3자리를 매 프레임 각 14개씩 뽑아 Slot에 무작위 배정한다. 실제 설비 값 분포를 추정한 것이 아닌 자릿수 균형 조건이다. 선행 0이나 음수는 이번 선택 범위에 추가하지 않았으며 정답은 문자열로 저장한다. Camera·Light·Material의 추가 랜덤화는 하지 않는다.

## 중앙 카메라

`/World/Cameras/training`은 `/World/Cabinet/Panels`의 실제 USD 경계를 기준으로 정면 중앙에 배치한다. 직교 투영으로 앞면의 원근 기울어짐과 거리별 배율 차이를 없애고, 경계에 5%씩 여백을 둔다. 3840×2160 PNG를 생성한다. 숫자 자체의 기존 세그먼트 기울기는 형상이며 카메라 왜곡이 아니다.

현재 계산값은 위치 약 `(0.04257, -3.06400, 0.77213)` m, 표적 약 `(0.04257, -0.06400, 0.77213)` m, 화면 범위 약 `2.5613×1.4407` m다. 이는 가상 Scene 기준이며 실측값이 아니다. 메인 USD에 같은 카메라를 추가했고 기본 카메라로 지정했다. GUI에서 기존 시점이 남으면 Viewport 카메라 목록의 **training**을 선택한다. 재생성 시 Config와 Scene 경계에서 다시 계산한다.

기존 실영상 비교용 reference 카메라도 유지한다. 직교 시점은 왜곡 없는 초기 학습 샘플용이며, 이후 실제 영상에 대한 일반화 평가는 실제 시점·영상 열화 조건을 포함해 따로 진행해야 한다.

## 저장 형식과 검증

`datasets/synthetic/cp_training/<UTC Run ID>/`에 저장하며 Git에서는 제외한다.

| 파일 | 내용 |
|---|---|
| `frames/*.png` | 원본 4K 전체 CP 이미지 |
| `crops/*.png` | 발광 숫자 Mesh 투영 bbox + 4픽셀 여백으로 추출한 Recognition 이미지 |
| `frames.jsonl` | 프레임별 42개 문자열·PNG Hash·실제 subframe 수와 안정화 검사 |
| `labels.jsonl` | Crop 경로·정답·Slot·Frame·bbox·Hash 연결 |
| `manifest.json` | 상태·Seed·전체 Config·실제 카메라/렌더 조건·코드/Asset Hash·Commit/dirty·설치 버전 |
| `validation.json` | 저장 결과 재검증 결과 |
| `camera_preview.png`, `contact_sheet.png` | Crop 위치 및 첫 프레임 42개 숫자/정답 검토 이미지 |
| `verification/` | `0.0 → 999.0 → 0.0` 잔상 검사 이미지 |
| `capture_scene.usdc`, `training_camera.usda` | 생성용 초기 Scene과 카메라. 각 프레임의 동적 Fabric 값은 JSON 정답으로 재현 |

이전 reference 카메라의 고정 픽셀 ROI는 사용하지 않는다. 현재 카메라와 실제 선택된 발광 Mesh의 월드 좌표에서 Crop을 계산한다. 파일·Seed 기반 정답 재현·해상도·Crop과 전체 이미지의 픽셀 일치·경계 이탈·다른 Slot 숫자 혼입·최소 숫자 높이·반복값 잔상을 검사한다. 이전 숫자 잔상 검사는 42개 Slot 모두에서 복귀 차이가 직전 `999.0`과의 차이의 25% 미만이어야 한다.

별도 재검증:

```powershell
& C:\isaacsim\python.bat src/dataset/validate_training_capture.py datasets/synthetic/cp_training/<Run ID>
```

`manifest.json`이 PASS이고 `validation.json`도 PASS인 Run만 사용한다. FAILED/중단 Run은 학습에서 제외한다. Split은 아직 `unassigned`다. 같은 전체 이미지에서 나온 42개 Crop을 서로 다른 Train/Validation으로 나누지 않는다. 실영상 Train/Validation/Test 분할과 최종 Real Test 평가는 별도 확정한다. 독립 OCR 모델 판독과 학습 성능 평가는 아직 수행하지 않았다.

## 검증 결과 — 2026-10-01

`datasets/synthetic/cp_training/20261001T054612_229728Z/`에서 기본 10장·420 Crop과 별도 검증 3장을 생성했다. manifest와 독립 재검증 결과가 모두 PASS이며 생성·재검증 프로세스가 종료 코드 0으로 끝났다. 모든 저장 샘플은 48 subframe, 숫자 높이 21~28픽셀, 최종 비교 최대 차이 약 2.163/255였다. 동일 값 복귀 차이 비율은 최대 약 3.40%로 25% 기준을 통과했다. 전체 시점과 첫 프레임의 42개 Crop/정답 비교표를 시각 확인했다.

초기 2/255 기준으로 실행한 `20261001T054303_786631Z`는 고정 숫자의 픽셀 변동 때문에 FAILED로 종료했다. 이를 PASS로 소급 변경하지 않았으며 학습에서 제외한다. 최종 예비 기준은 위에서 설명한 3/255다.

## API 근거

- NVIDIA [Isaac Sim 6.1 SDG Workflows](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/replicator_tutorials/tutorial_replicator_sdg_workflows.html): 명시적 capture, subframe, 렌더 완료 대기.
- NVIDIA [Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/replicator_tutorials/tutorial_replicator_getting_started.html): DLSS Quality와 누적 초기화.
- OpenUSD [GfCamera](https://openusd.org/24.08/api/class_gf_camera.html): 직교 카메라와 aperture의 단위.
