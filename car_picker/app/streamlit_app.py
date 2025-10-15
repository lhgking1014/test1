"""Streamlit application entry point for the car quiz."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(ROOT))
    from app.game_state import GameState  # type: ignore  # noqa: E402
    from app.parser import CarMeta  # type: ignore  # noqa: E402
    from app.question_bank import QuestionGenerator  # type: ignore  # noqa: E402
    from app.store import CarIndex, load_index  # type: ignore  # noqa: E402
else:  # pragma: no cover
    from .game_state import GameState
    from .parser import CarMeta
    from .question_bank import QuestionGenerator
    from .store import CarIndex, load_index

INDEX_PATH = ROOT / "index.json"

ACCENT = "#B9985A"
ACCENT_DARK = "#8C6E3B"
BG_PRIMARY = "#0C0D0F"
BG_SECONDARY = "#16181D"
TEXT_PRIMARY = "#F7F6F3"
TEXT_SECONDARY = "#BFC4CD"


def inject_styles() -> None:
    """Apply Genesis-inspired luxury styling."""

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap');

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
            background-color: {BG_PRIMARY} !important;
            color: {TEXT_PRIMARY};
            font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #111217 0%, #0B0C0F 100%);
            border-right: 1px solid #1F2126;
        }}

        h1, h2, h3, h4 {{
            color: {TEXT_PRIMARY};
            letter-spacing: 0.02em;
        }}

        .quiz-header {{
            padding: 24px 28px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(15,16,20,0.95) 0%, rgba(24,26,32,0.85) 100%);
            border: 1px solid #1F2126;
            margin-bottom: 24px;
        }}

        .progress-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 16px;
            border-radius: 999px;
            background: rgba(191, 196, 205, 0.12);
            color: {TEXT_SECONDARY};
            font-size: 0.9rem;
        }}

        .score-card {{
            padding: 16px 20px;
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(19,21,26,0.9) 0%, rgba(12,13,15,0.9) 100%);
            border: 1px solid rgba(191, 196, 205, 0.14);
            margin-bottom: 16px;
        }}

        .score-card strong {{
            color: {ACCENT};
            font-size: 1.2rem;
        }}

        .stButton>button {{
            width: 100%;
            padding: 14px 18px;
            border-radius: 14px;
            border: 1px solid rgba(191,196,205,0.22);
            background: linear-gradient(135deg, rgba(24,26,32,0.95), rgba(14,15,18,0.95));
            color: {TEXT_PRIMARY};
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .stButton>button:hover {{
            border-color: {ACCENT};
            color: {ACCENT};
            background: linear-gradient(135deg, rgba(24,26,32,1), rgba(20,22,28,1));
        }}

        .stButton>button:disabled {{
            border-color: rgba(191,196,205,0.08);
            color: rgba(191,196,205,0.45);
            background: rgba(18,20,25,0.65);
            opacity: 1.0;
        }}

        .feedback-success {{
            background: rgba(185, 152, 90, 0.15);
            border-left: 4px solid {ACCENT};
            padding: 12px 18px;
            border-radius: 12px;
            color: {ACCENT};
            margin-top: 18px;
        }}

        .feedback-error {{
            background: rgba(189, 74, 74, 0.12);
            border-left: 4px solid #C25555;
            padding: 12px 18px;
            border-radius: 12px;
            color: #E07B7B;
            margin-top: 18px;
        }}

        .summary-card {{
            padding: 22px 24px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(19,21,26,0.95) 0%, rgba(13,14,17,0.95) 100%);
            border: 1px solid rgba(191, 196, 205, 0.18);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def load_data() -> CarIndex:
    """Load index.json and cache it."""

    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            "index.json을 찾을 수 없습니다. scripts/build_index.py를 먼저 실행하세요."
        )
    return load_index(INDEX_PATH)


def init_state() -> GameState:
    """Initialise or return the current game state."""

    if "game_state" not in st.session_state:
        st.session_state.game_state = GameState()
    return st.session_state.game_state


def ensure_question_set(state: GameState, generator: QuestionGenerator) -> None:
    """Ensure the session has a full question set."""

    if state.question_set:
        return

    questions = generator.make_session_questions(count=10, choice_count=10)
    state.question_set.extend(questions)


def get_image_path(car: CarMeta) -> Path:
    """Prefer the generated thumbnail if present."""

    if car.thumb_path and car.thumb_path.exists():
        return car.thumb_path
    return car.path


def render_question(state: GameState) -> None:
    """Render the active quiz question."""

    question = state.current_question()
    if question is None:
        return

    current_number = state.current_index + 1
    total_questions = len(state.question_set)

    image_path = get_image_path(question.car)
    image_col, content_col = st.columns([1.6, 1], gap="large")

    with image_col:
        st.markdown(
            f"""
            <div class="score-card" style="margin-bottom:18px;">
                <div class="progress-pill">문제 {current_number} / {total_questions}</div>
                <div style="margin-top:12px; font-size:0.95rem; color:{TEXT_SECONDARY};">
                    제조사 · 모델 · 연식을 모두 맞춰보세요.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.image(str(image_path), caption=None, width=720)

    with content_col:
        st.markdown(
            """
            <div style="font-size:1.2rem; font-weight:600; margin-bottom:14px; color:#f2f2f2;">
                정답을 골라주세요 (보기 10개)
            </div>
            """,
            unsafe_allow_html=True,
        )

        result = state.pending_result
        buttons_disabled = result is not None
        choice_columns = st.columns(2, gap="small")

        for idx, choice in enumerate(question.choices):
            column = choice_columns[idx % 2]
            label = choice.display_label
            key = f"{question.car.id}_choice_{idx}"
            with column:
                if st.button(label, key=key, disabled=buttons_disabled):
                    if result is None:
                        state.record_answer(idx, idx == question.correct_index)
                        st.rerun()

        result = state.pending_result
        if result is not None:
            correct_idx = question.correct_index
            correct_label = question.choices[correct_idx].display_label
            if result.correct:
                st.markdown(
                    f'<div class="feedback-success">정답입니다! ({correct_label})</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="feedback-error">틀렸습니다. 정답: {correct_label}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("다음 문제로", key=f"next_{question.car.id}"):
                state.advance()
                st.rerun()


def render_summary(state: GameState) -> None:
    """Render end-of-session summary."""

    total_questions = len(state.question_set)
    st.markdown(
        f"""
        <div class="summary-card">
            <h2 style="margin-top:0;">세션 완료</h2>
            <p style="font-size:1.05rem; color:{TEXT_SECONDARY}; margin-bottom:12px;">
                최종 점수는 <strong style="color:{ACCENT}; font-size:1.3rem;">{state.score} / {total_questions}</strong> 입니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if state.history:
        with st.expander("문항별 결과 보기"):
            for idx, result in enumerate(state.history, start=1):
                question = result.question
                status = "✅" if result.correct else "❌"
                st.write(f"{status} 문제 {idx}: {question.car.display_label}")
                if not result.correct and result.selected_index is not None:
                    chosen = question.choices[result.selected_index].display_label
                    st.write(f"- 선택: {chosen}")

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    if st.button("새 세션 시작"):
        state.reset()
        stale_keys: List[str] = [
            key
            for key in st.session_state
            if key.startswith(("question_", "ui_", "next_"))
        ]
        for key in stale_keys:
            del st.session_state[key]
        st.rerun()


def render_header(state: GameState) -> None:
    """Render the top status header."""

    remaining = len(state.question_set) - state.current_index
    st.markdown(
        f"""
        <div class="quiz-header">
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:2rem; font-weight:700; color:{TEXT_PRIMARY}; letter-spacing:0.04em;">
                        Whar car is it?
                    </div>
                    <div class="progress-pill">
                        남은 문제 {remaining:02d} · 현재 점수 {state.score:02d}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application entry point."""

    st.set_page_config(page_title="자동차 퀴즈", layout="wide")
    inject_styles()

    try:
        index = load_data()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    state = init_state()

    try:
        generator = QuestionGenerator(index.cars)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    ensure_question_set(state, generator)
    render_header(state)

    if state.current_index >= len(state.question_set):
        render_summary(state)
    else:
        render_question(state)


if __name__ == "__main__":
    main()
