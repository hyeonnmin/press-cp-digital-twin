# Phase 4 — 숫자 Mesh 갱신과 소규모 캡처 검증

검증일: 2026-10-01. Isaac Sim `6.1.0-rc.26+release.49347.2d230af4.gl`, Standalone headless.

이 문서는 초기 스냅샷 재로딩 방식의 동기화 검증 기록이다. 현재 학습용 생성은 [training_capture.md](training_capture.md)의 Fabric 갱신·subframe 안정화 방식과 [YOLO 추출](panel_detection.md)을 사용한다. 아래 성공 Run을 포함한 `outputs/dataset_sync`는 후속 정리 요청으로 삭제했으며, 실행 결과 수치는 당시 이력이다.

## 구현과 완료 기준

`display_controller.py`는 순차 생성기의 문자열을 42개 Slot의 숫자 Mesh로 만든다. 기존 숫자는 숨기고 새 Mesh를 Session Layer에 생성한다. Slot 위치·폭·높이는 기존 Scene Config에서 계산하며 녹색·주황색 발광 재질을 유지한다. 생성된 Mesh의 점·면·인덱스와 표시 문자열을 캡처 전후 검사한다.

`capture_dataset.py`는 숫자를 갱신한 **프레임별 USD 스냅샷을 저장하고 다시 열어** 렌더한다. 실행 중 기하 갱신만으로는 이전 숫자가 렌더에 남는 현상을 실제 이미지에서 확인했다. Mesh 교체와 OmniHydra 전환만으로도 해결되지 않아 스냅샷 재로딩을 채택했다. 근본 원인은 미확정이며 Fabric 하나만의 문제라고 단정하지 않는다. 원본 Scene·Asset·텍스처의 실행 전후 Hash가 같은지 확인하며 원본을 저장하지 않는다.

완료 기준은 42개 Slot의 숫자 갱신, 작은 배치의 Image/Label 생성, 캡처 상태 일치·파일 연결·Crop 픽셀 검증 및 동일 값 복귀 영상 비교 통과이다. 이번 작은 배치 기준은 충족했다. 대량 생성 속도·전체 범위 렌더 검증·최종 학습 품질은 별도 작업이다.

## 실행

저장소 루트 PowerShell에서 실행한다. 기존 Isaac Sim Python의 Pillow·NumPy를 사용하며 패키지 설치는 필요하지 않았다.

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/capture_dataset.py
# 별도 인덱스도 지정 가능. 인덱스 1은 0.1, 9990은 999.0이다.
& C:\isaacsim\python.bat isaac_sim/scripts/capture_dataset.py --indices 0 1 99 100 888 9990 9991
# 저장 결과 재검증
& C:\isaacsim\python.bat src/dataset/validate_sync_capture.py outputs/dataset_sync/20261001T023746_582393Z
```

기본 검증 인덱스와 렌더러는 `config/dataset_capture.json`에서 관리한다. 현재 구현은 프레임별 재로딩을 사용한다. 실행마다 UTC 시각 기반 디렉터리를 만들어 기존 Run을 덮어쓰지 않는다. 검증 실패 시 종료 코드 1이며 `DATASET_SYNC_OK`를 출력하지 않는다. 캡처 후 검사 실패 보고서는 `CAPTURED` 상태로 남는다.

## 산출물과 검증 결과

성공 Run: `outputs/dataset_sync/20261001T023746_582393Z/`.

- `frames/`: 1920×1080 PNG 7개. 문자열 순서 `0.0, 0.1, 9.9, 10.0, 88.8, 999.0, 0.0`.
- `crops/`: 원본 픽셀·크기 그대로 잘라낸 Crop 294개.
- `labels.jsonl`: 정확한 문자열, Run/Frame/Slot ID, 원본 프레임 연결, ROI, 이미지 Hash, Mesh Hash. Split은 `debug`.
- `snapshots/`: 해당 프레임을 렌더한 USD 7개. 스냅샷 Hash를 프레임 기록에 포함한다.
- `report.json`: 최종 `PASS`. Seed null, 전체 Config, ROI Config, 코드 Hash, 기반 Commit·dirty 상태, 원본 Asset·텍스처 Hash, 실제 렌더 설정, 저장된 카메라·설정과 적용 카메라, 프레임별 검사 결과.
- `validation.json`: 별도 파일 재읽기 검사 `PASS`. 디코딩·Hash·수량·중복·Slot 연결·순차 문자열·Crop/원본 픽셀 일치를 확인했다.
- `contact_sheet.png`: 42개 Slot × 7개 프레임 비교표. 원본 Crop은 유지하고 검토 표만 최근접 확대했다. 직접 시각 확인했다.

서로 다른 값의 연속 캡처에서 252개 ROI 변화 검사를 통과했다. 8-bit RGB 평균 절대 차이의 최솟값은 1.8613이다. 처음과 마지막 `0.0`의 42개 ROI 평균 차이는 최대 0.98이며, 마지막 `0.0`과 직전 `999.0`의 차이는 최소 6.2029이다. 반복값 ROI 차이가 이전 다른 값과의 차이의 25% 미만인지 검사한다. 이 비율은 **렌더 잔류 검출을 위한 초기 검사 가정**이며 OCR 정확도나 실영상 유사성 기준이 아니다.

7개 프레임과 294개 Crop 모두 읽기·연결 검사를 통과했고 최종 프로세스는 `DATASET_SYNC_OK`, 종료 코드 0이다. 순차 값 생성기 기존 테스트 4개도 통과했다. 원본 Scene·Asset·텍스처 Hash는 실행 전후 동일하다. Commit·Push는 수행하지 않았다.

## 확인한 제약과 다음 작업

- 현재 저장된 reference Camera는 Config와 다른 수동 조정이 들어 있고 일부 Bloom 기본값이 저장에서 생략되어 있었다. 원본은 보존하고 고정 ROI에 맞는 Config 카메라·렌더 설정을 메모리에 적용했다. 저장 조건과 실제 적용 조건은 보고서에 구분했다.
- 고정 ROI는 기존 예비 비교 검색창이다. 일부 진공 아래 표시와 Panel 5 주변 Crop에는 이웃 표시 일부가 들어 있다. 숫자 정답 bbox 또는 최종 Recognition Crop으로 확정하지 않는다.
- Mesh 검사와 픽셀 변화·복귀 비교를 수행했다. OCR 모델을 통한 독립 문자열 판독은 하지 않았다. 렌더의 바이트 동일성도 요구하지 않는다.
- 초기 인플레이스 갱신·새 Prim 교체 실험의 영상은 동기화 불합격이다. `20261001T023116_690490Z`, `20261001T023421_373836Z`, `20261001T023554_805359Z`는 학습에 사용하지 않는다. 초기 두 Run의 이전 코드가 쓴 `PASS`는 이번 강화된 동기화 기준을 충족하지 않는다. 최종 성공 Run과 구분한다.
- 스냅샷 재로딩은 안전한 소규모 검증 경로이며 USD 용량·로딩 비용이 있다. 실시간 GUI 숫자 갱신과 대량 캡처 효율은 아직 검증하지 않았다.
- 다음 작업 하나: 학습용 Crop ROI를 숫자 영역 중심으로 정리하고 전체 자릿수 범위의 경계·이웃 문자열 혼입을 검사한다. Real Split 미정과 실영상 보정 제약은 유지한다.

## 공식 API 근거

- [Isaac Sim 6.1 Python 유틸리티](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/python_scripting/util_snippets.html)
- [OpenUSD Mesh 속성](https://openusd.org/release/api/class_usd_geom_mesh.html)
- [Viewport 캡처 API](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.utility/latest/omni.kit.viewport.utility/omni.kit.viewport.utility.capture_viewport_to_file.html)
- [Fabric Scene Delegate 설정과 USD 변경 전달 제약](https://docs.omniverse.nvidia.com/kit/docs/usdrt.scenegraph/latest/fabricsd/configuration.html)

Kit·OpenUSD 공통 API 문서는 해당 문서가 제공하는 버전 기준이다. 설치된 RC에 대한 호환 여부는 위 실제 실행으로 확인했다.
