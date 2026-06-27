"""Load the official Nifty 100 constituent universe with an offline fallback."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
import requests

OFFICIAL_UNIVERSE_URL = (
    "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
)
REQUIRED_COLUMNS = ["Company Name", "Industry", "Symbol"]


class UniverseError(RuntimeError):
    """Raised when a valid stock universe cannot be constructed."""


def _validate_universe(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise UniverseError(f"Universe is missing column(s): {', '.join(missing)}")

    clean = frame.copy()
    for column in REQUIRED_COLUMNS:
        clean[column] = clean[column].astype(str).str.strip()
    clean = clean.loc[(clean["Symbol"] != "") & (clean["Symbol"] != "nan")]
    clean = clean.drop_duplicates(subset="Symbol").sort_values("Symbol").reset_index(drop=True)
    clean["Yahoo Symbol"] = clean["Symbol"] + ".NS"
    if len(clean) < 10:
        raise UniverseError("Universe contains fewer than 10 valid NSE symbols.")
    return clean


def load_universe(
    snapshot_path: Path,
    custom_path: Path | None = None,
    refresh: bool = False,
) -> tuple[pd.DataFrame, str]:
    """Return universe and source; refresh failure falls back to committed snapshot."""
    if custom_path:
        if not custom_path.exists():
            raise UniverseError(f"Universe file does not exist: {custom_path}")
        return _validate_universe(pd.read_csv(custom_path)), str(custom_path.resolve())

    if refresh:
        try:
            response = requests.get(
                OFFICIAL_UNIVERSE_URL,
                headers={"User-Agent": "Mozilla/5.0 (educational stock screener)"},
                timeout=30,
            )
            response.raise_for_status()
            return _validate_universe(pd.read_csv(StringIO(response.text))), OFFICIAL_UNIVERSE_URL
        except (requests.RequestException, pd.errors.ParserError, UniverseError):
            pass

    if not snapshot_path.exists():
        raise UniverseError(
            "The official universe refresh failed and the bundled snapshot is missing."
        )
    return _validate_universe(pd.read_csv(snapshot_path)), f"Bundled snapshot: {snapshot_path.name}"

