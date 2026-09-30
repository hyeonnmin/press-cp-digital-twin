\# 프로젝트 작업 규칙



\## 목표와 범위

\- 실제 프레스 CP 환경을 Isaac Sim에서 재현한다.

\- 합성 데이터로 OCR Recognition 모델을 학습하고 실제 영상에서 평가한다.

\- Baseline, Synthetic Only, Mixed를 공통 Real Test에서 비교한다.

\- FastAPI, Web, DB 연동과 기존 모니터링 서비스 확장은 제외한다.



\## 작업 시작

\- docs/project\_overview.md와 docs/progress.md를 먼저 확인한다.

\- 기존 코드, Config, 폴더 구조를 확인한 뒤 수정한다.

\- 한 번에 기능 하나와 완료 기준 하나를 중심으로 작업한다.

\- 계획이나 파일 생성만으로 실제 동작이 완료됐다고 판단하지 않는다.



\## Isaac Sim

\- 정확한 버전과 GUI Script, Extension, Standalone 실행 방식을 확인한다.

\- API는 해당 버전의 공식 문서를 확인한 뒤 사용한다.

\- USD Scene/Asset과 Python 자동화 로직을 분리한다.

\- Camera, Light, Material, Display 설정은 Config로 관리한다.

\- 실제 자료를 확인하기 전 수치나 랜덤화 범위를 확정하지 않는다.



\## 데이터와 실험

\- 화면 문자열의 소수점, 음수, 자릿수, 선행 0을 보존한다.

\- 생성 데이터에 Seed, Config, 코드 Commit, 실제 적용 조건을 기록한다.

\- 이미지와 정답의 연결 정보를 검증한다.

\- Real Train, Validation, Test 사이의 연속 프레임 누수를 방지한다.

\- 튜닝에는 Validation을 사용하고 Real Test는 최종 평가에 사용한다.

\- 비교 시 모델, 초기 가중치, 전처리, 데이터 수, 학습 예산을 기록한다.

\- 대량 이미지, 모델 Weight, 캐시는 일반 Git에 추가하지 않는다.



\## 문서와 보고

\- 답변과 문서는 한국어로 작성한다.

\- 확인한 사실, 가정, 제안을 구분한다.

\- 변경 내용, 수행한 검증, 남은 문제, 다음 작업을 보고한다.

\- 진행 상황은 docs/progress.md에 기록한다.

\- 중요한 결정은 docs/decisions.md에 이유와 영향을 기록한다.

