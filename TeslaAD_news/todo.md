# TeslaAD 뉴스 앱 구현 계획

## 1. 프로젝트 구조 & 환경 준비
- [ ] `src/` 디렉터리 구성: `services/`, `adapters/`, `web/`, `config/`, `tests/`.
- [ ] Python 3.11 기준 `pyproject.toml` 혹은 `requirements.txt` 정의 (Flask, Requests, BeautifulSoup4, APScheduler, pytz, httpx 등).
- [ ] `.env.example` 작성: API 키, 프록시, 스케줄 설정 등 환경변수 명세.
- [ ] 기본 설정 로더(`config/settings.py`) 구현하여 KST 타임존, 데이터 경로, 스케줄 시간(매일 07:00 KST) 중앙 관리.

## 2. 데이터 수집 파이프라인
- [ ] **Google News RSS**: 자동주행 관련 검색어(테슬라, Autopilot, FSD 등) 중심으로 필터링하는 수집기 작성.
- [ ] **Naver 뉴스**: PC HTML 구조가 비어있었으므로 모바일 검색 페이지+`site:naver.com` RSS 대체 전략을 혼합하고, 24시간 필터링 적용.
- [ ] **X(Twitter)**: 공개 Nitter 미러(`r.jina.ai` 등)를 이용한 크롤러 또는 향후 정식 API 슬롯을 고려한 어댑터 설계. 캐시 & 중복 제거 구조 포함.
- [ ] 수집 결과를 표준 `NewsItem` 데이터클래스로 통합하고, JSON 스냅샷(`data/news.json`)에 저장.
- [ ] 공통 필터: 24시간 이내, 자율주행 키워드 포함, 주가/재무 위주 기사 제외 로직 재사용.

## 3. 비즈니스 로직 & 스케줄러
- [ ] `collector/manager.py`에서 여러 소스 결과를 병합·중복 제거하고 우선순위 정렬(자율주행 > 일반).
- [ ] APScheduler 혹은 시스템 크론을 이용해 KST 07:00에 자동 갱신. 장애 대비 수동 트리거 CLI(`python -m teslaad_news.refresh`) 준비.
- [ ] 로그 및 예외 처리: 네트워크 오류, 빈 결과, 레이트 리밋 발생 시 재시도 및 경고 로그 출력.

## 4. 웹 UI & API
- [ ] Flask 블루프린트 구조 (`web/app.py`): 
  - `/` : HTML 대시보드 (최신 기사 카드, 소스, 발행시각, 요약, 원문 링크)
  - `/api/news` : JSON 응답 (프론트 혹은 외부 연동용)
- [ ] 템플릿(`Jinja2`)과 정적 리소스(다크 모드 CSS) 작성.
- [ ] 24시간 범위 내 부족한 경우 사용자 안내 문구 표시.

## 5. 테스트 & 품질
- [ ] 수집 모듈 단위 테스트: 키워드 필터, 중복 제거, 24시간 필터.
- [ ] 통합 테스트: 가짜 RSS/HTML/X 응답을 사용해 전체 파이프라인 검증.
- [ ] `pre-commit` 훅 (black, isort, flake8) 설정.

## 6. 배포 & 운영
- [ ] README 작성: 설치, 실행(`python app.py`), 수동 갱신, Windows 작업 스케줄러/cron 등록 안내.
- [ ] Dockerfile(Optional): prod 실행용 WSGI 서버(gunicorn) 포함 이미지 정의.
- [ ] 로그 로테이션 및 모니터링 가이드 (예: Windows Event Viewer, systemd journal 등) 문서화.
- [ ] 향후 확장 TODO: OpenAI 요약, 슬랙/텔레그램 알림, 정식 X API 연동.
