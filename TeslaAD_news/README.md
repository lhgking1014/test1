## TeslaAD News

Streamlit 기반의 데일리 대시보드로 테슬라 자율주행 관련 뉴스를 모아 보여줍니다. 기본적으로 최근 24시간의 기사만 사용하지만, 수량이 부족하면 48시간 전까지 확장해 최대 12개의 카드로 채워집니다. 기사당 한글 요약과 원문 링크, OG/Twitter 썸네일(가능한 경우)이 제공되며, 사용자 피드백을 학습해 관련성을 지속적으로 개선합니다.

### 주요 구성 요소
- `src/pipeline.py`: Google · Naver 수집 → 유사 기사 제거 → 24/48h 필터 → 이미지 보강 → 번역 → JSON 저장
- `src/image_cache.py`: 원문 페이지에서 OG/Twitter 이미지를 추출하고 캐싱
- `src/feedback.py`: 토큰 가중치·기사 피드백 기록, 점수 계산
- `fetch_news.py`: 스케줄러/수동 실행용 CLI
- `app.py`: Streamlit UI (4열 카드, Hover 효과, 수동 새로고침·피드백 위젯)
- `data/news.json`: 최신 데이터 스냅샷
- `feedback/relevance.json`: 사용자 피드백 저장 파일

### 설치 & 실행
```bash
cd TeslaAD_news
python -m pip install -r requirements.txt
python fetch_news.py      # 최초 데이터 수집
streamlit run app.py
```
브라우저에서 `http://localhost:8501` 로 접속하세요.

### 피드백 & 학습
- 각 카드 아래에서 `관련성 높음/낮음`을 선택하면 토큰 가중치가 업데이트되어 다음 수집 시 기사 순위와 필터링에 반영됩니다.
- Low relevance로 표시된 기사는 이후 새로고침에서 즉시 제외되며, 동일한 기준의 키워드는 자동으로 더 낮은 가중치를 받습니다.

### 자동 갱신 (선택)
- Windows 작업 스케줄러(또는 cron)에 `python C:\...\TeslaAD_news\fetch_news.py` 를 등록해 매일 07:00 KST에 실행하세요.
- Streamlit 상단의 **뉴스 새로고침** 버튼으로도 즉시 갱신할 수 있습니다.

### 향후 확장 아이디어
- 정식 X API 연동 및 참여 지표 기반 가중치
- Slack/Discord/Email 알림 채널
- LLM 기반 고품질 요약/분석
