from __future__ import annotations

import json
from datetime import datetime
from html import escape
from typing import Any, Dict, List

import streamlit as st

from src import config, feedback
from src.pipeline import collect_news, write_news


st.set_page_config(
    page_title="Tesla Autonomous Driving Daily",
    page_icon="??",
    layout="wide",
)

CARD_STYLE = """
<style>
.tesla-card {
  background: linear-gradient(180deg, rgba(13,17,23,0.95) 0%, rgba(22,27,34,0.9) 100%);
  border-radius: 16px;
  border: 1px solid rgba(240,246,252,0.08);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}
.tesla-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 35px rgba(2,12,27,0.35);
  border-color: rgba(88,166,255,0.6);
}
.tesla-card a {
  color: inherit;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1.2rem;
  gap: 0.8rem;
}
.tesla-card-content {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  flex: 1;
}
.tesla-card h3 {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.45;
  color: #f0f6fc;
}
.tesla-card ul {
  margin: 0;
  padding-left: 1.1rem;
  color: #c9d1d9;
}
.tesla-card li {
  margin-bottom: 0.35rem;
  line-height: 1.45;
}
.tesla-card-footer {
  font-size: 0.8rem;
  color: #8b949e;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.feedback-toggle {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.35rem;
}
.feedback-toggle button {
  flex: 1;
}
.feedback-note {
  font-size: 0.75rem;
  color: #8b949e;
  margin-top: -0.45rem;
  margin-bottom: 0.35rem;
}
</style>
"""


def load_news() -> Dict[str, Any]:
    if not config.DATA_FILE.exists():
        items = collect_news()
        return write_news(items)
    try:
        return json.loads(config.DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        items = collect_news()
        return write_news(items)


def render_cards(items: List[Dict[str, Any]]) -> None:
    st.markdown(CARD_STYLE, unsafe_allow_html=True)
    columns_per_row = 4
    cols = st.columns(columns_per_row)

    for idx, item in enumerate(items):
        if idx != 0 and idx % columns_per_row == 0:
            cols = st.columns(columns_per_row)
        col = cols[idx % columns_per_row]
        with col:
            highlights = item.get("highlights") or []
            if highlights:
                bullet_html = "<ul>" + "".join(f"<li>{escape(point)}</li>" for point in highlights) + "</ul>"
            else:
                summary_text = escape(item.get("summary", ""))
                bullet_html = f"<p>{summary_text}</p>" if summary_text else ""

            card_html = f"""
            <div class=\"tesla-card\">
              <a href=\"{item['url']}\" target=\"_blank\" rel=\"noopener noreferrer\">
                <div class=\"tesla-card-content\">
                  <h3>{escape(item['title'])}</h3>
                  {bullet_html}
                  <div class=\"tesla-card-footer\">
                    <span>{escape(item['source'])}</span>
                    <span>{format_time(item['published_at'])}</span>
                  </div>
                </div>
              </a>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            feedback_info = feedback.get_article_feedback(item["url"])
            current_label = feedback_info.get("relevance")
            current_reason = feedback_info.get("reason") if feedback_info else None

            reason_key = f"{hash(item['url'])}_low_reason"
            if reason_key not in st.session_state:
                st.session_state[reason_key] = current_reason or ""

            col_high, col_low = st.columns(2)
            with col_high:
                high_pressed = st.button(
                    "High relevance",
                    key=f"{hash(item['url'])}_high",
                    use_container_width=True,
                )
            with col_low:
                low_pressed = st.button(
                    "Low relevance",
                    key=f"{hash(item['url'])}_low",
                    use_container_width=True,
                )

            st.text_area(
                "Low relevance reason (optional)",
                key=reason_key,
                placeholder="예: 기사 내용이 자율주행과 관련이 없어요.",
                height=80,
            )
            st.markdown(
                "<div class='feedback-note'>Low relevance 선택 시 간단한 이유를 남겨주시면 기사 선별에 도움이 됩니다.</div>",
                unsafe_allow_html=True,
            )

            feedback_label = None
            reason_to_submit = None
            if high_pressed:
                feedback_label = "High relevance"
            elif low_pressed:
                feedback_label = "Low relevance"
                reason_to_submit = st.session_state.get(reason_key, "").strip()

            should_submit = False
            if feedback_label == "High relevance":
                should_submit = current_label != "High relevance"
            elif feedback_label == "Low relevance":
                should_submit = True

            if should_submit:
                if feedback.record_feedback(
                    item["url"],
                    item["title"],
                    item["summary"],
                    feedback_label,
                    reason_to_submit,
                ):
                    if feedback_label != "Low relevance":
                        st.session_state[reason_key] = ""
                    updated = feedback.get_article_feedback(item["url"])
                    current_label = updated.get("relevance")
                    current_reason = updated.get("reason")
                    st.toast("Feedback saved.", icon="?")

            if current_label:
                caption = f"Current feedback: **{current_label}**"
                if current_label == "Low relevance" and current_reason:
                    caption += f" · Reason: {current_reason}"
                st.caption(caption)


def format_time(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = config.KST.localize(dt)
        else:
            dt = dt.astimezone(config.KST)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str


def main() -> None:
    st.title("Tesla Autonomous Driving Daily Briefing")
    st.caption("Latest Tesla autonomous driving news, refreshed daily at 07:00 KST")

    data = load_news()
    updated_at = format_time(data.get("updated_at", datetime.now(config.KST).isoformat()))

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Refresh now", use_container_width=True):
            with st.spinner("Fetching the latest headlines..."):
                items = collect_news()
                data.update(write_news(items))
                st.rerun()
    with col2:
        st.markdown(f"**Last updated:** {updated_at}")

    items = data.get("items", [])
    if not items:
        st.info("No news to display. Please try again shortly.")
        return

    render_cards(items)


if __name__ == "__main__":
    main()
