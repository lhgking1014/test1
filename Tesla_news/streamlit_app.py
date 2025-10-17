"""Streamlit interface for reviewing Tesla news relevance."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Set, Tuple

import pandas as pd
from streamlit import runtime
import streamlit as st

from fetch_news import DATA_PATH, KST, collect_news, ensure_data_directory, write_news

LOW_RELEVANCE_REASON_PLACEHOLDER = "요약이 부족하거나 주제가 맞지 않는 이유를 적어주세요."

EVALUATIONS_PATH = DATA_PATH.parent / "evaluations.json"
EVALUATIONS_CSV_PATH = DATA_PATH.parent / "evaluations.csv"


def _collect_and_store_news(exclude_keys: Set[str] | None = None) -> Tuple[Dict, int]:
    """Collect Tesla news items, optionally excluding specific keys, and persist them."""
    items = collect_news()
    removed_count = 0
    if exclude_keys:
        filtered_items = []
        for item in items:
            key = item.url or item.title
            if key and key in exclude_keys:
                removed_count += 1
                continue
            filtered_items.append(item)
        items = filtered_items
    payload = write_news(items)
    return payload, removed_count


def _load_news_payload(force_refresh: bool = False, exclude_keys: Set[str] | None = None) -> Dict:
    """Return cached Tesla news payload, refreshing if requested or missing."""
    ensure_data_directory()
    if force_refresh:
        payload, _ = _collect_and_store_news(exclude_keys)
        return payload
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            st.warning("저장된 뉴스 데이터가 손상되어 새로 불러옵니다.")
    payload, _ = _collect_and_store_news(exclude_keys)
    return payload


def _load_evaluations() -> Dict:
    """Load saved relevance evaluations from disk."""
    ensure_data_directory()
    if EVALUATIONS_PATH.exists():
        try:
            return json.loads(EVALUATIONS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            st.warning("저장된 평가 데이터가 손상되어 새로 작성합니다.")
    return {"updated_at": None, "items": []}


def _save_evaluations(entries: List[Dict]) -> Dict:
    """Persist evaluation entries to disk and return the saved payload."""
    ensure_data_directory()
    payload = {
        "updated_at": datetime.now(KST).isoformat(),
        "items": entries,
    }
    EVALUATIONS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    df = pd.DataFrame(entries)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "title",
                "source",
                "url",
                "summary",
                "relevance",
                "reason",
                "evaluated_at",
            ]
        )
    df.to_csv(EVALUATIONS_CSV_PATH, index=False, encoding="utf-8-sig")
    return payload


def extract_low_relevance_keys(evaluations: Dict) -> Set[str]:
    keys: Set[str] = set()
    for entry in evaluations.get("items", []):
        if entry.get("relevance") != "low":
            continue
        key = entry.get("url") or entry.get("title")
        if key:
            keys.add(key)
    return keys


def reset_rating_state() -> None:
    """Clear cached rating values so new articles start fresh."""
    prefixes = ("rating_value_", "reason_", "radio_")
    to_delete = [
        key for key in list(st.session_state.keys()) if any(key.startswith(prefix) for prefix in prefixes)
    ]
    for key in to_delete:
        del st.session_state[key]


def format_timestamp(raw: str | None) -> str:
    if not raw:
        return "-"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return raw
    if dt.tzinfo is None:
        dt = KST.localize(dt)
    else:
        dt = dt.astimezone(KST)
    return dt.strftime("%Y-%m-%d %H:%M KST")


def initialise_state() -> Tuple[Dict, Dict]:
    if "evaluations_payload" not in st.session_state:
        st.session_state["evaluations_payload"] = _load_evaluations()
    evaluations_payload = st.session_state["evaluations_payload"]
    if "news_payload" not in st.session_state:
        low_keys = extract_low_relevance_keys(evaluations_payload)
        st.session_state["news_payload"] = _load_news_payload(exclude_keys=low_keys)
    return st.session_state["news_payload"], st.session_state["evaluations_payload"]


def refresh_news(exclude_keys: Set[str] | None = None) -> None:
    with st.spinner("최신 뉴스를 불러오는 중..."):
        payload, removed_count = _collect_and_store_news(exclude_keys)
        st.session_state["news_payload"] = payload
        reset_rating_state()
    st.success("뉴스를 새로고침했습니다.")
    if exclude_keys and removed_count:
        st.info(f"관련성이 낮다고 평가된 {removed_count}건의 기사를 제외했습니다.")


def render_news_items(items: List[Dict], existing_map: Dict[str, Dict]) -> None:
    if not items:
        st.info("표시할 뉴스가 없습니다. 사이드바에서 새로고침을 눌러보세요.")
        return

    for index, item in enumerate(items):
        container = st.container()
        with container:
            st.subheader(item.get("title", "제목 없음"))
            meta_parts = [item.get("source", "출처 미상"), format_timestamp(item.get("published_at"))]
            st.caption(" · ".join(meta_parts))
            summary = item.get("summary", "요약이 제공되지 않았습니다.")
            st.write(summary)
            url = item.get("url")
            if url:
                st.markdown(f"[기사 열기]({url})")

            rating_key = f"rating_value_{index}"
            reason_key = f"reason_{index}"
            previous = existing_map.get(url or item.get("title", ""), {})
            default_value = previous.get("relevance", "")
            options = {
                "평가를 선택하세요": "",
                "관련성 높음": "high",
                "관련성 낮음": "low",
            }
            reverse_options = {v: k for k, v in options.items()}
            default_label = reverse_options.get(default_value, "평가를 선택하세요")
            rating_label = st.radio(
                "관련성 평가",
                list(options.keys()),
                index=list(options.keys()).index(default_label),
                key=f"radio_{index}",
            )
            rating_value = options[rating_label]
            st.session_state[rating_key] = rating_value

            if rating_value == "low":
                reason_default = previous.get("reason", "")
                st.text_area(
                    "관련성이 낮은 이유",
                    value=reason_default,
                    key=reason_key,
                    placeholder=LOW_RELEVANCE_REASON_PLACEHOLDER,
                )
            else:
                st.session_state[reason_key] = ""
        st.divider()


def collect_evaluation_entries(items: List[Dict]) -> Tuple[List[Dict], List[str]]:
    entries: List[Dict] = []
    missing_reasons: List[str] = []
    now = datetime.now(KST).isoformat()

    for index, item in enumerate(items):
        rating_value = st.session_state.get(f"rating_value_{index}", "")
        if not rating_value:
            continue
        reason = st.session_state.get(f"reason_{index}", "").strip()
        if rating_value == "low" and not reason:
            missing_reasons.append(item.get("title", f"항목 {index + 1}"))
        entry = {
            "title": item.get("title", "제목 없음"),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "summary": item.get("summary", ""),
            "relevance": rating_value,
            "reason": reason if rating_value == "low" else "",
            "evaluated_at": now,
        }
        entries.append(entry)
    return entries, missing_reasons


def merge_evaluations(existing: Dict[str, Dict], new_entries: List[Dict]) -> List[Dict]:
    merged = existing.copy()
    for entry in new_entries:
        key = entry.get("url") or entry.get("title")
        if key:
            merged[key] = entry
    return sorted(merged.values(), key=lambda item: item.get("evaluated_at", ""), reverse=True)


def render_saved_evaluations(evaluations: Dict) -> None:
    items = evaluations.get("items", [])
    if not items:
        return

    st.subheader("저장된 평가")
    df = pd.DataFrame(items)
    display_df = df[["title", "source", "relevance", "reason", "evaluated_at"]]
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "CSV로 다운로드",
        data=csv_data,
        file_name="tesla_news_evaluations.csv",
        mime="text/csv",
    )
    json_data = json.dumps(items, ensure_ascii=False, indent=2)
    st.download_button(
        "JSON으로 다운로드",
        data=json_data,
        file_name="tesla_news_evaluations.json",
        mime="application/json",
    )


def main() -> None:
    st.set_page_config(page_title="Tesla 뉴스 선별", layout="wide")
    news_payload, evaluations = initialise_state()

    st.title("Tesla 뉴스 선별 도구")
    st.caption("관련성 기준을 직접 설정하고 기사 선별 기준을 축적하세요.")

    with st.sidebar:
        st.header("데이터 관리")
        st.text(f"뉴스 갱신 시각: {format_timestamp(news_payload.get('updated_at'))}")
        if st.button("뉴스 새로고침", use_container_width=True):
            latest_evaluations = st.session_state.get("evaluations_payload", evaluations)
            low_relevance_keys = extract_low_relevance_keys(latest_evaluations)
            refresh_news(low_relevance_keys)
            news_payload = st.session_state["news_payload"]
        st.text(f"평가 갱신 시각: {format_timestamp(evaluations.get('updated_at'))}")

    items = news_payload.get("items", [])
    existing_map = {
        (entry.get("url") or entry.get("title")): entry
        for entry in evaluations.get("items", [])
    }

    render_news_items(items, existing_map)

    save_clicked = st.button("평가 저장", type="primary")
    if save_clicked:
        new_entries, missing_reasons = collect_evaluation_entries(items)
        if missing_reasons:
            st.warning(
                "관련성을 낮음으로 표시한 기사에는 반드시 이유를 입력해주세요: "
                + ", ".join(missing_reasons)
            )
            return
        if not new_entries:
            st.info("저장할 평가가 없습니다.")
            return
        merged_entries = merge_evaluations(existing_map, new_entries)
        st.session_state["evaluations_payload"] = _save_evaluations(merged_entries)
        st.success("평가를 저장했습니다.")
        render_saved_evaluations(st.session_state["evaluations_payload"])
    else:
        render_saved_evaluations(evaluations)


def _running_inside_streamlit() -> bool:
    """Return True when the script is executed via `streamlit run`."""

    try:
        return runtime.exists()
    except Exception:
        return False


if __name__ == "__main__":
    if _running_inside_streamlit():
        main()
    else:
        print("이 앱은 Streamlit 명령으로 실행해야 합니다.")
        print("streamlit run Tesla_news/streamlit_app.py")
