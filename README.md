# Press CP Digital Twin

실제 프레스 CP 환경을 Isaac Sim에서 재현하고, 합성 데이터로 학습한 OCR Recognition 모델을 실제 영상에서 평가하는 프로젝트다. Baseline, Synthetic Only, Mixed를 공통 Real Test에서 비교할 계획이며 모델 학습·최종 평가는 아직 수행하지 않았다.

## 현재 상태 — 2026-10-02

Phase 4 진행 중이다. 7 Panel·21 Module·42 Slot의 CP Scene, 숫자 순차 표시, 프레임별 학습 데이터 생성 및 Panel 단위 YOLO 라벨 출력을 구현하고 소규모 검증을 마쳤다. 대량 생성·실험 Split 확정·단계별 랜덤화·모델 학습은 남아 있다.

기존 CP를 보존하면서 주변 배관·밸브·프레스 외형과 공장 기둥·보·천장·창·통로를 추가했다. 천장등 9개·창측 보조광 4개를 배치했으며 실제 Isaac Sim 생성·별도 프로세스 재열기·렌더 검증을 통과했다. 사진 밖 구조와 치수는 추정 구성이다. [공장 환경 안내](docs/factory_environment.md)에서 결과와 실행법을 확인한다.

메인 Scene은 `isaac_sim/stages/press_cp_main.usda`다. Play에서 기본 0.1초 간격으로 `0.0~999.0`을 0.1씩 증가시키고, Pause는 유지, Stop은 0.0으로 초기화한다. 학습 저장은 별도 생성 명령을 사용한다.

Scene 기본 시점은 `/World/Cameras/factory`, CP 주변 근접 시점은 `workcell`이다. 학습 생성기는 기존 정면 직교 `training`을 사용한다. 숫자 자동화의 기존 Timeline 검증과 새 환경의 정적 렌더 검증을 구분하며, 새 환경의 GUI Play·학습 생성 회귀는 아직 수행하지 않았다.

최신 학습용 데이터는 [`20261001T064808_756110Z`](datasets/synthetic/cp_training/20261001T064808_756110Z/)다.

이 Run은 **2026-10-02 공장 환경 확장 전** 생성한 데이터다. 새 Scene으로 생성하면 조명·주변 반사 조건이 달라지므로 별도 Run으로 검증한다.

| 산출물 | 수량·조건 |
|---|---|
| 전체 프레임 | 2장, 3840×2160 |
| Recognition Crop·정답 | 84개 |
| YOLO Panel·bbox | 14장·84개, 단일 클래스 `0: slot` |
| YOLO 분할 | 원본 프레임 단위 Train 7장 / Validation 7장 |
| 생성 조건 | Seed 42, Bloom scale 0.4 / cutoff 0.5 / isotropic falloff 5 |
| 검증 | 생성·독립 저장 데이터 검사 PASS, 정상 종료 코드 0 |

별도 잔상 검증 이미지 3장은 학습 프레임 수에 포함하지 않는다. 이전 합성 Run과 과거 출력은 정리 요청으로 삭제했다. 위 링크는 로컬 산출물이며 대량 데이터·로그는 Git에 포함하지 않는다.

## 실행

확인한 설치본은 Isaac Sim `6.1.0-rc.26+release.49347.2d230af4.gl`이다. 저장소 루트 PowerShell에서 실행한다.

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/generate_training_data.py --frames 2 --seed 42 --export-yolo
```

숫자 선택 → subframe 렌더 안정화 → 이미지·정답 저장 순서로 실행한다. 학습 생성 기본 카메라는 `/World/Cameras/training`(정면 중앙 직교 시점)이며, 기존 `reference`, `overview`, `detail`도 유지한다. 설정은 `config/press_cp_scene.json`, `config/training_capture.json`, `config/panel_detection.json`에서 관리한다. 공장 구조·추가 조명·전경 카메라는 `config/factory_environment.json`에서 관리한다. 검토용 출력은 `--output-root outputs/<검토 폴더>`로 분리할 수 있다.

## 문서

- [현재까지의 진행 요약·검증 결과·남은 작업](docs/progress.md)
- [프로젝트 목표·범위·로드맵](docs/project_overview.md)
- [주요 결정과 이유](docs/decisions.md)
- [실행 환경](docs/real_environment.md)
- [전체 CP 환경 열기·생성](docs/phase2_full_scene.md)
- [공장 실내·주변 설비·추가 카메라와 검증 결과](docs/factory_environment.md)
- [Play/Pause/Stop 및 연속 숫자 표시](docs/display_playback.md)
- [학습 데이터 생성·저장 형식·빛번짐 설정](docs/training_capture.md)
- [YOLO Panel 이미지·Slot bbox 추출](docs/panel_detection.md)
- [초기 Mesh 동기화 검증 이력](docs/phase4_capture.md)

## 폴더 역할

- `docs`: 계획·환경·진행·실험 기록
- `config`: Camera·Light·Material·Display·데이터 생성 설정
- `isaac_sim`: USD Scene/Asset과 Isaac Sim 실행 코드
- `src`: 값 생성·데이터 변환·검증 로직
- `datasets`: 합성·실제 데이터
- `outputs`: 검토 이미지·실행 로그·검증 보고서
- `tests`: 생성 규칙·좌표 변환 등 단위 테스트

실제 치수·광학 조건·Real Train/Validation/Test 구간은 미확정이다. 현재의 이미지·정답 동기화 검증과 실제 영상에서의 모델 성능 평가를 구분한다. 작업 규칙은 [AGENTS.md](AGENTS.md)를 따른다.
