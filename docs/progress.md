# 프로젝트 진행 상황

최종 갱신: 2026-09-30 (Asia/Seoul)

현재 Phase: 1 — 실제 CP 환경 분석 진행 중

현재 작업: Panel·Module·Slot 목록 초안 작성 완료, 실제 OCR 기준 프레임 확보 대기

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

## Phase 1 — 진행 중

### 완료한 분석 작업

- 첨부 `IMG_2631.MOV`의 메타데이터와 여러 시점 프레임 확인.
- 영상에서 7개 HP 그룹, 21개 온도·압력·진공 컨트롤러, 42개 주요 숫자 표시줄 확인.
- 왼쪽 문에 HP1~HP5, 오른쪽 문에 HP6·번호 7 그룹 배치 확인.
- 논리적 Panel과 물리 제어반의 좌우 문을 구분해 목록 작성.
- `panel_1`~`panel_7` / `temperature`·`pressure`·`vacuum` / `slot_1`(위)·`slot_2`(아래) ID 규칙 제안.
- 관찰 사실, 제안, 미확인 항목과 추가 측정 방법을 `docs/real_environment.md`에 작성.
- 문서의 Module 21개 행과 고유 Slot ID 42개의 개수·중복 여부 검증.

영상은 스마트폰 촬영 자료이며 1920×1080이다. 이 해상도와 영상 속 시점을 실제 OCR 운용 카메라의 해상도·고정 ROI로 확정하지 않는다. 번호 7은 확인했지만 HP7 문자 라벨은 명확하게 판독하지 못했다.

### 미확인·미완료

- 기존 OCR 라벨과 제안 Panel·Module·Slot ID의 대응.
- 위·아래 Slot의 현재값/설정값 의미 및 보조 숫자·기호의 OCR 포함 여부.
- 표시 단위, 자릿수, 소수점·음수·선행 0·공백·오류 문자열 규칙과 값 범위.
- 실제 OCR 운용 카메라 원본 프레임과 저장·전처리 해상도.
- Slot별 bbox·표시 문자열·판독 상태.
- Panel·Module·표시창의 물리 치수, 설치 위치와 깊이.
- 기준 Camera·Lighting·Material·반사·번짐 특성의 측정값.

## Windows 저장소 반영 상태

- 이번 작성본: `docs/real_environment.md`, `docs/progress.md`.
- 작성본은 현재 작업 공간에서 검토되었으며 Windows 저장소에는 아직 반영되지 않았다.
- 이번 변경의 Commit·Push는 아직 수행·확인하지 않았다.
- 다음 Commit 메시지 제안: `docs: record phase 1 CP environment inventory`.
- 로컬 반영과 Commit·Push 성공 후 실제 Commit ID와 확인 결과로 이 절을 갱신한다.
- 문서 변경이 Windows 저장소·Notion·프로젝트의 다른 소스에 자동 반영된다고 가정하지 않는다.

## 다음 작업 하나

**실제 OCR 운용 카메라 원본 프레임 1장에서 Panel 1의 6개 주요 Slot 경계와 문자열을 기록한다.**

입력 자료:

- 실제 OCR 운용 카메라로 획득한 전체 원본 프레임 1장. 업로드용 리사이즈나 스크린샷을 거치지 않은 PNG/JPG 등을 사용한다.
- 기존 OCR Crop 또는 라벨이 있으면 이를 함께 대조한다. 없으면 대상 범위는 제안 상태로 기록한다.
- 기준 프레임의 원본 해상도와 촬영 시점을 기록한다. 실제 전처리 후 영상을 사용한다면 원본과 구분한다.

완료 기준:

- `panel_1`의 온도·압력·진공 × 위·아래 = 6개 Slot 각각에 ID, bbox, 화면 문자열, 판독 상태가 연결된다.
- bbox 좌표 기준과 Crop 여백을 기록하고 이미지 위 표시로 범위를 검토한다.
- 불명확한 문자열은 임의 정답 대신 미판독으로 기록한다.
- 기존 데이터의 대상 범위가 이번 목록과 다르면 차이를 기록하고 ID·대상 범위를 조정한다.

Panel 1에서 기준을 확인한 뒤 나머지 Panel로 확대한다. Phase 1 전체 완료는 Scene 재현의 기준값과 미측정 항목을 문서화한 후 판단한다.

## 이후 확인이 필요한 사항

- 대용량 USD Asset 관리 방식.
- 별도 OCR 학습용 Python·프레임워크 환경.
- 저장된 Base Scene에서 Stage 축·단위와 생성·수정·저장 동작 검증.

위 항목은 이번 자료에서 완료 여부가 확인되지 않았다. 이전 문서에서 완료 기록과 중복되었던 기본 폴더·Stage 축·최소 스크립트 반복 실행 관련 오래된 미완료 항목은 정리했다.
