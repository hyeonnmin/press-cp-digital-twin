# 프로젝트 진행 상황

최종 갱신: 2026-09-30 (Asia/Seoul)

현재 Phase: 2 — 전체 정적 Base Scene 구축·실행 검증 완료, 영상 유사성 정량 검증은 남음

현재 작업: 영상 기반 7 Panel·21 Module·42 Slot과 제어반·HMI·조작부·주변 구조 제작 완료. 다음은 주요 Slot의 실영상·렌더 Crop 비교.

## 최신 결과 — 전체 CP 가상환경

- 사용자 요청에 따라 Panel 1 시험 모델에서 전체 제어반과 주변 환경으로 확대했다. 완료 기준은 전체 Scene을 실제 Isaac Sim에서 생성·저장·재열기하고 렌더로 확인하는 것이다.
- 진입점: `isaac_sim/stages/press_cp_main.usda`. 영상 비교용 `reference`, 전체 사선 `overview`, 근접 `detail` Camera를 제공한다.
- 좌측 5개·우측 2개 Panel, 21개 계측기, 42개 발광 숫자열, 문·손잡이·경첩·버튼·HMI·명판·초록 커버 및 주변 배관·바닥·벽을 구성했다.
- `config/press_cp_scene.json`에서 배치·문자열·Camera·Light·Material을 관리한다. 제어반·주변 USD와 Python 생성 로직을 분리했으며 Asset·텍스처는 상대 참조한다.
- 설치된 Isaac Sim 6.1.0 RC의 Standalone headless에서 2026-09-30 14:31 KST 생성 실행과 별도 프로세스 재열기가 모두 `FULL_SCENE_OK`, 종료 코드 0으로 통과했다. Z-up·단위, 7/21/42 개수·고유 ID·배치·문자열·텍스처 참조를 확인했다.
- 1920×1080의 세 시점과 재열기 렌더를 기록했다. 기준·전체 렌더에서 전체 배치와 숫자, Panel 7 커버 주변 표시를 직접 확인했다. 코드·Config·Asset·렌더 Hash 및 실행 조건은 `outputs/full_scene/build_report.json`, `reopen_report.json`에 있다.
- 중간 실행에서 Viewport 준비 시간 초과 뒤 Fabric native crash가 1회 발생했다. 실제 렌더 프레임을 기다리도록 보완한 뒤 최종 두 실행은 통과했다. 근본 원인은 확정하지 않았다.
- 치수·가상 카메라·광원은 영상 재현용 근사값이다. HMI·안전 안내문·보이지 않는 주변 구조는 모식 표현이며 초기 문자열은 검증된 실영상 정답이 아니다.
- 사용법·근거·한계: [phase2_full_scene.md](phase2_full_scene.md). 기존 Panel 1 결과는 아래에 작업 이력으로 유지한다.

다음 작업 하나: **주요 Slot의 실영상·렌더 Crop을 대응시켜 위치·크기·색상·가림을 비교한다.** 최종 보정 조건을 고정하기 전에 기존 영상의 Train/Test 사용 구간을 확인한다. 동적 표시값 변경과 학습용 데이터 생성은 후속 Phase로 남긴다.

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

## Phase 2 초기 작업 이력 — Panel 1 Geometry

### 완료한 작업과 검증

- 지정된 로컬 MOV에서 2·4·10·18초 프레임 추출, 4·18초 영상 직접 확인. 4초 프레임의 수동 근사 bbox로 배치 구성.
- `config/panel_1_geometry.json`에 영상 기준, 임시 배율·깊이, 주요 표시 영역, 검토용 Camera·Light·Material 기록.
- `isaac_sim/assets/cp_panel/panel_1_geometry.usda`와 `isaac_sim/stages/panel_1_preview.usda` 생성. Asset과 Scene/Python 로직 분리.
- 실제 Isaac Sim에서 모듈 3개·주요 표시 영역 6개, 좌우·위아래 관계, 표시 영역의 모듈 내 포함과 전면 배치 확인.
- 디스크 열기→앱 열기→저장→닫기→재열기 검사 통과. 별도 새 프로세스의 `--reopen-only`도 통과. Z-up·metersPerUnit 1.0 유지.
- 최종 두 실행의 종료 코드 0, `PANEL1_GEOMETRY_OK`, 1200×600 PNG 기록·디코딩·시각 확인 완료.
- 상세 결과: `outputs/phase2_validation/build_report.json`, `reopen_report.json` (Git 제외). 코드·Config·USD·PNG Hash, 원본 영상 Hash, 적용 Config, 버전과 실행 모드 기록.
- 구현·실행법·임시 치수·공식 API 근거: [phase2_panel_1.md](phase2_panel_1.md). 주요 결정: [decisions.md](decisions.md).

### 환경 차이와 남은 한계

- 직접 확인한 설치 버전은 **6.1.0-rc.26+release.49347.2d230af4.gl**이다. 기존 6.0.1 기록과 다르며 이번 작업에서 설치를 변경하지 않았다.
- Windows GUI 제어 연결 실패로 실제 검증은 **Standalone headless**에서 수행했다. GUI Script Editor용 동일 함수 실행법은 제공했으나 이번 GUI 직접 실행은 미검증이다.
- 배경판은 Panel 1 주변 일부, 크기는 실측값이 아닌 임시값이다. 녹색·황색 사각형은 표시 영역 placeholder이며 숫자 구현이 아니다.
- 이 초기 작업 시점에는 전체 제어반과 7 Panel 확장이 미완료였다. 이후 확장 결과는 위 최신 결과에 기록했다. 실영상과의 정량 유사성 검증은 여전히 남아 있다.

### 당시 계획 — 이후 전체 환경 제작 요청으로 확대

**Panel 1의 가상 투시 Camera를 구성해 참조 프레임과 모듈·표시 영역의 위치·크기·원근을 비교한다.** 현재 정면 직교 Camera는 배치 검토용이다. 최종 실험용 보정 프레임은 Train/Test 사용 이력을 확인한 뒤 고정한다. 이후 조명·Material, 나머지 Panel 확대를 진행하며 숫자 자동화는 Phase 3에서 수행한다.

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

## Windows 저장소 반영 상태 — 직접 확인

- 작업 시작 시 `git status --short`는 비어 있었고, HEAD는 `4faf060` — `docs: close phase 1 with phone video reference`였다.
- 이번 Phase 2 코드·Config·USD·문서는 현재 Windows 저장소에 생성·수정했다. Commit·Push는 하지 않았다.
- 원본 MOV, 추출 프레임, 디코더, 상세 보고서와 렌더는 일반 Git에 추가하지 않는다.
- GitHub·Notion·다른 프로젝트 소스의 동기화는 수행하지 않았다.
