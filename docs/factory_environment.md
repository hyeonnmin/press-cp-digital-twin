# CP 주변 설비와 공장 실내

2026-10-02. 사용자 제공 `frame_000001.png`를 참고해 기존 CP를 보존하고 주변 공간을 확장했다. 생성·별도 프로세스 재열기·정적 렌더 검증을 완료했다.

## 사용

Isaac Sim에서 `isaac_sim/stages/press_cp_main.usda`를 다시 연다. 기본 시점은 공장 전체를 보는 `/World/Cameras/factory`이다. 기존 GUI에 이미 열려 있다면 저장 전 변경분을 별도로 보존한 다음 파일을 다시 열어 새 환경을 읽는다.

| 카메라 | 용도 |
|---|---|
| `/World/Cameras/factory` | 기둥·보·천장·배경 설비와 CP를 함께 보는 실내 전경 |
| `/World/Cameras/workcell` | CP와 좌우 설비·배관의 근접 사선 시점 |
| `/World/Cameras/reference` | 기존 실영상 비교 구도 |
| `/World/Cameras/training` | 기존 정면 중앙 직교 학습 구도 |
| `/World/Cameras/overview`, `detail` | 기존 사선 및 숫자 근접 구도 |

## 구성과 근거

- 사진에서 관측: CP 왼쪽의 회색 설비와 금속 배관, 오른쪽 수직 배관·플랜지·녹색 밸브·어두운 핸드휠, 설비 베이스, 회색 바닥.
- 가정으로 확장: 12×14 m 실내, 약 4.8 m 높이의 기둥·보·지붕, 상부 창, 후방 셔터문, 천장등 9개, 케이블 트레이·공급 배관, 바닥 줄눈·작업 통로, 좌측 및 후방 프레스 외형.
- 모든 크기·위치·재질·광도는 임시 시각 모델링 값이다. 사진 한 장으로 보이지 않는 공장 구조나 실제 설비 기능을 복원했다고 해석하지 않는다. 랜덤화는 없고 Seed는 null이다.
- 기존 CP Asset·명판 텍스처·표시 문자열·계측기 배치·Play 연결·기존 4개 카메라·기존 조명은 유지한다. 천장등 9개·창측 보조광 4개와 주변 반사체 추가로 렌더의 밝기·반사는 달라질 수 있다.
- 충돌·구동·배관 유체 연결을 구현한 공정 시뮬레이션이 아닌 정적 시각 환경이다.

## 파일과 재실행

환경 치수·배치·재질·조명·추가 카메라는 `config/factory_environment.json`, 생성 로직은 `isaac_sim/scripts/factory_environment.py`, 형상은 `isaac_sim/assets/environment/workcell.usda`에 분리했다. 메인 USD는 기존 상대 경로로 환경을 참조한다.

```powershell
# CP를 재생성하지 않고 환경만 갱신하고 렌더·보존 검증
& C:\isaacsim\python.bat isaac_sim/scripts/verify_factory_environment.py
# 별도 프로세스에서 저장 파일 재열기·검증
& C:\isaacsim\python.bat isaac_sim/scripts/verify_factory_environment.py --reopen-only
```

결과는 `outputs/factory_environment/<실행 ID>/`의 PNG와 `verification.json`이다. 생성 실행에서는 수정 직전 메인 USD와 환경 USD도 이 폴더에 보관한다. 이 복사본은 상대 참조를 사용하므로 다른 폴더에서 단독 Scene으로 여는 용도가 아니라 원래 위치에 복구할 때 쓰는 백업이다.

기존 `verify_full_scene.py` 전체 재생성 경로도 새 환경 생성기를 호출한다. **전체 재생성은 기존 설계대로 CP Asset도 다시 작성**하므로 이번처럼 CP 원본을 그대로 유지하는 작업에는 위 환경 전용 명령을 사용한다.

검증기는 CP·텍스처 등 보존 파일 SHA-256, CP/기존 카메라/기존 조명/Behavior 속성과 관계, 7/21/42 구성과 고유 ID, 새 실내 구성, 텍스처 해석, 저장 파일 재열기, 실제 PNG 저장을 검사한다. 코드·Config·Asset·렌더 Hash, 실제 렌더 설정, Isaac 버전·Commit·dirty 상태를 기록한다. 실제 실행 결과는 `docs/progress.md`에 기록한다.

Kit이 열기/카메라 전환 시 기존 노출 설정을 `exposure:*`, `omni:rtx:autoExposure:*` Camera 속성으로 자동 변환하는 동작을 확인했다. 이 런타임 차이는 보고서와 별도 diff JSON에 기록하고 저장 파일에는 쓰지 않는다. 디스크 파일 Hash와 변환 이전 보호 속성 비교는 별도로 수행한다.

## 완료한 검증과 결과

| 실행 | 결과 | 산출물 |
|---|---|---|
| 환경 생성 | PASS, 종료 코드 0 | [보고서](../outputs/factory_environment/20261002T023626_551882Z/verification.json), [전경](../outputs/factory_environment/20261002T023626_551882Z/factory.png), [근접](../outputs/factory_environment/20261002T023626_551882Z/workcell.png) |
| 별도 프로세스 재열기 | PASS, 종료 코드 0 | [보고서](../outputs/factory_environment/20261002T023707_135387Z/verification.json), [전경](../outputs/factory_environment/20261002T023707_135387Z/factory.png) |

생성 실행은 `factory`·`workcell`·`reference`·`training` 4개 시점, 재열기는 `factory`·`reference` 2개 시점을 1920×1080으로 저장했다. 이 해상도는 검토용이며 학습 생성의 3840×2160 설정과 구분한다. CP·기존 카메라·조명·Behavior 등 701개 보호 Prim과 7/21/42 구성, CP Asset·텍스처 등 보존 파일 Hash를 확인했다. 2026-10-02 문서 갱신에서도 두 보고서의 코드·Config·Asset·렌더·보존 파일 Hash를 현재 파일과 대조해 일치를 확인했다.

## 한계와 다음 작업

새 조명 환경에서 학습 생성·OCR 성능과 GUI Play를 다시 검증한 것은 아니다. 기존 학습 Run의 생성 조건도 소급 변경하지 않는다. 다음 작업은 새 환경의 시점과 밝기를 검토한 뒤 필요한 경우 별도 Run으로 학습 데이터 생성 회귀 검증을 하는 것이다. 제공 프레임은 외형 구성에 사용한 자료로 기록하며 최종 Real Test 구간 선정 시 보정 이력을 고려한다.

## 확인한 공식 API

- [Isaac Sim 6.1 OpenUSD](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/omniverse_usd/open_usd.html)
- [Isaac Sim 6.1 SimulationApp](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)
- [OpenUSD Xformable](https://openusd.org/release/api/class_usd_geom_xformable.html)
- [OpenUSD RectLight](https://openusd.org/release/api/class_usd_lux_rect_light.html)
- [Omniverse Viewport 캡처](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.viewport.utility/latest/omni.kit.viewport.utility/omni.kit.viewport.utility.capture_viewport_to_file.html)

설치본은 `6.1.0-rc.26+release.49347.2d230af4.gl`이며 Standalone headless에서 검증한다. GUI Script/Extension 실행과 구분한다.
