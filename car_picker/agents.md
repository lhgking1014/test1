# AGENTS.md

## 프로젝트 개요
- Streamlit 기반 10문항 자동차 식별 퀴즈입니다.
- 메타데이터는 `index.json`(약 40 MB), UI에 쓰이는 썸네일은 `thumbs/`에서 제공합니다.
- UI 스타일은 `app/streamlit_app.py`에 있으며 Streamlit >= 1.38을 기준으로 합니다(프래그먼트, 콜백 버튼, `st.container(..., border=True)` 등).

## 환경 및 설정
- 타깃 파이썬 버전은 3.10 이상(개발은 3.11에서 진행).
- 의존성 설치: `pip install -r car_picker/requirements.txt`.
- 로컬 실행: `streamlit run car_picker/app/streamlit_app.py`.

## 데이터 및 에셋
- 원본 이미지는 `data/`, 썸네일은 `thumbs/` 아래에 있습니다.
- `index.json`은 수동 수정 금지. `python car_picker/scripts/build_index.py`(Pillow 필요)로 재생성합니다.
- 썸네일 생성: `python car_picker/scripts/make_thumbs.py`.
- 이미지를 추가할 때는 `make_thumbs.py` 실행 후 `build_index.py`를 실행하세요.
- 큰 바이너리는 가급적 커밋에 포함하지 말고 필요 시 스크립트로 재생성하세요.

## 패키지 구조
- `app/` - Streamlit 앱 코드(상태 관리, 문제 생성, 저장소/파서).
- `scripts/` - 메타데이터·썸네일 관리용 유틸리티 스크립트.
- `data/` & `thumbs/` - 자산 디렉터리(새로운 대용량 파일은 사전 협의 없이 커밋하지 않습니다).
- `DESIGN.md` - 퀴즈 흐름에 대한 원래 UX 문서.

## 코딩 가이드라인
- PEP 8을 따르되 소프트 한계는 88자입니다.
- 기존 스타일에 맞춰 `pathlib.Path`, 타입 지정된 dataclass, 순수 함수를 선호합니다.
- Streamlit 콜백은 부작용 없이 유지하고, 공유 상태는 `get_state`, `record_choice` 등의 헬퍼 함수를 사용해 조작합니다.
- 번역된 UI 텍스트(현재 일부 구문은 한국어) 수정 시 일관되게 업데이트하세요.

## Streamlit 패턴
- 인터랙티브 영역에는 `st.fragment`를 사용해 전체 리런을 방지합니다.
- 인라인 HTML 대신 기존 CSS 주입 로직을 재사용하고, 스타일이 필요하면 `inject_styles()`를 확장하세요.
- 버튼은 수동 `st.rerun()` 호출 대신 `on_click` 콜백을 활용합니다.
- 피드백은 리뉴얼된 디자인에 맞춰 `st.toast`, `st.progress`, 테두리 있는 컨테이너를 사용하세요.

## 테스트 및 QA
- 수동 스모크 테스트: `streamlit run ...` 실행 후 퀴즈를 진행하며 진행 표시기, 토스트, 요약 테이블, 재시작 버튼이 정상 동작하는지 확인합니다.
- 스크립트: 메타데이터 파싱을 수정했다면 변경 전후로 `python car_picker/scripts/build_index.py --help`를 실행합니다(아직 CLI는 없음).
- 파서 로직이 바뀌면 `data/`의 대표 파일을 대상으로 테스트해 `CarMeta.display_label`과 필터링이 정상 작동하는지 확인하세요.

## 배포 노트
- 기본 배포 대상은 Streamlit Cloud입니다. `requirements.txt`를 최소한으로 유지하세요.
- 새 의존성을 추가할 때는 Streamlit Sharing과의 호환성(가능하면 순수 파이썬)을 확인합니다.
- 비밀 값은 Streamlit Sharing UI를 통해 관리하며, 현재 필요한 값은 없습니다.

## 커뮤니케이션
- 주요 워크플로 변경은 `DESIGN.md`와 커밋 메시지에 기록하세요.
- 스크립트 재실행이나 에셋 재생성이 필요하면 PR 설명에 명시하세요.
