"""Beginner-friendly command-line entry point for the NSE stock screener."""

from __future__ import annotations

import argparse
from pathlib import Path

from stock_screener.models import ScreeningCriteria
from stock_screener.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Screen a liquid NSE universe using value, momentum, and size criteria."
    )
    parser.add_argument("--max-pe", type=float, default=30.0, help="Maximum trailing P/E.")
    parser.add_argument(
        "--min-return",
        type=float,
        default=10.0,
        help="Minimum one-year return in percent (default: 10).",
    )
    parser.add_argument(
        "--min-market-cap-crore",
        type=float,
        default=10_000.0,
        help="Minimum market capitalisation in INR crore (default: 10000).",
    )
    parser.add_argument("--top", type=int, default=15, help="Candidates shown in charts/report.")
    parser.add_argument(
        "--universe-file",
        type=Path,
        help="Optional NSE-style CSV containing Company Name, Industry, and Symbol.",
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        help="Rerank a saved all_stocks.csv without downloading live data.",
    )
    parser.add_argument(
        "--refresh-universe",
        action="store_true",
        help="Request the latest Nifty 100 constituents from Nifty Indices.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Yahoo fundamental workers (default: 1 for reliability; maximum: 4).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "analysis_outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    criteria = ScreeningCriteria(
        max_pe=args.max_pe,
        min_one_year_return=args.min_return / 100,
        min_market_cap_crore=args.min_market_cap_crore,
        top_n=args.top,
    )
    result = run_pipeline(
        criteria=criteria,
        output_dir=args.output_dir,
        universe_file=args.universe_file,
        input_csv=args.input_csv,
        refresh_universe=args.refresh_universe,
        workers=args.workers,
    )

    print("\nScreen complete.")
    print(f"Universe       : {len(result.all_stocks)} stocks")
    print(f"Complete data  : {result.complete_count} stocks")
    print(f"Passed filters : {len(result.candidates)} stocks")
    if not result.candidates.empty:
        leader = result.candidates.iloc[0]
        print(
            f"Top candidate  : {leader['Symbol']} — score {leader['Composite Score']:.1f}/100"
        )
    print(f"Open report    : {args.output_dir.resolve() / 'analysis_summary.md'}")


if __name__ == "__main__":
    main()
