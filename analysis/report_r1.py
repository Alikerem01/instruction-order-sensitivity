"""Tables and the RESULTS_SUMMARY section for review round 1 (decision R1 §3). Every value is read from summary.json;
post-hoc items carry the label "post-hoc (decision R1)"."""

from __future__ import annotations

import itertools
from pathlib import Path

from analysis.data import ARM_IDS, CONSTRAINTS, FAMILIES
from analysis.posthoc_r1 import FENCE_TYPES
from analysis.report import CNAMES, FNAMES, NAMES, Writer, _md_table, _write_csv, dec, olabel, pct, pval
from src.common import atomic_write_text

P = "main.posthoc_r1"



def _peq(p) -> str:
    text = pval(p)
    return text if text.startswith("<") or text == "n/a" else f"= {text}"

def tables_r1(s: dict, models: list[str], out_dir: Path) -> dict[str, str]:
    md = {}
    # order level
    parts, rows_csv = [], []
    for arm, ids in ARM_IDS.items():
        for m in models:
            rows = []
            for cid in ids:
                rows.append([olabel(cid)] + [Writer(s).cell(f"{P}.order_level.{arm}.{m}.{cid}.{x}") for x in ("csr", "pcr", "format")])
                rows_csv += [[arm, m, olabel(cid), cid, x] + [s.get(f"{P}.order_level.{arm}.{m}.{cid}.{x}.{k}")
                                                              for k in ("mean", "ci_low", "ci_high")] for x in ("csr", "pcr", "format")]
            rows.append(["Span (max − min)"] + [Writer(s).cell(f"{P}.order_level.{arm}.{m}.span.{x}") for x in ("csr", "pcr")] + [""])
            rows_csv += [[arm, m, "span", "", x] + [s.get(f"{P}.order_level.{arm}.{m}.span.{x}.{k}")
                                                     for k in ("mean", "ci_low", "ci_high")] for x in ("csr", "pcr")]
            parts.append(f"**{NAMES[m]}, {arm} arm**\n\n" + _md_table(["Condition", "CSR", "PCR", "FORMAT"], rows))
    rank_rows = []
    for x, y in itertools.combinations(models, 2):
        cells = []
        for arm in ARM_IDS:
            for metric in ("csr", "pcr"):
                k = f"{P}.order_level.{arm}.rank.{x}_vs_{y}.{metric}"
                cells.append(f"{s.get(k + '.n_a_higher')} / {s.get(k + '.n_b_higher')} / {s.get(k + '.n_ties')}")
        rank_rows.append([f"{NAMES[x]} vs {NAMES[y]}"] + cells)
    md["tableR1_order_level"] = (
        "Table R1a. **Post-hoc (decision R1)**: compliance per order (order arm, O01-O10) and per formatting variant "
        "(format arm, V01-V10), mean [95% CI, task-clustered bootstrap over the 100 tasks], with the span (max − min "
        "over the ten conditions) and its bootstrap CI.\n\n" + "\n\n".join(parts)
        + "\n\nRank stability: number of conditions (of 10) in which the first model's mean is higher / the second "
        "model's mean is higher / tied.\n\n"
        + _md_table(["Pair", "CSR, order arm", "PCR, order arm", "CSR, format arm", "PCR, format arm"], rank_rows))
    _write_csv(out_dir / "tableR1_order_level.csv", ["arm", "model", "label", "condition_id", "metric", "mean", "ci_low",
                                                      "ci_high"], rows_csv)
    # fence tolerant
    rows, rows_csv = [], []
    for arm in ARM_IDS:
        for m in models + ["pooled"]:
            f = f"{P}.fence_tolerant.{arm}.{m}"
            rows.append([f"{NAMES[m]}, {arm}"] + [Writer(s).cell(f"{f}.{x}") for x in ("format", "csr", "pcr")]
                        + [Writer(s).cell(f"main.{arm}.{m}.{x}") for x in ("csr", "pcr")])
            rows_csv += [[arm, m, x] + [s.get(f"{f}.{x}.{k}") for k in ("mean", "ci_low", "ci_high")] for x in ("format", "csr", "pcr")]
    g = f"{P}.fence_tolerant.cochran_q.gemma4e4b"
    cq = (f"Cochran's Q of PCR_ft across the ten orders for Gemma 4 E4B (post-hoc): Q({s.get(g + '.df')}) = "
          f"{dec(s.get(g + '.q'), 2)}, p {pval(s.get(g + '.p'))}." if s.get(g + ".status") == "estimated" else
          f"Cochran's Q of PCR_ft for Gemma 4 E4B: {s.get(g + '.status')}.")
    pd_ = f"{P}.fence_tolerant.paired.gemma4e4b_vs_phi4mini"
    if s.get(pd_ + ".csr.mean") is not None:
        cq += (" Paired difference Gemma 4 E4B − Phi-4-mini under the fence-tolerant reading, order arm (post-hoc, "
               "decision R2; task-clustered bootstrap as in S2): " + "; ".join(
                   f"{lab} {Writer(s).cell(f'{pd_}.{x}')} (percentage points), bootstrap p {_peq(s.get(f'{pd_}.{x}.p'))}"
                   for x, lab in (("csr", "CSR_ft"), ("pcr", "PCR_ft"))) + ".")
    md["tableR1_fence_tolerant"] = (
        "Table R1b. **Post-hoc (decision R1)**: fence-tolerant FORMAT and the CSR and PCR that follow from it, next to "
        "strict CSR and PCR (mean [95% CI]). " + str(s.get(f"{P}.fence_tolerant.definition")) + "\n\n"
        + _md_table(["Model, arm", "FORMAT_ft", "CSR_ft", "PCR_ft", "CSR (strict)", "PCR (strict)"], rows)
        + "\n\nRanking by CSR_ft, order arm: " + " > ".join(NAMES[m] for m in s.get(f"{P}.fence_tolerant.order.ranking.csr", []))
        + "; by PCR_ft: " + " > ".join(NAMES[m] for m in s.get(f"{P}.fence_tolerant.order.ranking.pcr", [])) + ". " + cq)
    _write_csv(out_dir / "tableR1_fence_tolerant.csv", ["arm", "model", "metric", "mean", "ci_low", "ci_high"], rows_csv)
    # secondary (pre-specified)
    rows, rows_csv = [], []
    cols = [("VSR, format arm", "main.format.{m}.vsr", "pct"), ("Flip rate, format arm", "main.format.{m}.flip_rate", "pct"),
            ("QA max token F1", "main.secondary.order.F1_QA.{m}.max_token_f1", "dec"),
            ("CLS unresolved label", "main.secondary.order.F2_CLASSIFICATION.{m}.unresolved_rate", "pct"),
            ("CLS no label (post-hoc)", "main.secondary.order.F2_CLASSIFICATION.{m}.no_label_rate", "pct"),
            ("EXT exact all fields", "main.secondary.order.F4_EXTRACTION.{m}.exact_all_fields", "pct"),
            ("TRF exact all fields", "main.secondary.order.F5_TRANSFORMATION.{m}.exact_all_fields", "pct"),
            ("VERBATIM case-insensitive", "main.robustness.diagnostics.order.{m}.verbatim_case_insensitive", "pct")]
    for m in models:
        rows.append([NAMES[m]] + [Writer(s).cell(k.format(m=m), kind) for _, k, kind in cols])
        rows_csv += [[m, c] + [s.get(k.format(m=m) + "." + x) for x in ("mean", "ci_low", "ci_high")] + [k.format(m=m)] for c, k, _ in cols]
    md["tableR1_secondary"] = (
        "Table R1c. Pre-specified outcomes not reported before review round 1 (ANALYSIS_PLAN §3; S1 format arm and the "
        "secondary task-quality outcomes; order arm unless stated; mean [95% CI]). CLS rates are among CLS outputs with "
        "a parsed answer. The CLS no-label rate is post-hoc (decision R2, Q10): the frozen plan and evaluator documentation "
        "name only the unresolved-label rate as reported. Format-arm values of the secondary outcomes are under `main.secondary.format.*` (e.g. CLS "
        "unresolved labels: " + ", ".join(f"{NAMES[m]} {s.get(f'main.secondary.format.F2_CLASSIFICATION.{m}.n_unresolved')}"
                                         for m in models) + " in the format arm).\n\n" + _md_table(["Model"] + [c for c, _, _ in cols], rows))
    _write_csv(out_dir / "tableR1_secondary.csv", ["model", "outcome", "mean", "ci_low", "ci_high", "key"], rows_csv)
    # format failures
    parts, rows_csv = [], []
    for m in ("smollm2", "qwen25"):
        rows = []
        for k in range(1, 6):
            n = s.get(f"{P}.format_failures.{m}.{k}.n_outputs")
            counts = [s.get(f"{P}.format_failures.{m}.{k}.{t}") for t in FENCE_TYPES]
            rows.append([str(k), str(n), str(sum(counts))] + [f"{c} ({100 * c / n:.1f}%)" for c in counts])
            rows_csv += [[m, "position", k, t, c, n] for t, c in zip(FENCE_TYPES, counts)]
        parts.append(f"**{NAMES[m]}, by FORMAT position**\n\n" + _md_table(["Position", "Outputs", "Failures"] + list(FENCE_TYPES), rows))
    rows = []
    for fam in FAMILIES:
        n = s.get(f"{P}.format_failures.qwen25.by_family.{fam}.n_outputs")
        counts = [s.get(f"{P}.format_failures.qwen25.by_family.{fam}.{t}") for t in FENCE_TYPES]
        rows.append([FNAMES[fam], str(n), str(sum(counts))] + [f"{c} ({100 * c / n:.1f}%)" for c in counts])
        rows_csv += [["qwen25", "family", fam, t, c, n] for t, c in zip(FENCE_TYPES, counts)]
    parts.append("**Qwen2.5-3B, by family**\n\n" + _md_table(["Family", "Outputs", "Failures"] + list(FENCE_TYPES), rows))
    md["tableR1_format_failures"] = (
        "Table R1d. **Descriptive, post-hoc (decision R1)**: strict FORMAT failures in the order arm by type and FORMAT "
        "position (count and share of the outputs in the row): fenced; invalid_json = no JSON object; "
        "missing_or_extra_key = valid JSON with a missing or extra key; other = surrounding text or duplicate keys.\n\n"
        + "\n\n".join(parts))
    _write_csv(out_dir / "tableR1_format_failures.csv", ["model", "breakdown", "level", "type", "count", "n_outputs"], rows_csv)
    # parsed-only TQS
    rows, rows_csv = [], []
    for fam in FAMILIES:
        cells = []
        for m in models:
            k = f"{P}.tqs_parsed.{fam}.{m}"
            flag = " †" if s.get(k + ".differs_from_prespecified") else ""
            value = Writer(s).cell(k, "dec") if s.get(k + ".status") == "estimated" else "not computable"
            cells.append(f"{value} (n = {s.get(k + '.n_task_model_pairs')}){flag}")
            rows_csv.append([fam, m] + [s.get(f"{k}.{x}") for x in ("mean", "ci_low", "ci_high", "n_task_model_pairs",
                                                                      "differs_from_prespecified")]
                            + [s.get(f"main.quality.{fam}.{m}.tqs.mean")]
                            + [s.get(f"{k}.{x}") for x in ("n_orders_median", "n_orders_min")])
        rows.append([FNAMES[fam]] + cells)
    md["tableR1_tqs_parsed"] = (
        "Table R1e. **Post-hoc (decision R1)**: parsed-only TQS, " + str(s.get(f"{P}.tqs_parsed.definition"))
        + " (mean [95% CI]; n = task-model pairs that qualify; † = differs from the pre-specified TQS of Table 5 by "
        "more than 0.05; not computable = no task with at least 2 parsed orders).\n\n" + _md_table(["Family"] + [NAMES[m] for m in models], rows)
        + "\n\nParsed orders per qualifying task, median (minimum), of 10 (decision R2, m19). A range taken over a subset "
        "of the orders cannot exceed the range over all ten orders had all of them been parsed, so the cells with few "
        "parsed orders (SmolLM2-1.7B QA, Qwen2.5-3B SUM) are lower bounds.\n\n" + _md_table(["Family"] + [NAMES[m] for m in models], [
            [FNAMES[fam]] + [(f"{dec(s.get(f'{P}.tqs_parsed.{fam}.{m}.n_orders_median'), 1)} "
                              f"({s.get(f'{P}.tqs_parsed.{fam}.{m}.n_orders_min')})")
                             if s.get(f"{P}.tqs_parsed.{fam}.{m}.status") == "estimated" else "–" for m in models]
            for fam in FAMILIES]))
    _write_csv(out_dir / "tableR1_tqs_parsed.csv", ["family", "model", "mean", "ci_low", "ci_high", "n_task_model_pairs",
                                                     "differs_from_prespecified", "tqs_prespecified", "n_orders_median",
                                                     "n_orders_min"], rows_csv)
    # descriptives
    rows, rows_csv = [], []
    for m in models:
        kw, ev, ed = f"{P}.kendall_w.{m}", f"{P}.evidence_length.{m}", f"{P}.edit_distance.{m}"
        vals = [s.get(f"main.tests.friedman.{m}.kendall_w"), s.get(kw + ".n_constant_tasks"), s.get(kw + ".kendall_w_nonconstant"),
                s.get(ev + ".median_tokens"), s.get(ev + ".share_1_token"), s.get(ev + ".share_2_tokens"), s.get(ev + ".n_items"),
                s.get(ed + ".median_format_variants"), s.get(ed + ".median_reorderings")]
        rows.append([NAMES[m], dec(vals[0]), str(vals[1]), dec(vals[2]), dec(vals[3], 0), pct(vals[4]), pct(vals[5]),
                     str(vals[6]), dec(vals[7], 0), dec(vals[8], 0)])
        rows_csv.append([m] + vals)
    md["tableR1_descriptives"] = (
        "Table R1f. Descriptive companions (decision R1 §3.6, §3.7, §3.10): Kendall's W of P2 and the tie-corrected W "
        "among the tasks whose CSR is not constant across the ten orders; evidence-item length (\\S+ tokens, string items "
        "of list evidence, 1,900 unique generations per model); median token-level edit distance of a prompt to its "
        "task's O01 prompt under the model's tokenizer (post-hoc).\n\n"
        + _md_table(["Model", "W (P2)", "Tasks with constant CSR", "W, non-constant tasks", "Median evidence tokens",
                     "1-token items", "2-token items", "Evidence items", "Edit distance, formatting variants",
                     "Edit distance, reorderings"], rows))
    _write_csv(out_dir / "tableR1_descriptives.csv", ["model", "kendall_w", "n_constant_tasks", "kendall_w_nonconstant",
                                                       "median_evidence_tokens", "share_1_token", "share_2_tokens", "n_items",
                                                       "edit_distance_format", "edit_distance_reorder"], rows_csv)
    for name, text in md.items():
        atomic_write_text(out_dir / f"{name}.md", text + "\n")
    return md


def summary_section_r1(s: dict, models: list[str], w: Writer) -> list[str]:
    L = ["## Post-hoc analyses and checks of review round 1 (decision R1)", "",
         "**Cascade PS_format check (Q1, m16).** The E6a P3 contrast uses PS_format under cascade scoring; there is no "
         "analysis error. In the format arm, cascade scoring changes "
         + "; ".join(f"{NAMES[m]} {w.num(f'{P}.cascade_check.format.{m}.n_outputs_changed', 'int')} outputs and the PS of "
                     f"{w.num(f'{P}.cascade_check.format.{m}.n_tasks_ps_up', 'int')} tasks upwards and "
                     f"{w.num(f'{P}.cascade_check.format.{m}.n_tasks_ps_down', 'int')} downwards" for m in models)
         + ". Qwen2.5-3B's and Phi-4-mini's format-arm FORMAT failures are all non-JSON outputs, which already score 0 on "
         "all five constraints; for SmolLM2-1.7B the upward and downward changes (all in "
         + ", ".join(FNAMES[f] for f in s.get(f"{P}.cascade_check.format.smollm2.families_changed", [])) + " tasks) cancel in the "
         f"mean ({w.num('main.posthoc_r1.cascade_check.format.smollm2.ps_primary', 'dec')} under both policies). For Gemma 4 E4B cascade "
         f"PS_format is {w.num('main.robustness.cascade.format.gemma4e4b.ps.mean', 'dec')} (primary "
         f"{w.num('main.format.gemma4e4b.ps.mean', 'dec')}). SmolLM2-1.7B's cascade P3 result stands: "
         f"{w.num('main.robustness.cascade.p3.smollm2.mean_diff', 'dec')} [{w.num('main.robustness.cascade.p3.smollm2.ci_low', 'dec')}, "
         f"{w.num('main.robustness.cascade.p3.smollm2.ci_high', 'dec')}], p {w.peq('main.robustness.cascade.p3.smollm2.p')}.", ""]
    L.append("**Order-level results (post-hoc).** Span (max − min over the ten orders) of mean CSR, order arm versus "
             "format arm: " + "; ".join(
                 f"{NAMES[m]} {w.est(f'{P}.order_level.order.{m}.span.csr', 'dec')} versus "
                 f"{w.num(f'{P}.order_level.format.{m}.span.csr.mean', 'dec')}" for m in models)
             + ". Span of PCR, order arm: " + "; ".join(f"{NAMES[m]} {w.est(f'{P}.order_level.order.{m}.span.pcr', 'dec')}"
                                                      for m in models) + ". Model ranking: " + "; ".join(
        f"{lab}, {arm} arm, " + " > ".join(NAMES[m] for m in s.get(f'{P}.order_level.{arm}.rank.overall.{metric}.ranking', []))
        + f" (mean over the ten conditions) in {w.num(f'{P}.order_level.{arm}.rank.overall.{metric}.n_conditions_reproducing', 'int')} "
        "of 10 conditions" for metric, lab in (("csr", "CSR"), ("pcr", "PCR")) for arm in ("order", "format"))
             + "; pairwise counts are in Table R1a.")
    L.append("")
    L.append("**Fence-tolerant FORMAT (post-hoc).** Order arm: " + "; ".join(
        f"{NAMES[m]} FORMAT_ft {w.num(f'{P}.fence_tolerant.order.{m}.format.mean')}, CSR_ft "
        f"{w.est(f'{P}.fence_tolerant.order.{m}.csr')}, PCR_ft {w.est(f'{P}.fence_tolerant.order.{m}.pcr')}" for m in models)
        + f". Under strict scoring {NAMES[max(models, key=lambda m: s.get(f'main.order.{m}.csr.mean'))]} has the highest "
        f"CSR; under the fence-tolerant reading {NAMES[s.get(f'{P}.fence_tolerant.order.ranking.csr')[0]]} has. "
        f"Cochran's Q of PCR_ft across orders for Gemma 4 E4B: Q({w.num(f'{P}.fence_tolerant.cochran_q.gemma4e4b.df', 'int')}) = "
        f"{w.num(f'{P}.fence_tolerant.cochran_q.gemma4e4b.q', 'dec2')}, p {w.peq(f'{P}.fence_tolerant.cochran_q.gemma4e4b.p')}. "
        "Paired difference Gemma 4 E4B − Phi-4-mini under the fence-tolerant reading (post-hoc, decision R2; "
        "task-clustered bootstrap as in S2): " + "; ".join(
            f"{lab} {w.est(f'{P}.fence_tolerant.paired.gemma4e4b_vs_phi4mini.{x}')}, bootstrap p "
            f"{w.peq(f'{P}.fence_tolerant.paired.gemma4e4b_vs_phi4mini.{x}.p')}" for x, lab in (("csr", "CSR"), ("pcr", "PCR")))
        + ".")
    L.append("")
    L.append("**Kendall's W companion (descriptive).** " + "; ".join(
        f"{NAMES[m]}: {w.num(f'{P}.kendall_w.{m}.n_constant_tasks', 'int')} of 100 tasks with constant CSR, W among the "
        f"others {w.num(f'{P}.kendall_w.{m}.kendall_w_nonconstant', 'dec')}" for m in models) + ".")
    L.append("")
    L.append("**Token edit distance to O01 (post-hoc, descriptive).** Median over the formatting variants versus the "
             "reorderings: " + "; ".join(
                 f"{NAMES[m]} {w.num(f'{P}.edit_distance.{m}.median_format_variants', 'dec2')} versus "
                 f"{w.num(f'{P}.edit_distance.{m}.median_reorderings', 'dec2')} tokens" for m in models
                 if s.get(f"{P}.edit_distance.{m}.status") == "estimated") + ".")
    L.append("")
    L.append("Further R1 tables: secondary outcomes (Table R1c, pre-specified), FORMAT failure types (R1d), parsed-only "
             "TQS (R1e), evidence lengths and the descriptives (R1f).")
    L.append("")
    return L
