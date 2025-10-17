# Tesla News Daily Update

Daily Tesla news snapshots pulled from Google News and Naver, summarised and ready by 07:00 KST.

## Features
- Fetches 5–10 Tesla headlines with summaries, source name, and original links.
- Stores each refresh in `data/news.json` for reuse across the app.
- Streamlit UI (`streamlit_app.py`) lets you score relevance (높음/낮음) and 기록 이유 for 낮은 관련성, building a reusable 평가 기준.
- Prioritises autonomous-driving topics, drops stock-price driven coverage, and ensures at least one Naver-sourced headline plus recent X chatter.

## Source Strategy
- Google News RSS (KR/US) filtered to autonomous-driving keywords.
- Naver coverage gathered via Google News `site:naver.com` queries so links land on the original Naver articles.
- X posts scraped through the public Nitter bridge (via `r.jina.ai`) and linked back to matching Nitter search results.

## First-Time Setup
```bash
cd Tesla_news
python -m pip install -r requirements.txt
```

## Updating The Dataset Manually
```bash
cd Tesla_news
python fetch_news.py
```
The script writes fresh data into `data/news.json`. Expect between 5 and 10 items depending on source availability.

## Running The Web App
```bash
cd Tesla_news
streamlit run streamlit_app.py
```
Streamlit automatically reloads on save. Use the 사이드바의 “뉴스 새로고침” 버튼 to force an update from the remote sources, 평가 each 기사, and 저장 your 판단. 평가 결과는 `data/evaluations.json`에 누적되며, 화면에서 CSV/JSON으로 내려받을 수 있습니다.

## Scheduling Daily Updates On Windows
1. Open **Task Scheduler** and create a **Basic Task**.
2. Trigger: **Daily**, start time `07:00:00`.
3. Action: **Start a program**.
   - Program/script: `python`
   - Add arguments: `"C:\Users\user\Desktop\test1\test1\Tesla_news\fetch_news.py"`
   - Start in: `C:\Users\user\Desktop\test1\test1\Tesla_news`
4. Finish and ensure the task runs whether the user is logged on or not if needed.

> If the machine is not running at 07:00 KST, configure the task to run as soon as possible after the scheduled time.

## Extending Sources
- Google News feeds can be tweaked inside `fetch_news.collect_news`.
- Adding Naver API powered searches requires client credentials; the HTML scraper included here is rate limited and should be used responsibly.
- X (Twitter) support needs official API access; hook into `collect_news` once credentials are available.

## Project Tree
```
Tesla_news/
├── app.py
├── data/
│   ├── news.json
│   └── evaluations.json (생성 후)
├── fetch_news.py
├── streamlit_app.py
├── requirements.txt
├── static/
│   └── styles.css
└── templates/
    └── index.html
```
