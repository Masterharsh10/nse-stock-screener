"""Apply value/momentum filters and build transparent percentile rankings."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .models import ScreeningCriteria

REQUIRED_METRICS = ["Trailing PE", "1Y Return", "Market Cap (INR Crore)"]


def _reason(row: pd.Series, criteria: ScreeningCriteria) -> str:
    reasons: list[str] = []
    pe = row["Trailing PE"]
    one_year_return = row["1Y Return"]
    market_cap = row["Market Cap (INR Crore)"]

    if pd.isna(pe):
        reasons.append("Missing trailing P/E")
    elif pe <= 0:
        reasons.append("Non-positive trailing P/E")
    elif pe > criteria.max_pe:
        reasons.append(f"P/E above {criteria.max_pe:g}")

    if pd.isna(one_year_return):
        reasons.append("Missing 1Y return")
    elif one_year_return < criteria.min_one_year_return:
        reasons.append(f"1Y return below {criteria.min_one_year_return:.0%}")

    if pd.isna(market_cap):
        reasons.append("Missing market cap")
    elif market_cap < criteria.min_market_cap_crore:
        reasons.append(f"Market cap below INR {criteria.min_market_cap_crore:,.0f} crore")
    return "; ".join(reasons) if reasons else "Passed all filters"


def screen_and_rank(
    frame: pd.DataFrame, criteria: ScreeningCriteria
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return scored universe, candidates, sector champions, and excluded stocks."""
    missing_columns = [column for column in REQUIRED_METRICS if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Input data is missing: {', '.join(missing_columns)}")

    scored = frame.copy()
    for column in REQUIRED_METRICS:
        scored[column] = pd.to_numeric(scored[column], errors="coerce")

    complete = scored[REQUIRED_METRICS].notna().all(axis=1) & (scored["Trailing PE"] > 0)
    scored["Data Complete"] = complete
    scored["Value Score"] = np.nan
    scored["Momentum Score"] = np.nan

    scored.loc[complete, "Value Score"] = (
        scored.loc[complete, "Trailing PE"].rank(method="average", ascending=False, pct=True)
        * 100
    )
    scored.loc[complete, "Momentum Score"] = (
        scored.loc[complete, "1Y Return"].rank(method="average", ascending=True, pct=True)
        * 100
    )
    scored["Value Contribution"] = scored["Value Score"] * criteria.value_weight
    scored["Momentum Contribution"] = (
        scored["Momentum Score"] * criteria.momentum_weight
    )
    scored["Composite Score"] = (
        scored["Value Contribution"] + scored["Momentum Contribution"]
    )
    scored["Momentum Efficiency"] = scored["1Y Return"] / scored["Annualised Volatility"]

    scored["Screen Result"] = scored.apply(_reason, axis=1, criteria=criteria)
    scored["Passed"] = scored["Screen Result"].eq("Passed all filters")

    candidates = scored.loc[scored["Passed"]].copy()
    candidates = candidates.sort_values(
        ["Composite Score", "1Y Return"], ascending=[False, False]
    ).reset_index(drop=True)
    candidates["Overall Rank"] = np.arange(1, len(candidates) + 1)
    candidates["Industry Rank"] = (
        candidates.groupby("Industry")["Composite Score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    candidates["Selection Tier"] = pd.cut(
        candidates["Composite Score"],
        bins=[-np.inf, 50, 75, np.inf],
        labels=["Eligible", "Strong", "Top Quartile"],
    ).astype(str)

    sector_champions = candidates.loc[candidates["Industry Rank"] == 1].copy()
    sector_champions = sector_champions.sort_values("Composite Score", ascending=False)
    excluded = scored.loc[~scored["Passed"]].copy()
    excluded = excluded.sort_values(["Data Complete", "Composite Score"], ascending=False)
    return scored, candidates, sector_champions, excluded

