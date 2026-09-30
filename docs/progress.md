# 프로젝트 진행 상황

최종 갱신: 2026-09-30 (Asia/Seoul)

현재 Phase: 2 — Base Scene 착수 준비

현재 작업: Phase 1 종료 문서 작성 완료, Phase 2 첫 Geometry 작업 준비

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

## Phase 2 — 착수 준비, 미구현

### 다음 작업 하나

**Panel 1의 온도·압력·진공 Module 배치를 단순 Geometry로 구성하고 USD로 저장한다.**

실행환경: Isaac Sim 6.0.1, GUI Script Editor, Z-up, metersPerUnit 1.0.

먼저 Windows 저장소의 AGENTS.md·폴더·Config를 확인한다. 제어반 바탕과 Panel 1의 세 Module 및 각 두 표시 영역을 만든다. 실제 치수가 없으므로 수정 가능한 임시 크기로 시작하고 근거를 기록한다.

완료 기준: USD 저장·재열기 후 Stage 축·단위가 유지되며, Panel 1의 세 Module과 여섯 주요 표시 영역이 관찰한 좌우·위아래 관계대로 존재한다. 사용한 크기와 임시값 여부가 문서화된다.

이후 Camera·Lighting과 실제/합성 영상 비교, 나머지 Panel 확대를 진행한다. 숫자 변경 자동화는 Phase 3에서 수행한다. 이번 종료 작업에서는 Stage나 코드를 생성하지 않았다.

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

## Windows 저장소 반영 상태

- 이번 갱신 파일: docs/real_environment.md, docs/progress.md.
- 이번 작성본의 Windows 저장소 반영과 Commit·Push는 미확인이다. 앞선 문서 변경의 Commit·Push 성공 여부도 이번 대화에서 보고받지 않았다.
- 권장 Commit 메시지: docs: close phase 1 with phone video reference.
- 마지막 확인된 Commit은 Phase 0의 af11aaa이다. 새로운 Commit ID를 임의로 기록하지 않는다.
- 로컬 반영 및 Commit·Push 후 실제 결과를 기준으로 이 절을 갱신한다. 문서 변경은 Windows 저장소·Notion·다른 프로젝트 소스에 자동 반영되지 않는다.
