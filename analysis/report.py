"""Tables 2-5 (CSV + Markdown) and results/report/RESULTS_SUMMARY.md from the flat summary (implementation specification
§6.6-§6.7). Every number shown is read from a summary.json key; the key index at the end of RESULTS_SUMMARY.md
maps each one back (decision G3 §4 presentation rules included)."""

from __future__ import annotations

import csv
import itertools
from pathlib import Path

from analysis.data import CONSTRAINTS, FAMILIES, ORDER_IDS
from src.common import atomic_write_text, load_models
from src.evaluators.tags import TAG_ORDER

NAMES = {"smollm2": "SmolLM2-1.7B", "qwen25": "Qwen2.5-3B", "phi4mini": "Phi-4-mini", "gemma4e4b": "Gemma 4 E4B",
         "pooled": "Pooled"}
CNAMES = {"format": "FORMAT", "length": "LENGTH", "cardinality": "CARDINALITY", "t4": "NO_COMMA",
          "verbatim": "VERBATIM"}
FNAMES = {"F1_QA": "QA", "F2_CLASSIFICATION": "CLS", "F3_SUMMARIZATION": "SUM", "F4_EXTRACTION": "EXT",
          "F5_TRANSFORMATION": "TRF"}  # decision R1 (m8)


def olabel(cid: str) -> str:
    """Display label of an order (decision R1, m8): P01-P10 -> O01-O10; format variants keep V01-V10."""
    return "O" + cid[1:] if cid.startswith("P") else cid


def pct(x) -> str:
    return "n/a" if x is None or x != x else f"{100 * x:.1f}%"


def dec(x, d: int = 3) -> str:
    return "n/a" if x is None or x != x else f"{x:.{d}f}"


def pval(p) -> str:
    if p is None or p != p:
        return "n/a"
    return "< .001" if p < 0.001 else f"{p:.3f}".replace("0.", ".", 1)


class Writer:
    """Formats values from the summary and records every number it prints for the key index."""

    def __init__(self, s: dict) -> None:
        self.s = s
        self.index: list[tuple[str, str]] = []

    def v(self, key: str):
        return self.s.get(key)

    def num(self, key: str, kind: str = "pct") -> str:
        """kind: pct (percentage), p (p or q value), int, dec (3 decimals) or dec2 (2 decimals)."""
        x = self.s.get(key)
        if kind == "pct":
            text = pct(x)
        elif kind == "p":
            text = pval(x)
        elif kind == "int":
            text = "n/a" if x is None else str(int(x))
        else:
            text = dec(x, 2 if kind == "dec2" else 3)
        if x is not None:
            self.index.append((text, key))
        return text

    def peq(self, key: str) -> str:
        """'= .123' or '< .001' for use after p or q in a sentence."""
        text = self.num(key, "p")
        return text if text.startswith("<") or text == "n/a" else f"= {text}"

    def est(self, prefix: str, kind: str = "pct") -> str:
        """'63.4% [62.1%, 64.5%]' from prefix.mean / .ci_low / .ci_high."""
        m, lo, hi = (self.num(f"{prefix}.{k}", kind) for k in ("mean", "ci_low", "ci_high"))
        return f"{m} [{lo}, {hi}]"

    def cell(self, prefix: str, kind: str = "pct") -> str:
        f = pct if kind == "pct" else dec
        return f"{f(self.s.get(prefix + '.mean'))} [{f(self.s.get(prefix + '.ci_low'))}, {f(self.s.get(prefix + '.ci_high'))}]"


def _md_table(header: list[str], rows: list[list[str]], align: str | None = None) -> str:
    align = align or "|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|"
    return "\n".join(["| " + " | ".join(header) + " |", align] + ["| " + " | ".join(r) + " |" for r in rows])


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def zero_width_note(s: dict, prefixes: list[tuple[str, str]]) -> str:
    """Decision G4a §3.3a: name zero-width intervals (constant outcome within every family) with one example."""
    zero = [(label, p) for label, p in prefixes
            if s.get(p + ".ci_low") is not None and s.get(p + ".ci_low") == s.get(p + ".ci_high")]
    zero.sort(key=lambda lp: s.get(lp[1] + ".mean") in (0.0, 1.0))  # prefer an example strictly between 0 and 1
    for label, p in zero[:1]:
        lo, hi = s.get(p + ".ci_low"), s.get(p + ".ci_high")
        if True:
            return (" Zero-width intervals occur where the outcome is constant within every family, so the "
                    f"family-stratified bootstrap cannot vary it (e.g., {label}: {pct(s.get(p + '.mean'))} "
                    f"[{pct(lo)}, {pct(hi)}]).")
    return ""


def evaluable_note(s: dict, models: list[str]) -> str:
    """Decision G4a §3.3b: non-evaluable outputs score 0 on constraints 2-5 (brief §5.8)."""
    rates = ", ".join(f"{NAMES[m]} {pct(s.get(f'main.order.{m}.evaluable_rate.mean'))}" for m in models)
    sm = "main.order.smollm2.evaluable_rate_by_family."
    return (f" Evaluable outputs (a JSON object could be parsed), order arm: {rates}. Non-evaluable outputs score 0 on "
            "constraints 2-5 (brief §5.8); SmolLM2-1.7B's non-JSON outputs in F1 and F3 (evaluable "
            f"{pct(s.get(sm + 'F1_QA'))} and {pct(s.get(sm + 'F3_SUMMARIZATION'))}) explain much of its low CSR.")


def gemma_note(s: dict) -> str:
    return (f"Gemma 4 E4B's strict FORMAT score is driven by fenced JSON: it wrapped "
            f"{pct(s.get('main.exploratory.e5.order.gemma4e4b.code_fence'))} of its order-arm outputs and "
            f"{pct(s.get('main.exploratory.e5.format.gemma4e4b.code_fence'))} of its format-arm outputs in a ```json "
            f"fence (E5, descriptive), so its strict FORMAT compliance and PCR are 0 and its CSR is at most 0.8.")


# ---- Tables 2-5 ---------------------------------------------------------------------------------------
def tables(s: dict, models: list[str], out_dir: Path) -> dict[str, str]:
    names = models + ["pooled"]
    md = {}

    # Table 2
    cols = [("CSR", "main.order.{m}.csr", "pct"), ("PCR", "main.order.{m}.pcr", "pct"),
            ("PS_order", "main.order.{m}.ps", "dec"), ("PS_format", "main.format.{m}.ps", "dec"),
            ("VSR", "main.order.{m}.vsr", "pct"), ("Flip rate", "main.order.{m}.flip_rate", "pct")]
    w = Writer(s)
    rows = [[NAMES[m]] + [w.cell(k.format(m=m), kind) for _, k, kind in cols] for m in names]
    md["table2_main"] = ("Table 2. Main results by model (order arm unless stated; mean [95% CI], task-clustered "
                         "bootstrap).\n\n" + _md_table(["Model"] + [c for c, _, _ in cols], rows)
                         + "\n\nCSR, PCR, VSR and flip rate are proportions shown as percentages; PS is a difference "
                         "of CSR (0-1). " + gemma_note(s) + evaluable_note(s, models)
                         + zero_width_note(s, [(f"{NAMES[m]} {c}", k.format(m=m)) for m in names for c, k, _ in cols]))
    _write_csv(out_dir / "table2_main.csv", ["model", "metric", "mean", "ci_low", "ci_high", "key"],
               [[m, c, s.get(k.format(m=m) + ".mean"), s.get(k.format(m=m) + ".ci_low"), s.get(k.format(m=m) + ".ci_high"),
                 k.format(m=m)] for m in names for c, k, _ in cols])

    # Table 3
    rows, csv_rows = [], []
    for m in models:
        f, c = f"main.tests.friedman.{m}", f"main.tests.cochran_q.{m}"
        fr = ([f"{dec(s.get(f + '.chi2'), 1)} ({s.get(f + '.df')})", pval(s.get(f + ".p")), pval(s.get(f + ".q_bh")),
               dec(s.get(f + ".kendall_w"))] if s.get(f + ".status") == "estimated" else [s.get(f + ".status")] + [""] * 3)
        cq = ([f"{dec(s.get(c + '.q'), 1)} ({s.get(c + '.df')})", pval(s.get(c + ".p")), pval(s.get(c + ".q_bh"))]
              if s.get(c + ".status") == "estimated" else [s.get(c + ".status"), "", ""])
        rows.append([NAMES[m]] + fr + cq)
        csv_rows.append([m, s.get(f + ".status"), s.get(f + ".chi2"), s.get(f + ".df"), s.get(f + ".p"), s.get(f + ".q_bh"),
                         s.get(f + ".kendall_w"), s.get(c + ".status"), s.get(c + ".q"), s.get(c + ".df"), s.get(c + ".p"),
                         s.get(c + ".q_bh")])
    md["table3_order_tests"] = ("Table 3. Tests of systematic order effects across the 10 orders (P2; 100 tasks per "
                                "model). q = Benjamini-Hochberg across the four models, separately for each test.\n\n"
                                + _md_table(["Model", "Friedman χ² (df)", "p", "q", "Kendall's W", "Cochran's Q (df)", "p",
                                             "q"], rows) + "\n\n" + gemma_note(s))
    _write_csv(out_dir / "table3_order_tests.csv",
               ["model", "friedman_status", "friedman_chi2", "friedman_df", "friedman_p", "friedman_q", "kendall_w",
                "cochran_status", "cochran_q", "cochran_df", "cochran_p", "cochran_q_bh"], csv_rows)

    # Table 4
    parts, csv_rows, gee_rows = [], [], []
    gee_pooled = s.get("main.order.format_gee_sample_pooled_key")
    for c in CONSTRAINTS:
        rows = [[NAMES[m]] + [Writer(s).cell(f"main.order.{m}.position.{c}.{k}") for k in range(1, 6)] for m in names]
        if c == "format" and gee_pooled:
            rows.append(["Pooled, GEE sample (Gemma 4 E4B excluded)"]
                        + [Writer(s).cell(f"main.order.{gee_pooled}.position.format.{k}") for k in range(1, 6)])
            csv_rows += [[c, gee_pooled, k, s.get(f"main.order.{gee_pooled}.position.format.{k}.mean"),
                          s.get(f"main.order.{gee_pooled}.position.format.{k}.ci_low"),
                          s.get(f"main.order.{gee_pooled}.position.format.{k}.ci_high"),
                          f"main.order.{gee_pooled}.position.format.{k}"] for k in range(1, 6)]
        csv_rows += [[c, m, k, s.get(f"main.order.{m}.position.{c}.{k}.mean"), s.get(f"main.order.{m}.position.{c}.{k}.ci_low"),
                      s.get(f"main.order.{m}.position.{c}.{k}.ci_high"), f"main.order.{m}.position.{c}.{k}"]
                     for m in names for k in range(1, 6)]
        p = f"main.p1.{c}"
        excl = s.get(p + ".excluded_models") or {}
        excl_text = ("; excluded for constant compliance: " + ", ".join(f"{NAMES[m]} ({pct(r)})" for m, r in excl.items())
                     if excl else "")
        if s.get(p + ".status") == "estimated":
            gw = Writer(s)
            gee = (f"GEE (P1): Wald χ²({s.get(p + '.df')}) = {dec(s.get(p + '.wald_chi2'), 2)}, p {gw.peq(p + '.p')}, "
                   f"q {gw.peq(p + '.q')}{excl_text}.")
        else:
            gee = f"GEE (P1): {s.get(p + '.status')} ({s.get(p + '.reason')}){excl_text}."
        parts.append(f"**{CNAMES[c]}**\n\n" + _md_table(["Model", "Position 1", "2", "3", "4", "5"], rows) + "\n\n" + gee)
        gee_rows.append([c, s.get(p + ".status"), s.get(p + ".wald_chi2"), s.get(p + ".df"), s.get(p + ".p"), s.get(p + ".q"),
                         ";".join(f"{m}={r}" for m, r in excl.items()), s.get(p + ".reason", "")]
                        + [s.get(f"{p}.or.{k}.{x}") for k in range(2, 6) for x in ("estimate", "ci_low", "ci_high")])
    md["table4_position"] = ("Table 4. Observed compliance by instruction and position (order arm; mean [95% CI], "
                             "task-clustered bootstrap), pooled over models and per model, with the GEE Wald test of "
                             "position (P1; q = Benjamini-Hochberg across the five instructions).\n\n"
                             + "\n\n".join(parts) + "\n\n" + gemma_note(s)
                             + zero_width_note(s, [(f"{NAMES[m]} {CNAMES[c]} at position {k}", f"main.order.{m}.position.{c}.{k}")
                                                   for c in CONSTRAINTS for m in names for k in range(1, 6)]))
    _write_csv(out_dir / "table4_position.csv", ["instruction", "model", "position", "mean", "ci_low", "ci_high", "key"],
               csv_rows)
    _write_csv(out_dir / "table4_position_gee.csv",
               ["instruction", "status", "wald_chi2", "df", "p", "q", "excluded_models", "reason"]
               + [f"or_pos{k}_{x}" for k in range(2, 6) for x in ("estimate", "ci_low", "ci_high")], gee_rows)

    # Table 5
    q_rows = [[FNAMES[f]] + [Writer(s).cell(f"main.quality.{f}.{m}.q", "dec") for m in models] for f in FAMILIES]
    t_rows = [[FNAMES[f]] + [Writer(s).cell(f"main.quality.{f}.{m}.tqs", "dec") for m in models] for f in FAMILIES]
    md["table5_quality"] = ("Table 5. Task quality by family and model (order arm; mean [95% CI], bootstrap within "
                            "the family's 20 tasks). Q: F1 whole-token containment, F2 label accuracy, F3 ROUGE-L F1, "
                            "F4/F5 field accuracy, all on a 0-1 scale; Q = 0 when no answer can be parsed. Never averaged "
                            "across families.\n\n"
                            "Mean Q\n\n" + _md_table(["Family"] + [NAMES[m] for m in models], q_rows)
                            + "\n\nTQS (max Q − min Q over the 10 orders, per task)\n\n"
                            + _md_table(["Family"] + [NAMES[m] for m in models], t_rows))
    _write_csv(out_dir / "table5_quality.csv", ["family", "model", "quantity", "mean", "ci_low", "ci_high", "key"],
               [[f, m, q, s.get(f"main.quality.{f}.{m}.{q}.mean"), s.get(f"main.quality.{f}.{m}.{q}.ci_low"),
                 s.get(f"main.quality.{f}.{m}.{q}.ci_high"), f"main.quality.{f}.{m}.{q}"]
                for f in FAMILIES for m in models for q in ("q", "tqs")])
    md.update(post_hoc_tables(s, models, out_dir))
    md.update(appendix_tables(s, models, out_dir))
    from analysis.report_r1 import tables_r1  # decision R1 §3

    md.update(tables_r1(s, models, out_dir))
    for name, text in md.items():
        atomic_write_text(out_dir / f"{name}.md", text + "\n")
    return md


def post_hoc_tables(s: dict, models: list[str], out_dir: Path) -> dict[str, str]:
    """Decision G4a §3.1-§3.2: option B (Table 4b) and constraint-level instability, both labelled post-hoc."""
    md = {}
    rows, csv_rows = [], []
    for c in CONSTRAINTS:
        p = f"main.robustness.p1_independence.{c}"
        excl = s.get(p + ".excluded_models") or {}
        fam = s.get(p + ".excluded_families") or {}
        left_out = "; ".join([f"{NAMES[m]} (constant, {pct(r)})" for m, r in excl.items()]
                             + [f"{FNAMES[f]} (constant across included models, {pct(r)})" for f, r in fam.items()]) or "none"
        if s.get(p + ".status") == "estimated":
            gw = Writer(s)
            ors = "; ".join(f"{k}: {dec(s.get(f'{p}.or.{k}.estimate'), 2)} [{dec(s.get(f'{p}.or.{k}.ci_low'), 2)}, "
                            f"{dec(s.get(f'{p}.or.{k}.ci_high'), 2)}]" for k in range(2, 6))
            rows.append([CNAMES[c], f"{dec(s.get(p + '.wald_chi2'), 2)} ({s.get(p + '.df')})", pval(s.get(p + ".p")),
                         pval(s.get(p + ".q")), ors, left_out, str(s.get(p + ".n"))])
        else:
            rows.append([CNAMES[c], f"{s.get(p + '.status')} ({s.get(p + '.reason')})", "", "", "", left_out, str(s.get(p + ".n"))])
        csv_rows.append([c, s.get(p + ".status"), s.get(p + ".wald_chi2"), s.get(p + ".df"), s.get(p + ".p"), s.get(p + ".q"),
                         ";".join(f"{m}={r}" for m, r in excl.items()), ";".join(f"{f}={r}" for f, r in fam.items()),
                         s.get(p + ".n"), s.get(p + ".reason", "")]
                        + [s.get(f"{p}.or.{k}.{x}") for k in range(2, 6) for x in ("estimate", "ci_low", "ci_high")])
    md["table4b_position_gee_independence"] = (
        "Table 4b. **Post-hoc robustness analysis** (decision G4a §2.1; not a pre-specified test): the P1 mean model "
        "`pass ~ C(position) + C(model) + C(family)`, groups = task, with an independence working correlation and robust "
        "(sandwich) standard errors. Models and family levels with constant compliance were left out mechanically before "
        "fitting. q = Benjamini-Hochberg across the five instructions (its own family). The pre-specified result is "
        "Table 4.\n\n" + _md_table(["Instruction", "Wald χ² (df)", "p", "q", "OR vs position 1 (positions 2-5) [95% CI]",
                                     "Left out before fitting", "n"], rows))
    _write_csv(out_dir / "table4b_position_gee_independence.csv",
               ["instruction", "status", "wald_chi2", "df", "p", "q", "excluded_models", "excluded_families", "n", "reason"]
               + [f"or_pos{k}_{x}" for k in range(2, 6) for x in ("estimate", "ci_low", "ci_high")], csv_rows)

    names = models + ["pooled"]
    rows, csv_rows = [], []
    for arm in ("order", "format"):
        for m in names:
            rows.append([f"{NAMES[m]}, {arm} arm"] + [Writer(s).cell(f"main.robustness.constraint_instability.{arm}.{m}.{c}")
                                                    for c in CONSTRAINTS])
            csv_rows += [[arm, m, c] + [s.get(f"main.robustness.constraint_instability.{arm}.{m}.{c}.{x}")
                                         for x in ("mean", "ci_low", "ci_high")] for c in CONSTRAINTS]
    md["tableA_constraint_instability"] = (
        "Table A3. **Post-hoc, descriptive** (decision G4a §3.2): constraint-level instability, the share of tasks whose "
        "flag for a constraint is not constant across the arm's 10 prompts (mean [95% CI], task-clustered bootstrap). A "
        "constraint that never varies cannot contribute to PS, so a model with several (near-)constant constraints has a "
        "mechanically bounded PS.\n\n" + _md_table(["Model, arm"] + [CNAMES[c] for c in CONSTRAINTS], rows)
        + "\n\n" + gemma_note(s))
    _write_csv(out_dir / "tableA_constraint_instability.csv", ["arm", "model", "constraint", "mean", "ci_low", "ci_high"],
               csv_rows)
    return md


def appendix_tables(s: dict, models: list[str], out_dir: Path) -> dict[str, str]:
    """Table 1 (models) and the appendix tables of the implementation specification §6.6: error tags and robustness."""
    md = {}
    specs = load_models()["models"]
    rows, csv_rows = [], []
    notes = {"smollm2": "official template; system role native", "qwen25": "official template; system role native",
             "phi4mini": "official template; system role native; Hub remote code never used",
             "gemma4e4b": "official template; native system turn; thinking disabled (enable_thinking=False)"}
    for m in models:
        sp = specs[m]
        params = sp.get("parameters_effective") or sp.get("parameters_nominal") or ""
        total = sp.get("parameters_safetensors")
        rows.append([NAMES[m], f"`{sp['hf_id']}`", f"{params}" + (f"; {total:,} stored" if total else ""), sp["license"],
                     f"`{sp['revision'][:12]}`", notes[m]])
        csv_rows.append([m, sp["hf_id"], params, total, sp["license"], sp["revision"], sp["chat_template_sha256"], notes[m]])
    md["table1_models"] = ("Table 1. Models (pinned revisions; bf16, greedy decoding, batch size 1 in the main run).\n\n"
                           + _md_table(["Model", "Hugging Face id", "Parameters", "License", "Revision", "Chat template"],
                                       rows, "|---|---|---|---|---|---|"))
    _write_csv(out_dir / "table1_models.csv", ["model", "hf_id", "parameters", "parameters_stored", "license", "revision",
                                               "chat_template_sha256", "chat_template_note"], csv_rows)

    rows, csv_rows = [], []
    for tag in TAG_ORDER:
        rows.append([tag] + [pct(s.get(f"main.exploratory.e5.{arm}.{m}.{tag}")) for m in models for arm in ("order", "format")])
        csv_rows += [[tag, m, arm, s.get(f"main.exploratory.e5.{arm}.{m}.{tag}")] for m in models for arm in ("order", "format")]
    md["tableA_errors"] = ("Table A1. Error-tag rates by model and arm (share of the 1,000 outputs per model and arm; E5, "
                           "exploratory).\n\n" + _md_table(["Tag"] + [f"{NAMES[m]} {a}" for m in models for a in ("order", "format")],
                                                            rows) + "\n\n" + gemma_note(s))
    _write_csv(out_dir / "tableA_errors.csv", ["tag", "model", "arm", "rate"], csv_rows)

    rows, csv_rows = [], []
    for m in models:
        cs, st_ = f"main.robustness.cascade.order.{m}", f"main.robustness.strict_format.order.{m}"
        p3 = f"main.robustness.cascade.p3.{m}"
        strict = (f"{Writer(s).cell(st_ + '.csr')} (n = {s.get(st_ + '.n_outputs')})" if s.get(st_ + ".csr.mean") is not None
                  else str(s.get(st_ + ".status")))
        strict_pcr = Writer(s).cell(st_ + ".pcr") if s.get(st_ + ".pcr.mean") is not None else "n/a"
        p3txt = (f"{dec(s.get(p3 + '.mean_diff'))} [{dec(s.get(p3 + '.ci_low'))}, {dec(s.get(p3 + '.ci_high'))}], p "
                 f"{pval(s.get(p3 + '.p'))}" if s.get(p3 + ".status") == "estimated" else str(s.get(p3 + ".status")))
        rows.append([NAMES[m], Writer(s).cell(cs + ".csr"), Writer(s).cell(cs + ".pcr"), Writer(s).cell(cs + ".ps", "dec"), p3txt,
                     strict, strict_pcr])
        csv_rows.append([m] + [s.get(f"{cs}.{q}.{x}") for q in ("csr", "pcr", "ps") for x in ("mean", "ci_low", "ci_high")]
                        + [s.get(p3 + ".mean_diff"), s.get(p3 + ".p"), s.get(st_ + ".n_outputs")]
                        + [s.get(f"{st_}.{q}.{x}") for q in ("csr", "pcr") for x in ("mean", "ci_low", "ci_high")])
    p1 = "; ".join(f"{CNAMES[c]}: " + (f"χ²({s.get(f'main.robustness.cascade.p1.{c}.df')}) = "
                                       f"{dec(s.get(f'main.robustness.cascade.p1.{c}.wald_chi2'), 2)}, p "
                                       f"{pval(s.get(f'main.robustness.cascade.p1.{c}.p'))}"
                                       if s.get(f"main.robustness.cascade.p1.{c}.status") == "estimated"
                                       else str(s.get(f"main.robustness.cascade.p1.{c}.status"))) for c in CONSTRAINTS)
    md["tableA_robustness"] = ("Table A2. Robustness (E6, exploratory; order arm): cascade scoring (no strict FORMAT pass → "
                               "all five constraints score 0) and the subset of outputs that pass FORMAT strictly.\n\n"
                               + _md_table(["Model", "Cascade CSR", "Cascade PCR", "Cascade PS_order",
                                            "Cascade PS_order − PS_format", "Strict-FORMAT CSR", "Strict-FORMAT PCR"], rows)
                               + f"\n\nCascade P1 GEE (pre-specified estimator): {p1}.\n\n" + gemma_note(s))
    _write_csv(out_dir / "tableA_robustness.csv",
               ["model"] + [f"cascade_{q}_{x}" for q in ("csr", "pcr", "ps") for x in ("mean", "ci_low", "ci_high")]
               + ["cascade_p3_mean_diff", "cascade_p3_p", "strict_n_outputs"]
               + [f"strict_{q}_{x}" for q in ("csr", "pcr") for x in ("mean", "ci_low", "ci_high")], csv_rows)
    return md


# ---- RESULTS_SUMMARY.md ----------------------------------------------------------------------------------
def results_summary(s: dict, models: list[str], meta: dict, md_tables: dict[str, str]) -> str:
    w = Writer(s)
    L: list[str] = []
    a = L.append
    a("# RESULTS_SUMMARY — main run")
    a("")
    a(f"Run `{meta['run_id']}`; analysis plan frozen at tag `{meta['analysis_plan_tag']}`; bootstrap {meta['n_boot']} "
      f"replicates, seed {meta['seed']}; generated {meta['generated_utc']}. Every number below is a key of "
      "`results/metrics/summary.json` (key index at the end). Proportions are shown as percentages with one decimal, "
      "95% CIs in brackets (task-clustered bootstrap, percentile), p to three decimals or \"< .001\"; q = "
      "Benjamini-Hochberg within the families of ANALYSIS_PLAN §7. Model differences are descriptive of these four "
      "models and are not attributed to size or family (D06 §5).")
    a("")
    a("**Reading note (decision G3 §4).** " + gemma_note(s))
    a("")
    a("## Data")
    a("")
    a(f"{w.num('main.counts.evaluation_records', 'int')} evaluation records: {w.num('main.counts.tasks', 'int')} tasks × "
      f"{w.num('main.counts.models', 'int')} models × 20 prompt ids (order arm O01-O10 = data ids P01-P10, format arm V01-V10; O01 and V01 "
      "share one generation). All outputs were generated at batch size 1 (decision G2). Outputs at the length limit: "
      + ", ".join(f"{NAMES[m]} {w.num(f'main.counts.{m}.truncated_rate')}" for m in models) + ". Evaluable outputs (a "
      "JSON object could be parsed), order arm: " + ", ".join(f"{NAMES[m]} {w.est(f'main.order.{m}.evaluable_rate')}"
                                                             for m in models)
      + ". Non-evaluable outputs score 0 on constraints 2-5 (brief §5.8); SmolLM2-1.7B's non-JSON outputs in F1 and F3 "
      f"(evaluable {w.num('main.order.smollm2.evaluable_rate_by_family.F1_QA')} and "
      f"{w.num('main.order.smollm2.evaluable_rate_by_family.F3_SUMMARIZATION')}) explain much of its low CSR.")
    a("")

    # RQ1
    a("## RQ1 — Do orders change compliance systematically? (P2, S1)")
    a("")
    a(md_tables["table3_order_tests"].split("\n\n", 1)[1].rsplit("\n\n", 1)[0])
    a("")
    for m in models:
        f, c = f"main.tests.friedman.{m}", f"main.tests.cochran_q.{m}"
        if s.get(f + ".status") == "estimated":
            a(f"- {NAMES[m]}: Friedman χ²({w.num(f + '.df', 'int')}) = {w.num(f + '.chi2', 'dec2')}, p "
              f"{w.peq(f + '.p')}, q {w.peq(f + '.q_bh')}, Kendall's W = {w.num(f + '.kendall_w', 'dec')} (CSR across "
              "the 10 orders).")
        else:
            a(f"- {NAMES[m]}: Friedman test: {s.get(f + '.status')}.")
        if s.get(c + ".status") == "estimated":
            a(f"- {NAMES[m]}: Cochran's Q({w.num(c + '.df', 'int')}) = {w.num(c + '.q', 'dec2')}, p {w.peq(c + '.p')}, q "
              f"{w.peq(c + '.q_bh')} (PCR across the 10 orders).")
        else:
            a(f"- {NAMES[m]}: Cochran's Q test of PCR: {s.get(c + '.status')} (PCR "
              f"{w.num(f'main.order.{m}.pcr.mean')} in every order).")
    a("")
    a("Task-level sensitivity (S1):")
    a("")
    a(md_tables["table2_main"].split("\n\n", 1)[1].rsplit("\n\n", 1)[0])
    a("")
    for m in models + ["pooled"]:
        a(f"- {NAMES[m]}: PS_order {w.est(f'main.order.{m}.ps', 'dec')}, PS_format {w.est(f'main.format.{m}.ps', 'dec')}; "
          f"VSR order {w.est(f'main.order.{m}.vsr')}, format {w.est(f'main.format.{m}.vsr')}; flip rate order "
          f"{w.est(f'main.order.{m}.flip_rate')}, format {w.est(f'main.format.{m}.flip_rate')}.")
    a("")

    # RQ2
    a("## RQ2 — Does an instruction's position change its compliance? (P1)")
    a("")
    a("The primary display is the observed compliance by position (Table 4, decision D05 §1); the GEE supplies the "
      "Wald test and odds ratios when it is estimable. A GEE that fails to converge or shows separation is reported as "
      "not estimable, and the bootstrap descriptives are relied on (ANALYSIS_PLAN §8).")
    a("")
    for c in CONSTRAINTS:
        p = f"main.p1.{c}"
        excl = s.get(p + ".excluded_models") or {}
        ex = ("; " + ", ".join(f"{NAMES[m]} excluded for constant compliance ({w.num(f'main.order.{m}.compliance.{c}.mean')})"
                               for m in excl)) if excl else ""
        if s.get(p + ".status") == "estimated":
            ors = "; ".join(f"position {k}: OR {w.num(f'{p}.or.{k}.estimate', 'dec2')} [{w.num(f'{p}.or.{k}.ci_low', 'dec2')}, "
                            f"{w.num(f'{p}.or.{k}.ci_high', 'dec2')}]" for k in range(2, 6))
            a(f"- {CNAMES[c]}: GEE Wald χ²({w.num(p + '.df', 'int')}) = {w.num(p + '.wald_chi2', 'dec2')}, p {w.peq(p + '.p')}, "
              f"q {w.peq(p + '.q')}{ex}. Odds ratios against position 1: {ors}.")
        else:
            a(f"- {CNAMES[c]}: GEE {s.get(p + '.status')} ({s.get(p + '.reason')}){ex}.")
        pooled = [(k, s.get(f"main.order.pooled.position.{c}.{k}.mean")) for k in range(1, 6)]
        lo_k = min(pooled, key=lambda t: t[1])[0]
        hi_k = max(pooled, key=lambda t: t[1])[0]
        a(f"  Observed pooled compliance ranged from {w.est(f'main.order.pooled.position.{c}.{lo_k}')} at position {lo_k} to "
          f"{w.est(f'main.order.pooled.position.{c}.{hi_k}')} at position {hi_k}.")
    a("")
    a("A post-hoc robustness analysis with an independence working correlation (decision G4a §2.1) is reported "
      "separately under \"Post-hoc analyses\" (Table 4b); it is not a pre-specified test.")
    a("")
    a(md_tables["table4_position"].split("\n\n", 1)[1].rsplit("\n\n", 1)[0])
    a("")

    # RQ3
    a("## RQ3 — Do the models differ? (S2; descriptive of these four models)")
    a("")
    for metric, label in (("ps", "mean PS_order"), ("csr", "mean CSR (order arm)")):
        for x, y in itertools.combinations(models, 2):
            p = f"main.s2.{x}_vs_{y}.{metric}_diff"
            a(f"- {label}, {NAMES[x]} − {NAMES[y]}: {w.est(p, 'dec' if metric == 'ps' else 'pct')}, bootstrap p "
              f"{w.peq(p + '.p')}, q {w.peq(p + '.q')}.")
    a("")
    for c in CONSTRAINTS:
        p = f"main.s2.interaction.{c}"
        if s.get(p + ".status") == "estimated":
            a(f"- Position × model interaction, {CNAMES[c]}: Wald χ²({w.num(p + '.df', 'int')}) = {w.num(p + '.wald_chi2', 'dec2')}, "
              f"p {w.peq(p + '.p')}, q {w.peq(p + '.q')}.")
        else:
            a(f"- Position × model interaction, {CNAMES[c]}: {s.get(p + '.status')} ({s.get(p + '.reason')}).")
    a("")

    ci = "main.robustness.constraint_instability.order"
    others = [m for m in models if m != "gemma4e4b"]

    def other_range(c: str) -> str:
        vals = sorted(others, key=lambda m: s.get(f"{ci}.{m}.{c}.mean"))
        return f"{w.num(f'{ci}.{vals[0]}.{c}.mean')}-{w.num(f'{ci}.{vals[-1]}.{c}.mean')}"

    a("Gemma 4 E4B's lower PS_order has two sources (Table A3; post-hoc and descriptive, the comparison is not "
      "tested, decision G4b §2.2): (i) three of its constraints are (near-)constant: its FORMAT, LENGTH and NO_COMMA flags "
      "vary across the 10 orders in " + ", ".join(f"{w.num(f'{ci}.gemma4e4b.{c}.mean')}" for c in ("format", "length", "t4"))
      + " of its tasks, which bounds its PS mechanically; (ii) on the two constraints that vary for every model, its "
      f"instability is also lower: CARDINALITY {w.num(f'{ci}.gemma4e4b.cardinality.mean')} against "
      f"{other_range('cardinality')} for the other models, VERBATIM {w.num(f'{ci}.gemma4e4b.verbatim.mean')} against "
      f"{other_range('verbatim')}; for CARDINALITY this holds at a base rate similar to Phi-4-mini's (compliance "
      f"{w.num('main.order.gemma4e4b.compliance.cardinality.mean')} against "
      f"{w.num('main.order.phi4mini.compliance.cardinality.mean')}).")
    a("")

    # RQ4
    a("## RQ4 — Is reordering more disruptive than reformatting? (P3)")
    a("")
    for m in models:
        p = f"main.p3.{m}"
        test = (f"Wilcoxon signed-rank statistic {w.num(p + '.wilcoxon_stat', 'dec2')}, p {w.peq(p + '.p')}, q "
                f"{w.peq(p + '.q')}" if s.get(p + ".status") == "estimated" else s.get(p + ".status"))
        a(f"- {NAMES[m]}: mean PS_order − PS_format = {w.num(p + '.mean_diff', 'dec')} [{w.num(p + '.ci_low', 'dec')}, "
          f"{w.num(p + '.ci_high', 'dec')}] over {w.num(p + '.n', 'int')} tasks ({w.num(p + '.n_pos', 'int')} positive, "
          f"{w.num(p + '.n_neg', 'int')} negative, {w.num(p + '.n_zero', 'int')} zero); {test}.")
    a("")

    # S3
    a("## Task quality (S3)")
    a("")
    a(md_tables["table5_quality"].split("\n\n", 1)[1])
    a("")

    # Exploratory
    a("## Exploratory analyses (E1-E6; no confirmatory claims, no adjustment)")
    a("")
    a("**E1 — instruction-type groups** (structural: FORMAT, CARDINALITY; answer-level: LENGTH, NO_COMMA; content: VERBATIM; key name `lexical`), "
      "pooled over models:")
    a("")
    for g in ("structural", "lexical", "content"):  # display: "lexical" is the answer-level group (decision R1, m7)
        a(f"- {g}: " + "; ".join(f"position {k} {w.est(f'main.exploratory.e1.{g}.pooled.{k}')}" for k in range(1, 6)) + ".")
    a("")
    a("**E2 — instructions placed before FORMAT** (compliance when the instruction precedes FORMAT minus when it "
      "follows, within the positions where both occur; for NO_COMMA and VERBATIM only position 3 informs the contrast):")
    a("")
    for c in ("length", "cardinality", "t4", "verbatim"):
        a(f"- {CNAMES[c]} (positions {s.get(f'main.exploratory.e2.{c}.informative_positions')}): pooled "
          f"{w.est(f'main.exploratory.e2.{c}.pooled.diff')}; " + "; ".join(
              f"{NAMES[m]} {w.est(f'main.exploratory.e2.{c}.{m}.diff')}" for m in models) + ".")
    a("")
    a("**E3 — hard-to-easy order index** (difficulty from the batch-1 order-arm pilot outputs, decision G2 §2.3). The "
      "Williams design was not built to vary HE, and 10 orders give it a limited range.")
    a("")
    for m in models:
        p = f"main.exploratory.e3.{m}"
        diff = ", ".join(f"{CNAMES[c]} {w.num(f'{p}.difficulty.{c}', 'dec2')}" for c in CONSTRAINTS)
        parts = []
        for outcome in ("csr", "pcr"):
            k = f"{p}.he_vs_{outcome}"
            parts.append(f"ρ(HE, order-level {outcome.upper()}) = {w.num(k + '.rho', 'dec2')} [{w.num(k + '.ci_low', 'dec2')}, "
                         f"{w.num(k + '.ci_high', 'dec2')}]" if s.get(k + ".status") == "estimated"
                         else f"ρ(HE, order-level {outcome.upper()}): {s.get(k + '.status')}")
        a(f"- {NAMES[m]}: difficulties {diff}; " + "; ".join(parts) + ".")
    a("")
    a("**E4 — task-quality impact**: Spearman ρ between TQS and PS_order across the 20 tasks of each family:")
    a("")
    rows = [[FNAMES[f]] + [w.num(f"main.exploratory.e4.{f}.{m}.rho_tqs_ps", "dec2") if s.get(f"main.exploratory.e4.{f}.{m}.status")
                           == "estimated" else "n/a" for m in models] for f in FAMILIES]
    a(_md_table(["Family"] + [NAMES[m] for m in models], rows))
    a("")
    a("**E5 — error taxonomy** (share of outputs with each tag; order arm):")
    a("")
    tags = ("code_fence", "invalid_json", "leading_text", "trailing_text", "extra_keys", "missing_evidence", "evidence_count_1",
            "evidence_count_3plus", "evidence_not_verbatim", "evidence_duplicate", "truncated")
    a(_md_table(["Tag"] + [NAMES[m] for m in models],
                [[t] + [w.num(f"main.exploratory.e5.order.{m}.{t}") for m in models] for t in tags]))
    a("")
    a("Comma spill-over into the evidence spans (exploratory, descriptive; decision G4b §2.1, Q-C2): share of "
      "non-verbatim evidence items that are comma-only, order arm: " + "; ".join(
          f"{NAMES[m]} {w.est(f'main.exploratory.e5.order.{m}.evidence_comma_only.items')} "
          f"({w.num(f'main.exploratory.e5.order.{m}.evidence_comma_only.n_items_comma_only', 'int')} of "
          f"{w.num(f'main.exploratory.e5.order.{m}.evidence_comma_only.n_items_not_verbatim', 'int')})" for m in models)
      + ". " + str(s.get("main.exploratory.e5.evidence_comma_only.procedure")))
    a("")
    a("Non-JSON outputs (`invalid_json`) by family, order arm (Q-C3):")
    a("")
    a(_md_table(["Family"] + [NAMES[m] for m in models],
                [[FNAMES[f]] + [w.num(f"main.exploratory.e5.order.{m}.by_family.invalid_json.{f}") for m in models]
                 for f in FAMILIES]))
    a("")
    a("**E6 — robustness** (cascade scoring: no strict FORMAT pass → all five constraints score 0; strict-FORMAT "
      "subset: only outputs that pass FORMAT strictly):")
    a("")
    for m in models:
        cs = f"main.robustness.cascade.order.{m}"
        st_ = f"main.robustness.strict_format.order.{m}"
        strict = (f"strict-FORMAT subset CSR {w.est(st_ + '.csr')} over {w.num(st_ + '.n_outputs', 'int')} outputs"
                  if s.get(st_ + ".csr.mean") is not None else f"strict-FORMAT subset: {s.get(st_ + '.status')}")
        a(f"- {NAMES[m]}: cascade CSR {w.est(cs + '.csr')}, cascade PS_order {w.est(cs + '.ps', 'dec')}; {strict}.")
    for m in models:
        p = f"main.robustness.cascade.p3.{m}"
        test = (f"p {w.peq(p + '.p')}" if s.get(p + ".status") == "estimated" else s.get(p + ".status"))
        a(f"- Cascade P3, {NAMES[m]}: mean PS_order − PS_format = {w.num(p + '.mean_diff', 'dec')} "
          f"[{w.num(p + '.ci_low', 'dec')}, {w.num(p + '.ci_high', 'dec')}]; {test}.")
    for c in CONSTRAINTS:
        p = f"main.robustness.cascade.p1.{c}"
        a(f"- Cascade P1, {CNAMES[c]}: {s.get(p + '.status')}"
          + (f", Wald χ²({w.num(p + '.df', 'int')}) = {w.num(p + '.wald_chi2', 'dec2')}, p {w.peq(p + '.p')}"
             if s.get(p + ".status") == "estimated" else f" ({s.get(p + '.reason')})") + ".")
    a("- Diagnostics: VERBATIM under the former 3-token rule (`verbatim_min3`), order arm: " + "; ".join(
        f"{NAMES[m]} {w.est(f'main.robustness.diagnostics.order.{m}.verbatim_min3')}" for m in models)
      + ". F1 character-level containment (`containment_char`): " + "; ".join(
        f"{NAMES[m]} {w.est(f'main.robustness.diagnostics.order.{m}.f1_containment_char')}" for m in models) + ".")
    a("")

    # Post-hoc
    a("## Post-hoc analyses (decision G4a; labelled post-hoc, not pre-specified)")
    a("")
    a("**Option B — P1 with an independence working correlation** (robustness analysis; same mean model and clusters "
      "as P1, robust SEs; constant models and constant family levels left out mechanically before fitting; q across "
      "the five instructions as its own family):")
    a("")
    for c in CONSTRAINTS:
        p = f"main.robustness.p1_independence.{c}"
        excl = list((s.get(p + ".excluded_models") or {}).items())
        fam = list((s.get(p + ".excluded_families") or {}).items())
        for m, r in excl:
            w.index.append((pct(r), f"{p}.excluded_models"))
        left = "; ".join([f"{NAMES[m]} left out (constant, {pct(r)})" for m, r in excl]
                         + [f"{FNAMES[f]} left out (constant across the included models, {pct(r)})" for f, r in fam])
        if s.get(p + ".status") == "estimated":
            ors = "; ".join(f"position {k}: {w.num(f'{p}.or.{k}.estimate', 'dec2')} [{w.num(f'{p}.or.{k}.ci_low', 'dec2')}, "
                            f"{w.num(f'{p}.or.{k}.ci_high', 'dec2')}]" for k in range(2, 6))
            a(f"- {CNAMES[c]}: Wald χ²({w.num(p + '.df', 'int')}) = {w.num(p + '.wald_chi2', 'dec2')}, p {w.peq(p + '.p')}, "
              f"q {w.peq(p + '.q')} (n = {w.num(p + '.n', 'int')}{'; ' + left if left else ''}). Odds ratios against "
              f"position 1: {ors}.")
        else:
            a(f"- {CNAMES[c]}: {s.get(p + '.status')} ({s.get(p + '.reason')}).")
    a("")
    a("**Constraint-level instability** (descriptive): share of tasks whose flag is not constant across the arm's 10 "
      "prompts, order arm:")
    a("")
    a(_md_table(["Model"] + [CNAMES[c] for c in CONSTRAINTS],
                [[NAMES[m]] + [w.est(f"main.robustness.constraint_instability.order.{m}.{c}") for c in CONSTRAINTS]
                 for m in models + ["pooled"]]))
    a("")

    from analysis.report_r1 import summary_section_r1  # decision R1

    L.extend(summary_section_r1(s, models, w))

    # Method validation
    a("## Method validation (technical checks; not results)")
    a("")
    a("- A1 run-to-run determinism (smoke, two passes): byte-identical for " + ", ".join(
        f"{NAMES[m]} {'yes' if s.get(f'checks.a1.{m}.byte_identical') else 'NO'}" for m in models) + ".")
    a("- A3 batch invariance (pilot, three original models): below the pre-specified 98% rule, so all main outputs were "
      "generated at batch size 1 (decision G2).")
    a("- A6 determinism at batch size 1 (start of each model's main run): byte-identical to the batch-1 pilot for " + ", ".join(
        f"{NAMES[m]} {'yes' if s.get(f'checks.a6.{m}.byte_identical') else 'NO'}" for m in models) + "; one environment per "
      "model (" + ", ".join(sorted({str(s.get(f'checks.environment.{m}.gpu_name')) for m in models})) + ").")
    a("- Analysis software: Python " + str(s.get("checks.software.analysis.python")) + ", " + ", ".join(
        f"{lab} {s.get(f'checks.software.analysis.{pkg}')}" for pkg, lab in (
            ("numpy", "NumPy"), ("scipy", "SciPy"), ("statsmodels", "statsmodels"), ("pandas", "pandas"),
            ("pyarrow", "pyarrow"), ("matplotlib", "Matplotlib"))) + ".")
    a("")

    # Caveats
    a("## Anomalies and caveats")
    a("")
    for line in meta["caveats"]:
        a(f"- {line}")
    a("")

    # Key index
    a("## Key index")
    a("")
    a("Tables: Table 2 `main.<arm>.<model>.{csr,pcr,ps,vsr,flip_rate}.{mean,ci_low,ci_high}`; Table 3 "
      "`main.tests.friedman.<model>.{chi2,df,p,q_bh,kendall_w}` and `main.tests.cochran_q.<model>.{q,df,p,q_bh}` (here "
      "`.q` is Cochran's statistic and `.q_bh` the Benjamini-Hochberg value); Table 4 "
      "`main.order.<model>.position.<c>.<k>.{mean,ci_low,ci_high}` and `main.p1.<c>.{status,wald_chi2,df,p,q,excluded_models,"
      "reason,or.<k>.*}` (FORMAT GEE-sample row: `main.order.pooled_excl_gemma4e4b.position.format.<k>.*`); Table 4b "
      "(post-hoc) `main.robustness.p1_independence.<c>.{status,wald_chi2,df,p,q,n,excluded_models,excluded_families,"
      "or.<k>.*}`; Table 5 `main.quality.<family>.<model>.{q,tqs}.{mean,ci_low,ci_high}`; Table A3 (post-hoc) "
      "`main.robustness.constraint_instability.<arm>.<model>.<c>.{mean,ci_low,ci_high}`; evaluable rates "
      "`main.<arm>.<model>.evaluable_rate.*`, `main.<arm>.<model>.evaluable_rate_by_family.<family>` and "
      "`main.counts.<model>.evaluable_rate` (both arms); comma spill-over (exploratory, Q-C2) "
      "`main.exploratory.e5.<arm>.<model>.evidence_comma_only.{items,outputs_all,outputs_any}.{mean,ci_low,ci_high}`, "
      "`.n_items_not_verbatim`, `.n_items_comma_only`, `.n_outputs_not_verbatim`, procedure "
      "`main.exploratory.e5.evidence_comma_only.procedure`; non-JSON outputs by family (Q-C3) "
      "`main.exploratory.e5.order.<model>.by_family.invalid_json.<family>`; generation hours "
      "`checks.compute.main.<model>.generation_hours`; review round 1 (decision R1; post-hoc unless stated): order level "
      "`main.posthoc_r1.order_level.<arm>.<model>.<condition>.{csr,pcr,format}.*` (condition = data id P01-P10 shown as "
      "O01-O10, or V01-V10), `.span.{csr,pcr}.*`, `main.posthoc_r1.order_level.<arm>.rank.<a>_vs_<b>.{csr,pcr}."
      "{n_a_higher,n_b_higher,n_ties}`, `main.posthoc_r1.order_level.<arm>.rank.overall.{csr,pcr}.{ranking,"
      "n_conditions_reproducing}`; fence-tolerant `main.posthoc_r1.fence_tolerant.<arm>.<model>.{format,csr,pcr}.*`, "
      "`main.posthoc_r1.fence_tolerant.<arm>.ranking.{csr,pcr}`, `main.posthoc_r1.fence_tolerant.cochran_q.gemma4e4b."
      "{q,df,p,status}`, paired difference (post-hoc, decision R2) `main.posthoc_r1.fence_tolerant.paired."
      "gemma4e4b_vs_phi4mini.{csr,pcr}.{mean,ci_low,ci_high,p}`; pooled VSR and flip rate, both arms "
      "`main.<arm>.pooled.{vsr,flip_rate}.{mean,ci_low,ci_high}`; pre-specified outcomes first reported in round 1: S1 format arm `main.format.<model>.{vsr,"
      "flip_rate}.*`, VERBATIM case-insensitive `main.robustness.diagnostics.<arm>.<model>.verbatim_case_insensitive.*`, "
      "secondary outcomes `main.secondary.<arm>.F1_QA.<model>.max_token_f1.*`, `main.secondary.<arm>.F2_CLASSIFICATION."
      "<model>.{unresolved_rate,no_label_rate}.*` (no-label rate post-hoc, decision R2) and `.{n_with_answer,n_unresolved}`, `main.secondary.<arm>."
      "{F4_EXTRACTION,F5_TRANSFORMATION}.<model>.exact_all_fields.*`; parsed-only TQS "
      "`main.posthoc_r1.tqs_parsed.<family>.<model>.{status,mean,ci_low,ci_high,n_task_model_pairs,differs_from_prespecified,"
      "n_orders_median,n_orders_min}`; "
      "Kendall's W companion `main.posthoc_r1.kendall_w.<model>.{n_constant_tasks,n_nonconstant_tasks,"
      "kendall_w_nonconstant}`; evidence length `main.posthoc_r1.evidence_length.<model>.{median_tokens,share_1_token,"
      "share_2_tokens,n_items}`; FORMAT failure types `main.posthoc_r1.format_failures.<model>.<position>.{n_outputs,"
      "invalid_json,missing_or_extra_key,fenced,other}` (smollm2, qwen25) and `main.posthoc_r1.format_failures.qwen25."
      "by_family.<family>.*`; edit distance `main.posthoc_r1.edit_distance.<model>.{median_format_variants,"
      "median_reorderings,n_pairs_each,status}`; cascade check `main.posthoc_r1.cascade_check.format.<model>.{ps_primary,"
      "ps_cascade,n_outputs_changed,n_tasks_ps_up,n_tasks_ps_down,families_changed}`; analysis software "
      "`checks.software.analysis.<package>`; Table A1 "
      "`main.exploratory.e5.<arm>.<model>.<tag>`; Table A2 `main.robustness.{cascade,strict_format}.*`. `<model>` is one "
      "of `smollm2`, `qwen25`, `phi4mini`, `gemma4e4b` or `pooled` (equal weight over the four models).")
    a("")
    a("Numbers in the text, in order of appearance:")
    a("")
    seen = set()
    for text, key in w.index:
        if key not in seen:
            seen.add(key)
            a(f"- {text} → `{key}`")
    return "\n".join(L) + "\n"
