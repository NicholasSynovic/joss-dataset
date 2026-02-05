#!/usr/bin/env python3
# Copyright (c) 2026.
# SPDX-License-Identifier: MIT

"""
Plot the top N issue labels per year.

This script reads the normalized submissions file produced by the transform step,
aggregates labels by the year an issue was opened, selects the top N labels per
year, and writes a PNG plot using matplotlib.

Bars are color-coded by label, with a legend indicating which color corresponds
to which label.

Pipeline:
- ingest:    src/ingest/github_issues.py (raw issue JSONs; not committed)
- transform: src/transform/normalize_joss_submissions.py
  -> data/derived/joss_submissions.json
- analysis:  src/analysis/top_labels_per_year.py
  -> data/plots/top_labels_per_year.png
"""

from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from .utils import load_submissions, unix_to_year

LOGGER: logging.Logger = logging.getLogger(__name__)


def _extract_labels(submission: dict[str, Any]) -> list[str]:
    """
    Extract label names from a normalized submission.

    Args:
        submission: A normalized submission record.

    Returns:
        A list of label names (strings). Non-string values are ignored.

    """
    labels_obj = submission.get("Labels", [])
    if not isinstance(labels_obj, list):
        return []

    return [item for item in labels_obj if isinstance(item, str)]


def _opened_year(submission: dict[str, Any]) -> int | None:
    """
    Extract the opened year from a normalized submission.

    Args:
        submission: A normalized submission record.

    Returns:
        The opened year (UTC), or None if not available.

    """
    opened = submission.get("Opened")
    if not isinstance(opened, int):
        return None
    return unix_to_year(opened)


def _count_labels_by_year(
    submissions: list[dict[str, Any]],
) -> dict[int, Counter[str]]:
    """
    Count label frequencies grouped by opened year.

    Each submission contributes +1 to each label it contains (deduplicated
    defensively within a submission).

    Args:
        submissions: Normalized submissions list.

    Returns:
        A mapping of year -> Counter(label -> count).

    """
    by_year: dict[int, Counter[str]] = {}

    for sub in submissions:
        year = _opened_year(sub)
        if year is None:
            continue

        labels = set(_extract_labels(sub))
        if not labels:
            continue

        if year not in by_year:
            by_year[year] = Counter()

        for label in labels:
            by_year[year][label] += 1

    return by_year


def _top_n_labels(counter: Counter[str], n: int) -> list[tuple[str, int]]:
    """
    Select the top N labels from a Counter.

    Args:
        counter: Counter mapping label -> count.
        n: Number of labels to return.

    Returns:
        A list of (label, count) pairs sorted by count desc, then label asc.

    """
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def _prepare_top_label_plot_data(
    by_year: dict[int, Counter[str]],
    *,
    top_n: int,
) -> tuple[
    list[int],
    list[int],
    list[str],
    list[float],
    list[str],
    dict[str, str],
]:
    """
    Prepare bar positions, heights, colors, and tick labels for plotting.

    Returns:
        A 6-tuple of:
        - x_positions: Bar x positions.
        - heights: Bar heights (counts).
        - colors: Bar colors aligned to x_positions.
        - year_tick_positions: X positions for year tick labels (group centers).
        - year_tick_labels: Year tick labels.
        - color_map: Mapping of label -> color used in the plot.

    """
    years = sorted(by_year.keys())

    per_year_top: dict[int, list[tuple[str, int]]] = {
        year: _top_n_labels(by_year[year], top_n) for year in years
    }

    top_labels_global: set[str] = set()
    for top in per_year_top.values():
        top_labels_global.update(label for label, _ in top)

    sorted_labels = sorted(top_labels_global)
    cmap = plt.get_cmap("tab10")
    color_map: dict[str, str] = {
        label: cmap(i % cmap.N) for i, label in enumerate(sorted_labels)
    }

    x_positions: list[int] = []
    heights: list[int] = []
    colors: list[str] = []
    year_tick_positions: list[float] = []
    year_tick_labels: list[str] = []

    x = 0
    for year in years:
        top = per_year_top.get(year, [])
        if not top:
            year_tick_positions.append(x)
            year_tick_labels.append(str(year))
            x += top_n + 1
            continue

        start_x = x
        for rank, (label, count) in enumerate(top):
            x_positions.append(x + rank)
            heights.append(count)
            colors.append(color_map[label])

        end_x = x + len(top) - 1
        year_tick_positions.append((start_x + end_x) / 2)
        year_tick_labels.append(str(year))

        x += top_n + 1

    return (
        x_positions,
        heights,
        colors,
        year_tick_positions,
        year_tick_labels,
        color_map,
    )


def _plot_top_labels_per_year(
    by_year: dict[int, Counter[str]],
    *,
    top_n: int,
    out_path: Path,
) -> None:
    """
    Plot the top N issue labels per year and save to a PNG.

    Uses the precomputed plotting data from `_prepare_top_label_plot_data()`.
    Bars are color-coded by label, and a legend maps colors to label names.

    Args:
        by_year: Mapping of year -> Counter(label -> count).
        top_n: Number of top labels to show per year.
        out_path: Output PNG path.

    Raises:
        RuntimeError: If there is no data to plot.

    """
    if not by_year:
        msg = "No year/label data available to plot."
        raise RuntimeError(msg)

    (
        x_positions,
        heights,
        colors,
        year_tick_positions,
        year_tick_labels,
        color_map,
    ) = _prepare_top_label_plot_data(by_year, top_n=top_n)

    if not x_positions:
        msg = "No bars to plot (no labels found in any year)."
        raise RuntimeError(msg)

    fig, ax = plt.subplots()
    ax.bar(x_positions, heights, color=colors)
    ax.set_title(f"Top {top_n} issue labels per year (editorialbot)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Label count")

    ax.set_xticks(year_tick_positions)
    ax.set_xticklabels(year_tick_labels, rotation=45)

    sorted_labels = sorted(color_map.keys())
    legend_handles = [
        Patch(color=color_map[label], label=label) for label in sorted_labels
    ]
    ax.legend(
        handles=legend_handles,
        title="Issue label",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0,
    )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    """
    Parse CLI args.

    Returns:
        Parsed CLI namespace.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Plot top N label frequencies per year from normalized JOSS submissions."
        )
    )
    parser.add_argument(
        "--in-file",
        default="data/derived/joss_submissions.json",
        help="Input normalized submissions JSON",
    )
    parser.add_argument(
        "--out-file",
        default="data/plots/top_labels_per_year.png",
        help="Output PNG file path",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of top labels to show per year (default: 5)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG/INFO/WARNING/ERROR)",
    )
    return parser.parse_args()


def main() -> int:
    """
    Run the top-labels-per-year plotter.

    Returns:
        Process exit code.

    Raises:
        RuntimeError: If the input file is missing or no data is available.

    """
    args = parse_args()

    level_name = str(args.log_level).upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="%(levelname)s: %(message)s",
    )

    in_file = Path(str(args.in_file))
    out_file = Path(str(args.out_file))
    top_n = int(args.top_n)

    if top_n <= 0:
        msg = "--top-n must be a positive integer."
        raise RuntimeError(msg)

    if not in_file.exists():
        msg = (
            f"Input file not found: {in_file}\n"
            "Run the normalization step first to generate "
            "data/derived/joss_submissions.json"
        )
        raise RuntimeError(msg)

    submissions = load_submissions(in_file)
    LOGGER.info("Loaded %s submissions from %s", len(submissions), in_file)

    by_year = _count_labels_by_year(submissions)
    LOGGER.info("Found %s years with label data", len(by_year))

    _plot_top_labels_per_year(by_year, top_n=top_n, out_path=out_file)
    LOGGER.info("Wrote top-labels-per-year plot to %s", out_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
