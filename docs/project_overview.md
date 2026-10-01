# Press CP Digital Twin — Project Overview

작성일: 2026-09-30 (Asia/Seoul)

현재 구현 상태 갱신: 2026-10-01 (Asia/Seoul).

기준 자료: [프레스 CP AI 모니터링 시스템 Digital Twin — Notion](https://app.notion.com/p/CP-AI-Digital-Twin-3e944825e9c680f9a9ace42c09e042ef)

확인한 원본의 마지막 수정 시각: 2026-09-28 07:18:46 UTC.

이 문서는 Notion의 목표·범위·Phase 0~6 로드맵과 저장소의 구현 현황을 정리한 프로젝트 공통 자료이다. 초기 계획과 이후 확인한 실행 결과를 구분하며, 상세 검증 근거와 남은 작업은 [진행 상황](progress.md)에 기록한다.

## 1. 목표와 연구 질문

실제 프레스 CP 패널 및 주변 환경을 Isaac Sim에서 재현한다. 가상환경의 Pressure / Temperature / Vacuum 표시값을 자동 변경하고, 실제 카메라 영상과 유사한 합성 이미지와 정답을 생성한다. 생성 데이터로 OCR Recognition 모델을 학습하여 실제 영상에서 평가하고, 실제 데이터 학습 모델과 비교한다.

핵심 연구 질문:

> 실제 Press CP 환경을 모사한 Digital Twin에서 생성한 합성 데이터만으로 학습한 OCR 모델이 실제 환경에서 어느 수준까지 일반화하는가?

추가 질문:

- Camera, Lighting, Material, Display, Blur/Noise 중 Domain Gap에 크게 기여하는 요소는 무엇인가?
- 단계별 Domain Randomization이 실제 영상의 OCR 성능을 얼마나 바꾸는가?
- 실제 데이터와 합성 데이터를 혼합하면 성능이나 취약 조건의 인식이 개선되는가?

## 2. 범위

| 포함 | 현재 범위에서 제외 |
|---|---|
| CP 패널·표시 모듈·주변 구조의 시각적 재현 | FastAPI·Web·DB 연동 |
| 실제 카메라 시점·해상도·영상 특성 맞추기 | 기존 모니터링 서비스 확장 |
| 숫자 표시 자동화, 이미지·정답 생성 | 프레스의 전체 물리 공정 해석·실시간 제어 |
| Domain Randomization, OCR Recognition 학습·평가 | Detection 모델 신규 개발을 기본 과제로 삼는 것 |

Detection이나 Crop 추출은 Recognition 실험에 필요한 입력 처리로 다룬다. 기존 Detector를 사용할지, 정해진 ROI 또는 가상환경의 위치 정보를 사용할지는 Dataset 설계에서 결정한다. 추후 범위 변경은 이유와 영향을 기록한다.

2026-10-01 사용자 요청으로 **YOLO Detection 학습용 Panel 이미지와 Slot bbox 데이터 생성**을 추가했다. Panel당 표시기 3개·주요 숫자 Slot 6개이며 클래스는 사용자 확인에 따라 단일 `slot`이다. 이번 추가 범위는 데이터 생성·검증이고 Detection 모델 학습은 별도 작업이다.

## 3. 비교 실험

| 실험 | 학습 데이터 | 평가 데이터 | 목적 |
|---|---|---|---|
| Baseline | Real Train | 공통 Real Test | 실제 데이터 학습 기준 확보 |
| Synthetic Only | Synthetic Train | 공통 Real Test | 합성 데이터 단독 일반화 평가 |
| Mixed | Real Train + Synthetic Train | 공통 Real Test | 합성 데이터의 보강 효과 평가 |

진행 원칙:

1. Real Train / Validation / Test를 구분하고, 같은 촬영 세션의 유사한 연속 프레임이 서로 다른 Split에 섞이지 않도록 분할 기준을 기록한다.
2. 랜덤화 범위·학습 조건 선택은 Validation을 사용한다. Real Test를 반복 튜닝의 기준으로 사용하지 않는다.
3. 모델 구조, 초기 가중치/사전학습, 입력 전처리, 문자 집합, 학습 예산을 기록한다. ‘Synthetic Only’는 학습 데이터 조건을 뜻하며 사전학습 유무는 별도 표기한다.
4. Mixed는 데이터 양이 증가할 수 있으므로 혼합 비율과 총 학습량을 공개한다. 필요한 경우 데이터 수 또는 학습 Step을 맞춘 보조 비교를 수행한다.
5. 기존 서비스의 OCR 성능은 배경 정보로만 사용한다. 이번에 고정한 Real Test에서 다시 평가하기 전에는 신규 Baseline 수치로 간주하지 않는다.

## 4. 기술 및 확인할 환경

주요 기술: NVIDIA Isaac Sim, Python, USD, Git/GitHub, OCR Recognition 학습 프레임워크. 필요에 따라 OpenCV 및 PyTorch/PaddleOCR을 사용한다.

초기 사용자 보고는 Isaac Sim 6.0.1이었고, 실제 설치본은 `6.1.0-rc.26+release.49347.2d230af4.gl`로 확인했다. 기준 검증 경로는 Windows의 `C:\isaacsim\python.bat`를 사용하는 Standalone headless이며, 메인 USD에는 GUI Play용 Behavior Script를 연결했다. 실제 Timeline 이벤트 검증과 GUI 직접 클릭 검증을 구분한다. 환경 기록은 [real_environment.md](real_environment.md)를 따른다.

- Isaac Sim 정확한 버전, OS, GPU 및 Driver
- GUI 내부 Script / Extension / Standalone 중 기준 실행 방식
- Python 및 OCR 프레임워크 버전
- Stage Up-axis와 metersPerUnit
- 실제 카메라·렌즈·획득 해상도·전처리 후 해상도

센서의 최대 해상도와 실제 저장 이미지 또는 OCR 입력 해상도를 구분한다. 카메라 설정값과 실제 측정값을 확인하기 전에는 수치를 기본 Config로 확정하지 않는다.

## 5. Digital Twin 구성과 검증

목표는 실제 OCR 카메라 영상의 분포를 재현하는 것이다. 화면 밖 설비의 세부 형상보다 숫자 인식에 영향을 주는 요소를 우선한다.

| 요소 | 확보할 기준 정보 | 검증 방법 |
|---|---|---|
| Geometry | 패널·모듈 크기/배치, 간격, 주변 프레임, 실제 단위 | 기준점 및 이미지에서의 패널 크기·위치 비교 |
| Camera | 설치 위치/각도, Resolution, Focal Length/FOV, Exposure | 숫자 영역의 픽셀 크기·원근·위치 비교 |
| Display | 숫자 형상/색상, 밝기, 소수점·음수·자릿수 규칙 | 같은 문자열의 실제/합성 Crop 비교 |
| Material | 패널 표면, 반사, Roughness, Background 대비 | 반사 위치와 밝기 분포 비교 |
| Lighting | 위치, 세기, 색온도, 주변광, 그림자 | 대표 실제 영상과 Render의 밝기·그림자 비교 |
| 영상 효과 | 번짐/Glow, Blur, Noise, Depth of Field 필요성 | 숫자 경계와 작은 문자·기호의 가독성 비교 |

현재 숫자는 발광 재질을 적용한 세그먼트 Mesh로 구현했고, 미리 준비한 숫자 Mesh를 Fabric Transform으로 선택·배치한다. 렌더러 FFT Bloom으로 빛번짐을 표현하며 현재 scale 0.4, cutoff RGB 0.5, isotropic falloff RGB 5다. 이는 시각 조정값이며 실측 광학값이나 최종 랜덤화 범위는 아니다. Base Scene과 실영상의 정량 비교 및 최종 허용 기준은 남아 있다.

## 6. Dataset 생성

기본 순서: Config 로드 → 표시 문자열 생성 → CP Display 갱신 → Camera/Lighting 적용 → Render → Image와 Ground Truth 저장 → 검증.

현재 전체 프레임과 Recognition Crop을 함께 저장한다. 정면 중앙 직교 카메라의 3840×2160 프레임에서 숫자 Mesh 투영 bbox에 4픽셀 여백을 더해 Crop하고, 정확한 문자열·Frame/Panel/Slot ID·Hash를 연결한다. YOLO용으로 Panel별 이미지와 단일 `slot` 클래스의 6개 bbox도 출력한다. 구현된 규격은 [training_capture.md](training_capture.md), [panel_detection.md](panel_detection.md)를 따른다. 아래 항목 중 실제 값 분포·Real Split 등은 후속 실험에서 확정한다.

데이터 규격에서 결정할 내용:

- Panel / Module / Slot 구성 및 ID 규칙. 동일 Module에 표시창이 여러 개면 Slot을 구분한다.
- 이미지 크기·파일 형식·Crop 여백·좌표계
- Pressure / Temperature / Vacuum별 값 범위, 샘플링 분포, 표시 문자열 규칙
- 소수점·음수·선행 0·단위 문자 및 오류 표시의 포함 여부
- Image ID와 Label 연결, Split, 생성 Run 식별 방법
- 학습 프레임워크가 요구하는 Label 파일 형식

Ground Truth는 부동소수점 값만 저장하지 않고 화면에 표시한 정확한 문자열을 보존한다. 아래는 설명용 예시이며 실제 값 범위나 확정된 규격이 아니다.

```json
{
  "image": "crops/rec_000001.png",
  "text": "-0.82",
  "panel_id": "panel_1",
  "module": "vacuum",
  "slot_id": "slot_1",
  "run_id": "synth_run_001",
  "frame_id": "frame_000001"
}
```

Run별 재현 정보: Random Seed, 코드 Commit, Isaac Sim 버전, Scene/Asset 버전 또는 Hash, 기본 Config, 실제 샘플링한 조건, 이미지 수, 생성 시각. Seed만으로 Render의 바이트 단위 동일성을 보장한다고 가정하지 않는다.

최소 검증: 파일 누락, 읽을 수 없는 이미지, 중복 ID, Label 누락, 허용되지 않은 문자, Crop 경계 이탈, 이미지와 정답의 불일치. 표시 갱신 직후의 이전 프레임이 저장되지 않는지도 작은 샘플로 확인한다.

## 7. Domain Randomization

원본 계획의 후보: 표시값, LED/Emission 밝기, Light 세기/위치, Exposure, Camera 위치/회전, Blur, Noise, Contrast/Brightness, Material Roughness/Reflection.

권장 진행:

1. 실제 조건에 맞춘 Base Scene의 데이터 생성·학습 조건을 고정한다.
2. 한 요소씩 범위를 추가하고 Validation 성능·오류 변화로 효과를 확인한다.
3. 유효한 요소의 조합을 검토하고, 선택한 조건으로 최종 Real Test를 평가한다.

3D Scene에서 적용한 변화와 렌더링 후 이미지에 적용한 효과를 구분해 기록한다. 범위는 실제 측정·관찰 또는 명시된 가설에 근거한다.

## 8. 권장 Repository

아래는 Notion의 권장 구조를 바탕으로 공통 개요와 결정 기록을 추가한 설계안이다. 아직 생성되었다는 뜻은 아니다.

```text
press-cp-digital-twin/
├── README.md
├── AGENTS.md
├── .gitignore
├── .gitattributes
├── docs/
│   ├── project_overview.md
│   ├── architecture.md
│   ├── real_environment.md
│   ├── dataset_spec.md
│   ├── experiments.md
│   ├── progress.md
│   └── decisions.md
├── isaac_sim/
│   ├── stages/press_cp_main.usda
│   ├── assets/{press,cp_panel,environment}/
│   ├── materials/
│   └── scripts/
│       ├── full_scene_setup.py
│       ├── display_controller.py
│       ├── camera_controller.py
│       └── capture_dataset.py
├── src/
│   ├── generation/{value_generator.py,domain_randomizer.py}
│   ├── dataset/{annotation_writer.py,dataset_validator.py}
│   └── evaluation/compare_results.py
├── config/{scene.yaml,camera.yaml,display.yaml,randomization.yaml}
├── datasets/{synthetic,real}/
├── experiments/{configs,results}/
└── tests/
```

`{...}`는 여러 경로를 간략하게 나타낸 표기다.

코드, Config, 간단한 결과 요약은 Git으로 관리한다. 대량 이미지, 모델 Weight, Cache, 로그는 일반 Git 관리 대상에서 제외한다. 대용량 Asset의 관리 방법은 Phase 0에서 결정한다.

Notion의 Branch 제안은 `main` / `develop` / `feature/*`이다. 예: `feature/base-scene`, `feature/cp-display`, `feature/camera-matching`, `feature/dataset-capture`, `feature/domain-randomization`. 실제 운영 방식은 Phase 0에서 확정한다.

## 9. Phase 0~6 로드맵

| Phase | 작업 | 완료 기준 |
|---|---|---|
| 0 — Repository / 개발환경 | Git, 폴더, ignore/attributes, README/AGENTS, 환경·Dataset 문서, Isaac Sim Script 동작 확인 | 연구 목적과 구조가 문서화되고, 기준 실행 방식으로 앱과 Script를 반복 실행할 수 있음 |
| 1 — 실제 환경 분석 | 패널·모듈 측정, Camera 위치·방향·해상도/FOV, 대표 이미지, Lighting 분석 | Scene 재현의 기준값과 미측정 항목이 문서화됨 |
| 2 — Base Scene | Geometry, Scale, Display 영역, Camera, Lighting, 실제 이미지와 비교 | 패널과 숫자 영역의 위치·크기·원근감을 비교하여 합의한 기준을 충족함 |
| 3 — Display 자동화 | 3종 표시값 변경, 자릿수·소수점·음수 규칙, 값 생성 | Script로 모든 표시값을 변경할 수 있고 표시 문자열과 정답이 일치함 |
| 4 — Dataset Capture | Capture, 명명 규칙, Label, Crop 방식, Validation, Seed/Config 저장 | 지정한 수량의 Image + Label을 일괄 생성하고 데이터 검증을 통과함 |
| 5 — Domain Randomization | Light, Camera, Display, Material, Blur/Noise의 단계별 실험 | 각 조건을 Config로 전환할 수 있고 결과와 생성 조건을 추적할 수 있음 |
| 6 — OCR 학습·비교 | Baseline / Synthetic Only / Mixed, 공통 Real Test 평가, 오류·Domain Gap 분석 | 동일한 평가 조건에서 정량 결과와 재현 정보를 제시할 수 있음 |

Phase 5의 조건 선택에는 Validation을 사용하며, 필요하면 Phase 6의 학습 처리를 먼저 소규모로 실행한다. 현재 Phase 0·1은 기록된 범위에서 종료했고, Base Scene·숫자 자동화·소규모 캡처를 구현·검증했다. Phase 4 진행 상태로 관리하며 대량 생성·실험 Split 확정·단계별 랜덤화·모델 학습과 Real 평가는 남아 있다. 빛번짐 한 가지의 고정 설정 조정을 Phase 5 전체 완료로 간주하지 않는다.

## 10. 평가와 실험 기록

주요 지표: Recognition Accuracy(정답 문자열과 완전히 일치한 Crop 수 ÷ 평가 Crop 총수). 정규화의 적용 여부와 규칙을 명시하고, 문자열 평가와 수치 오차를 혼동하지 않는다.

보조 평가: Character Error Rate / Edit Distance, Pressure·Temperature·Vacuum별, Panel별, 음수·소수점·자릿수·문자별 오류 사례. 계산 방법과 평가 건수를 함께 기록한다.

실험별 기록 항목:

- Experiment ID, 코드 Commit, Dataset/Split 버전, Seed
- Real/Synthetic 이미지 수, Mixed 비율, 학습량
- Scene, Camera, Lighting, Display, Randomization Config
- OCR Model, 초기 Weight, 학습 Config, 전처리
- Validation Accuracy, Real Test Accuracy, 세부 결과, 오류 이미지
- 변경한 요소, 관측 결과, 해석, 다음 검증

1차 성공은 Scene과 Virtual Camera 재현, 숫자 자동 변경, Image/GT 생성, Synthetic 학습, Real Test 정량 평가, Real/Synthetic 학습 비교가 모두 가능해지는 것이다. 성능의 수치 목표는 아직 정하지 않았으므로 99% 등을 임의로 합격 기준에 넣지 않는다.

## 11. 문서와 현재 상태

| 정보 | 지속 관리 위치 |
|---|---|
| 전체 계획·사람이 확인하는 작업 관리 | Notion |
| 구현·실측·Config·정식 실험 결과 | Git Repository |
| GPT 공통 참조용 개요 | 이 파일의 최신 업로드 버전 |
| 현재 Phase·완료 근거·문제·다음 Task | docs/progress.md |
| 채택한 판단·이유·영향 | docs/decisions.md |

2026-10-01 현재 7 Panel·21 Module·42 Slot의 CP 환경, `0.0~999.0` 순차 표시, 프레임별 무작위 숫자 선택·렌더 안정화·이미지/정답 저장, Panel 단위 YOLO 내보내기가 구현됐다. 기존 합성 산출물 정리 후 현재 빛번짐 설정으로 `20261001T064808_756110Z` Run을 새로 생성했다. 전체 프레임 2장·Crop 84개·YOLO Panel 14장/박스 84개이며 생성 및 저장 데이터 검증을 통과했다.

현재 산출물과 재실행 명령, 과거 삭제된 검증 이력은 [progress.md](progress.md)에서 구분한다. 다음 작업은 생성 규모와 실험 분할 조건을 정하고 모델 학습·실영상 평가로 연결하는 것이다. 이 문서 정리에서는 코드 변경·추가 렌더·학습·Commit/Push를 수행하지 않았다.
