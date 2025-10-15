"""Question and choice generation logic for the car quiz."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .parser import CarMeta

ChoiceList = List[CarMeta]


@dataclass
class Question:
    """Data structure passed to the UI layer."""

    car: CarMeta
    choices: ChoiceList

    @property
    def correct_index(self) -> int:
        for idx, choice in enumerate(self.choices):
            if choice.id == self.car.id:
                return idx
        raise ValueError("Correct answer missing from choices.")


class QuestionGenerator:
    """Generate quiz questions from the car dataset."""

    def __init__(self, cars: Sequence[CarMeta]):
        if len(cars) < 10:
            raise ValueError("At least 10 images are required.")

        # Deduplicate by make-model-year label to avoid repeated questions.
        unique_by_label: Dict[str, CarMeta] = {}
        for car in cars:
            unique_by_label.setdefault(car.display_label, car)
        self.cars: List[CarMeta] = list(unique_by_label.values())

        if len(self.cars) < 10:
            raise ValueError("Not enough unique vehicles after filtering.")

        self.by_make: dict[str, List[CarMeta]] = {}
        self.by_model: dict[Tuple[str, str], List[CarMeta]] = {}

        for car in self.cars:
            self.by_make.setdefault(car.make, []).append(car)
            self.by_model.setdefault((car.make, car.model), []).append(car)

    def make_session_questions(
        self, count: int = 10, choice_count: int = 10
    ) -> List[Question]:
        """Create the full set of questions for a session."""

        pool = list(self.cars)
        random.shuffle(pool)

        questions: List[Question] = []
        used_labels: Set[str] = set()
        attempted = 0
        max_attempts = len(pool) * 3

        while len(questions) < min(count, len(self.cars)) and attempted < max_attempts:
            attempted += 1
            candidate = random.choice(pool)
            if candidate.display_label in used_labels:
                continue

            try:
                question = self.make_question(candidate, choice_count=choice_count)
            except ValueError:
                continue

            questions.append(question)
            used_labels.add(candidate.display_label)

        if len(questions) < count:
            raise ValueError(
                "충분한 문제를 생성하지 못했습니다. 사용 가능한 이미지 수가 부족할 수 있습니다."
            )

        return questions

    def make_question(self, answer_car: CarMeta, choice_count: int = 10) -> Question:
        """Create a single multiple-choice question."""

        if choice_count < 2:
            raise ValueError("choice_count must be at least 2.")

        answer_key = (answer_car.make, answer_car.model)

        same_model_all = [
            car for car in self.by_model.get(answer_key, []) if car.id != answer_car.id
        ]
        same_model = self._limit_year_variation(same_model_all, answer_car.year)
        same_make = [
            car
            for car in self.by_make.get(answer_car.make, [])
            if car.id != answer_car.id and car.model != answer_car.model
        ]
        others = [car for car in self.cars if car.make != answer_car.make]

        selections: List[CarMeta] = []
        used_ids: Set[str] = {answer_car.id}
        used_labels: Set[str] = {answer_car.display_label}

        quotas = (
            (same_model, 3),
            (same_make, 3),
            (others, choice_count),
        )

        for candidate_pool, quota in quotas:
            self._extend_with_pool(
                selections, candidate_pool, quota, used_ids, used_labels
            )
            if len(selections) >= choice_count - 1:
                break

        if len(selections) < choice_count - 1:
            self._extend_with_pool(
                selections, self.cars, choice_count - 1, used_ids, used_labels
            )

        if len(selections) < choice_count - 1:
            raise ValueError("Not enough distractors available.")

        options = selections[: choice_count - 1]
        options.append(answer_car)
        random.shuffle(options)

        return Question(car=answer_car, choices=options)

    @staticmethod
    def _extend_with_pool(
        target: List[CarMeta],
        pool: Iterable[CarMeta],
        quota: int,
        used_ids: Set[str],
        used_labels: Set[str],
    ) -> None:
        """Append unique options to the target list without exceeding quota."""

        if quota <= 0:
            return

        candidates = [car for car in pool if car.id not in used_ids]
        random.shuffle(candidates)

        added = 0
        for car in candidates:
            label = car.display_label
            if label in used_labels:
                continue
            target.append(car)
            used_ids.add(car.id)
            used_labels.add(label)
            added += 1
            if added >= quota:
                break

    @staticmethod
    def _limit_year_variation(
        cars: Iterable[CarMeta], answer_year: int
    ) -> List[CarMeta]:
        """Allow at most one distinct alternative year for the same model."""

        groups: Dict[int, List[CarMeta]] = {}
        for car in cars:
            if car.year == answer_year:
                continue
            groups.setdefault(car.year, []).append(car)

        if not groups:
            return []

        years = list(groups.keys())
        random.shuffle(years)
        selected_years = years[:1]

        return [random.choice(groups[year]) for year in selected_years]

