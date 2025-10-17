# Tesla News Daily Update

Daily Tesla news snapshots pulled from Google News and Naver, summarised and ready by 07:00 KST.

## Features
- Fetches 5–10 Tesla headlines with summaries, source name, and original links.
- Stores each refresh in `data/news.json` for reuse across the app.
- Flask web UI (`app.py`) renders the latest snapshot and exposes `/api/news`.
- APScheduler keeps the cache fresh at 07:00 KST (Asia/Seoul).
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
python app.py
```
The server listens on `http://127.0.0.1:5000/` by default. When the app starts it loads the cache (creating it if missing) and schedules the daily refresh for 07:00 KST.

To use the Flask development server instead:
```bash
set FLASK_APP=app:create_app
flask run
```

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
│   └── news.json
├── fetch_news.py
├── requirements.txt
├── static/
│   └── styles.css
└── templates/
    └── index.html
```
