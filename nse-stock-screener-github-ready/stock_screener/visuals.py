"""Presentation-ready charts for the stock-screening results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

from .models import ScreenResult

NAVY = "#102A43"
BLUE = "#2878B5"
TEAL = "#2A9D8F"
GOLD = "#E9C46A"
RED = "#E76F51"
GREY = "#9AA5B1"
LIGHT = "#F3F6F9"


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    ax.grid(axis="y", color="#D9E2EC", linewidth=0.8, alpha=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors="#627D98")


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_screening_map(result: ScreenResult, path: Path) -> None:
    frame = result.all_stocks.dropna(subset=["Trailing PE", "1Y Return", "Market Cap (INR Crore)"])
    failed = frame.loc[~frame["Passed"]]
    passed = frame.loc[frame["Passed"]]

    fig, ax = plt.subplots(figsize=(12, 7))
    _style(ax)
    failed_sizes = np.clip(np.sqrt(failed["Market Cap (INR Crore)"]) * 1.5, 20, 260)
    passed_sizes = np.clip(np.sqrt(passed["Market Cap (INR Crore)"]) * 1.5, 35, 300)
    ax.scatter(
        failed["Trailing PE"], failed["1Y Return"], s=failed_sizes,
        color=GREY, alpha=0.35, label="Did not pass"
    )
    ax.scatter(
        passed["Trailing PE"], passed["1Y Return"], s=passed_sizes,
        color=TEAL, alpha=0.75, edgecolor="white", linewidth=0.6, label="Passed"
    )
    ax.axvline(result.criteria.max_pe, color=RED, linestyle="--", linewidth=1.5)
    ax.axhline(
        result.criteria.min_one_year_return, color=RED, linestyle="--", linewidth=1.5
    )
    offsets = [(8, -14), (8, 5), (8, 15), (8, 5), (8, -12)]
    for offset, (_, row) in zip(offsets, result.candidates.head(5).iterrows()):
        ax.annotate(
            row["Symbol"],
            (row["Trailing PE"], row["1Y Return"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
            color=NAVY,
        )
    x_limit = max(
        result.criteria.max_pe * 2,
        min(150.0, float(frame["Trailing PE"].quantile(0.95)) * 1.15),
    )
    ax.set_xlim(left=0, right=x_limit)
    ax.set_xlabel("Trailing P/E (lower is cheaper, all else equal)")
    ax.set_ylabel("Trailing one-year return")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("Value–Momentum Screening Map", color=NAVY, fontsize=17, weight="bold")
    ax.legend(frameon=False)
    _save(fig, path)


def plot_ranked_candidates(result: ScreenResult, path: Path) -> None:
    top = result.candidates.head(result.criteria.top_n).sort_values("Composite Score")
    fig, ax = plt.subplots(figsize=(11, 7))
    _style(ax)
    ax.barh(top["Symbol"], top["Value Contribution"], color=BLUE, label="Value (45%)")
    ax.barh(
        top["Symbol"],
        top["Momentum Contribution"],
        left=top["Value Contribution"],
        color=GOLD,
        label="Momentum (55%)",
    )
    for index, (_, row) in enumerate(top.iterrows()):
        ax.text(row["Composite Score"] + 0.8, index, f"{row['Composite Score']:.1f}", va="center")
    ax.set_xlim(0, max(100, top["Composite Score"].max() + 10) if not top.empty else 100)
    ax.set_xlabel("Composite percentile score (0–100)")
    ax.set_title("Top Candidates: Score Decomposition", color=NAVY, fontsize=17, weight="bold")
    ax.legend(frameon=False, ncols=2)
    _save(fig, path)


def plot_sector_champions(result: ScreenResult, path: Path) -> None:
    champions = result.sector_champions.head(12).sort_values("Composite Score")
    labels = [f"{row.Symbol} — {row.Industry}" for row in champions.itertuples()]
    fig, ax = plt.subplots(figsize=(12, 7))
    _style(ax)
    bars = ax.barh(labels, champions["Composite Score"], color=TEAL)
    ax.bar_label(bars, labels=[f"{x:.1f}" for x in champions["Composite Score"]], padding=4)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Composite score")
    ax.set_title("Best Eligible Stock in Each Industry", color=NAVY, fontsize=17, weight="bold")
    _save(fig, path)


def plot_dashboard(result: ScreenResult, path: Path) -> None:
    fig = plt.figure(figsize=(16, 10), constrained_layout=True)
    grid = fig.add_gridspec(2, 2)
    ax_map = fig.add_subplot(grid[:, 0])
    ax_rank = fig.add_subplot(grid[0, 1])
    ax_risk = fig.add_subplot(grid[1, 1])
    fig.suptitle("NSE Quantamental Stock Screener", color=NAVY, fontsize=22, weight="bold")
    for ax in (ax_map, ax_rank, ax_risk):
        _style(ax)

    frame = result.all_stocks.dropna(subset=["Trailing PE", "1Y Return", "Market Cap (INR Crore)"])
    colors = np.where(frame["Passed"], TEAL, GREY)
    sizes = np.clip(np.sqrt(frame["Market Cap (INR Crore)"]) * 1.2, 18, 240)
    ax_map.scatter(frame["Trailing PE"], frame["1Y Return"], s=sizes, c=colors, alpha=0.55)
    ax_map.axvline(result.criteria.max_pe, color=RED, linestyle="--")
    ax_map.axhline(result.criteria.min_one_year_return, color=RED, linestyle="--")
    ax_map.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax_map.set_xlabel("Trailing P/E")
    ax_map.set_ylabel("One-year return")
    ax_map.set_title("Eligibility map", weight="bold")
    dashboard_x_limit = max(
        result.criteria.max_pe * 2,
        min(150.0, float(frame["Trailing PE"].quantile(0.95)) * 1.15),
    )
    ax_map.set_xlim(left=0, right=dashboard_x_limit)

    top = result.candidates.head(10).sort_values("Composite Score")
    ax_rank.barh(top["Symbol"], top["Composite Score"], color=BLUE)
    ax_rank.set_xlim(0, 100)
    ax_rank.set_title("Top composite scores", weight="bold")

    risk = result.candidates.head(15).dropna(subset=["Annualised Volatility", "1Y Return"])
    ax_risk.scatter(
        risk["Annualised Volatility"], risk["1Y Return"],
        s=80, color=GOLD, edgecolor=NAVY, linewidth=0.6
    )
    for _, row in risk.head(8).iterrows():
        ax_risk.annotate(
            row["Symbol"],
            (row["Annualised Volatility"], row["1Y Return"]),
            xytext=(4, 4), textcoords="offset points", fontsize=8,
        )
    ax_risk.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax_risk.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax_risk.set_xlabel("Annualised volatility")
    ax_risk.set_ylabel("One-year return")
    ax_risk.set_title("Candidate risk–return", weight="bold")
    _save(fig, path)


def create_all_charts(result: ScreenResult, chart_dir: Path) -> None:
    chart_dir.mkdir(parents=True, exist_ok=True)
    plot_screening_map(result, chart_dir / "01_value_momentum_map.png")
    plot_ranked_candidates(result, chart_dir / "02_ranked_candidates.png")
    plot_sector_champions(result, chart_dir / "03_sector_champions.png")
    plot_dashboard(result, chart_dir / "04_screener_dashboard.png")
