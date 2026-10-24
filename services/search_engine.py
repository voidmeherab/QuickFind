"""
QuickFind Search Engine
Implements multi-tiered fuzzy search, prefix matching, acronym matching,
and recency/frequency score weighting.
"""

import re
import time
from typing import List, Dict, Tuple, Optional
from services.app_scanner import AppEntry, AppScanner
from storage.history_db import HistoryDB


class SearchResult:
    """Represents a scored matching application."""

    def __init__(self, app: AppEntry, score: float, match_indices: Optional[List[int]] = None):
        self.app = app
        self.score = score
        self.match_indices = match_indices or []

    def __repr__(self):
        return f"<SearchResult '{self.app.name}' score={self.score:.1f}>"


class SearchEngine:
    """Fast in-memory search index and ranking engine."""

    def __init__(self, history_db: Optional[HistoryDB] = None):
        self.history_db = history_db or HistoryDB()
        self._apps: List[AppEntry] = []
        self._history_stats: Dict[str, Tuple[int, float]] = {}
        self.refresh_stats()

    def set_apps(self, apps: List[AppEntry]) -> None:
        """Update the in-memory application index."""
        self._apps = list(apps)

    def get_apps(self) -> List[AppEntry]:
        """Return the current list of indexed applications."""
        return self._apps

    def refresh_stats(self) -> None:
        """Reload launch counts and timestamps from the history database."""
        self._history_stats = self.history_db.get_all_stats()

    def search(self, query: str, max_results: int = 6, prioritize_recent: bool = True) -> List[SearchResult]:
        """
        Search for applications matching the query string.
        Returns top results sorted by score descending.
        """
        query_clean = query.strip().lower()
        if not query_clean:
            # If query is empty, return top frequently/recently launched apps
            return self._get_default_suggestions(max_results, prioritize_recent)

        results: List[SearchResult] = []

        for app in self._apps:
            base_score = self._compute_match_score(query_clean, app.name.lower())

            # If no match on name, try matching on executable filename
            if base_score <= 0 and app.target_path:
                exe_name = app.target_path.split("\\")[-1].lower()
                base_score = self._compute_match_score(query_clean, exe_name) * 0.75

            if base_score > 0:
                # Add recency/frequency bonus
                bonus = 0.0
                if prioritize_recent and app.id in self._history_stats:
                    count, last_time = self._history_stats[app.id]
                    # Frequency bonus: up to 100 points
                    freq_bonus = min(100.0, count * 15.0)
                    # Recency bonus: if launched within last 7 days, up to 50 points
                    days_ago = (time.time() - last_time) / 86400.0
                    recency_bonus = max(0.0, 50.0 - (days_ago * 7.0))
                    bonus = freq_bonus + recency_bonus

                total_score = base_score + bonus
                results.append(SearchResult(app=app, score=total_score))

        # Sort descending by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]

    def _compute_match_score(self, query: str, target: str) -> float:
        """
        Compute matching score between query and target name.
        Tier 1: Exact match -> 1000
        Tier 2: Prefix match -> 900
        Tier 3: Acronym match -> 850
        Tier 4: Word-boundary prefix match -> 800
        Tier 5: Substring match -> 600
        Tier 6: Fuzzy subsequence match -> 300 - 500
        """
        if not target:
            return 0.0

        # Tier 1: Exact Match
        if query == target:
            return 1000.0

        # Tier 2: Prefix Match
        if target.startswith(query):
            # Shorter names get a slight density bonus
            density = len(query) / len(target)
            return 900.0 + (density * 50.0)

        # Tier 3: Acronym / Initials Match (e.g. "vs" for "Visual Studio")
        words = re.findall(r"\b[a-zA-Z0-9]", target)
        acronym = "".join(words).lower()
        if acronym == query:
            return 850.0
        if acronym.startswith(query):
            return 820.0

        # Tier 4: Word Boundary Prefix Match (e.g. "code" for "Visual Studio Code")
        target_words = re.split(r"[\s\-_]+", target)
        for i, word in enumerate(target_words):
            if word.startswith(query):
                # Earlier word position gets higher score
                position_penalty = i * 15.0
                density = len(query) / len(word)
                return max(700.0, 800.0 - position_penalty + (density * 30.0))

        # Tier 5: Substring Match
        sub_idx = target.find(query)
        if sub_idx != -1:
            position_penalty = sub_idx * 5.0
            density = len(query) / len(target)
            return max(500.0, 600.0 - position_penalty + (density * 40.0))

        # Tier 6: Subsequence / Fuzzy Match
        return self._fuzzy_subsequence_score(query, target)

    def _fuzzy_subsequence_score(self, query: str, target: str) -> float:
        """Fuzzy character matching preserving sequential order."""
        qi = 0
        score = 0.0
        consecutive = 0
        last_match_idx = -1

        for ti, char in enumerate(target):
            if qi < len(query) and char == query[qi]:
                qi += 1
                if last_match_idx == ti - 1:
                    consecutive += 1
                else:
                    consecutive = 0
                score += 20.0 + (consecutive * 10.0)
                last_match_idx = ti

        if qi == len(query):
            # All query characters matched in sequence
            coverage = len(query) / len(target)
            return min(480.0, 300.0 + score + (coverage * 50.0))

        return 0.0

    def _get_default_suggestions(self, max_results: int, prioritize_recent: bool) -> List[SearchResult]:
        """Return default top applications when query is empty."""
        results: List[SearchResult] = []
        for app in self._apps:
            score = 10.0
            if prioritize_recent and app.id in self._history_stats:
                count, last_time = self._history_stats[app.id]
                score += (count * 20.0)
                days_ago = (time.time() - last_time) / 86400.0
                score += max(0.0, 50.0 - (days_ago * 5.0))
            results.append(SearchResult(app=app, score=score))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]
