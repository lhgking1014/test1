"""Streamlit 세션 상태 유틸리티."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .question_bank import Question


@dataclass
class QuestionResult:
    """한 문제에 대한 결과."""

    question: Question
    selected_index: Optional[int] = None
    correct: Optional[bool] = None


@dataclass
class GameState:
    """세션 동안 유지될 상태."""

    question_set: List[Question] = field(default_factory=list)
    current_index: int = 0
    score: int = 0
    history: List[QuestionResult] = field(default_factory=list)
    pending_result: Optional[QuestionResult] = None

    def reset(self) -> None:
        """세션을 초기화."""
        self.question_set.clear()
        self.current_index = 0
        self.score = 0
        self.history.clear()
        self.pending_result = None

    def current_question(self) -> Optional[Question]:
        if 0 <= self.current_index < len(self.question_set):
            return self.question_set[self.current_index]
        return None

    def record_answer(self, selected_index: int, correct: bool) -> None:
        question = self.current_question()
        if question is None:
            return

        result = QuestionResult(
            question=question,
            selected_index=selected_index,
            correct=correct,
        )
        if correct:
            self.score += 1
        self.pending_result = result

    def advance(self) -> None:
        """다음 문제로 이동."""
        if self.pending_result is not None:
            self.history.append(self.pending_result)
            self.pending_result = None
        self.current_index += 1
