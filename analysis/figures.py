"""Figures 1-5 (implementation specification §6.6; decision G4a §3.5), the order-level figure (decision R1) and Fig. 7, strict
versus fence-tolerant scoring (decision GV §3.1): 300 dpi PNG plus PDF, 16 cm wide, serif font, the
Okabe-Ito colour-blind-safe palette with a distinct marker and line style per model (readable in grayscale), no
titles inside the images (captions go in the paper). Every plotted value is read from results/metrics/summary.json.

Usage: python -m analysis.figures   (``make figures``)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

from analysis.data import CONSTRAINTS, FAMILIES  # noqa: E402
from analysis.report import CNAMES, FNAMES, NAMES, olabel  # noqa: E402
from src.common import RESULTS_DIR  # noqa: E402
from src.orders import ORDERS  # noqa: E402

CM = 1 / 2.54
WIDTH = 16 * CM
STYLE = {  # Okabe-Ito colours; marker and line style keep the models apart in grayscale
    "smollm2": {"color": "#E69F00", "marker": "o", "ls": "-"},
    "qwen25": {"color": "#0072B2", "marker": "s", "ls": "--"},
    "phi4mini": {"color": "#009E73", "marker": "^", "ls": "-."},
    "gemma4e4b": {"color": "#CC79A7", "marker": "D", "ls": ":"},
    "pooled": {"color": "#000000", "marker": None, "ls": "-"},
}
LETTER_COLOR = {"A": "#E69F00", "B": "#56B4E9", "C": "#009E73", "D": "#F0E442", "E": "#CC79A7"}
LETTER_NAME = {"A": "FORMAT", "B": "LENGTH", "C": "CARDINALITY", "D": "NO_COMMA", "E": "VERBATIM"}


def setup() -> None:
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 8,
        "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
        "savefig.dpi": 300, "figure.dpi": 100,
    })


def save(fig, out_dir: Path, name: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / f"{name}.png", out_dir / f"{name}.pdf"]
    for p in paths:  # no tight cropping: the canvas stays exactly 16 cm wide
        meta = {"Software": None} if p.suffix == ".png" else {"CreationDate": None, "ModDate": None}
        fig.savefig(p, metadata=meta)  # no timestamps: rebuilding gives byte-identical files
    plt.close(fig)
    return paths


def est(s: dict, prefix: str, scale: float = 100.0) -> tuple[float, float, float]:
    return tuple(s[f"{prefix}.{k}"] * scale for k in ("mean", "ci_low", "ci_high"))


def panel_label(ax, text: str) -> None:
    ax.text(0.01, 1.02, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=8, fontweight="bold")


def fig1_design(s: dict, out_dir: Path) -> list[Path]:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(WIDTH, 7.4 * CM), layout="constrained",
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    ax1.set_axis_off()
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    blocks = [
        (0.82, 0.16, "System", "You are a precise assistant.\nFollow all user instructions exactly."),
        (0.47, 0.32, "User: INSTRUCTIONS", "- {instruction in position 1}\n- {instruction in position 2}\n"
                                           "- {instruction in position 3}\n- {instruction in position 4}\n"
                                           "- {instruction in position 5}"),
        (0.25, 0.18, "TASK", "{task directive of the family}\n{question (QA only)}"),
        (0.02, 0.19, "INPUT", "{input text: SQuAD passage, AG News article,\nXSum document or synthetic record}"),
    ]
    for y, h, head, body in blocks:
        ax1.add_patch(FancyBboxPatch((0.02, y), 0.96, h, boxstyle="round,pad=0.01", fc="#F2F2F2", ec="#4D4D4D", lw=0.6))
        ax1.text(0.04, y + h - 0.025, head, fontsize=7.5, fontweight="bold", va="top")
        ax1.text(0.04, y + h - 0.075, body, fontsize=6.6, va="top", family="serif")
    panel_label(ax1, "(a)")
    orders = list(ORDERS)
    for i, oid in enumerate(orders):
        for j, letter in enumerate(ORDERS[oid]):
            y = len(orders) - 1 - i
            ax2.add_patch(Rectangle((j, y), 1, 1, fc=LETTER_COLOR[letter], ec="white", lw=1.2))
            ax2.text(j + 0.5, y + 0.5, letter, ha="center", va="center", fontsize=7.5, fontweight="bold")
    ax2.set_xlim(0, 5)
    ax2.set_ylim(0, len(orders))
    ax2.set_xticks([j + 0.5 for j in range(5)], [str(j + 1) for j in range(5)])
    ax2.set_yticks([len(orders) - 1 - i + 0.5 for i in range(len(orders))], [olabel(o) for o in orders])
    ax2.set_xlabel("Position in the INSTRUCTIONS block")
    ax2.tick_params(length=0)
    for side in ("left", "bottom"):
        ax2.spines[side].set_visible(False)
    handles = [Rectangle((0, 0), 1, 1, fc=LETTER_COLOR[k]) for k in LETTER_NAME]
    fig.legend(handles, [f"{k} = {v}" for k, v in LETTER_NAME.items()], loc="outside right upper", frameon=False,
               handlelength=1.0)
    panel_label(ax2, "(b)")
    return save(fig, out_dir, "fig1_design")


def fig2_compliance(s: dict, models: list[str], out_dir: Path, name: str = "fig2_compliance",
                    note: str | None = "Gemma 4 E4B: fenced JSON (0%)") -> list[Path]:
    fig, ax = plt.subplots(figsize=(WIDTH, 6.8 * CM), layout="constrained")
    cats = [(c, f"main.order.{{m}}.compliance.{c}") for c in CONSTRAINTS] + [("PCR", "main.order.{m}.pcr")]
    off = {m: (i - (len(models) - 1) / 2) * 0.17 for i, m in enumerate(models)}
    for m in models:
        st = STYLE[m]
        for x, (_, key) in enumerate(cats):
            mean, lo, hi = est(s, key.format(m=m))
            ax.errorbar(x + off[m], mean, yerr=[[mean - lo], [hi - mean]], fmt=st["marker"], color=st["color"], ms=4,
                        capsize=1.5, lw=0.8, label=NAMES[m] if x == 0 else None)
    ax.set_xticks(range(len(cats)), [CNAMES.get(c, c) for c, _ in cats])
    ax.set_ylabel("Compliance, order arm (%)")
    ax.set_ylim(-3, 103)
    ax.axvline(len(cats) - 1.5, color="#999999", lw=0.5, ls="--")
    if note:
        ax.annotate(note, xy=(off["gemma4e4b"], 1), xytext=(0.35, 12), fontsize=6.5,
                    arrowprops={"arrowstyle": "-", "lw": 0.5, "color": "#555555"})
    fig.legend(loc="outside lower center", ncol=4, frameon=False)
    return save(fig, out_dir, name)


def fig3_position(s: dict, models: list[str], out_dir: Path, name: str = "fig3_position",
                  note: str | None = "Gemma 4 E4B: fenced JSON (0%)", note_y: float = 4) -> list[Path]:
    fig, axes = plt.subplots(2, 3, figsize=(WIDTH, 10.5 * CM), layout="constrained")
    xs = list(range(1, 6))
    for idx, c in enumerate(CONSTRAINTS):
        ax = axes.flat[idx]
        for m in models + ["pooled"]:
            st = STYLE[m]
            vals = [est(s, f"main.order.{m}.position.{c}.{k}") for k in xs]
            means, los, his = zip(*vals)
            ax.fill_between(xs, los, his, color=st["color"], alpha=0.12 if m != "pooled" else 0.18, lw=0)
            ax.plot(xs, means, color=st["color"], ls=st["ls"], marker=st["marker"], ms=3,
                    lw=1.6 if m == "pooled" else 1.0, label=NAMES[m])
        if c == "format" and note:
            ax.text(1.0, note_y, note, fontsize=6.3, color="#555555", va="bottom")
        ax.set_ylim(-3, 103)
        ax.set_xticks(xs)
        panel_label(ax, f"({'abcde'[idx]}) {CNAMES[c]}")
        if idx % 3 == 0:
            ax.set_ylabel("Compliance (%)")
        ax.set_xlabel("Position")
    leg = axes.flat[5]
    leg.set_axis_off()
    handles, labels = axes.flat[0].get_legend_handles_labels()
    leg.legend(handles, labels, loc="center", frameon=False, title="Order arm; 95% CI bands")
    return save(fig, out_dir, name)


def fig4_noise_floor(s: dict, models: list[str], out_dir: Path, name: str = "fig4_noise_floor") -> list[Path]:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(WIDTH, 6.8 * CM), layout="constrained",
                                   gridspec_kw={"width_ratios": [1.2, 1]})
    for i, m in enumerate(models):
        st = STYLE[m]
        f_mean, f_lo, f_hi = est(s, f"main.format.{m}.ps", 1)
        o_mean, o_lo, o_hi = est(s, f"main.order.{m}.ps", 1)
        xs = [i - 0.12, i + 0.12]
        ax1.plot(xs, [f_mean, o_mean], color=st["color"], ls=st["ls"], lw=0.9)
        ax1.errorbar(xs[0], f_mean, yerr=[[f_mean - f_lo], [f_hi - f_mean]], fmt="o", mfc="white", color=st["color"],
                     ms=4, capsize=1.5, lw=0.8)
        ax1.errorbar(xs[1], o_mean, yerr=[[o_mean - o_lo], [o_hi - o_mean]], fmt=st["marker"], color=st["color"], ms=4,
                     capsize=1.5, lw=0.8)
        d, lo, hi = (s[f"main.p3.{m}.{k}"] for k in ("mean_diff", "ci_low", "ci_high"))
        ax2.errorbar(d, len(models) - 1 - i, xerr=[[d - lo], [hi - d]], fmt=st["marker"], color=st["color"], ms=4,
                     capsize=1.5, lw=0.8)
    ax1.set_xticks(range(len(models)), [NAMES[m] for m in models], rotation=15)
    ax1.set_ylabel("Mean PS (open: format arm; filled: order arm)")
    ax1.set_ylim(0, None)
    panel_label(ax1, "(a)")
    ax2.axvline(0, color="#777777", lw=0.6, ls="--")
    ax2.set_yticks(range(len(models)), [NAMES[m] for m in reversed(models)])
    ax2.set_xlabel("PS_order − PS_format (mean, 95% CI)")
    panel_label(ax2, "(b)")
    return save(fig, out_dir, name)


def fig5_task_quality(s: dict, models: list[str], out_dir: Path) -> list[Path]:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(WIDTH, 7.2 * CM), sharey=True, layout="constrained")
    off = {m: (i - (len(models) - 1) / 2) * 0.17 for i, m in enumerate(models)}
    for m in models:
        st = STYLE[m]
        for y, f in enumerate(FAMILIES):
            for ax, q in ((ax1, "q"), (ax2, "tqs")):
                mean, lo, hi = est(s, f"main.quality.{f}.{m}.{q}", 1)
                ax.errorbar(mean, len(FAMILIES) - 1 - y - off[m], xerr=[[mean - lo], [hi - mean]], fmt=st["marker"],
                            color=st["color"], ms=3.5, capsize=1.2, lw=0.8, label=NAMES[m] if (y == 0 and q == "q") else None)
    ax1.set_yticks(range(len(FAMILIES)), [FNAMES[f] for f in reversed(FAMILIES)])
    ax1.set_xlabel("Mean Q, order arm (0-1)")
    ax1.set_xlim(-0.03, 1.03)
    ax2.set_xlabel("TQS: max Q − min Q over the 10 orders")
    ax2.set_xlim(-0.02, None)
    panel_label(ax1, "(a)")
    panel_label(ax2, "(b)")
    fig.legend(loc="outside lower center", ncol=4, frameon=False)
    return save(fig, out_dir, "fig5_task_quality")


def figR1_order_level(s: dict, models: list[str], out_dir: Path, name: str = "figR1_order_level",
                      note: str | None = "Gemma 4 E4B: fenced JSON (0%)", note_y: float = 4) -> list[Path]:
    """Decision R1 §3.2 (post-hoc): mean CSR (a) and FORMAT compliance (b) per order O01-O10, one line per model,
    95% CI bars."""
    from analysis.data import ORDER_IDS

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(WIDTH, 7.0 * CM), layout="constrained")
    xs = list(range(len(ORDER_IDS)))
    off = {m: (i - (len(models) - 1) / 2) * 0.12 for i, m in enumerate(models)}
    for ax, metric, label in ((ax1, "csr", "Mean CSR, order arm (%)"), (ax2, "format", "FORMAT compliance, order arm (%)")):
        for m in models:
            st = STYLE[m]
            vals = [est(s, f"main.posthoc_r1.order_level.order.{m}.{cid}.{metric}") for cid in ORDER_IDS]
            means, los, his = zip(*vals)
            x = [v + off[m] for v in xs]
            ax.errorbar(x, means, yerr=[[a - b for a, b in zip(means, los)], [b - a for a, b in zip(means, his)]],
                        color=st["color"], ls=st["ls"], marker=st["marker"], ms=3, lw=0.9, capsize=1.2,
                        label=NAMES[m] if metric == "csr" else None)
        ax.set_xticks(xs, [olabel(c) for c in ORDER_IDS], rotation=90)
        ax.set_ylabel(label)
        ax.set_ylim(-3, 103)
    if note:
        ax2.text(0, note_y, note, fontsize=6.3, color="#555555", va="bottom")
    panel_label(ax1, "(a)")
    panel_label(ax2, "(b)")
    fig.legend(loc="outside lower center", ncol=4, frameon=False)
    return save(fig, out_dir, name)


FT_METRICS = (("format", "FORMAT", "main.order.{m}.compliance.format"), ("csr", "CSR", "main.order.{m}.csr"),
              ("pcr", "PCR", "main.order.{m}.pcr"))


FT_OPEN_KEY = "main.posthoc_r1.fence_tolerant.order.{m}.{metric}"
FT_LABELS = ("Filled: strict scoring (primary)", "Open: fence-tolerant reading (post-hoc)")


def fence_tolerant_values(s: dict, models: list[str], open_key: str | dict = FT_OPEN_KEY) -> dict:
    """{(metric, model, reading): (mean, ci_low, ci_high)} in %, order arm. Strict values are the primary keys; the
    open-marker values are read with ``open_key`` (default: the fence-tolerant keys of decision R1 §3.3). No value
    is computed here."""
    out = {}
    for metric, _, strict_key in FT_METRICS:
        for m in models:
            out[(metric, m, "strict")] = est(s, strict_key.format(m=m))
            pattern = open_key[metric] if isinstance(open_key, dict) else open_key
            out[(metric, m, "fence_tolerant")] = est(s, pattern.format(m=m, metric=metric))
    return out


def fig7_fence_tolerant(s: dict, models: list[str], out_dir: Path, name: str = "fig7_fence_tolerant",
                        open_key: str | dict = FT_OPEN_KEY, fill_labels: tuple[str, str] = FT_LABELS) -> list[Path]:
    """Decision GV §3.1 (post-hoc, presentation): strict (filled) versus fence-tolerant (open) FORMAT, CSR and PCR per
    model, order arm, 95% CIs. The title goes in the caption, as for every other figure."""
    from matplotlib.lines import Line2D

    vals = fence_tolerant_values(s, models, open_key)
    fig, ax = plt.subplots(figsize=(WIDTH, 7.0 * CM), layout="constrained")
    off = {m: (i - (len(models) - 1) / 2) * 0.2 for i, m in enumerate(models)}
    pair = 0.045
    for m in models:
        st = STYLE[m]
        for x, (metric, _, _) in enumerate(FT_METRICS):
            pts = []
            for reading, dx, face in (("strict", -pair, st["color"]), ("fence_tolerant", pair, "white")):
                mean, lo, hi = vals[(metric, m, reading)]
                ax.errorbar(x + off[m] + dx, mean, yerr=[[mean - lo], [hi - mean]], fmt=st["marker"], color=st["color"],
                            mfc=face, ms=4, capsize=1.5, lw=0.8)
                pts.append((x + off[m] + dx, mean))
            ax.plot(*zip(*pts), color=st["color"], lw=0.6, ls=st["ls"])
    ax.set_xticks(range(len(FT_METRICS)), [label for _, label, _ in FT_METRICS])
    ax.set_xlim(-0.5, len(FT_METRICS) - 0.5)
    ax.set_ylabel("Score, order arm (%)")
    ax.set_ylim(-3, 103)
    handles = [Line2D([], [], color=STYLE[m]["color"], marker=STYLE[m]["marker"], ls="none", ms=4) for m in models]
    labels = [NAMES[m] for m in models]
    handles += [Line2D([], [], color="#4D4D4D", marker="o", ls="none", ms=4),
                Line2D([], [], color="#4D4D4D", marker="o", mfc="white", ls="none", ms=4)]
    labels += list(fill_labels)
    fig.legend(handles, labels, loc="outside lower center", ncol=3, frameon=False)
    return save(fig, out_dir, name)


def main() -> int:
    setup()
    s = json.loads((RESULTS_DIR / "metrics" / "summary.json").read_text(encoding="utf-8"))
    models = s["_meta"]["models"]
    out = RESULTS_DIR / "figures"
    paths = (fig1_design(s, out) + fig2_compliance(s, models, out) + fig3_position(s, models, out)
             + fig4_noise_floor(s, models, out) + fig5_task_quality(s, models, out) + figR1_order_level(s, models, out)
             + fig7_fence_tolerant(s, models, out))
    print("Wrote " + ", ".join(p.name for p in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
