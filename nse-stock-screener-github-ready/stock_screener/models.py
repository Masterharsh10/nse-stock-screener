"""Shared data structures for the screener."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ScreeningCriteria:
    """Visible, user-editable rules—no magic thresholds hidden in formulas."""

    max_pe: float = 30.0
    min_one_year_return: float = 0.10
    min_market_cap_crore: float = 10_000.0
    top_n: int = 15
    value_weight: float = 0.45
    momentum_weight: float = 0.55

    def __post_init__(self) -> None:
        if self.max_pe <= 0:
            raise ValueError("Maximum P/E must be positive.")
        if self.min_market_cap_crore < 0:
            raise ValueError("Minimum market cap cannot be negative.")
        if self.top_n < 1:
            raise ValueError("Top N must be at least 1.")
        if abs(self.value_weight + self.momentum_weight - 1.0) > 1e-9:
            raise ValueError("Value and momentum weights must add to 1.0.")


@dataclass(frozen=True)
class ScreenResult:
    criteria: ScreeningCriteria
    all_stocks: pd.DataFrame
    candidates: pd.DataFrame
    sector_champions: pd.DataFrame
    excluded: pd.DataFrame
    complete_count: int
    as_of_date: str
    universe_source: str

