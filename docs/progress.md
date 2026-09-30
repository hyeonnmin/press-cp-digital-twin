\# 프로젝트 진행 상황



최종 갱신: 2026-09-30

현재 Phase: 1 — 실제 환경 분석 준비

현재 작업: 대표 실제 CP 이미지 확보



\## 확인된 완료 항목

\- Git 2.50.1.windows.1 설치 확인

\- Git 작성자 이름·이메일과 기본 브랜치 설정 확인

\- 저장소 위치: C:\\Projects\\press-cp-digital-twin

\- 현재 브랜치: main

\- .gitignore와 .gitattributes를 Git에 추가

\- datasets와 checkpoints 제외 규칙 검증 통과

\- 첫 Commit: 5c0f003 — chore: configure project version control

\- 첫 Commit 후 working tree clean 확인

\- 폴더 생성·문서 작성·Commit

\- 기본 구조·작업 문서 Commit: 9080cd2

\- GitHub origin/main 연결 및 첫 Push 성공

\- Isaac Sim 6.0.1 및 isaac-sim.bat 실행 방식 사용자 확인

\- 환경 확인 스크립트를 GUI Script Editor에서 2회 실행 성공

\- 내부 Python 3.12.13 확인

\- 현재 익명 Stage의 Z-up, metersPerUnit 1.0 확인

\- GPU: NVIDIA GeForce RTX 4070 SUPER, 12282 MiB

\- GPU Driver: 591.86

\- Isaac Sim 재시작 후 환경 확인 스크립트 실행 성공

\- 환경 확인 코드·기록 Commit: f54f878, GitHub 동기화 확인



\## 진행 중

\- 기본 폴더 생성

\- project\_overview.md를 docs로 이동

\- AGENTS.md와 이 진행 문서 작성

\- 위 변경의 내용 검토와 Commit



\## 미확인·미완료

\- 대용량 USD Asset 관리 방식

\- Python·OCR 프레임워크 환경

\- Stage Up-axis와 metersPerUnit

\- 기준 실행 방식에서 최소 Script 반복 실행 확인



\## 다음 작업

\- 최종 문서의 Commit·Push 확인 후 Phase 0 완료 기록

\- Phase 1: 대표 실제 CP 이미지에서 패널·숫자 영역 분석 시작



\## Phase 0 완료 판단



2026-09-30 초기 세팅 완료.



\- Git/GitHub 연결과 Commit·Push 확인

\- 기본 구조와 작업 규칙·환경 문서 준비

\- Isaac Sim 내부 환경 확인 스크립트 반복 실행 성공

\- 앱 재시작 후 CHECK\_OK 확인

\- 마무리 문서 Commit: af11aaa



Base Scene 구현과 데이터 생성·OCR 학습은 아직 시작하지 않았다.

