# 프로젝트 진행 상황

최종 갱신: 2026-10-01 (Asia/Seoul)

현재 Phase: 4 진행 — 프레임 단위 학습 생성·정면 중앙 카메라·Mesh 기반 Crop 구현과 소규모 검증 완료. 대량 생성·실험 Split·OCR 학습 평가는 남음

현재 작업: 강화한 빛번짐 설정으로 학습용 전체 프레임 2장, 숫자 Crop 84개, YOLO Panel 14장·박스 84개를 새로 생성하고 검증했다.

## 현재까지의 진행 요약 — 2026-10-01

| 항목 | 구현·확인한 결과 | 한계·남은 작업 |
|---|---|---|
| 개발 환경·실영상 분석 | Phase 0·1 종료 기록, Isaac Sim 6.1.0 RC의 Standalone 실행 확인 | 실제 치수·렌즈·조도는 미측정 |
| CP 환경 | 7 Panel·21 Module·42 Slot, 제어반·버튼·HMI·주변 환경의 USD 구성 및 재열기·렌더 검증 | 실영상과의 정량 유사성은 미확정 |
| 숫자 자동화 | `0.0~999.0`, 기본 0.1씩 증가·상한 순환, Play/Pause/Stop 연결 | 기본 0.1초는 최소 간격; 전 범위 9,991값의 실제 렌더 저장은 미실시 |
| 프레임 저장 | Slot별 무작위 값 선택 → 렌더 안정화 → PNG·정답 저장; 정면 중앙 직교 카메라·4K | 실제 촬영 시점 및 영상 열화와의 차이는 남음 |
| Recognition 데이터 | 숫자 Mesh 투영 bbox + 4픽셀 여백 Crop, 문자열·Slot ID·원본 연결 | 모델 학습·독립 OCR 판독 미실시 |
| YOLO 데이터 | Panel별 표시기 3개·주요 Slot 6개, 단일 클래스 `0: slot`, 정규화 bbox·YAML | 실제 YOLO 학습·로더 실행 미실시 |
| 빛번짐 | Bloom scale 0.4, cutoff RGB 0.5, isotropic falloff RGB 5; 전후 시각 비교 | 사용자 요청에 따른 시각 조정이며 실측값·랜덤화 범위가 아님 |
| 데이터 정리 | 기존 합성 Run·과거 출력 삭제 후 현재 설정으로 2프레임 재생성 | 삭제된 경로는 아래의 과거 실행 이력으로만 취급 |

현재 사용 가능한 학습용 Run은 [`20261001T064808_756110Z`](../datasets/synthetic/cp_training/20261001T064808_756110Z/)다. 전체 프레임 2장(3840×2160), Recognition Crop 84개, YOLO Panel 14장·박스 84개를 포함한다. Seed 42, 소수점 한 자리, 값 범위 `0.0~999.0`; 프레임마다 정수부 1·2·3자리 각 14개를 무작위 Slot에 배정한다. 별도 probe 3장은 학습 프레임 수에 포함하지 않는다.

현재 Run의 [Recognition 검증](../datasets/synthetic/cp_training/20261001T064808_756110Z/validation.json)과 [YOLO 검증](../datasets/synthetic/cp_training/20261001T064808_756110Z/yolo_panels/validation.json)은 모두 PASS다. 두 프레임은 각각 48 subframe에서 안정화됐으며 생성 프로세스는 종료 코드 0으로 끝났다. Panel 14장은 원본 프레임 단위로 Train 7장·Validation 7장에 배정했다. 원본 Recognition 메타데이터의 Split은 `unassigned`이며 Real Train/Validation/Test 분할은 아직 정하지 않았다.

재실행 명령(저장소 루트 PowerShell):

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/generate_training_data.py --frames 2 --seed 42 --export-yolo
```

실행마다 새 Run을 만들지만, 같은 Seed·프레임 번호는 같은 숫자 조합을 생성한다. `outputs/bloom_check`의 비교용 샘플을 현재 Run과 합쳐 독립 샘플로 세지 않는다. Run의 manifest에 Seed·Config·실제 적용 조건·코드/Asset Hash·기반 Commit과 dirty 상태를 기록한다. 이 작업까지 Commit·Push는 수행하지 않았다.

남은 작업은 대량 생성 수량·Synthetic 실험 Split 확정, Real Train/Validation/Test 구간 분리, 단계별 영상 조건 랜덤화, OCR/YOLO 학습 환경 구성과 실제 영상 평가다. Play 중 화질 저하는 반복되는 렌더 누적 초기화가 유력 원인으로 기록돼 있으며 원인 분리 실험·GUI 직접 시각 검증은 남아 있다. Phase 4의 소규모 생성 기준은 충족했으나 전체 연구나 모델 성능 검증이 완료된 것은 아니다.

이번 문서 정리는 기존 실행 기록과 현재 Run의 manifest·validation·실제 파일 수를 대조한 작업이다. 렌더·모델 학습을 다시 실행하지 않았다. 자세한 사용법은 [연속 표시](display_playback.md), [학습 생성](training_capture.md), [YOLO 추출](panel_detection.md), 판단 근거는 [주요 결정](decisions.md)을 따른다.

## 2026-10-01 — 현재 빛번짐 설정으로 학습 프레임 2장 생성

- 사용자 요청에 따라 `generate_training_data.py --frames 2 --seed 42 --export-yolo`를 실행했다. 출력은 `datasets/synthetic/cp_training/20261001T064808_756110Z/`, 실행 로그는 `outputs/training_frames_2.log`이다.
- 결과: 3840×2160 전체 프레임 2장, 숫자 Crop/정답 84개, YOLO 단일 클래스 slot Panel 이미지 14장·bbox 84개. 프레임 단위 Train/Validation 각각 7장으로 분리했다. 별도 잔상 검증 이미지 3장은 학습 프레임 수에 포함하지 않는다.
- 실제 적용: Bloom scale 0.4, cutoff RGB 0.5, isotropic falloff RGB 5, Seed 42. 두 프레임 모두 48 subframe에서 안정화했다. Seed가 이전 비교 Run과 같으므로 숫자 선택도 같으며 outputs의 검토용 Run을 별도 학습 샘플로 합치지 않는다.
- 검증: 생성·YOLO 자동 출력 PASS, 앱 정상 종료 코드 0. 독립 Recognition·YOLO 저장 결과 검증도 PASS. 문자열/이미지 연결·Crop 픽셀·Hash·bbox·프레임 Split 누수 검사 및 Panel 1 미리보기 시각 확인을 마쳤다. 코드·렌더 설정 변경은 없다.
- 남은 작업: 실제 모델 학습과 실영상 성능 평가는 수행하지 않았다. 이후 필요 수량으로 확대 생성한다.

## 2026-10-01 — 합성 데이터 정리와 숫자 빛번짐 강화

- 정리 완료: 기존 `datasets/synthetic/cp_training` 전체, `outputs/{dataset_sync,display_playback,full_scene,led_comparison,timeline_playback}`와 과거 로그를 삭제했다. 2,350개 파일·406,431,850 byte. 삭제 전 절대 경로가 작업공간 내 지정 대상인지 확인했고 내역은 `outputs/bloom_check/cleanup.json`에 기록했다. 정리 직후 `datasets/synthetic`은 비어 있었고 이후 사용자 요청으로 위 2프레임 Run을 새로 생성했다. 아래 이전 Run·산출물 경로는 **삭제된 과거 검증 이력**이다.
- 유지: 비교 코드의 입력인 `outputs/phase2_reference`(실영상 기준 프레임), `outputs/tools`(기존 도구), 이번 `outputs/bloom_check`만 남긴다. 삭제 전 전체 프레임 1장과 그 출처 메타데이터는 변경 전후 비교용으로 보존했다. 원본 실영상·Scene/Asset·코드·Config는 삭제하지 않았다.
- 변경: `config/press_cp_scene.json`의 Bloom scale `0.1 → 0.4`, cutoff `0.2 → 0.5`, isotropic falloff `50 → 5`. 강도만 올렸을 때와 falloff 200 시험에서는 배경 전체가 밝아졌다. 최종 falloff 5에서는 밝은 숫자 주변의 국소 빛번짐이 증가한 것을 Panel/Crop 비교표에서 확인했다. 실제 광학 측정값이 아닌 사용자 요청에 따른 시각 조정값이다.
- 적용: 학습 생성기는 공통 Config를 적용하고, 메인 USD의 Bloom scale/cutoff/falloff 속성도 동기화했다. 저장 위치를 지정하는 `--output-root`를 추가해 검증 Run은 학습 폴더에 만들지 않는다. GUI 버튼을 통한 실제 시각 확인은 하지 않았으며 메인 Scene을 다시 열어 사용한다.
- 실제 검증: Isaac Sim 6.1.0 RC / Standalone, Seed 42, 최종 Run `outputs/bloom_check/runs/20261001T064415_666348Z`. 전체 프레임 2장·Recognition Crop 84개·YOLO Panel 14장·박스 84개, Train/Val 각 7장. 생성·검증 PASS 및 정상 종료(0). probe `0.0 → 999.0 → 0.0`와 두 학습 프레임 모두 48 subframe에서 안정화. 이미지/정답 연결·bbox·원본 Crop 픽셀·Hash·Split 검사 통과.
- 비교: 동일 42개 Slot의 문자열·bbox·digit_bbox·slot_roi가 이전과 일치했다. 숫자 bbox 내부에서 digit_bbox 바깥 4픽셀 띠의 평균 max(RGB)가 45.24 → 59.02/255로 증가했다. 이는 배경·광학 확산을 포함한 영상 지표이며 실제 휘도나 OCR 성능 점수가 아니다. `panel_comparison.png`, `slot_comparison.png`, `comparison.json`을 보관한다.
- 발견 사항: 첫 실행에서 GPU `Device lost`로 중단됐고 재실행은 통과했다. 최종 렌더 후 customLayerData의 벡터 설정 경고를 유발하던 중복 벡터 기록을 제거하고 RenderProduct의 float3 속성을 유지했다. 학습 생성은 Config를 명시 적용한다. 중간 시험 Run은 정리했다.
- 검사: 단위 테스트 12개·Python 문법 검사·독립 저장 결과 재검증·diff 공백 검사 통과. 다음은 미리보기 기준 빛번짐 강도 확정 및 필요 수량 재생성이다. 대량 데이터 생성·모델 학습·실영상 성능 검증·Commit/Push는 수행하지 않았다.

## 2026-10-01 — YOLO 학습용 Panel 이미지와 Slot bbox

- 사용자 요청: 제공 이미지처럼 Panel별로 분리한 이미지와 각 Panel의 Slot bounding box를 생성한다. 후속 확인에서 **단일 클래스 slot**을 선택했다. YOLO 모델 학습을 실제 실행한 것은 아니다.
- 변경: `src/dataset/panel_yolo.py`, `config/panel_detection.json`, 좌표/분할 단위 테스트 추가. 신규 캡처는 USD Housing의 실제 투영 경계를 `panel_regions`에 기록하며 `generate_training_data.py --export-yolo`로 생성 직후 변환할 수 있다. 이전 Run도 저장 Config와 Slot ROI 교차 검사로 재렌더 없이 변환한다.
- 출력: Panel 이미지마다 3개 표시기와 6개 주요 숫자 bbox. PNG/TXT 1:1, 클래스 0:slot, Panel 내부 정규화 xywh. 원본 Frame·Panel·Slot·문자열·원본/지역 좌표 연결은 `annotations.jsonl`에 보존한다. 박스 그림은 previews에만 저장하고 학습 PNG는 원본 Crop 그대로다.
- 기존 Run 실제 변환: `datasets/synthetic/cp_training/20261001T054612_229728Z/yolo_panels/`에 이미지 70장·bbox 420개, Train 56장·Validation 14장 생성. 원본 프레임 단위 8/2 분할로 같은 프레임의 7개 Panel이 서로 다른 Split에 들어가지 않는다. 7개 Panel의 시각 검토와 저장 결과 검증 PASS.
- 신규 통합 실제 검증: `generate_training_data.py --frames 2 --export-yolo` 실행으로 `datasets/synthetic/cp_training/20261001T060410_362510Z/yolo_panels/`에 이미지 14장·bbox 84개, Train/Validation 각각 7장 생성. 실제 USD 경계 기록 경로, 데이터 생성·자동 변환 모두 PASS·종료 코드 0.
- 검증: 두 출력의 독립 재검증 PASS. 이미지·라벨 1:1, Panel당 6개 Slot, bbox 경계/잘림, 정규화 역변환 0.001픽셀 이내, source Frame/Slot/문자열 연결, Crop 원본 픽셀 일치, Hash, Split 누수 없음. YAML 파서로 dataset.yaml 로딩 확인. 단위 테스트 12개·Python 문법 검사·diff 공백 검사 통과.
- 남은 문제: 현재 Isaac Python에는 Ultralytics가 없어 모델 학습·로더 실제 실행은 하지 않았다. Synthetic 내부 Validation은 실제 영상 성능 평가를 대신하지 않는다. Panel 6·7에는 원본의 녹색 덮개 일부가 보이나 대상 숫자를 가리지 않는 것을 미리보기에서 확인했다.
- 다음 작업: [실행 안내](panel_detection.md)의 변환 명령 또는 `--export-yolo` 옵션을 사용한다. 대량 생성과 실제 YOLO 학습/Real 평가 조건은 별도 결정한다. Commit·Push는 수행하지 않았다.

## 2026-10-01 — 학습 데이터 생성 모드와 중앙 카메라

- 요청: 숫자를 선택한 뒤 안정된 프레임과 정답을 저장하는 반복 모드, 모든 CP Panel 숫자가 왜곡 없이 보이는 중앙 카메라.
- 구현: `training_capture.py`, `generate_training_data.py`, `training_camera.py`, `random_values.py`, `validate_training_capture.py`, `config/training_capture.json` 추가. 기존 Play 동작을 유지하며 생성용 Stage에서는 자동 숫자 Behavior를 비활성화한다. 실제 Replicator `step_async(delta_time=0.0, rt_subframes=..., wait_for_render=True)`와 RGB Annotator를 사용한다.
- 카메라: 정면 중앙 `/World/Cameras/training`, 직교 투영, 3840×2160, Panel 경계 기준 사방 5% 여백. 메인 USD 기본 시점과 Scene 생성기에도 반영했다. 계산 위치 약 `(0.04257, -3.06400, 0.77213)` m. 실측 카메라 복원이 아닌 왜곡 없는 학습 기준 시점이다.
- 샘플링: Seed 42, 각 프레임에 정수부 1·2·3자리 각각 14개를 무작위 Slot에 배정한다. 범위 `0.0~999.0`, 소수점 한 자리. 최종 실제 값 분포를 확정한 것은 아니다.
- Crop: 기존 reference 고정 ROI 대신, 선택된 발광 Mesh의 실제 투영 bbox에 4픽셀 여백을 더한다. 렌더 후 Fabric Transform·문자열 유지, 42개 ID, bbox 경계, 다른 Slot 숫자 혼입 여부를 검증한다.
- 실제 결과: `datasets/synthetic/cp_training/20261001T054612_229728Z/`의 manifest·validation 모두 PASS. 4K 전체 이미지 10장, Crop 420개, 별도 `0.0 → 999.0 → 0.0` 검증 이미지 3장. 모든 샘플이 48 subframe(초기 32 + 8 + 8)에서 안정화됐다. 최종 두 검사에서 최대 ROI 평균 차이는 약 2.163/255, 복귀 차이/직전 다른 값 차이 비율은 최대 약 3.40%로 25% 기준 이내였다. 숫자 높이는 21~28픽셀, 잘림·다른 Slot 숫자 혼입 없음.
- 검증 근거: 실제 full-frame·42개 Crop/정답 비교표를 시각 확인했다. 별도 프로세스의 저장 데이터 재검증도 PASS·종료 코드 0. 생성기 역시 `TRAINING_DATA_OK`·종료 코드 0이다. 단위 테스트 8개, Python 문법 검사, diff 공백 검사 통과. 코드/Asset Hash·Commit/dirty·Seed·전체 Config·실제 카메라/렌더 설정·subframe 검사 결과를 기록했다. 생성 실행 중 원본 Scene/Asset/텍스처 Hash 불변을 확인했다.
- 실험 중 발견: 초기 2/255 기준에서 숫자를 고정하고 160 subframe까지 기다려도 약 2~2.5의 변동이 남아 기본 배치가 FAILED로 종료됐다. 예비 기준을 3/255로 조정하고 두 번 연속 통과 및 별도 잔상 검사 기준을 유지했다. 실패 Run `20261001T054303_786631Z`와 초기 렌더 모드 오류 Run `20261001T053024_174553Z`는 학습에서 제외한다. 소규모 초기 성공 Run은 `20261001T053118_860776Z`(3장·126 Crop)다.
- 남은 문제: 독립 OCR 모델 판독, 학습 효과, 실영상 카메라/열화와의 차이, 대량 생성 성능은 미검증이다. Split은 unassigned이며 같은 전체 프레임의 Crop은 함께 분리해야 한다. GUI 직접 실행·카메라 선택은 headless 검증과 구분한다.
- 다음 작업: [실행 안내](training_capture.md)로 수량·Seed를 지정해 생성한다. 대량 생성 전에 현재 Crop 품질과 Synthetic Train/Validation 분할 기준을 확정한다. Commit·Push는 수행하지 않았다.

## 2026-10-01 — 메인 Scene의 Play 버튼 연결

### 후속 관찰: Play 중 화질 저하, Pause 후 회복

- 사용자 관찰: 재생 중 해상도가 떨어져 보이고 Pause하면 다시 선명해진다.
- 코드에서 확인: 숫자가 기본 0.1초 간격으로 바뀔 때마다 `FabricDisplay.apply()`가 `reset_renderer_accumulation()`을 호출한다. Pause에서는 갱신과 초기화가 중단된다. 저장된 메인 USD의 DLSS 모드는 `performance`다. 현재 GUI의 실제 적용 모드·내부 렌더 해상도는 직접 조회하지 않았다.
- 원인 추정: 반복되는 전체 렌더 누적 초기화로 DLSS·AA·조명 이력이 충분히 쌓이지 못하고, Pause에서는 이력이 쌓여 선명도가 회복되는 것이 유력하다. 이 초기화는 이전 숫자 잔상 방지를 위해 추가했다. NVIDIA [6.1 공식 설명](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/replicator_tutorials/tutorial_replicator_getting_started.html#dlss-temporal-reset)에서 해당 API의 전체 이력 초기화 범위를 확인했다.
- 다음 검증 제안: DLSS Quality와 DLSS 이력만 초기화하는 방법을 각각 비교하고 재생 화질·갱신 속도·숫자 잔상을 함께 검사한다. 이번 질의에서는 원인 설명만 수행했으며 실행 코드·설정을 변경하거나 원인 분리 실험을 완료한 것은 아니다.

- 변경: 메인 USD의 `/World/DisplayPlayback`에 Behavior Script 상대 참조를 추가했다. `press_cp_play_behavior.py`는 로딩 진입점, `timeline_display.py`는 Play/Pause/Stop 구현이다. Scene 생성기를 다시 실행해도 연결이 유지된다. 숫자 Mesh 생성은 기존 별도 실행기와 공유한다.
- 동작: 최초 Play에서 실행용 Mesh를 준비하고 `0.0`부터 기본 0.1초 간격으로 증가한다. Pause는 값 유지, 재개는 다음 값, Stop은 `0.0` 초기화다. 현재 카메라와 Stage를 교체하지 않는다. 숫자 형상과 `display_text`는 SessionLayer/Fabric에서 동기화한다.
- 실제 검증: Isaac Sim `6.1.0-rc.26` / Behavior Scripting Core `110.3.0`에서 저장된 USD의 자동 스크립트 로딩과 실제 Timeline 이벤트를 검사했다. 연속 20회 증가(0.1~2.0), Pause·재개, Stop·재시작, `999.0 → 0.0`, 42개 Slot 문자열과 5장 렌더를 통과했다. 실제 갱신 간격 0.109~0.171초, 값 건너뛰기 없음.
- 영상 검증: Stop·순환 후 `0.0` 영상과 최초 `0.0`을 비교했다. 42개 ROI의 복귀 차이는 `999.0`과의 차이 대비 최대 9.49%로, 기존 25% 기준을 통과했다. `2.0` 변화도 모든 ROI에서 확인했다. Scene/Asset 디스크 Hash와 카메라 Transform은 보존되었다.
- 산출물: `outputs/timeline_playback/20261001T043800_392647Z/verification.json`과 `initial_0.png`, `paused_value.png`, `stopped_0.png`, `maximum_999.png`, `wrapped_0.png`. Config·코드/Asset Hash·Commit/dirty·설치 버전·Seed(null)를 기록했다. 콘솔 `TIMELINE_PLAYBACK_OK` 확인. 단위 테스트 7개·Python 문법 검사·diff 공백 검사 통과.
- 공통 코드 회귀 확인: 별도 실행기도 6회 `998.8, 998.9, 999.0, 0.0, 0.1, 0.2`로 완료했다. `outputs/display_playback/20261001T043931_844846Z/playback.json`은 STOPPED, updates=6이다. 이 프로세스도 앱 종료 대기가 남아 Ctrl+C로 정리했다.
- 발견/해결: Windows CP949로 읽는 Kit 의존성 스캐너 오류는 ASCII 진입점과 표준 import 분리로 해결했다. Play에서 Kit이 원본 레이어 메모리에 추가한 `/PhysicsScene`·렌더 EcoMode 속성은 diff로 별도 기록하며 파일에 저장하지 않는다. 숫자 변경 자체는 SessionLayer에 한정한다.
- 한계: 실제 GUI 버튼 클릭·허용 창 조작은 미검증이며 동일 Timeline 이벤트를 headless에서 검증했다. PASS 후 SimulationApp 종료 대기가 남아 해당 검증 프로세스는 Ctrl+C로 종료했다. GUI의 일반 재생 동작과 별도인 검증 실행기 종료 문제로 남긴다. 전체 9,991개 값 렌더·학습용 ROI·실영상 OCR 평가는 아직 남아 있다.
- 다음 작업: [실행 안내](display_playback.md)에 따라 메인 Scene을 다시 열고 스크립트 실행을 허용한 뒤 Play로 사용한다. 이후 학습용 ROI 정리로 진행한다. Commit·Push는 수행하지 않았다.

## 2026-10-01 — Isaac Sim 연속 숫자 표시

- 사용자 지시: 학습용 ROI 작업 전에 `0.0 → 999.0` 숫자가 일정 간격으로 증가하는 실행 기능을 구현한다.
- 변경: `display_playback.py`, `run_display_playback.py`, `config/display_playback.json`, `glyph_layout.py` 추가. 초기 간격은 0.1초, 증가 폭은 기존 Config의 0.1이다. GUI Script Editor start/stop/status와 Standalone 실행 명령을 제공한다.
- 구현: 숫자 Mesh를 미리 준비하고 Fabric 로컬 Transform으로 필요한 숫자의 위치·크기만 갱신한다. 숫자 변경 시 RTX 누적 영상을 초기화한다. 시작할 때 한 번만 실행 Stage를 로드하며 갱신 중 Scene을 다시 열지 않는다. 원본 Asset은 보존한다.
- 실제 검증: `outputs/display_playback/20261001T041035_827388Z/verification.json` PASS. 20회 순차 증가, 실제 시작 간격 0.109~0.110초, stop 이후 값 유지와 index 23·24 재개, Stage 재로딩 0회, 42개 Slot의 Transform·영상 변화·`999.0 → 0.0` 복귀를 확인했다. 비교표도 직접 시각 확인했다.
- 일반 실행 확인: `outputs/display_playback/20261001T041139_537888Z/updates.jsonl`에 `998.8, 998.9, 999.0, 0.0, 0.1, 0.2` 순서가 기록되었고 여섯 번 갱신 뒤 정상 종료했다. 종료 코드 0.
- 검증 프로세스는 PASS·앱 종료 메시지 후 도구 세션이 종료 대기에 남아 직접 중단했다. 영상 검사 성공과 종료 성공을 구분하며 일반 실행의 종료 코드 0은 별도로 확인했다. 종료 대기 원인은 미확정이다.
- 테스트: 7개 통과. 전체 9,991개 값의 생성·순환과 전 범위의 숫자 선택·정렬·크기를 검증했다. 모든 값을 실제 렌더 저장한 것은 아니다.
- 발견 사항: 초기 Mesh/Transform 갱신 실험에서 이전 숫자 잔류가 발생했다. 최종 정적 숫자·Fabric Transform·RTX 누적 초기화 조합에서 실제 영상 검사를 통과했다. 각 초기 방식의 근본 원인은 분리 확정하지 않았다.
- 한계: 0.1초는 최소 간격이며 부하 시 지연된다. 이번 직접 검증은 Standalone headless이며 GUI Script Editor 직접 조작은 미검증이다. 학습용 ROI·실영상 유사성·OCR 판독·대량 데이터 생성은 남아 있다.
- 다음 작업: 사용자에게 [display_playback.md](display_playback.md)의 시작·중지 실행법을 제공한다. 이후 학습용 ROI 정리를 진행한다. Commit·Push는 수행하지 않았다.

## 2026-10-01 — 숫자 Mesh 갱신과 이미지·정답 동기화

- 변경: `display_controller.py`, `capture_dataset.py`, `validate_sync_capture.py` 추가. Config의 순차 문자열로 Mesh를 생성하고 프레임별 USD 스냅샷을 재로딩해 캡처한다. 원본 Scene·Asset·텍스처는 실행 전후 Hash가 동일하다.
- 실제 검증: Isaac Sim 6.1.0 RC / Standalone headless에서 `0.0, 0.1, 9.9, 10.0, 88.8, 999.0, 0.0` 7개 프레임과 294개 Crop을 생성했다. 문자열·Mesh 속성·캡처 전후 상태, 디코딩·Hash·중복·Slot/Frame 연결·Crop과 원본 픽셀 일치를 통과했다. 42개 ROI의 동일 값 복귀 영상도 검사했다. 최종 `DATASET_SYNC_OK`, 종료 코드 0.
- 산출물: `outputs/dataset_sync/20261001T023746_582393Z/`의 이미지·Label·스냅샷·보고서·비교표. Seed·전체 Config·실제 적용 설정·코드/Asset Hash·Commit/dirty 상태를 기록한다. Split은 debug이며 Git 제외 산출물이다.
- 발견한 문제: 런타임 Mesh 갱신은 USD 속성 검사만 통과하고 실제 영상에 이전 숫자가 남았다. 새 Prim 교체와 OmniHydra 전환도 반복값 영상 검증에 실패했다. 스냅샷 재로딩으로 최종 동기화 기준을 통과했다. 근본 원인은 미확정이다. 초기 실패 Run은 학습에 사용하지 않는다.
- 원본 Scene의 수동 카메라 조정과 생략된 Bloom 기본값은 보존했다. 캡처에는 ROI에 맞는 Config 카메라·렌더 설정을 메모리에 적용하고 저장 조건과 구분 기록했다.
- 남은 문제: 일부 Crop에 이웃 표시가 포함되어 학습용 ROI 정리가 필요하다. OCR 독립 판독, 전체 범위 렌더·대량 생성 성능, 실시간 GUI 갱신은 미검증이다. Real Split도 아직 미정이다.
- 다음 작업 하나: **학습용 Crop ROI를 숫자 영역 중심으로 정리하고 경계·이웃 문자열 혼입을 검증한다.** 상세 실행법과 한계는 [phase4_capture.md](phase4_capture.md). Commit·Push는 수행하지 않았다.

## 2026-10-01 — Phase 4 첫 기능: 순차 값 생성

- 확인한 요구: 사용자 지정 범위 `0.0 ~ 999.0`, 순차 변화.
- 변경: `config/dataset_capture.json`, `src/generation/value_generator.py` 추가. 정수 단위로 진행해 부동소수점 누적 오차를 방지하고 소수점 한 자리 문자열을 보존한다. 기존 Scene Config의 42개 Slot ID에 문자열을 연결한다.
- 가정: `0.0 → 0.1 → … → 999.0 → 0.0`, 모든 Slot에 같은 값을 사용한다. 실측 범위나 최종 학습 조건이 아니다. 랜덤화가 없어 Seed는 null이다.
- 검증: `python -m unittest discover -s tests -v` 4개 테스트 통과. 9,991개 값 전체 순회·순환, 시작값·순환 중지, 42개 고유 Slot 연결, 잘못된 범위·정밀도 거부를 확인했다. CLI에서 프레임 9990의 42개 문자열 `999.0`도 확인했다.
- 완료 기준: 정확한 소수점 문자열을 순차 생성하고 Slot 연결을 검증한다. 이번 기준은 충족했다.
- 남은 문제: Isaac Sim 화면 갱신과 이미지·Crop·Label 저장은 아직 수행하지 않았다. Phase 3 동적 표시 검증과 Phase 4 전체 완료는 남아 있다. 영상 유사성 보정과 Real Split 미정 사항도 유지한다.
- 다음 작업: 생성기와 USD 숫자 Mesh 갱신을 연결하고 작은 배치의 이미지·Label 동기화를 실제 렌더로 검증한다. Commit·Push는 수행하지 않았다.

## 최신 결과 — 2026-10-01 Slot Crop 비교와 LED 발광

- 실영상 4초 프레임과 변경 전후 1920×1080 렌더에서 42개 고유 Slot의 같은 좌표를 잘라 비교했다. 원본 크기 Crop 126개, Panel별 4배 확대 비교표 7개, Hash·ROI·측정값·렌더 조건을 포함한 `outputs/led_comparison/comparison/comparison.json`을 생성했다.
- 기존 숫자도 `UsdPreviewSurface.emissiveColor`를 사용했지만 밝고 노란 색과 또렷한 경계가 실영상과 달랐다. 발광 색·세기를 Config에서 분리하고 숫자 자체 발광과 렌더러의 FFT Bloom을 함께 적용했다. 문자열·세그먼트 형상·위치는 변경하지 않았다.
- 밝은 숫자 픽셀의 RGB 중앙값: 녹색 실영상 `(183,223,49)`, 변경 전 `(239,246,28)`, 수정 후 `(193.5,231,75)`; 주황색 실영상 `(195,154,85)`, 변경 전 `(237,212,26)`, 수정 후 `(195,152,71.5)`. 색 차이는 줄었지만 실제 광도나 전체 영상 유사도 점수가 아니다.
- Isaac Sim 6.1.0 RC / Standalone headless에서 생성·저장·재열기·렌더를 수행했다. 7/21/42 구성·문자열·42개 발광 재질·Config와 USD 렌더 설정을 검증했다. 환경 조명과 Bloom을 끈 뒤 Emission 켬/끔 대조에서도 42개 Slot 모두 발광 차이를 확인했다. 보고서는 `outputs/full_scene/build_report.json`, `reopen_report.json`이다.
- 최종 생성과 별도 프로세스 재열기 모두 `FULL_SCENE_OK`, 종료 코드 0. 코드·Asset·렌더 Hash가 각 보고서와 일치하고, Crop 126개의 연결·디코딩·Hash 및 색 마스크의 검색창 경계 검사를 통과했다. Emission 켬/끔의 동일 발광 픽셀 밝기 차이는 Slot별 중앙값 기준 최소 155/160(생성/재열기)이었다.
- 중간에 샌드박스의 OmniCache 접근 제한과 Kit 저장 시 기본 렌더 설정 생략을 확인했다. 허용된 환경에서 실행하고 저장 후 Config 값을 명시하도록 보완했다. 최초 발광 검사는 빈 배경을 포함한 ROI 95백분위 때문에 획이 적은 숫자에서 실패해, 발광 픽셀의 동일 좌표끼리 켬/끔을 비교하도록 수정했다.
- 사용자 확인: **Train/Test 구간은 아직 정하지 않았다.** 이번 4초 프레임 사용은 예비 외형 보정 이력으로 기록한다. 추후 인접 프레임 누수를 방지하고, 보정에 사용한 구간을 최종 Test로 재사용하지 않도록 분리한다.
- 남은 차이: 색 마스크 중심 거리 중앙값은 위·아래 약 8 px이며, 문자 폭·기울기·모듈별 밝기·반사·영상 흐림도 다르다. 일부 검색창에는 이웃 표시줄 가장자리가 포함되어 색 마스크로 구분한다. 정답 bbox·OCR 정확도·유사성 합격 검증은 아니다.
- 실행법과 상세 결과: [phase2_full_scene.md](phase2_full_scene.md). Commit·Push는 하지 않았다.

당시 다음 작업이었던 실영상 기준 위치·폭·기울기 보정은 미완료로 유지한다. 현재 우선 작업은 위 Phase 4 학습용 ROI 정리이며 최종 실험 전 Train/Validation/Test 구간을 나눈다.

## 2026-09-30 결과 — 전체 CP 가상환경 구축

- 사용자 요청에 따라 Panel 1 시험 모델에서 전체 제어반과 주변 환경으로 확대했다. 완료 기준은 전체 Scene을 실제 Isaac Sim에서 생성·저장·재열기하고 렌더로 확인하는 것이다.
- 진입점: `isaac_sim/stages/press_cp_main.usda`. 영상 비교용 `reference`, 전체 사선 `overview`, 근접 `detail` Camera를 제공한다.
- 좌측 5개·우측 2개 Panel, 21개 계측기, 42개 발광 숫자열, 문·손잡이·경첩·버튼·HMI·명판·초록 커버 및 주변 배관·바닥·벽을 구성했다.
- `config/press_cp_scene.json`에서 배치·문자열·Camera·Light·Material을 관리한다. 제어반·주변 USD와 Python 생성 로직을 분리했으며 Asset·텍스처는 상대 참조한다.
- 설치된 Isaac Sim 6.1.0 RC의 Standalone headless에서 2026-09-30 14:31 KST 생성 실행과 별도 프로세스 재열기가 모두 `FULL_SCENE_OK`, 종료 코드 0으로 통과했다. Z-up·단위, 7/21/42 개수·고유 ID·배치·문자열·텍스처 참조를 확인했다.
- 1920×1080의 세 시점과 재열기 렌더를 기록했다. 기준·전체 렌더에서 전체 배치와 숫자, Panel 7 커버 주변 표시를 직접 확인했다. 코드·Config·Asset·렌더 Hash 및 실행 조건은 `outputs/full_scene/build_report.json`, `reopen_report.json`에 있다.
- 중간 실행에서 Viewport 준비 시간 초과 뒤 Fabric native crash가 1회 발생했다. 실제 렌더 프레임을 기다리도록 보완한 뒤 최종 두 실행은 통과했다. 근본 원인은 확정하지 않았다.
- 치수·가상 카메라·광원은 영상 재현용 근사값이다. HMI·안전 안내문·보이지 않는 주변 구조는 모식 표현이며 초기 문자열은 검증된 실영상 정답이 아니다.
- 사용법·근거·한계: [phase2_full_scene.md](phase2_full_scene.md). 단일 Panel 시험 파일은 2026-10-01 사용자 요청으로 정리했다.

당시 다음 작업이었던 Slot Crop 예비 비교와 LED 발광 수정은 위 2026-10-01 결과에 기록했다. 동적 표시값 변경과 학습용 데이터 생성은 후속 Phase로 남긴다.

## Phase 0 — 완료

아래 내용은 사용자가 제공한 실행 결과와 이전 진행 문서의 완료 기록에 근거한다. 이번 작업 공간에서 Windows 저장소를 직접 조회하거나 Isaac Sim을 실행한 결과는 아니다.

- Git 2.50.1.windows.1 설치 및 작성자 이름·이메일·기본 브랜치 설정 확인.
- 저장소 위치: `C:\Projects\press-cp-digital-twin`.
- 마지막 확인 브랜치: `main`, GitHub `origin/main` 연결과 Commit·Push 성공.
- `.gitignore`, `.gitattributes` 추가 및 datasets·checkpoints 제외 규칙 검증 통과.
- 첫 Commit: `5c0f003` — `chore: configure project version control`, 당시 working tree clean 확인.
- 기본 구조·작업 문서 Commit: `9080cd2`.
- Isaac Sim 6.0.1, `C:\isaacsim\isaac-sim.bat` 실행, GUI Script Editor 사용 확인.
- 내부 Python 3.12.13, 익명 Stage의 Z-up·metersPerUnit 1.0 확인.
- GPU: NVIDIA GeForce RTX 4070 SUPER, 12282 MiB, Driver 591.86.
- `isaac_sim/scripts/check_environment.py`: 동일 앱 세션 2회 실행 및 앱 재시작 후 `CHECK_OK` 확인.
- 환경 확인 코드·기록 Commit: `f54f878`, GitHub 동기화 확인.
- 마무리 문서 Commit: `af11aaa`, 사용자 보고로 `main`과 `origin/main` 동기화 확인.

2026-09-30 기준 Phase 0 초기 세팅 완료. Stage 생성·수정·저장, Base Scene 구현, 데이터 생성 및 OCR 학습은 아직 검증·구현 완료로 기록하지 않는다.

## Phase 1 — 완료 (현재 보유 자료 범위)

완료일: 2026-09-30.

### 완료한 내용

- 첨부 IMG_2631.MOV의 메타데이터와 여러 시점 프레임 확인.
- 영상에서 7개 HP 그룹, 21개 온도·압력·진공 컨트롤러, 42개 주요 숫자 표시줄 확인.
- 왼쪽 문에 HP1~HP5, 오른쪽 문에 HP6·번호 7 그룹 배치 확인.
- 논리적 Panel과 물리 제어반의 좌우 문을 구분하고 Panel·Module·Slot ID 제안 작성.
- Module 21개 행과 고유 Slot ID 42개의 개수·중복 여부 검증.
- 관측 색상·숫자 형태·소수점·주변 구성·반사·프레임 간 구도 변화 기록.
- 정확한 설계도·실측값·조명 위치·카메라 설정이 없는 자료 한계와 후속 처리 방침 기록.
- 사용자 지시에 따라 추가 실측·설치 카메라 자료를 기다리지 않고 Phase 1 종료.

### 종료 기준과 한계

현재 가진 휴대폰 영상에서 확인할 수 있는 구조·시각 특성 및 미확인 항목을 문서화한 것으로 분석을 종료한다. 정밀 실측이 완료되었거나 실제 설비·카메라 설정을 정확히 복원했다는 뜻은 아니다.

현재 실제 데이터는 휴대폰 영상 하나이며, 기존 모니터링 모델은 앞부분으로 학습하고 뒷부분으로 테스트했다. 정확한 구간 경계·추출 수·Crop·라벨·테스트 활용 이력은 미확인이다. 첨부 MOV의 확인된 해상도는 1920×1080이며 기존 OCR 전처리 후 해상도는 미확인이다.

번호 7 그룹은 확인되지만 HP7 문자 라벨은 명확하게 판독하지 못했다. 위·아래 Slot의 현재값/설정값 의미, 보조 표시의 포함 여부와 기존 라벨의 ID 대응은 확정하지 않았다.

### 결정 사항

- 현재 재현·평가 대상은 휴대폰 CP 영상으로 한다.
- 영상의 상대 배치와 시각 특성에 맞춰 Base Scene을 먼저 구축한다.
- 실제 치수·조명 위치·촬영 설정은 미확인으로 유지하며 가상환경의 임시값·근사값과 구분한다.
- 기준 카메라에서의 Base Scene 비교 후 카메라·조명 등의 다양화를 단계적으로 진행한다.
- 실사 학습 모델과 합성 학습 모델은 동일한 Real Test에서 비교한다. Mixed는 추가 비교 조건으로 유지한다.

## 2026-10-01 — 단일 Panel 시험 파일 정리

- 변경: 단일 Panel 전용 Config 1개, USD 2개, Python 스크립트 3개, 설명 문서 1개를 삭제했다. 해당 로컬 검증 렌더·보고서·로그·Python 캐시도 삭제했다.
- 유지: 전체 환경의 7 Panel·21 Module·42 Slot, 전체 환경 생성/검증 코드·Config·USD·텍스처와 렌더·보고서, 공통 참조 프레임을 유지한다.
- 문서: 단일 Panel 실행 안내와 삭제 파일 참조를 정리하고 전체 환경 실행법으로 통일했다. 초기 시험의 상세 구현은 Git 이력, 주요 판단은 decisions.md에 남긴다.
- 검증: 남은 Python 5개 문법 검사, USD의 Asset·텍스처 상대 참조 27개 존재 확인, Config와 USD 텍스트의 7 Panel·21 Module·42 Slot 및 Slot ID 중복 검사를 통과했다. 유지한 코드·Config·USD·텍스처 34개는 HEAD와 내용이 같고, 삭제 파일 참조 검색과 `git diff --check`도 통과했다.
- 검증 한계: 일반 Isaac Python 실행에서는 `pxr` 모듈을 찾지 못해 기존 USD 런타임 검증 함수를 실행하지 못했다. 이번 검증은 정적 검사이며 Isaac Sim 앱 재실행·재렌더는 수행하지 않았다. 위 2026-09-30 실행 결과와 구분한다. 이번 정리의 Commit·Push는 수행하지 않았다.
- 남은 문제와 다음 작업: 실영상과의 정량 유사성 검증은 남아 있다. 주요 Slot의 실영상·렌더 Crop 비교를 진행한다.

## 후속 작업으로 넘긴 미확인 항목

| 항목 | 처리 시점 |
|---|---|
| Panel·Module의 상대 크기·위치와 가상 Camera·Lighting 조정값 | Phase 2 구축 및 영상 비교 |
| 물리 치수·실제 Camera·조명 설정 | 자료 확보 시 보완; 현재는 미확인으로 유지 |
| Slot 의미·문자 규칙·보조 표시 범위 | Phase 3 Display 작업, 기존 Crop·라벨 대조 |
| 슬롯별 bbox·문자열·전처리 및 Label 규격 | Phase 4 Dataset 준비 |
| 기존 Train/Test 구간과 활용 이력, Validation·공통 Test 고정 | 최종 데이터 생성 조건 선택·학습 비교 전 |
| 대용량 USD Asset 관리 방식 | 대용량 Asset 추가 전 |
| OCR 학습용 Python·프레임워크 환경 | Phase 6 준비 |

## Windows 저장소 반영 상태 — 2026-09-30 초기 구축 이력

- 작업 시작 시 `git status --short`는 비어 있었고, HEAD는 `4faf060` — `docs: close phase 1 with phone video reference`였다.
- 이번 Phase 2 코드·Config·USD·문서는 현재 Windows 저장소에 생성·수정했다. Commit·Push는 하지 않았다.
- 원본 MOV, 추출 프레임, 디코더, 상세 보고서와 렌더는 일반 Git에 추가하지 않는다.
- GitHub·Notion·다른 프로젝트 소스의 동기화는 수행하지 않았다.
