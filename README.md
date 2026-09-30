\# Press CP Digital Twin



실제 프레스 CP 환경을 NVIDIA Isaac Sim에서 재현하고,

합성 데이터로 학습한 OCR Recognition 모델의 실제 영상 일반화 성능을 평가한다.



\## 비교 실험

\- Baseline: Real Train으로 학습

\- Synthetic Only: Synthetic Train으로 학습

\- Mixed: Real Train + Synthetic Train으로 학습

\- 평가: 공통 Real Test Dataset 사용



\## 주요 문서

\- 공통 계획: docs/project\_overview.md

\- 진행 상태: docs/progress.md

\- 환경 정보: docs/real\_environment.md

\- Codex 작업 규칙: AGENTS.md



\## 폴더 역할

\- docs: 계획, 환경, 진행 및 실험 기록

\- config: Camera, Light, Material, Display 설정

\- isaac\_sim: USD Scene/Asset과 앱 내부 스크립트

\- src: 데이터 생성, 검증, 평가 로직

\- experiments: 실험 설정과 결과 요약

\- tests: 필요한 검증 코드



빈 폴더는 Git에 기록되지 않으며 세부 구조는 구현 시 추가한다.



\## 현재 검증된 실행 방식

\- Isaac Sim 6.0.1

\- 앱 실행: C:\\isaacsim\\isaac-sim.bat

\- 코드 실행: GUI의 Window > Script Editor



Script Editor에서 다음 코드를 실행한다.



```python

script\_path = r"C:\\Projects\\press-cp-digital-twin\\isaac\_sim\\scripts\\check\_environment.py"



with open(script\_path, encoding="utf-8-sig") as file:

&#x20;   exec(compile(file.read(), script\_path, "exec"))

