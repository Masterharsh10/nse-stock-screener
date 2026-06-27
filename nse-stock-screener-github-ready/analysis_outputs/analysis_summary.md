# NSE Quantamental Stock Screener — Results

**As of:** 2026-06-19  
**Universe:** Nifty 100 constituents (102 stocks)  
**Universe source:** https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv  
**Fundamentals/prices:** Yahoo Finance via `yfinance`

## Screening rules

| Rule | Threshold |
|---|---:|
| Positive trailing P/E | ≤ 30.0x |
| Trailing one-year return | ≥ 10.0% |
| Market capitalisation | ≥ ₹10,000 crore |

Stocks must pass all three rules. Missing values fail safely rather than being filled
with estimates.

## Result

- **96** of 102 stocks had all required fields.
- **18** stocks passed every filter.
- **6** industries produced at least one eligible champion.

The largest candidate group is **Financial Services** with **9 of 18** names (50%). This concentration is a screening result, not a diversification recommendation.

## Top-ranked candidates

| Rank | Symbol | NSE industry | P/E | 1Y return | Market cap | Score |
|---:|---|---|---:|---:|---:|---:|
| 1 | CANBK | Financial Services | 6.2x | 31.7% | ₹121,311 cr | 90.1 |
| 2 | UNIONBANK | Financial Services | 6.9x | 30.1% | ₹134,168 cr | 88.0 |
| 3 | SBIN | Financial Services | 11.4x | 34.2% | ₹955,461 cr | 87.9 |
| 4 | HINDALCO | Metals & Mining | 16.8x | 58.6% | ₹225,851 cr | 87.4 |
| 5 | COALINDIA | Oil Gas & Consumable Fuels | 8.9x | 25.7% | ₹278,124 cr | 83.8 |
| 6 | BANKBARODA | Financial Services | 7.3x | 25.2% | ₹145,341 cr | 83.5 |
| 7 | SHRIRAMFIN | Financial Services | 18.8x | 55.2% | ₹235,739 cr | 83.5 |
| 8 | JSWSTEEL | Metals & Mining | 14.1x | 29.6% | ₹314,305 cr | 83.2 |
| 9 | HINDZINC | Metals & Mining | 17.2x | 31.2% | ₹238,118 cr | 80.6 |
| 10 | PFC | Financial Services | 5.5x | 14.6% | ₹142,234 cr | 79.6 |

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
