# 실행환경과 실제 CP 환경 분석

최종 갱신: 2026-10-02 (Asia/Seoul)

분석 상태: Phase 1 완료 — 현재 보유 자료 범위의 분석 종료

현재 프로젝트 Phase: 4 진행 — 숫자 자동화·소규모 학습 생성 검증 완료, 대량 생성·Split·모델 학습·평가는 남음. 이 문서의 본문은 주로 Phase 1 분석 및 Phase 2 구축 당시의 관측 이력이다.

2026-10-02 추가 확인: 기존 CP를 보존한 공장 실내 확장을 설치본 `6.1.0-rc.26+release.49347.2d230af4.gl`의 Standalone headless에서 생성·재열기·렌더 검증했다. 사진 밖 구조·치수·조명은 가정이며 실제 환경의 추가 실측은 없다. 새 환경의 GUI Play·학습 생성 회귀는 남아 있다. [공장 환경 안내](factory_environment.md), [현재 진행 상황](progress.md)을 따른다.

2026-10-01 추가 확인: 사용자가 Train/Test 구간은 아직 정하지 않았다고 밝혔다. 4초 프레임의 42 Slot Crop 비교와 LED Emission·Bloom 수정을 수행했다. 최종 실험 분할과 유사성 합격은 미완료이며 상세 결과는 [phase2_full_scene.md](phase2_full_scene.md)에 기록한다.

Phase 1 완료는 휴대폰 영상의 관찰 결과와 자료 한계를 정리했다는 뜻이다. Phase 2에서는 Panel 1 예비 모델에 이어 전체 7 Panel 환경을 만들었다. 실제 치수·조명·카메라 실측이나 영상 유사성의 정량 검증 완료를 뜻하지 않는다.

## 1. 개발 실행환경

| 항목 | 값 | 확인 근거 |
|---|---|---|
| OS | Windows-11-10.0.26200-SP0 | Phase 0 스크립트 출력 |
| Isaac Sim 현재 설치본 | 6.1.0-rc.26+release.49347.2d230af4.gl | 2026-09-30 VERSION·앱 Config·실제 Standalone 실행 직접 확인. 기존 6.0.1은 Phase 0 사용자 보고 이력 |
| 앱 실행 | `C:\isaacsim\isaac-sim.bat` | 사용자 확인 |
| 기준 검증 방식 | Standalone headless (`C:\isaacsim\python.bat`) | Phase 2 이후 직접 실행 및 2026-10-02 공장 환경 생성·재열기 검증. GUI Script Editor는 Phase 0 사용자 실행 이력이며, 현재 메인 USD에는 GUI Play용 Behavior를 연결함 |
| Isaac Sim 내부 Python | 3.12.13 | Phase 0 스크립트 출력 |
| GPU | NVIDIA GeForce RTX 4070 SUPER | Phase 0 nvidia-smi 출력 |
| GPU Driver | 591.86 | Phase 0 nvidia-smi 출력 |
| GPU 메모리 | 12282 MiB | Phase 0 nvidia-smi 출력 |

### Stage 확인 결과

- Phase 0 확인 대상: 당시 열린 미저장 익명 Stage.
- Up-axis: Z.
- Meters per unit: 1.0.
- 위 값은 Phase 0의 해당 Stage에서 읽은 결과다. Phase 2의 전체 `press_cp_main.usda`도 저장·재열기 및 별도 프로세스 재열기 후 Z-up·metersPerUnit 1.0을 확인했다.

### 최소 스크립트 검증

- 스크립트: `isaac_sim/scripts/check_environment.py`.
- 실행: Script Editor에서 파일을 읽어 실행.
- 동일 앱 세션에서 2회 `CHECK_OK`, 앱 재시작 후에도 `CHECK_OK` 확인.
- Phase 0에서는 Stage 생성·수정·저장이 미검증이었다. Phase 2에서는 `full_scene_setup.py`로 전체 환경 생성·저장·닫기·재열기와 PNG 렌더를 검증했다. GUI Script Editor 직접 실행은 이번에 수행하지 못했다.

## 2. 진행 상태와 근거 자료

### 진행 상태

Phase 0 초기 세팅은 이전 완료 기록에 따라 완료로 유지한다. Phase 1 종료 당시 마지막 보고 Commit은 `af11aaa`였으며, 이번 Phase 2 착수 때 Windows 저장소를 직접 조회해 HEAD `4faf060`과 변경 없는 작업 트리를 확인했다. GitHub 원격 동기화는 이번에 검증하지 않았다.

2026-09-30 사용자는 정확한 CP 설계도·조명 위치·카메라 설정이 없고 휴대폰 영상 하나만 보유하고 있으며, 이를 고려해 Phase 1을 마무리하도록 지시했다. 이에 현재 자료로 확인할 수 있는 구조·시각 특성을 기록하고, 미확인 항목과 다음 Phase의 조정 방식을 명시하는 것으로 Phase 1 종료 기준을 적용한다.

추가 실측이나 설치 카메라 자료 확보를 Phase 2 착수의 선행 조건으로 두지 않는다. 대용량 USD 관리 방식과 OCR 학습환경의 완료 여부는 여전히 미확인이다.

### 사용자 확인한 데이터 현황

- 현재 실제 데이터는 휴대폰으로 촬영한 CP 영상 하나이다.
- 기존 AI 모니터링 모델은 해당 영상의 앞부분으로 학습하고 뒷부분으로 테스트했다.
- 정확한 분할 시각, 추출 프레임 수, Recognition Crop·라벨 및 테스트를 활용한 수정 이력은 이번 작업에서 확인하지 않았다.
- 실제 설치 카메라로 취득한 CP 데이터는 현재 확보되지 않았다. 현재 재현·평가 대상은 휴대폰 영상이다.
- 핵심 비교는 실제 데이터로 학습한 Recognition 모델과 가상 데이터로 학습한 Recognition 모델을 공통 Real Test에서 평가하는 것이다. Mixed는 공통 계획의 추가 비교 조건으로 유지한다.

### 이번 분석 자료

| 항목 | 확인 내용 | 한계 |
|---|---|---|
| 원본 | 첨부 `IMG_2631.MOV` | 별도 정지 이미지는 이번 첨부에 없음 |
| 영상 크기 | 1920×1080 px | 이 MOV의 해상도이며 실제 OCR 입력 해상도로 확정하지 않음 |
| 영상 길이 | 약 20.54초 | 전체 운전 조건이나 표시 범위를 대표한다고 볼 수 없음 |
| 촬영 기기 | 파일 메타데이터: Apple iPhone 14 Pro Max | 현재 실제 데이터의 촬영 기기이며 실제 사용 렌즈·초점거리·노출은 미확인 |
| 관찰 방식 | 약 2·6·10·14·18초의 개요 프레임, 약 4·20초의 원본 해상도 프레임 확인 | 전 프레임 정답 라벨링은 수행하지 않음 |
| 작업용 외형 참조 | 영상 시작 기준 약 4초 프레임 | 목록 및 초기 배치 비교용. 기존 Train/Test 소속 미확인으로 최종 실험의 보정용 프레임으로는 아직 확정하지 않음 |

기기 메타데이터만으로 실제 촬영 위치, 초점거리, 노출 또는 전처리를 확정하지 않는다. 아래 목록은 이 영상에서 보이는 구성에 한정한다. 1920×1080은 MOV의 확인된 해상도로서 초기 전체 프레임 비교에 사용할 수 있으나, 기존 OCR 전처리 후 해상도는 별도로 확인해야 한다.

## 3. 용어와 ID 규칙 — 제안

기존 첨부 문서에는 Panel·Module·Slot ID 규칙이 없다. 아래는 이번 목록 정리를 위한 제안이며, 기존 데이터 라벨·Config와 대조하기 전에는 호환성이 확인된 규칙으로 취급하지 않는다.

| 계층 | 이번 문서의 의미 | 제안 ID |
|---|---|---|
| Panel | HP1~HP7 각각의 계측기 그룹 | `panel_1`~`panel_7` |
| Module | Panel 안의 온도·압력·진공 컨트롤러 각각 | `temperature`, `pressure`, `vacuum` |
| Slot | Module의 오른쪽 주요 숫자 표시줄 각각 | `slot_1`=위, `slot_2`=아래 |
| 전체 식별자 | Panel·Module·Slot의 조합 | 예: `panel_1/temperature/slot_1` |

물리 제어반의 왼쪽·오른쪽 문과 논리적 Panel을 구분한다. 영상에서 HP1~HP5는 왼쪽 문, HP6~HP7은 오른쪽 문에 있다. 제어반 문 2개를 Panel 2개로 세지 않는다.

온도·압력 컨트롤러에는 주요 숫자열 왼쪽의 작은 숫자·기호도 보인다. 이번 Slot은 오른쪽 주요 숫자열만을 대상으로 한다. 작은 숫자·기호의 기능과 OCR 포함 여부는 추가 확인 사항이다.

## 4. 영상에서 확인한 구성

### 4.1 Panel 목록

| 제안 Panel ID | 실제 표기 | 영상 내 배치 | 확인된 Module | 주요 Slot 수 |
|---|---|---|---|---:|
| `panel_1` | HP1 / 번호 1 | 왼쪽 문, 위에서 1번째 | 온도·압력·진공 | 6 |
| `panel_2` | HP2 / 번호 2 | 왼쪽 문, 위에서 2번째 | 온도·압력·진공 | 6 |
| `panel_3` | HP3 / 번호 3 | 왼쪽 문, 위에서 3번째 | 온도·압력·진공 | 6 |
| `panel_4` | HP4 / 번호 4 | 왼쪽 문, 위에서 4번째 | 온도·압력·진공 | 6 |
| `panel_5` | HP5 / 번호 5 | 왼쪽 문, 위에서 5번째 | 온도·압력·진공 | 6 |
| `panel_6` | HP6 / 번호 6 | 오른쪽 문, HMI 아래의 윗 그룹 | 온도·압력·진공 | 6 |
| `panel_7` | 번호 7 | 오른쪽 문, HP6 아래의 그룹 | 온도·압력·진공 | 6 |

번호 7은 확인되지만 HP7 문자 라벨은 이 영상에서 명확하게 판독되지 않는다. `panel_7`은 번호 7과 배치에 근거한 대응이다.

### 4.2 Module과 Slot의 공통 특성

| 제안 Module ID | 컨트롤러 위 라벨 | 각 Panel 안의 위치 | 외형 | `slot_1` | `slot_2` |
|---|---|---|---|---|---|
| `temperature` | TEMPERATURE CONTROLLER | 왼쪽 | 검정색, 비교적 넓은 직사각형 | 위쪽 주요 숫자열, 녹색 계열 | 아래쪽 주요 숫자열, 주황/황색 계열 |
| `pressure` | PRESSURE CONTROLLER | 가운데 | 검정색, 온도 모듈과 유사한 외형 | 위쪽 주요 숫자열, 녹색 계열 | 아래쪽 주요 숫자열, 주황/황색 계열 |
| `vacuum` | VACUUM CONTROLLER | 오른쪽 | 폭이 좁은 세로형, 밝은색 하부 조작부 | 위쪽 주요 숫자열, 녹색 계열 | 아래쪽 주요 숫자열, 주황/황색 계열 |

각 Module에는 위·아래 두 주요 숫자 표시줄이 보인다. 숫자는 분절된 세그먼트 형태이며 일부 표시에는 소수점이 보인다. 정확한 세그먼트 형상·전체 문자 집합·최대 자릿수는 미확인으로 남긴다. 이후 기존 영상의 Crop으로 추가 분석하고, 근접 자료가 확보되면 보완한다. 색상은 촬영 영상에서의 관측 색이며 LED의 정확한 색도나 Emission 값이 아니다.

위·아래 표시줄의 현재값/PV·설정값/SV 의미, 단위, 배율은 미확인이다. Slot 이름에 의미를 부여하지 않는다.

### 4.3 전체 Module·Slot 목록

아래 각 행의 두 Slot은 해당 Panel·Module 아래에 속한다. 합계는 7 Panel × 3 Module × 2 Slot = 21 Module, 42 주요 숫자 Slot이다.

| Panel | Module | 위쪽 Slot의 전체 ID | 아래쪽 Slot의 전체 ID |
|---|---|---|---|
| `panel_1` | 온도 | `panel_1/temperature/slot_1` | `panel_1/temperature/slot_2` |
| `panel_1` | 압력 | `panel_1/pressure/slot_1` | `panel_1/pressure/slot_2` |
| `panel_1` | 진공 | `panel_1/vacuum/slot_1` | `panel_1/vacuum/slot_2` |
| `panel_2` | 온도 | `panel_2/temperature/slot_1` | `panel_2/temperature/slot_2` |
| `panel_2` | 압력 | `panel_2/pressure/slot_1` | `panel_2/pressure/slot_2` |
| `panel_2` | 진공 | `panel_2/vacuum/slot_1` | `panel_2/vacuum/slot_2` |
| `panel_3` | 온도 | `panel_3/temperature/slot_1` | `panel_3/temperature/slot_2` |
| `panel_3` | 압력 | `panel_3/pressure/slot_1` | `panel_3/pressure/slot_2` |
| `panel_3` | 진공 | `panel_3/vacuum/slot_1` | `panel_3/vacuum/slot_2` |
| `panel_4` | 온도 | `panel_4/temperature/slot_1` | `panel_4/temperature/slot_2` |
| `panel_4` | 압력 | `panel_4/pressure/slot_1` | `panel_4/pressure/slot_2` |
| `panel_4` | 진공 | `panel_4/vacuum/slot_1` | `panel_4/vacuum/slot_2` |
| `panel_5` | 온도 | `panel_5/temperature/slot_1` | `panel_5/temperature/slot_2` |
| `panel_5` | 압력 | `panel_5/pressure/slot_1` | `panel_5/pressure/slot_2` |
| `panel_5` | 진공 | `panel_5/vacuum/slot_1` | `panel_5/vacuum/slot_2` |
| `panel_6` | 온도 | `panel_6/temperature/slot_1` | `panel_6/temperature/slot_2` |
| `panel_6` | 압력 | `panel_6/pressure/slot_1` | `panel_6/pressure/slot_2` |
| `panel_6` | 진공 | `panel_6/vacuum/slot_1` | `panel_6/vacuum/slot_2` |
| `panel_7` | 온도 | `panel_7/temperature/slot_1` | `panel_7/temperature/slot_2` |
| `panel_7` | 압력 | `panel_7/pressure/slot_1` | `panel_7/pressure/slot_2` |
| `panel_7` | 진공 | `panel_7/vacuum/slot_1` | `panel_7/vacuum/slot_2` |

### 4.4 주변 구성과 촬영상 관찰

- 제어반은 밝은색 외장이며 중앙에 좌우 문 경계가 보인다.
- 오른쪽 위에는 `OPERATION PANEL` 표기와 HMI 화면이 있다.
- 각 HP 그룹의 오른쪽에는 빨간 정지 버튼과 번호 표기가 보인다. 오른쪽 아래에는 별도 버튼 그룹과 `로더기` 표기가 있다.
- HP6·HP7 사이에는 초록색 반투명 커버가 보인다. 별도 숫자 Module로 세지 않으며 기능은 미확인이다.
- 외장과 표시창에는 위치에 따른 밝기 차이와 반사성 밝은 영역이 보인다. 광원 위치·개수·세기·표면 Roughness는 영상만으로 정량화하지 않았다.
- 주요 숫자열의 선명도와 밝기는 위치에 따라 다르게 보이며, 온도·압력 모듈의 작은 보조 표시 일부는 프레임에서 분절되거나 불완전하게 보인다. 원인이 표시 갱신, 촬영 노출, 흔들림 또는 압축 중 무엇인지는 미확인이다.
- 프레임 사이에 제어반의 이미지상 위치가 조금 달라진다. 특정 참조 프레임의 픽셀 좌표를 영상 전체에 적용되는 고정 ROI로 취급하지 않는다.

HMI, 버튼, 라벨, 커버는 주변 Geometry·Material 후보로 기록한다. 이번 42 Slot 목록에는 포함하지 않는다. 42는 주요 숫자 표시줄 수이며, 제어반의 모든 발광 요소나 문자 영역 수가 아니다.

## 5. 미확인 항목과 후속 처리

아래 항목은 Phase 1 종료를 막는 조건이 아니라 후속 구현·Dataset 작업에서 추적할 항목이다. 추가 자료가 없으면 관찰에 근거한 근사값이나 임시값을 명시적으로 사용하고, 실측값으로 기록하지 않는다.

| 항목 | 현재 확인 수준 | 추가 확보 또는 측정 방법 |
|---|---|---|
| Panel 대응 | 번호 1~7과 배치 확인 | 기존 OCR 라벨의 Panel 번호와 대조하고 번호 7 그룹의 HP 표기 근접 확인 |
| Slot 의미 | 위·아래 위치와 관측 색상 확인 | 기기 모델·매뉴얼·현장 설정으로 현재값/설정값 등 의미 확인; 두 줄 모두 OCR 대상인지 확인 |
| 보조 숫자·기호 | 온도·압력 모듈의 왼쪽에 존재 | 근접 촬영과 기존 Crop·라벨 대조로 주요 숫자열과 경계 및 포함 여부 결정 |
| Module 모델·단위 | TEMPERATURE/PRESSURE/VACUUM 라벨 확인 | 모델명·명판·설정과 매뉴얼에서 단위 및 배율 확인; ℃·MPa·kPa 등을 임의 확정하지 않음 |
| 문자열 표시 규칙 | 소수점이 포함된 숫자열 존재 | 대표 운전 조건의 원본 Crop과 매뉴얼로 자릿수, 소수점 위치, 음수, 선행 0, 공백, 오류 문자열 확인 |
| 표시값 범위 | 짧은 영상의 일부 값만 관찰 | 운전 조건별 기록과 설정을 확보; 이 영상의 최소·최대값을 생성 범위로 사용하지 않음 |
| 제어반·Module 물리 치수 | 외형과 상대 배치 확인 | 줄자로 문 폭·높이, Module 외곽 폭·높이, 표시창 크기 및 중심 간격 측정; mm 기록 후 m 변환 |
| 각 Module의 설치 위치 | 순서와 문별 배치 확인 | 기준 원점과 측정 기준면을 정해 중심 위치·설치 깊이·문 사이 관계를 실측 |
| 기준 영상과 픽셀 좌표 | MOV는 1920×1080 | 기존 영상의 참조 프레임에서 Panel·Module·Slot 경계와 숫자 높이를 측정. 최종 보정용 프레임은 학습/개발 구간에서 선정 |
| Camera 설정 | 스마트폰 촬영 메타데이터만 확인 | 촬영 위치·렌즈·노출의 실제값은 미확인으로 유지. Phase 2에서 가상 카메라의 구도·투영을 영상과 비교하며 조정하고 조정값을 기록 |
| 원본→OCR 전처리 | 이번 첨부로 미확인 | 실제 저장 해상도, 리사이즈·ROI·Crop 여백·색상 변환 및 좌표 변환 규칙 기록 |
| Lighting·Material | 반사와 밝기 차이 관찰 | 기존 영상의 밝기·반사 위치를 비교 목표로 사용. 가상 Light·Material 설정을 조정하되 실제 광원 위치·물성의 복원값으로 주장하지 않음 |
| 번짐·Blur·촬영에 따른 표시 누락 | 원인 미확인 | 기존 영상의 여러 프레임·Crop으로 발생 패턴을 확인. 원인이 미확인인 효과는 재현 후보로 기록하고 랜덤화 범위는 이후 결정 |

측정값에는 단위, 측정 기준점, 촬영/측정 조건과 근거 자료를 함께 남긴다. 아직 물리 치수, Camera Config, Display 구현 방식, Domain Randomization 범위는 확정하지 않았다.

## 6. Phase 1 종료 결정과 Phase 2 구축 방침

### 종료 근거

- 현재 제공된 영상의 해상도·길이·촬영 기기 메타데이터와 복수 시점 프레임을 확인했다.
- 7 Panel, 21 Module, 42 주요 숫자 Slot의 목록과 배치를 작성했다.
- 관찰 사실, ID 제안, 미확인 의미 및 실측 부재를 구분했다.
- 사용자가 현재 보유 자료의 한계를 전제로 분석을 종료하고 구축으로 진행하도록 지시했다.

따라서 Phase 1은 현재 보유 자료 범위에서 완료로 기록한다. 정밀 실측, 모든 Slot의 bbox·정답 전사, 최종 Dataset Split 확정까지 완료한 것으로 취급하지 않는다.

### 구축 방침

| 요소 | Phase 2에서 사용할 근거 | 미확인값 처리 |
|---|---|---|
| Geometry | 영상에서 보이는 문·Module의 상대 배치와 크기 비율 | 실제 치수는 미확인. 모델링용 임시 크기는 별도로 표시하고 수정 가능하게 관리 |
| Camera | 참조 프레임의 구도, Module의 이미지상 크기와 원근 | 실제 촬영 설정과 분리한 가상 조정값을 사용 |
| Render 해상도 | 확인된 원본 MOV 1920×1080 | 초기 전체 프레임 비교 기준으로 사용. Recognition 입력 크기는 이후 전처리 규격에서 결정 |
| Lighting·Material | 표시창 대비, 외장의 밝기 차이와 반사 위치 | 가상 설정은 영상 재현용 근사값으로 기록 |
| Display | 두 주요 표시줄, 관측 색상, 분절된 숫자 형태와 소수점 | 현재값/설정값 의미와 미관측 문자열 규칙은 확정하지 않음 |

단일 영상에서 물리 치수·카메라 거리·초점거리의 조합을 유일하게 확정할 근거가 없다. Stage의 metersPerUnit 1.0은 단위 규칙이며 실제 제어반 크기를 알려주는 측정값이 아니다. 영상에 맞춘 설정은 원래 설비·카메라·조명의 정확한 복원값으로 주장하지 않는다.

합성 이미지의 픽셀 단위 일치나 실제 촬영 설정값의 완전 복제를 완료 기준으로 삼지 않는다. 우선 기본 조건에서 숫자 영역의 위치·크기·원근·표시 특성을 비교한다. 카메라·조명 다양화는 Base Scene 검증 후 단계적으로 추가하며, 현재는 수치 범위를 임의 확정하지 않는다.

### Config·실험 기록 원칙

- 실제 측정값, 영상에서 확인한 값, 영상에 맞춘 근사값, 구현용 임시값을 구분한다.
- 값의 단위·근거·조정 목적을 기록한다. 아직 없는 실제값에 가상 조정값을 덮어쓰지 않는다.
- USD Scene/Asset과 Python 자동화 로직을 분리하고, 기존 저장소 구조를 확인한 뒤 Camera·Light·Material·Display 설정을 Config로 관리한다.
- 최종 실험의 Scene 보정·랜덤화 선택에는 Real Train/Validation을 사용한다. 기존 영상의 구간 사용 이력을 확인하기 전의 외형 비교는 예비 작업으로 기록한다.
- 두 주요 모델은 동일한 Real Test에서 평가한다. 모델·초기화·전처리·학습량과 Synthetic 데이터량을 기록한다.

### 후속 작업으로 넘기는 항목

- Phase 2: Panel·Module 이미지상 경계의 비교, 상대 Geometry·가상 Camera·Lighting 조정, Stage 생성·저장 검증.
- Phase 3: 표시 문자열 규칙과 변경 로직 검증, 필요한 OCR 대상·기호 범위 확인.
- Phase 4~6 준비: 기존 Train/Test 구간·사용 이력, Real Validation, Crop·Label 규격과 Split 고정. 기존 라벨이 제공되면 제안 ID와 대조.
- 자료 확보 시 보완: 설계도·실측 치수·기기 매뉴얼·실제 조명 및 촬영 설정.

위 항목은 완료하지 않았으며 담당 Phase에서 진행한다.

## 7. Phase 2 첫 작업 이력 — Panel 1

**Panel 1의 세 Module·여섯 주요 표시 영역을 단순 Geometry로 구성하고 USD 저장·재열기를 검증했다.**

2026-09-30 사용자가 지정한 `C:\Users\rlaek\Downloads\IMG_2631.MOV`를 직접 읽었다. FFmpeg로 1920×1080, 약 20.54초를 재확인하고 2·4·10·18초 프레임을 추출했다. 4·18초 프레임을 직접 보았으며, 4초의 수동 근사 bbox를 Config에 기록했다. 영상·원본 프레임은 수정하지 않았다.

모델링 배율은 0.001 m/px 임시값이며 원근 보정이나 실측에 근거한 치수가 아니다. 모듈 폭×높이는 온도 0.143×0.134 m, 압력 0.140×0.134 m, 진공 0.067×0.132 m이다. 모든 깊이와 검토용 Camera·Light·Material도 임시 설정으로 구분했다. 숫자열의 값·문자 형상은 아직 구현하지 않았다.

실제 설치본은 기존 문서와 다른 6.1.0 RC였으며 설치를 변경하지 않았다. GUI 제어 도구 연결 실패로 같은 Python 생성·검증 함수를 Standalone headless에서 실행했다. 디스크 재열기, 앱 저장·닫기·재열기, 새 앱 프로세스 재열기에서 Z-up·metersPerUnit 1.0과 Module 3개·Slot 6개의 배치 검사가 통과했다. 1200×600 검토 렌더도 확인했다. 이 크기는 실영상/OCR 입력 해상도가 아니다.

이후 사용자의 전체 환경 제작 요청에 따라 8절의 범위로 확대했다. 2026-10-01 단일 Panel 시험 파일·설명 문서·검증 산출물은 사용자 요청으로 삭제했다. 위 내용은 초기 검증 이력이며 현재 실행 대상은 전체 환경이다. 실행법은 [phase2_full_scene.md](phase2_full_scene.md)를 사용한다.

이번 문서는 현재 Windows 저장소에 직접 갱신했다. Commit·Push, Notion·다른 프로젝트 소스 동기화는 수행하지 않았다.

## 8. 최신 Phase 2 결과 — 전체 정적 가상환경

`isaac_sim/stages/press_cp_main.usda`에 두 문·7 Panel·21 Module·42 Slot, 발광 세그먼트 숫자, HMI·조작부·명판·손잡이·초록 커버·주변 배관·바닥·벽을 구성했다. 원본 4초 프레임의 배치를 가상 투시 Camera로 근사했으며, 기준·전체 사선·근접 Camera를 각각 제공한다.

실제 치수는 계속 미확인이다. 폭 1.77 m·높이 1.50 m·깊이 0.30 m와 가상 초점거리 1800 px는 이번 전체 환경의 임시값이다. 7절의 0.001 m/px 배율은 초기 Panel 1 시험에만 해당한다. HMI·안전 안내문과 가려진 부분은 모식 표현이며 초기 숫자는 검증된 OCR 정답이 아니다.

2026-09-30 14:31 KST, 설치된 Isaac Sim 6.1.0 RC에서 생성·저장·닫기·재열기와 별도 프로세스 재열기가 모두 통과했다. 7/21/42 개수·고유 ID·배치·표시 문자열·텍스처 상대 참조·Z-up·metersPerUnit 1.0을 검사하고 1920×1080 렌더를 기록했다. 이번 직접 실행 방식은 Standalone headless이며 GUI Script Editor 조작 검증과 구분한다.

중간에 Viewport 준비 시간 초과 후 Fabric native crash가 1회 있었다. 실제 프레임 준비를 기다리도록 보완한 뒤 생성·재열기 두 실행이 통과했으며 근본 원인은 확정하지 않았다. 최종 보고서는 `outputs/full_scene/build_report.json`, `reopen_report.json`, 실행법과 한계는 [phase2_full_scene.md](phase2_full_scene.md)에 있다.

2026-10-01 주요 42 Slot의 실영상·렌더 Crop 예비 비교와 LED 발광 수정을 수행했다. 다음 작업은 숫자 위치·폭·기울기 보정이다. 반사·노이즈·표시 갱신 효과, 동적 문자열, 학습용 데이터 생성과 최종 평가까지 완료한 것은 아니다.
