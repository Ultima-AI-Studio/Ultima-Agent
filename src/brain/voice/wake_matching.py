"""Unicode-aware fuzzy wake phrase matching for the Windows voice chain.

Adapted from ``AdelElo13/DockWright-MacOS-Agent``
``Dockwright/Core/Voice/WakeWordDetector.swift`` at commit
``d6d3f3f71fc83afc9df3f74f9376413084777b90``.
MIT License, Copyright (c) 2026 Adel Elo.
See ``docs/research/sources/dockwright/LICENSE``.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def levenshtein_distance(left: str, right: str) -> int:
    """Return edit distance using one row of dynamic-programming storage."""
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def levenshtein_ratio(left: str, right: str) -> float:
    left_normalized = _normalize(left)
    right_normalized = _normalize(right)
    longest = max(len(left_normalized), len(right_normalized))
    if longest == 0:
        return 0.0
    return levenshtein_distance(left_normalized, right_normalized) / longest


class WakePhraseMatcher:
    def __init__(self, targets: Iterable[str], *, threshold: float = 0.35) -> None:
        if not 0.0 < threshold < 1.0:
            raise ValueError("threshold must be between 0 and 1")
        normalized = tuple(dict.fromkeys(_normalize(target) for target in targets if target.strip()))
        if not normalized:
            raise ValueError("at least one wake target is required")
        self.targets = normalized
        self.threshold = threshold

    @classmethod
    def from_keyword_lines(
        cls,
        lines: Iterable[str],
        *,
        threshold: float = 0.35,
    ) -> "WakePhraseMatcher":
        labels = []
        for line in lines:
            _, marker, label = line.partition("@")
            candidate = label if marker else line
            if candidate.strip():
                labels.append(candidate.strip())
        return cls(labels, threshold=threshold)

    def matches(self, transcription: str) -> bool:
        normalized = _normalize(transcription)
        for target in self.targets:
            if target in normalized:
                return True
            words = normalized.split()
            target_word_count = len(target.split())
            if len(words) < target_word_count:
                candidates = (normalized,)
            else:
                candidates = (
                    " ".join(words[start : start + target_word_count])
                    for start in range(len(words) - target_word_count + 1)
                )
            if any(levenshtein_ratio(candidate, target) < self.threshold for candidate in candidates):
                return True
        return False


__all__ = ["WakePhraseMatcher", "levenshtein_distance", "levenshtein_ratio"]
