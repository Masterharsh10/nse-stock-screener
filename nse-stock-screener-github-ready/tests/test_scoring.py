from __future__ import annotations

import pandas as pd
import pytest

from stock_screener.models import ScreeningCriteria
from stock_screener.scoring import screen_and_rank


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Symbol": ["CHEAP", "FAST", "EXPENSIVE", "LOSS", "MISSING"],
            "Company Name": ["Cheap Ltd", "Fast Ltd", "Expensive Ltd", "Loss Ltd", "Missing Ltd"],
            "Industry": ["Banks", "IT", "IT", "Energy", "Banks"],
            "Trailing PE": [10.0, 20.0, 45.0, -3.0, None],
            "1Y Return": [0.15, 0.40, 0.25, 0.50, 0.30],
            "Market Cap (INR Crore)": [50_000, 25_000, 30_000, 20_000, 40_000],
            "Annualised Volatility": [0.20, 0.30, 0.25, 0.40, 0.30],
        }
    )


def test_filters_require_all_three_rules() -> None:
    _, candidates, _, excluded = screen_and_rank(sample_frame(), ScreeningCriteria())
    assert candidates["Symbol"].tolist() == ["FAST", "CHEAP"]
    assert set(excluded["Symbol"]) == {"EXPENSIVE", "LOSS", "MISSING"}


def test_lower_pe_receives_higher_value_score() -> None:
    all_stocks, _, _, _ = screen_and_rank(sample_frame(), ScreeningCriteria())
    scores = all_stocks.set_index("Symbol")["Value Score"]
    assert scores["CHEAP"] > scores["FAST"] > scores["EXPENSIVE"]


def test_higher_return_receives_higher_momentum_score() -> None:
    all_stocks, _, _, _ = screen_and_rank(sample_frame(), ScreeningCriteria())
    scores = all_stocks.set_index("Symbol")["Momentum Score"]
    assert scores["FAST"] > scores["EXPENSIVE"] > scores["CHEAP"]


def test_missing_pe_fails_safely() -> None:
    all_stocks, _, _, _ = screen_and_rank(sample_frame(), ScreeningCriteria())
    missing = all_stocks.set_index("Symbol").loc["MISSING"]
    assert not missing["Passed"]
    assert "Missing trailing P/E" in missing["Screen Result"]


def test_weights_must_add_to_one() -> None:
    with pytest.raises(ValueError, match="add to 1.0"):
        ScreeningCriteria(value_weight=0.7, momentum_weight=0.7)

