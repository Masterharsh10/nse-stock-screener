"""Orchestrate universe loading, data collection, screening, and reporting."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .market_data import collect_stock_data
from .models import ScreenResult, ScreeningCriteria
from .report import save_tables, write_report
from .scoring import screen_and_rank
from .universe import load_universe
from .visuals import create_all_charts


def run_pipeline(
    criteria: ScreeningCriteria,
    output_dir: Path | str,
    universe_file: Path | None = None,
    input_csv: Path | None = None,
    refresh_universe: bool = False,
    workers: int = 1,
) -> ScreenResult:
    project_root = Path(__file__).resolve().parents[1]
    output_dir = Path(output_dir)
    data_dir = output_dir / "data"
    chart_dir = output_dir / "charts"

    if input_csv:
        raw = pd.read_csv(input_csv)
        source = f"Offline rerank: {input_csv.name}"
    else:
        universe, source = load_universe(
            snapshot_path=project_root / "config" / "nifty100_snapshot.csv",
            custom_path=universe_file,
            refresh=refresh_universe,
        )
        raw = collect_stock_data(
            universe=universe,
            cache_dir=project_root / ".cache" / "fundamentals",
            workers=workers,
        )

    scored, candidates, champions, excluded = screen_and_rank(raw, criteria)
    as_of = (
        scored["Price End"].dropna().max()
        if "Price End" in scored and scored["Price End"].notna().any()
        else date.today().isoformat()
    )
    result = ScreenResult(
        criteria=criteria,
        all_stocks=scored,
        candidates=candidates,
        sector_champions=champions,
        excluded=excluded,
        complete_count=int(scored["Data Complete"].sum()),
        as_of_date=str(as_of),
        universe_source=source,
    )
    save_tables(result, data_dir)
    create_all_charts(result, chart_dir)
    write_report(result, output_dir)
    return result
