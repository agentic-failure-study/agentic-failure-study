"""Figures for the analysis report.

All figures are generated from the same dictionaries the report tables are built
from, so a figure can never disagree with its table.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .common import FIG_DIR

PALETTE = {
    "ink": "#1F2933",
    "muted": "#6B7280",
    "grid": "#E5E7EB",
    "accent": "#1F3364",
    "accent2": "#2F6F8F",
    "warn": "#B45309",
    "bad": "#9B2226",
    "good": "#3F6F4A",
}
SERIES = ["#1F3364", "#2F6F8F", "#6B8E9B", "#B45309", "#9B2226",
          "#3F6F4A", "#7C5C8A", "#A8763E", "#4A5568", "#8FA3B0"]


def _style() -> None:
    plt.rcParams.update({
        "figure.dpi": 160,
        "savefig.dpi": 160,
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.edgecolor": PALETTE["grid"],
        "axes.labelcolor": PALETTE["ink"],
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.titlecolor": PALETTE["ink"],
        "axes.grid": True,
        "grid.color": PALETTE["grid"],
        "grid.linewidth": 0.7,
        "xtick.color": PALETTE["muted"],
        "ytick.color": PALETTE["muted"],
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def _finish(fig, path: Path, note: str | None = None) -> str:
    if note:
        fig.text(0.01, 0.005, note, fontsize=7, color=PALETTE["muted"])
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def freq_bar(rows: list[dict], path: Path, title: str,
             xlabel: str = "Share of failure records (%)") -> str:
    """Horizontal bar with Wilson CI whiskers."""
    _style()
    rows = [r for r in rows if r["count"] > 0]
    if not rows:
        return ""
    rows = sorted(rows, key=lambda r: r["proportion"])
    labels = [r["label"].replace("_", " ") for r in rows]
    vals = [r["proportion"] * 100 for r in rows]
    lo = [(r["proportion"] - r["ci_low"]) * 100 for r in rows]
    hi = [(r["ci_high"] - r["proportion"]) * 100 for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, max(2.4, 0.42 * len(rows) + 1.2)))
    y = np.arange(len(rows))
    ax.barh(y, vals, color=PALETTE["accent"], height=0.62, alpha=0.9)
    ax.errorbar(vals, y, xerr=[lo, hi], fmt="none", ecolor=PALETTE["muted"],
                elinewidth=1, capsize=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left")
    for i, (v, r) in enumerate(zip(vals, rows)):
        ax.text(v + max(hi) * 0.12 + 0.4, i, f"{v:.1f}%  (n={r['count']})",
                va="center", fontsize=8, color=PALETTE["ink"])
    ax.set_xlim(0, max(vals) * 1.32 if vals else 1)
    ax.grid(axis="y", visible=False)
    return _finish(fig, path, "Whiskers: Wilson 95% CI. Denominator: all retained failure records.")


def grouped_bar(categories: list[str], series: dict[str, list[float]],
                path: Path, title: str, ylabel: str = "Share (%)") -> str:
    _style()
    n_ser = max(1, len(series))
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    x = np.arange(len(categories))
    width = 0.8 / n_ser
    for i, (name, vals) in enumerate(series.items()):
        ax.bar(x + i * width - 0.4 + width / 2, vals, width,
               label=name, color=SERIES[i % len(SERIES)])
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", " ") for c in categories],
                       rotation=25, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="x", visible=False)
    return _finish(fig, path, "Percentages within each framework's retained records.")


def heatmap(matrix: list[list[float]], row_labels: list[str], col_labels: list[str],
            path: Path, title: str, cbar_label: str = "Row share (%)") -> str:
    _style()
    arr = np.asarray(matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(max(6.5, 0.85 * len(col_labels) + 3),
                                    max(3.2, 0.5 * len(row_labels) + 1.8)))
    im = ax.imshow(arr, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels([c.replace("_", " ") for c in col_labels],
                       rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels([r.replace("_", " ") for r in row_labels], fontsize=8)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if arr[i, j] > 0:
                ax.text(j, i, f"{arr[i, j]:.0f}", ha="center", va="center",
                        fontsize=7,
                        color="white" if arr[i, j] > arr.max() * 0.6 else PALETTE["ink"])
    ax.set_title(title, loc="left")
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label(cbar_label, fontsize=8)
    return _finish(fig, path, "Cells: percentage of the row's records. Empty cells omitted.")


def rate_with_ci(rows: list[dict], path: Path, title: str,
                 ylabel: str = "Rate (%)") -> str:
    _style()
    rows = [r for r in rows if r["denominator"] > 0]
    if not rows:
        return ""
    labels = [r["label"].replace("_", " ") for r in rows]
    vals = [r["proportion"] * 100 for r in rows]
    lo = [(r["proportion"] - r["ci_low"]) * 100 for r in rows]
    hi = [(r["ci_high"] - r["proportion"]) * 100 for r in rows]
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    x = np.arange(len(rows))
    ax.plot(x, vals, "o-", color=PALETTE["accent"], lw=1.6, ms=6)
    ax.errorbar(x, vals, yerr=[lo, hi], fmt="none", ecolor=PALETTE["muted"],
                elinewidth=1, capsize=4)
    for i, r in enumerate(rows):
        ax.annotate(f"n={r['denominator']}", (i, vals[i]), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=7, color=PALETTE["muted"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")
    ax.grid(axis="x", visible=False)
    return _finish(fig, path, "Whiskers: Wilson 95% CI.")


def confusion(cm: list[list[int]], labels: list[str], path: Path,
              title: str) -> str:
    _style()
    arr = np.asarray(cm, dtype=float)
    fig, ax = plt.subplots(figsize=(max(5.5, 0.6 * len(labels) + 2.5),
                                    max(4.2, 0.5 * len(labels) + 2)))
    im = ax.imshow(arr, cmap="Greens", aspect="auto")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([l.replace("_", " ") for l in labels], rotation=40, ha="right", fontsize=7)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([l.replace("_", " ") for l in labels], fontsize=7)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Annotated (reference)")
    ax.set_title(title, loc="left")
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if arr[i, j] > 0:
                ax.text(j, i, int(arr[i, j]), ha="center", va="center", fontsize=7,
                        color="white" if arr[i, j] > arr.max() * 0.55 else PALETTE["ink"])
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.85)
    return _finish(fig, path, "Diagonal: agreement between automated labeller and reference annotation.")


def timeline(rows: list[dict], path: Path, title: str) -> str:
    """rows: [{label, proportions: {type: pct}}]"""
    _style()
    if not rows:
        return ""
    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    x = np.arange(len(rows))
    types = sorted({t for r in rows for t in r["proportions"]})
    bottom = np.zeros(len(rows))
    for i, t in enumerate(types):
        vals = np.array([r["proportions"].get(t, 0.0) for r in rows])
        ax.bar(x, vals, bottom=bottom, label=t.replace("_", " "),
               color=SERIES[i % len(SERIES)], width=0.66)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels([str(r.get("label", r.get("year", ""))) for r in rows])
    ax.set_ylabel("Share of that year's records (%)")
    ax.set_title(title, loc="left")
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper left",
              bbox_to_anchor=(1.0, 1.0))
    ax.grid(axis="x", visible=False)
    return _finish(fig, path, "Years with fewer than 10 records are omitted.")




def trend_curve(rows: list[dict], path: Path, title: str,
                xlabel: str = "Declared complexity tier",
                ylabel: str = "Share of tier's records (%)",
                annotations: dict | None = None) -> str:
    """A line through an ordered ordinal variable, with Wilson intervals.

    The advisor asked for empirical results as curves, and a trend across ordered
    tiers is exactly that: four points, a monotone line, and an interval on each
    point so the slope can be read against its uncertainty rather than only
    asserted. A bar chart would have shown the same four numbers while hiding the
    one property being claimed - that the quantity rises with the tier.
    """
    _style()
    if not rows:
        return ""
    xs = [r.get("tier", r.get("x", i)) for i, r in enumerate(rows)]
    ys = [float(r["proportion"]) * 100.0 for r in rows]
    lo = [y - float(r["ci_low"]) * 100.0 for y, r in zip(ys, rows)]
    hi = [float(r["ci_high"]) * 100.0 - y for y, r in zip(ys, rows)]

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.errorbar(xs, ys, yerr=[lo, hi], fmt="o-", color=PALETTE["accent"],
                ecolor=PALETTE["accent2"], elinewidth=1.1, capsize=4,
                markersize=5.5, linewidth=1.6, zorder=3)
    for x, y, r in zip(xs, ys, rows):
        ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=8,
                    color=PALETTE["ink"])
    ax.set_xticks(xs)
    ax.set_xticklabels([f"Tier {r.get('tier', '')}" if "tier" in r
                        else str(r.get("label", "")) for r in rows])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")
    ax.grid(axis="x", visible=False)
    ax.set_ylim(bottom=0)

    if annotations:
        ax.text(0.99, 0.03, annotations.get("line", ""), transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7.5, color=PALETTE["muted"],
                style="italic")
    return _finish(fig, path, "Bars are Wilson 95% intervals on each tier's share.")


def architecture(path: Path) -> str:
    """The big picture: which agent connects to which, and how they talk.

    Solid arrows are messages that are genuinely posted to the blackboard and
    appear in transcript.jsonl. The dispatch arrow is a direct method call from the
    orchestrator, which is logged as a tool call rather than a message; the diagram
    distinguishes the two instead of drawing a message that does not exist. Dotted
    lines are shared state - every agent reads and writes the same blackboard.
    """
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    _style()
    ink, accent = PALETTE["ink"], PALETTE["accent"]
    muted, good, warn = PALETTE["muted"], PALETTE["good"], PALETTE["warn"]

    fig, ax = plt.subplots(figsize=(9.2, 6.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 66)
    ax.axis("off")
    ax.grid(False)

    def box(x, y, w, h, title, sub, edge=accent, fill="#F7F8FA"):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.35,rounding_size=1.0",
                                    linewidth=1.2, edgecolor=edge,
                                    facecolor=fill, zorder=3))
        ax.text(x + w / 2, y + h - 1.9, title, ha="center", va="top",
                fontsize=8.4, fontweight="bold", color=ink, zorder=4)
        ax.text(x + w / 2, y + h - 4.9, sub, ha="center", va="top",
                fontsize=6.7, color=muted, zorder=4, linespacing=1.4)

    def arrow(p, q, label, color=accent, ls="solid", rad=0.0, lx=0.0, ly=1.5,
              size=6.5, ha="center"):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10,
                                     linewidth=1.15, color=color,
                                     connectionstyle=f"arc3,rad={rad}",
                                     linestyle=ls, zorder=2))
        if label:
            ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label,
                    ha=ha, va="center", fontsize=size, color=color, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none",
                              alpha=0.95))

    # shared state
    ax.add_patch(FancyBboxPatch((3, 3), 94, 6.4,
                                boxstyle="round,pad=0.35,rounding_size=1.0",
                                linewidth=1.0, edgecolor=muted,
                                facecolor="#F2F4F6", linestyle=(0, (4, 2)),
                                zorder=3))
    ax.text(50, 6.2, "BLACKBOARD   records · results · verified · rejected · "
                     "tool calls · append-only transcript",
            ha="center", va="center", fontsize=7.2, color=ink, zorder=4)

    # row 1: decision layer
    box(4, 48, 21, 12, "PlannerAgent",
        "reads the RQ config and\nschema · ordered plan\n· refuses if a field is absent")
    box(33, 48, 23, 12, "Orchestrator",
        "dispatches each question\n· requests one corrective\npass on a revise",
        edge=ink, fill="#EEF1F6")
    box(64, 48, 21, 12, "TaggerAgent",
        "audits label completeness\nand confidence · queues\nlow-confidence records")

    # specialists
    spec = [("StatisticianAgent", "RQ1 RQ2 RQ7 RQ8 · Wilson CIs"),
            ("CausalAgent", "RQ3 · chi-square, Cramér's V, BH"),
            ("ComparatorAgent", "RQ4 RQ5 RQ9 · rates, lift"),
            ("ComplexityAgent", "RQ6 RQ10 · tiers, trend")]
    ys = [35.5, 28.0, 20.5, 13.0]
    for (name, sub), y in zip(spec, ys):
        box(33, y, 23, 6.2, name, sub)

    # verification and reporting
    box(64, 27.0, 21, 12.5, "CriticAgent",
        "recomputes each headline\nfrom raw records · checks\ndenominators · blocks causal\nverbs on associations",
        edge=warn, fill="#FDF7F1")
    box(64, 12.0, 21, 10.5, "ReporterAgent",
        "renders verified findings\nonly · tables, figures, prose",
        edge=good, fill="#F4F8F5")

    # recorded messages
    arrow((25.4, 54), (32.6, 54), "inform · plan")
    arrow((63.6, 54), (56.4, 54), "inform · audit")

    # dispatch: a direct call, not a message
    ax.plot([44.5, 44.5], [47.6, 41.9], color=muted, linewidth=1.15,
            linestyle=(0, (4, 2)), zorder=2)
    ax.add_patch(FancyArrowPatch((44.5, 42.6), (44.5, 41.9), arrowstyle="-|>",
                                 mutation_scale=9, linewidth=1.15, color=muted,
                                 zorder=2))
    ax.text(45.4, 44.6, "dispatch {rq, method}", fontsize=6.4, color=muted,
            ha="left", va="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none"))

    # proposals: four specialists converge on the critic's left edge
    for y in (38.6, 31.1, 23.6, 16.1):
        arrow((56.4, y), (63.6, 33.5), "", rad=-0.10, size=6.2)
    ax.text(59.9, 33.5, "propose", fontsize=6.2, color=accent, rotation=90,
            ha="center", va="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.14", fc="white", ec="none",
                      alpha=0.95))

    # verdict back to the orchestrator, then the report
    arrow((64.2, 41.2), (56.6, 47.4), "verify · accept / revise", color=warn,
          rad=0.16, size=6.3, lx=1.0, ly=1.9)
    arrow((74.5, 26.6), (74.5, 22.9), "verified only", color=good, size=6.3)

    # shared state connectors
    for x in (14.5, 44.5, 74.5):
        ax.plot([x, x], [9.6, 12.4], linestyle=(0, (2, 2)), linewidth=0.9,
                color=muted, zorder=1)
    ax.text(88.5, 10.9, "shared state", fontsize=6.3, color=muted,
            ha="right", va="center")

    # legend
    ax.plot([6, 12], [62.6, 62.6], color=accent, linewidth=1.15)
    ax.text(13, 62.6, "recorded message", fontsize=6.8, va="center", color=ink)
    ax.plot([31, 37], [62.6, 62.6], color=muted, linewidth=1.15,
            linestyle=(0, (4, 2)))
    ax.text(38, 62.6, "direct dispatch (tool call)", fontsize=6.8, va="center",
            color=ink)
    ax.plot([64, 70], [62.6, 62.6], color=muted, linewidth=0.9,
            linestyle=(0, (2, 2)))
    ax.text(71, 62.6, "shared state", fontsize=6.8, va="center", color=ink)

    ax.set_title("Blackboard multi-agent architecture: eight agents, one recorded "
                 "transcript, no number passes through a language model",
                 loc="left", fontsize=9.8, pad=16)
    return _finish(fig, path,
                   "Solid arrows are say() messages recorded in transcript.jsonl; "
                   "the dispatch arrow is the orchestrator's direct method call.")
