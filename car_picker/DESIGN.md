# 자동차 이미지 퀴즈 앱 설계

## 1. 목표
- `car_picker/data` 안의 자동차 이미지(예: `Acura_ILX_2013_28_16_110_15_4_70_55_179_39_FWD_5_4_4dr_Cvl`)를 활용해, 사용자가 제조사·모델·연식을 모두 맞추는 10지선다 퀴즈 앱을 만든다.
- 한 세션은 10문항으로 구성하며 시간 제한은 없다.
- 각 문제는 정답을 제출한 뒤 결과와 정답을 바로 알려준다.
- 구현 프레임워크는 **Streamlit**을 사용한다.

## 2. 전반적인 구조
```
car_picker/
├─ data/               # 원본 이미지 (이미 존재)
├─ thumbs/             # 썸네일 (사전 생성)
├─ scripts/
│  ├─ build_index.py   # 이미지 색인을 생성
│  └─ make_thumbs.py   # 썸네일 생성
├─ app/
│  ├─ __init__.py
│  ├─ game_state.py    # 세션 상태/점수 관리
│  ├─ parser.py        # 파일명 → 메타데이터 파싱
│  ├─ question_bank.py # 문제/보기 생성 로직
│  └─ streamlit_app.py # Streamlit UI 진입점
└─ index.json          # 사전 생성된 이미지 메타데이터
```

## 3. 데이터 파싱
1. 파일명 규칙은 스크래퍼 README를 따른다. 주요 키 포맷:  
   `Make_Model_Year_<기타 특성들>`.  
   - `Make`: 제조사 (예: `Acura`)  
   - `Model`: 모델명 (예: `ILX`)  
   - `Year`: 4자리 연식 (예: `2013`)  
   - 이후 값들은 차체 크기, 감각 지표, 구동 방식 등의 코드이므로 파싱 시 보조 정보로 보관하거나 무시한다.
2. `parser.py`는 다음 정보를 추출한다.
   - `id`: 파일명에서 확장자를 제거한 식별자
   - `make`: 첫 번째 토큰
   - `model`: 두 번째 토큰(필요 시 `_`를 공백으로 변환해 UI에 표기)
   - `year`: 세 번째 토큰(정수 변환)
   - `attributes`: 이후 토큰을 배열로 저장(필요 시 난이도 조절/통계에 활용)
3. 파싱 실패 케이스는 로그로 남기고 색인에서 제외한다(연식 누락 등).

## 4. 색인 생성(`build_index.py`)
1. `data/` 내 이미지를 순회하며 `parser.py`로 메타데이터를 추출한다.
2. JSON Schema(예시):
   ```json
   {
     "version": 1,
     "generated_at": "ISO8601",
     "items": [
       {
         "id": "Acura_ILX_2013_...",
         "path": "data/Acura_ILX_2013_...jpg",
         "make": "Acura",
         "model": "ILX",
         "model_display": "ILX",
         "year": 2013,
         "attributes": ["28", "16", "..."]
       }
     ],
     "catalog": {
       "makes": ["Acura", "Audi", "..."],
       "models": {
         "Acura": ["ILX", "TLX", "..."]
       },
       "years_by_model": {
         "Acura|ILX": [2013, 2014, ...]
       }
     }
   }
   ```
3. `catalog`는 빠른 오답 생성을 위해 미리 계산한다.

## 5. 썸네일 생성(`make_thumbs.py`)
- `Pillow`로 512px 이하의 정사각형 혹은 긴 변 기준 리사이즈 이미지를 생성한다.
- 썸네일 경로를 `index.json`의 각 항목에 `thumb_path`로 추가하거나, Streamlit에서 규칙적으로 유추한다.

## 6. 퀴즈 로직(`question_bank.py`)
1. **문제 선택**  
   - `index.json`에서 무작위로 하나를 선택하되, 세션 내 중복을 방지한다.
   - 선택한 항목 기준으로 `make`, `model`, `year`를 정답으로 사용한다.
2. **보기(10개 고정)**  
   - 정답 1개 + 오답 9개.
   - 오답 구성 전략:
     1. 동일 제조사, 다른 모델/연식
     2. 동일 모델, 다른 연식(해당 모델 생산 연식 내에서)
     3. 다른 제조사(같은 차급으로 추정되는 항목, `attributes` 참조 가능)
   - 충분한 후보가 없을 경우 우선순위대로 채우고, 남는 자리는 무작위로 보충하되 중복을 허용하지 않는다.
3. **출력 형식**  
   - 각 보기 라벨: `"제조사 모델 연식"` (예: `Acura ILX 2013`)
   - 문제 ID와 보기 ID(원본 item id)를 묶어서 반환한다.
4. **정답 검증**  
   - 사용자가 선택한 보기와 문제 ID를 비교해 정확히 일치하면 정답.
   - 정답 여부와 함께 정답 라벨을 반환해 Streamlit에서 즉시 표시한다.

## 7. 세션 및 점수 관리(`game_state.py`)
- Streamlit의 `st.session_state`를 사용.
- 저장 항목:
  - `questions`: 현재 세션에서 제시할 문제 리스트(사전 생성 또는 진행 중 생성)
  - `current_index`: 현재 문제 번호 (0~9)
  - `score`: 정답 개수
  - `history`: 각 문항의 선택/정답 기록
- 문제를 10개 풀면 세션 종료 화면과 점수/정답률을 보여준다.

## 8. Streamlit UI(`streamlit_app.py`)
1. **구조**
   - 상단 헤더: 제목, 진행 상황(예: `3 / 10`, 현재 점수)
   - 중앙: 이미지(썸네일 우선, 필요시 전체 이미지) + alt 텍스트(정답 정보 기반)
   - 하단: 10개의 버튼(세로 2열 또는 5×2 Grid), 키보드 `1`~`0`으로 선택 가능하도록 `st.button` / 커스텀 컴포넌트 사용
   - 제출 후: 정답 여부 메시지와 정답 표시, "다음 문제" 버튼
2. **상태 전환**
   - 사용자가 보기 클릭 → `game_state` 업데이트 → 정답 결과 출력 → 다음 문제 로드
3. **세션 종료**
   - 10문항 완료시 최종 점수, 정답 리스트(이미지 + 정답 라벨) 정리 및 재시작 버튼 표시

## 9. 필요 패키지 및 실행
- `requirements.txt` 예시:
  ```
  streamlit
  pillow
  ```
- `pip install -r requirements.txt` 실행
- `streamlit run car_picker/app/streamlit_app.py`

## 10. 투두 순서
1. `parser.py` 구현 및 샘플 파일명 테스트
2. `build_index.py` 실행으로 `index.json` 생성
3. `make_thumbs.py` 실행으로 썸네일 생성
4. `question_bank.py`, `game_state.py` 작성
5. `streamlit_app.py` 작성 및 UI 마감
6. 수동 테스트: 10문항 세션 플레이, 중복/오답 구성 확인
7. (선택) 모델명 표시 개선, 난이도 조정 로직 고도화

---
추가 요구나 규칙 변경 사항이 생기면 위 문서를 업데이트하면서 진행한다.
