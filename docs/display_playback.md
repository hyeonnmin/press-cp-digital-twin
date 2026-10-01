# Isaac Sim 연속 숫자 표시

작성일: 2026-10-01. 사용자 요청에 따라 학습용 ROI 작업보다 먼저 구현했다.

## 동작

42개 Slot이 `0.0 → 0.1 → 0.2 → … → 999.0 → 0.0` 순서로 함께 변한다. 범위·증가 폭·순환 여부는 `config/dataset_capture.json`의 sequence를 사용한다. 표시 간격은 `config/display_playback.json`의 `interval_seconds`이며 초기 기본값은 0.1초이다. 실제 장비의 갱신 주기를 측정한 값이 아니다.

숫자 0~9 Mesh와 소수점을 각 자릿수에 미리 생성하고 Fabric의 `omni:fabric:localMatrix`로 선택한 숫자의 위치·크기를 갱신한다. 정적 숫자 Mesh의 형상·색·발광 재질은 기존 생성기를 재사용한다. 표시하지 않는 숫자는 가상 카메라의 Clipping 범위 밖으로 이동한다. 실행 중 Mesh·Prim을 계속 추가하거나 Scene을 값마다 다시 열지 않는다.

숫자 변경 직후 `UsdContext.reset_renderer_accumulation()`을 호출해 이전 RTX 누적 영상을 초기화한다. 이 조치 없이 실제 영상에 이전 숫자가 남는 현상을 확인했다. 정적 Mesh·Fabric Transform·누적 초기화를 함께 사용하는 최종 방식에서 42개 Slot 영상 복귀 검사를 통과했다. 이전 Mesh 갱신 방식 각각의 근본 원인을 모두 분리 확인한 것은 아니다.

기본 실행은 아래의 **메인 Scene → Play** 방식이다. 숫자 Mesh와 표시 문자열은 현재 Stage의 SessionLayer/Fabric에만 갱신하며 원본 Scene·Asset·텍스처는 저장하지 않는다. 별도 실행기 방식만 시작할 때 `live_scene.usdc`를 구성해 로드한다.

## 메인 Scene을 열고 Play

1. Isaac Sim에서 `isaac_sim/stages/press_cp_main.usda`를 연다. 이미 열려 있다면 저장된 최신 파일을 다시 연다. 미저장 작업은 먼저 보관한다.
2. 스크립트 실행 허용 창이 나오면 이 프로젝트의 `press_cp_play_behavior.py` 실행을 허용한다.
3. **Play**를 누른다. 첫 실행은 숫자 Mesh 준비 후 `0.0 → 0.1 → … → 999.0 → 0.0`으로 진행한다.
4. **Pause**는 현재 값을 유지하고, 다시 Play하면 다음 값부터 이어진다. **Stop**은 `0.0`으로 초기화한다.

기본 간격은 `config/display_playback.json`의 `interval_seconds: 0.1`이다. 실제 경과 시간의 최소 간격이며 부하가 높으면 늦어지고 값을 건너뛰지 않는다. 파일에서 설정을 바꾼 뒤 Scene을 다시 열면 적용된다. 사용자가 현재 보고 있는 카메라와 구도는 유지한다. Config의 `camera`, `use_config_camera`는 아래 별도 실행기에만 적용한다.

Scene의 `/World/DisplayPlayback`에 `OmniScriptingAPI`와 상대 경로 스크립트가 연결되어 있다. 숫자 실행 코드를 Script Editor에서 별도로 실행할 필요는 없다. 자동 로딩이 되지 않으면 **Window → Extensions**에서 **Python Behavior Scripting Bundle** (`omni.behavior.scripting.bundle`)을 활성화하고 AUTOLOAD를 켠 뒤 Scene을 다시 연다. 기존 `omni.kit.scripting`과 새 Bundle을 동시에 켜지 않는다.

이 방식은 설치된 Isaac Sim `6.1.0-rc.26` / Behavior Scripting Core `110.3.0` 기준이다. 확장 활성화와 실행 허용 흐름은 NVIDIA [시작 안내](https://docs.omniverse.nvidia.com/extensions/latest/ext_python-scripting-component/getting_started.html)와 [사용 안내](https://docs.omniverse.nvidia.com/extensions/latest/ext_python-scripting-component/user_manual.html)를 따른다. 일반 GUI의 실행 허용 설정은 코드에서 해제하지 않는다.

Windows CP949 환경에서 Kit의 의존성 스캐너가 UTF-8 한국어 소스를 읽지 못하는 문제를 확인했다. USD에 연결하는 작은 진입 파일은 ASCII로 두고 한국어가 포함된 구현은 Python의 표준 import로 불러온다.

### Play 연결 검증

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/run_display_playback.py --headless --verify-timeline
```

`outputs/timeline_playback/20261001T043800_392647Z/verification.json`은 PASS다. 저장된 USD에서 자동 로딩한 실제 Behavior와 Timeline 이벤트로 연속 20회 증가, Pause·재개, Stop·재시작, 최대값·순환, 42개 Slot의 문자열과 영상 복귀를 확인했다. 실제 간격은 0.109~0.171초였다. GUI 버튼 직접 클릭·허용 창과 전체 9,991개 값 렌더는 별도 미검증이다. PASS 출력 후 검증 앱 종료 대기가 남아 해당 프로세스를 Ctrl+C로 종료했다.

최초/정지/순환 후 `0.0`, `2.0`, `999.0`의 5장 이미지를 저장했다. 원본 파일 Hash와 카메라 Transform 보존을 확인했으며, Kit이 메모리의 루트 레이어에 자동 추가하는 PhysicsScene·EcoMode 속성은 `root_runtime_diff.txt`에 구분 기록했다. 이 실행은 학습 데이터 생성이 아니다.

## 별도 실행 방식: GUI Script Editor

현재 Stage를 먼저 저장한 뒤 **Window → Script Editor**에서 실행한다. GUI 내부에서는 SimulationApp을 새로 만들지 않는다.

```python
import sys
script_dir = r"C:\Projects\press-cp-digital-twin\isaac_sim\scripts"
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
import display_playback

cp_task = display_playback.start()  # 기본 0.1초 간격
```

Timeline의 Play 버튼과 별도로 앱의 업데이트 루프와 실제 경과 시간을 사용한다. 이미 실행 중일 때 `start()`를 다시 호출하면 같은 Task를 반환한다. 실행 중 모듈을 reload하지 않는다.

```python
display_playback.status()  # running, index, text
display_playback.stop()    # 다음 앱 업데이트에서 중지; 마지막 숫자 유지
```

`cp_task.done()`이 True가 된 뒤 간격을 바꾸거나 다음 값부터 재개할 수 있다. 같은 실행 Stage가 유지되어 있으면 재사용한다.

```python
# 0.0부터 다시 시작, 0.5초 간격
cp_task = display_playback.start(interval_seconds=0.5)

# 중지한 다음 값부터 재개할 때
# last_index = display_playback.status()["index"]
# cp_task = display_playback.start(start_index=last_index + 1)
```

다른 Stage를 열면 Stage ID 변경을 감지해 숫자 갱신을 종료한다. Task 예외는 콘솔에 출력하며 `cp_task.result()`로도 확인할 수 있다. 보호 검사에서 미저장 Stage를 발견하면 저장 후 시작해야 한다.

## Standalone 실행

저장소 루트 PowerShell에서 실행한다. 기본 명령은 창이 있는 Isaac Sim을 실행하며 무제한으로 반복한다.

```powershell
& C:\isaacsim\python.bat isaac_sim/scripts/run_display_playback.py
# 간격 변경
& C:\isaacsim\python.bat isaac_sim/scripts/run_display_playback.py --interval 0.5
# 창 없이 998.8부터 여섯 번 갱신 후 종료
& C:\isaacsim\python.bat isaac_sim/scripts/run_display_playback.py --headless --updates 6 --start-index 9988
# 실제 렌더·연속 증가·중지/재개 검증
& C:\isaacsim\python.bat isaac_sim/scripts/run_display_playback.py --headless --verify
```

Standalone은 터미널에서 Ctrl+C로 종료한다. GUI Script Editor의 `stop()`은 Task만 중지하지만 Standalone의 유한 실행이 끝나면 자체 앱도 종료된다. interval은 유한한 양수, updates는 양수 정수, start-index는 0 이상의 정수이다. `wrap=false`이면 상한에 도달한 뒤 정상적으로 중지한다.

간격은 최소 대기 기준이다. 렌더 부하가 높으면 늦어지며 값을 건너뛰어 따라잡지 않는다. 0.1초를 하드 실시간 주기로 보장하지 않는다.

## 수행한 검증

환경: Isaac Sim `6.1.0-rc.26+release.49347.2d230af4.gl`, 설치된 USDRT 7.6.3의 공식 문서, Standalone headless.

- 최종 영상 검증 Run: `outputs/display_playback/20261001T041035_827388Z/`. `verification.json`은 PASS이며 `DISPLAY_PLAYBACK_OK`를 출력했다.
- 이 검증 프로세스는 검사 완료와 앱 종료 메시지 이후 도구 세션이 종료 대기에 남아 직접 중단했다. 영상 검사 PASS와 프로세스 종료 성공은 구분한다. 아래 일반 실행은 종료 코드 0을 별도로 확인했다. 종료 대기의 원인은 미확정이다.
- 실제 간격 루프에서 `0.0~1.9` 20회 갱신했다. 측정한 시작 간격은 0.109~0.110초였으며 인덱스 누락이 없었다.
- 무제한 루프에 `stop()`을 호출해 index 22에서 중지한 뒤 값이 유지됨을 확인했고 index 23, 24로 재개했다.
- 같은 Stage에서 `0.0, 0.1, 9.9, 10.0, 88.8, 999.0, 0.0`을 렌더했다. 갱신 중 Stage 재로딩은 0회이며 42개 Slot의 실제 Fabric Transform을 계산 조건과 대조했다.
- 42개 ROI 각각에서 값 변경 시 픽셀 변화와 마지막 `0.0`의 초기 영상 복귀 검사를 통과했다. 최대 반복값 평균 차이는 2.1167, 이전 `999.0`과의 차이는 최소 6.1273이다. Slot별 반복값 차이가 이전 다른 값과의 차이의 25% 미만인지 검사했다. 이 수치는 임시 잔류 검출 기준이며 OCR 정확도나 실영상 유사성 기준이 아니다.
- `contact_sheet.png`에서 42개 Slot의 숫자 변화와 상한 순환을 직접 시각 확인했다.
- 일반 실행 Run: `outputs/display_playback/20261001T041139_537888Z/`. `updates.jsonl`은 `998.8, 998.9, 999.0, 0.0, 0.1, 0.2`를 기록했고 `playback.json`은 STOPPED / updates 6이다. 일반 실행 프로세스 종료 코드 0.
- `python -m unittest discover -s tests -v`: 7개 테스트 통과. 9,991개 순차 값과 전 범위의 숫자 선택·정렬·크기, 상한·순환·잘못된 입력을 검사했다.
- 원본 Scene·Asset·텍스처 Hash는 영상 검증 전후 동일했다. 보고서에 Seed null, Config, 코드 Hash, 기반 Commit·dirty 상태와 실행 조건을 기록했다. Commit·Push는 수행하지 않았다.

GUI Script Editor API는 같은 실행 경로를 제공하지만 이번 직접 조작 검증은 Standalone headless이다. 전 범위 9,991개 값을 모두 렌더 저장한 것은 아니며, 전체 순회 테스트와 대표값 영상 검증을 구분한다. 실영상 보정, 학습용 ROI 정리·OCR 판독·대량 데이터 생성은 별도 후속 작업이다.

## 공식 API 근거

설치본 문서: `C:/isaacsim/extscache/usdrt.scenegraph-7.6.3+00c488ae.wx64.r.cp312/docs/fabricsd/fabric_hierarchy.rst`에서 로컬 Matrix 변경과 프레임 렌더 직전 World Transform 갱신 동작을 확인했다.

- [Fabric Transform과 계층 갱신](https://docs.omniverse.nvidia.com/kit/docs/usdrt.scenegraph/latest/fabricsd/fabric_hierarchy.html)
- [Isaac Sim 6.1 Python 유틸리티](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/python_scripting/util_snippets.html)
- [Isaac Sim 렌더 누적 초기화](https://docs.isaacsim.omniverse.nvidia.com/latest/replicator_tutorials/tutorial_replicator_getting_started.html#dlss-temporal-reset)

누적 초기화 문서는 latest의 공통 API 설명이며 설치된 RC의 실제 호환성은 위 실행으로 확인했다.
