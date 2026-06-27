"""Save auditable CSV outputs and generate the screening report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import ScreenResult

OUTPUT_COLUMNS = [
    "Overall Rank", "Symbol", "Company Name", "Industry", "Trailing PE", "1Y Return",
    "Market Cap (INR Crore)", "Annualised Volatility", "Maximum Drawdown",
    "Value Score", "Momentum Score", "Composite Score", "Momentum Efficiency",
    "Industry Rank", "Selection Tier",
]


def save_tables(result: ScreenResult, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    result.all_stocks.to_csv(data_dir / "all_stocks.csv", index=False)
    candidate_columns = [column for column in OUTPUT_COLUMNS if column in result.candidates.columns]
    result.candidates[candidate_columns].to_csv(data_dir / "ranked_candidates.csv", index=False)
    result.sector_champions[candidate_columns].to_csv(
        data_dir / "sector_champions.csv", index=False
    )
    excluded_columns = [
        "Symbol", "Company Name", "Industry", "Trailing PE", "1Y Return",
        "Market Cap (INR Crore)", "Screen Result", "Price Error", "Fundamental Error",
    ]
    excluded_columns = [column for column in excluded_columns if column in result.excluded.columns]
    result.excluded[excluded_columns].to_csv(data_dir / "excluded_stocks.csv", index=False)

    quality = pd.DataFrame(
        [
            {"Measure": "Universe size", "Value": len(result.all_stocks)},
            {"Measure": "Complete required fields", "Value": result.complete_count},
            {"Measure": "Passed all filters", "Value": len(result.candidates)},
            {
                "Measure": "Missing trailing P/E",
                "Value": int(result.all_stocks["Trailing PE"].isna().sum()),
            },
            {
                "Measure": "Missing one-year return",
                "Value": int(result.all_stocks["1Y Return"].isna().sum()),
            },
            {
                "Measure": "Missing market cap",
                "Value": int(result.all_stocks["Market Cap (INR Crore)"].isna().sum()),
            },
        ]
    )
    quality.to_csv(data_dir / "data_quality.csv", index=False)


def _candidate_table(result: ScreenResult) -> str:
    rows = []
    for _, row in result.candidates.head(10).iterrows():
        rows.append(
            f"| {int(row['Overall Rank'])} | {row['Symbol']} | {row['Industry']} | "
            f"{row['Trailing PE']:.1f}x | {row['1Y Return']:.1%} | "
            f"₹{row['Market Cap (INR Crore)']:,.0f} cr | {row['Composite Score']:.1f} |"
        )
    return "\n".join(rows) if rows else "| — | No stocks passed | — | — | — | — | — |"


def write_report(result: ScreenResult, output_dir: Path) -> Path:
    c = result.criteria
    path = output_dir / "analysis_summary.md"
    if result.candidates.empty:
        concentration_note = "No industry concentration is available because no stock passed."
    else:
        industry_counts = result.candidates["Industry"].value_counts()
        dominant_industry = industry_counts.index[0]
        dominant_count = int(industry_counts.iloc[0])
        dominant_share = dominant_count / len(result.candidates)
        concentration_note = (
            f"The largest candidate group is **{dominant_industry}** with "
            f"**{dominant_count} of {len(result.candidates)}** names ({dominant_share:.0%}). "
            "This concentration is a screening result, not a diversification recommendation."
        )
    text = f"""# NSE Quantamental Stock Screener — Results

**As of:** {result.as_of_date}  
**Universe:** Nifty 100 constituents ({len(result.all_stocks)} stocks)  
**Universe source:** {result.universe_source}  
**Fundamentals/prices:** Yahoo Finance via `yfinance`

## Screening rules

| Rule | Threshold |
|---|---:|
| Positive trailing P/E | ≤ {c.max_pe:.1f}x |
| Trailing one-year return | ≥ {c.min_one_year_return:.1%} |
| Market capitalisation | ≥ ₹{c.min_market_cap_crore:,.0f} crore |

Stocks must pass all three rules. Missing values fail safely rather than being filled
with estimates.

## Result

- **{result.complete_count}** of {len(result.all_stocks)} stocks had all required fields.
- **{len(result.candidates)}** stocks passed every filter.
- **{len(result.sector_champions)}** industries produced at least one eligible champion.

{concentration_note}

## Top-ranked candidates

| Rank | Symbol | NSE industry | P/E | 1Y return | Market cap | Score |
|---:|---|---|---:|---:|---:|---:|
{_candidate_table(result)}

## Ranking method

Filtering answers **which stocks qualify**. Ranking answers **which qualifying stocks
look strongest relative to this universe**.

- Value Score is the percentile rank of trailing P/E; lower positive P/E scores higher.
- Momentum Score is the percentile rank of trailing one-year return; higher scores higher.
- Composite Score = `45% × Value Score + 55% × Momentum Score`.
- Market capitalisation is an eligibility/liquidity filter, not a ranking reward.
- Industry Rank reduces the temptation to compare only the overall list and highlights
  the best eligible company within each NSE industry.

## Why this is a screener, not a recommendation engine

P/E can be distorted by cyclical earnings, one-off items, accounting differences, and
sector economics. Past return is not a forecast. The model does not inspect leverage,
cash flow quality, governance, future earnings, or valuation relative to growth. A
candidate is a prompt for deeper research—not an automatic buy.

## Data limitations

- Nifty 100 is a liquid large/mid-cap universe, not every NSE-listed security.
- Yahoo Finance is convenient but not an exchange-grade feed; fields can be delayed or
  missing.
- Trailing P/E uses historical earnings and may be unavailable for loss-making companies.
- A one-year momentum window is sensitive to the chosen start/end date.
- Percentile scores change when the universe or data date changes.
- P/E comparisons are more meaningful within similar industries than across all sectors.

> Educational analysis only. This is not investment advice.
"""
    path.write_text(text, encoding="utf-8")
    return path
