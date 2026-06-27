"""Collect prices and fundamental fields from Yahoo Finance."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252


class DataCollectionError(RuntimeError):
    """Raised when no usable market data can be collected."""


def _close_frame(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        level_zero = set(raw.columns.get_level_values(0))
        level_one = set(raw.columns.get_level_values(1))
        if "Close" in level_zero:
            close = raw["Close"]
        elif "Close" in level_one:
            close = raw.xs("Close", axis=1, level=1)
        else:
            return pd.DataFrame()
    elif "Close" in raw.columns:
        close = raw[["Close"]]
    else:
        return pd.DataFrame()
    return close.to_frame() if isinstance(close, pd.Series) else close


def download_price_statistics(symbols: list[str], chunk_size: int = 40) -> pd.DataFrame:
    """Batch-download adjusted closes and calculate trailing return/risk statistics."""
    close_parts: list[pd.DataFrame] = []
    for start in range(0, len(symbols), chunk_size):
        chunk = symbols[start : start + chunk_size]
        raw = yf.download(
            chunk,
            period="1y",
            interval="1d",
            auto_adjust=True,
            group_by="column",
            progress=False,
            threads=True,
            timeout=30,
        )
        close = _close_frame(raw)
        if len(chunk) == 1 and not close.empty:
            close.columns = chunk
        close_parts.append(close)

    closes = pd.concat(close_parts, axis=1)
    closes = closes.loc[:, ~closes.columns.duplicated()]
    rows: list[dict[str, float | int | str | None]] = []

    for symbol in symbols:
        if symbol not in closes.columns:
            rows.append({"Yahoo Symbol": symbol, "Price Error": "No close-price column"})
            continue
        series = pd.to_numeric(closes[symbol], errors="coerce").dropna()
        if len(series) < 200:
            rows.append(
                {
                    "Yahoo Symbol": symbol,
                    "Price Observations": int(len(series)),
                    "Price Error": "Fewer than 200 observations",
                }
            )
            continue

        returns = series.pct_change(fill_method=None).dropna()
        drawdown = series / series.cummax() - 1
        rows.append(
            {
                "Yahoo Symbol": symbol,
                "Current Price (INR)": float(series.iloc[-1]),
                "1Y Return": float(series.iloc[-1] / series.iloc[0] - 1),
                "Annualised Volatility": float(returns.std() * np.sqrt(TRADING_DAYS)),
                "Maximum Drawdown": float(drawdown.min()),
                "Price Observations": int(len(series)),
                "Price Start": series.index[0].date().isoformat(),
                "Price End": series.index[-1].date().isoformat(),
                "Price Error": "",
            }
        )
    return pd.DataFrame(rows)


def _cache_is_fresh(path: Path, max_age_hours: int = 24) -> bool:
    if not path.exists():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(timezone.utc) - modified).total_seconds() < max_age_hours * 3600


def _fetch_one_fundamental(yahoo_symbol: str, cache_dir: Path) -> dict[str, object]:
    cache_file = cache_dir / f"{yahoo_symbol.replace('.', '_')}.json"
    if _cache_is_fresh(cache_file):
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    try:
        info = yf.Ticker(yahoo_symbol).get_info()
        market_cap = info.get("marketCap")
        row: dict[str, object] = {
            "Yahoo Symbol": yahoo_symbol,
            "Trailing PE": info.get("trailingPE"),
            "Market Cap (INR)": market_cap,
            "Market Cap (INR Crore)": market_cap / 10_000_000 if market_cap else None,
            "Yahoo Sector": info.get("sector"),
            "Yahoo Industry": info.get("industry"),
            "Currency": info.get("currency"),
            "Fundamental Error": "",
            "Fundamental As Of": date.today().isoformat(),
        }
    except Exception as exc:  # yfinance surfaces several HTTP/JSON exception types
        row = {
            "Yahoo Symbol": yahoo_symbol,
            "Trailing PE": None,
            "Market Cap (INR)": None,
            "Market Cap (INR Crore)": None,
            "Yahoo Sector": None,
            "Yahoo Industry": None,
            "Currency": None,
            "Fundamental Error": type(exc).__name__,
            "Fundamental As Of": date.today().isoformat(),
        }

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    return row


def fetch_fundamentals(
    symbols: list[str], cache_dir: Path, workers: int = 1
) -> pd.DataFrame:
    """Fetch trailing P/E and market cap with a small, polite worker pool and cache."""
    workers = max(1, min(workers, 4))
    rows: list[dict[str, object]] = []
    if workers == 1:
        for symbol in symbols:
            rows.append(_fetch_one_fundamental(symbol, cache_dir))
        return pd.DataFrame(rows)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_fetch_one_fundamental, symbol, cache_dir): symbol
            for symbol in symbols
        }
        for future in as_completed(futures):
            rows.append(future.result())
    return pd.DataFrame(rows)


def collect_stock_data(
    universe: pd.DataFrame, cache_dir: Path, workers: int = 1
) -> pd.DataFrame:
    # yfinance stores cookies/time-zone metadata in SQLite. A project-specific location
    # avoids interference from another Python session using the global cache.
    yf.set_tz_cache_location(str(cache_dir.parent / "yfinance"))
    symbols = universe["Yahoo Symbol"].tolist()
    prices = download_price_statistics(symbols)
    fundamentals = fetch_fundamentals(symbols, cache_dir=cache_dir, workers=workers)
    merged = universe.merge(prices, on="Yahoo Symbol", how="left")
    merged = merged.merge(fundamentals, on="Yahoo Symbol", how="left")
    if merged["1Y Return"].notna().sum() == 0:
        raise DataCollectionError("No usable one-year price histories were returned.")
    return merged
