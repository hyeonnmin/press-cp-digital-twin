# Panel 이미지와 YOLO Slot 검출 데이터

작성일: 2026-10-01. 사용자가 제공한 예시처럼 온도·압력·진공 표시기 3개를 포함한 Panel 한 장을 만들고, 주요 숫자 문자열 6개를 검출 대상으로 저장한다. 클래스는 사용자 확인에 따라 **단일 클래스 `0: slot`**이다. 숫자 값은 클래스가 아니며 `annotations.jsonl`에 문자열로 보존한다.

## 기존 Run에서 변환

Isaac Sim을 다시 실행하거나 렌더할 필요가 없다. Pillow·NumPy가 있는 Python이면 실행 가능하며 현재 설치된 Isaac Python으로 검증했다.

```powershell
& C:\isaacsim\python.bat src/dataset/panel_yolo.py datasets/synthetic/cp_training/<Run ID>
```

결과는 해당 Run의 `yolo_panels/`에 저장된다. 이미 존재하는 출력은 덮어쓰지 않는다. 재생성이 필요하면 `--output datasets/synthetic/panel_detection/<새 이름>`을 지정한다. 입력 Run은 `manifest.json`이 PASS여야 하고 기존 이미지·정답 검증도 다시 통과해야 한다.

## 새 생성과 함께 실행

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/generate_training_data.py --frames 100 --seed 42 --export-yolo
```

전체 이미지 100장을 생성하면 Panel 이미지 700장과 Slot 박스 4,200개가 추가된다. Train/Validation 분할에 최소 2개 원본 프레임이 필요하다. 기존 생성 명령에서 `--export-yolo`를 생략하면 기존 Recognition 데이터 생성 동작을 유지한다.

## 출력과 좌표

```text
yolo_panels/
  dataset.yaml
  images/train/*.png
  images/val/*.png
  labels/train/*.txt
  labels/val/*.txt
  annotations.jsonl
  manifest.json
  validation.json
  previews/panel_1.png ... panel_7.png
  previews/contact_sheet.png
```

학습 PNG에는 박스를 그리지 않는다. 박스가 그려진 이미지는 `previews/`에만 저장한다. Panel 번호판·비상 정지 버튼이 아닌 세 표시기의 Housing 전체 경계를 합쳐 자른다. Panel 6·7의 기존 녹색 덮개 일부는 원본 Scene의 모습 그대로 남을 수 있으며 숫자를 가리지 않는지 비교 이미지로 확인했다.

각 TXT에는 다음 형식의 6개 행이 들어간다.

```text
0 x_center y_center width height
```

좌표는 **잘라낸 Panel 이미지의 너비·높이 기준 0~1 정규화 값**이다. 원본 전체 이미지 좌표에서 Panel의 좌상단을 빼고 변환한다. 클래스 번호는 0, 소수점도 숫자 문자열 bbox에 포함된다. 형식은 [Ultralytics YOLO Detection 공식 문서](https://docs.ultralytics.com/datasets/detect/)를 따른다. `dataset.yaml`은 YAML에서도 유효한 JSON 표기로 저장하며 YAML 파서로 읽는 것을 확인했다.

`annotations.jsonl`은 Panel 이미지와 원본 Frame의 연결, Panel bbox, 각 Slot의 ID·정답 문자열·원본/Panel 픽셀 bbox·정규화 좌표를 보존한다. 상단/하단 및 온도/압력/진공 구분은 이 정보와 위치로 판단한다. 작은 고정 보조 표시 `1 6`, `1 4`, `--`는 이번 6개 Slot 검출 대상에 포함하지 않는다.

설정은 `config/panel_detection.json`이다.

| 설정 | 기본값과 의미 |
|---|---|
| `class_mode` | `single`: 단일 slot. 필요시 `six_slots` 옵션도 제공 |
| `bbox_source` | `bbox`: 기존 숫자 Crop의 4픽셀 여백 포함 영역. `digit_bbox`는 여백 없는 숫자 형상, `slot_roi`는 고정 표시 영역 |
| `panel_padding_px` | 4: 세 표시기 Housing 경계 주변 여백 |
| `validation_fraction` | 0.2: Synthetic 내부 검증 비율 |
| `split_seed` | 42: 프레임 분할 재현용 Seed |

신규 Run은 USD의 실제 Housing 투영 경계 `panel_regions`를 기록한다. 이전 Run에 이 항목이 없으면 Run에 저장된 Scene/카메라 Config로 경계를 복원하고, 42개 Slot의 기존 ROI와 1픽셀 이내로 일치하는지 확인한다. 이 호환 경로는 현재 생성기의 정면 직교 카메라에 한정한다. 일치하지 않으면 임의로 자르지 않고 오류로 종료한다.

## 분할과 검증

같은 전체 프레임에서 나온 Panel 7개는 전부 같은 Split에 배정한다. 원본 프레임 ID를 Seed로 섞어 80/20으로 나누며, 작은 Run에서는 최소 한 프레임씩 Train/Validation에 둔다. 이는 Synthetic 내부 분할이며 Real Test를 대신하지 않는다. 서로 다른 Run을 합칠 때는 같은 Seed·프레임 번호의 중복 생성 여부도 고려해야 한다.

검증 항목은 이미지·라벨 1:1 연결, 7 Panel/프레임, 6 Slot/Panel, class 범위, 좌표 범위·역변환 오차, 박스 잘림, 정답/Slot 연결, 원본 이미지와 Panel Crop의 픽셀 일치, Hash, 원본 프레임 Split 누수다.

```powershell
& C:\isaacsim\python.bat src/dataset/panel_yolo.py datasets/synthetic/cp_training/<Run ID>/yolo_panels --validate-only
```

## 확인한 결과

아래 두 Run은 당시 검증 이력이며, 2026-10-01 후속 정리 요청으로 삭제했다. 빛번짐 검토 출력은 `outputs/bloom_check/`에 보관한다. 이후 사용자 요청으로 `datasets/synthetic/cp_training/20261001T064808_756110Z/yolo_panels/`를 새로 생성했다: 원본 프레임 2장, Panel 14장·bbox 84개, Train/Validation 각 7장, 생성·독립 검증 PASS.

- 기존 Run `20261001T054612_229728Z`: Panel 70장, bbox 420개, Train 56장·Validation 14장. 메타데이터 복원 경로 PASS, 7개 Panel 미리보기 시각 확인.
- 신규 통합 실행 `20261001T060410_362510Z`: 전체 프레임 2장 → Panel 14장·bbox 84개, Train/Validation 각각 7장. USD 실측 투영 경계 기록과 `--export-yolo` 자동 출력 확인.
- 실제 YOLO 라이브러리 학습은 수행하지 않았다. 현재 Isaac Python에 Ultralytics가 설치되어 있지 않으며 추가 설치하지 않았다. 이 작업의 완료 범위는 검출 데이터 생성·검증이다.
