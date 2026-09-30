# 실행환경과 실제 CP 환경 분석

최종 갱신: 2026-09-30 (Asia/Seoul)

현재 Phase: 1 — 실제 CP 환경 분석 진행 중

이번 작업: 실제 자료의 Panel·Module·Slot 목록 작성. 물리 치수, 기준 카메라, 표시 규칙은 아직 미확정이다.

## 1. 개발 실행환경

| 항목 | 값 | 확인 근거 |
|---|---|---|
| OS | Windows-11-10.0.26200-SP0 | Phase 0 스크립트 출력 |
| Isaac Sim | 6.0.1 | 사용자 확인 |
| 앱 실행 | `C:\isaacsim\isaac-sim.bat` | 사용자 확인 |
| 코드 실행 방식 | GUI Script Editor | 사용자 실행 결과 |
| Isaac Sim 내부 Python | 3.12.13 | Phase 0 스크립트 출력 |
| GPU | NVIDIA GeForce RTX 4070 SUPER | Phase 0 nvidia-smi 출력 |
| GPU Driver | 591.86 | Phase 0 nvidia-smi 출력 |
| GPU 메모리 | 12282 MiB | Phase 0 nvidia-smi 출력 |

### Stage 확인 결과

- 확인 대상: 현재 열린 미저장 익명 Stage.
- Up-axis: Z.
- Meters per unit: 1.0.
- 위 값은 해당 Stage에서 읽은 결과다. 프로젝트 Base Scene은 아직 생성하지 않았다.

### 최소 스크립트 검증

- 스크립트: `isaac_sim/scripts/check_environment.py`.
- 실행: Script Editor에서 파일을 읽어 실행.
- 동일 앱 세션에서 2회 `CHECK_OK`, 앱 재시작 후에도 `CHECK_OK` 확인.
- Stage 생성·수정·저장 기능은 미검증.

## 2. 진행 상태와 근거 자료

### 진행 상태

첨부 `progress.md` 마지막의 「Phase 0 완료 판단」에 따라 초기 세팅은 완료로 기록한다. 마무리 문서 Commit은 `af11aaa`이다. 이는 첨부 기록과 사용자 보고에 근거하며, 이번 분석에서 Windows 저장소나 GitHub를 직접 조회한 결과는 아니다.

같은 파일의 이전 「진행 중」·「미확인·미완료」에는 기본 폴더, Stage 축·단위, 반복 실행 등 이미 완료 기록이 있는 항목이 남아 있다. 이 항목은 오래된 상태로 보고 정리가 필요하다. 대용량 USD 관리 방식과 OCR 학습환경은 이번 자료로 완료 여부를 판단할 수 없다.

Phase 1은 진행 중이다. 이번 목록 작성만으로 Phase 1 전체가 완료된 것은 아니다.

### 이번 분석 자료

| 항목 | 확인 내용 | 한계 |
|---|---|---|
| 원본 | 첨부 `IMG_2631.MOV` | 별도 정지 이미지는 이번 첨부에 없음 |
| 영상 크기 | 1920×1080 px | 이 MOV의 해상도이며 실제 OCR 입력 해상도로 확정하지 않음 |
| 영상 길이 | 약 20.54초 | 전체 운전 조건이나 표시 범위를 대표한다고 볼 수 없음 |
| 촬영 기기 | 파일 메타데이터: Apple iPhone 14 Pro Max | OCR 운용 카메라 모델·렌즈 정보와 구분 |
| 관찰 방식 | 약 2·6·10·14·18초의 개요 프레임, 약 4·20초의 원본 해상도 프레임 확인 | 전 프레임 정답 라벨링은 수행하지 않음 |
| 대표 기준 | 영상 시작 기준 약 4초 프레임 | 현재 목록을 위한 참조 시점이며 최종 Base Scene 기준 영상은 미선정 |

자료 시각·기기 메타데이터만으로 실제 산업용 카메라의 위치, 초점거리, 노출 또는 전처리를 추정하지 않는다. 아래 목록은 이 영상에서 보이는 구성에 한정한다.

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

각 Module에는 위·아래 두 주요 숫자 표시줄이 보인다. 숫자는 분절된 세그먼트 형태이며 일부 표시에는 소수점이 보인다. 정확한 세그먼트 형상·전체 문자 집합·최대 자릿수는 근접 자료로 확인한다. 색상은 촬영 영상에서의 관측 색이며 LED의 정확한 색도나 Emission 값이 아니다.

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
- 프레임 사이에 제어반의 이미지상 위치가 조금 달라진다. 이 영상에서 얻은 픽셀 좌표를 고정 OCR 카메라의 ROI로 그대로 사용하지 않는다.

HMI, 버튼, 라벨, 커버는 주변 Geometry·Material 후보로 기록한다. 이번 42 Slot 목록에는 포함하지 않는다. 42는 주요 숫자 표시줄 수이며, 제어반의 모든 발광 요소나 문자 영역 수가 아니다.

## 5. 추가 확인·측정이 필요한 항목

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
| 기준 영상과 픽셀 좌표 | MOV는 1920×1080 | 실제 OCR 운용 카메라의 고정 시점 원본을 확보해 Panel·Module·Slot 경계와 숫자 높이 측정 |
| Camera 설정 | 스마트폰 촬영 메타데이터만 확인 | OCR 운용 카메라·렌즈 모델, 설치 거리·높이·방향, 초점거리/FOV, 노출·게인·초점 확인 |
| 원본→OCR 전처리 | 이번 첨부로 미확인 | 실제 저장 해상도, 리사이즈·ROI·Crop 여백·색상 변환 및 좌표 변환 규칙 기록 |
| Lighting·Material | 반사와 밝기 차이 관찰 | 현장 조명 사진·위치와 동일 시점의 원본 이미지 확보; 반사 위치와 숫자/배경 밝기 비교 |
| 번짐·Blur·촬영에 따른 표시 누락 | 원인 미확인 | 고정 카메라 연속 프레임과 근접 자료를 비교해 반복 발생 여부 확인; 랜덤화 범위는 이후 결정 |

측정값에는 단위, 측정 기준점, 촬영/측정 조건과 근거 자료를 함께 남긴다. 아직 물리 치수, Camera Config, Display 구현 방식, Domain Randomization 범위는 확정하지 않았다.

## 6. 이번 작업 결과와 다음 행동

### 완료한 내용

- 첨부 진행 문서의 마지막 완료 기록으로 Phase 0 완료 상태 확인.
- 영상 메타데이터와 복수 시점 프레임 확인.
- 7 Panel, 21 Module, 42 주요 숫자 Slot의 목록 및 위치 기준 ID 제안 작성.
- 관찰 사실, ID 제안, 미확인 의미 및 추가 측정 항목을 구분.

### 남은 문제

- ID 규칙과 OCR 대상 범위는 기존 데이터 라벨과 대조가 필요하다.
- Slot 의미·문자 규칙·물리 치수·OCR 기준 카메라와 픽셀 영역은 미확인이다.
- 영상의 표시 문자열을 모두 정답 라벨로 전사하거나 Base Scene을 구현하지 않았다.
- 이 파일의 갱신이 Windows 저장소·Notion·다른 업로드 파일에 자동 반영된 것은 아니다.

### 다음 작업 하나

**실제 OCR 운용 카메라의 고정 시점 원본 프레임 1장을 기준으로 숫자 영역을 정의한다.** 먼저 기존 라벨과 위·아래 주요 표시줄 및 보조 표시의 대상 범위를 대조한다. 스마트폰 영상의 영역 좌표는 참고용으로만 사용한다.

완료 기준: 대상 범위가 확인된 42 주요 Slot 각각에 대해 `Panel / Module / Slot / bbox / 화면 문자열 / 판독 상태`가 연결되고, 원본 해상도와 좌표 기준이 기록되어 있다. 불명확한 문자열은 추정 정답을 넣지 않고 미판독으로 표시한다. 기존 라벨의 대상이 다르면 그 차이를 먼저 문서화하고 목록을 수정한다.

권장 bbox 규칙은 이미지 좌상단 원점, x는 오른쪽·y는 아래쪽, 픽셀 단위의 `[x_min, y_min, x_max, y_max)`이다. 이는 제안이며 기존 데이터 형식을 확인한 뒤 확정한다.

### docs/progress.md에 반영할 요약 — 제안

```markdown
현재 Phase: 1 — 실제 CP 환경 분석 진행 중
현재 작업: Panel·Module·Slot 목록 초안 작성 완료

- IMG_2631.MOV에서 7개 HP 그룹, 21개 컨트롤러, 42개 주요 숫자 표시줄 확인
- panel_1~7 / temperature·pressure·vacuum / slot_1(위)·slot_2(아래) ID 제안
- Slot 의미와 기존 OCR 라벨 대응은 미확인
- 영상은 스마트폰 촬영 1920×1080이며 OCR 기준 카메라·전처리 해상도는 별도 확인 필요
- 다음 작업: 실제 OCR 고정 카메라 원본 프레임 1장과 기존 라벨을 대조해 Slot별 bbox·문자열·판독 상태 기록
- Phase 1 전체 완료는 아님; 물리 치수·Camera·Lighting 기준값 확보 필요
```

위 요약은 제안이며 이번 작업에서는 첨부 `progress.md`를 수정하지 않았다. 해당 문서의 오래된 진행 중·미확인 항목도 다음 갱신 때 정리한다.
