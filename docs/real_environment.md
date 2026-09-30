\# 실행환경과 실제 환경 정보



최종 갱신: 2026-09-30



\## 개발 실행환경



| 항목 | 값 | 확인 근거 |

|---|---|---|

| OS | Windows-11-10.0.26200-SP0 | 스크립트 출력 |

| Isaac Sim | 6.0.1 | 사용자 확인 |

| 앱 실행 | C:\\isaacsim\\isaac-sim.bat | 사용자 확인 |

| 이번 검증의 코드 실행 방식 | GUI Script Editor | 사용자 실행 결과 |

| Isaac Sim 내부 Python | 3.12.13 | 스크립트 출력 |

| GPU | NVIDIA GeForce RTX 4070 SUPER | nvidia-smi 출력 |

| GPU Driver | 591.86 | nvidia-smi 출력 |

| GPU 메모리 | 12282 MiB | nvidia-smi 출력 |



\## Stage 확인 결과



\- 확인 대상: 현재 열린 익명 Stage

\- 파일 저장 여부: 미저장

\- Up-axis: Z

\- Meters per unit: 1.0

\- 위 값은 현재 Stage에서 읽은 결과다.

\- 프로젝트 Base Scene은 아직 생성하지 않았다.



\## 최소 스크립트 검증



\- 스크립트: isaac\_sim/scripts/check\_environment.py

\- 실행 방식: Script Editor에서 파일을 읽어 실행

\- 검증 결과: 동일 앱 세션에서 2회 CHECK\_OK 확인

\- 앱 재시작 후 실행: CHECK\_OK 확인

\- Stage 생성·수정·저장 기능: 미검증



\## 실제 촬영환경



다음 항목은 Phase 1에서 확인한다.



\- 카메라·렌즈 모델과 설치 위치·방향

\- 실제 획득 해상도와 OCR 입력 해상도

\- 패널·모듈 크기와 배치

\- 조명·반사·숫자 표시 특성

