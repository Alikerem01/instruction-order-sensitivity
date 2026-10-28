"""Release preparation (decisions D03 §2, D04 §4, G2 §2.5; brief §7): no AG News or XSum text, e-mail addresses
redacted in released text, and a clean full-text scan."""

import json
import subprocess
import sys

import pytest

from scripts.make_release import (EXCLUDED_FILES, REDACTED, WORDING, build, check_wording_change, redact, scan,
                                  strip_prompt, strip_task, term_hits)
from src.common import REPO_ROOT

IN_SOURCE_REPOSITORY = (REPO_ROOT / "README_RELEASE.md").exists()  # the public tree holds only the release README
RELEASE_README = REPO_ROOT / ("README_RELEASE.md" if IN_SOURCE_REPOSITORY else "README.md")


def test_strip_and_redact_rules():
    t = strip_task({"family": "F3_SUMMARIZATION", "input_text": "x", "gold": {"summary": "y"}, "task_id": "sum_1"})
    assert "input_text" not in t and t["gold"] == {} and t["removed_for_release"] == ["input_text", "gold.summary"]
    assert strip_task({"family": "F1_QA", "input_text": "kept"})["input_text"] == "kept"
    assert "user_prompt" not in strip_prompt({"family": "F2_CLASSIFICATION", "user_prompt": "INPUT ..."})
    assert strip_prompt({"family": "F4_EXTRACTION", "user_prompt": "kept"})["user_prompt"] == "kept"
    text, n = redact("write to news" + "@" + "example.org or not")
    assert n == 1 and REDACTED in text


@pytest.mark.skipif(not IN_SOURCE_REPOSITORY, reason="the release is built from the source repository")
def test_release_tree(tmp_path):
    out = tmp_path / "release"
    report = build(out, allow_dirty=True)
    assert all(not (out / name).exists() for name in EXCLUDED_FILES - {"README.md"}) and not (out / "runs" / "dryrun").exists()
    assert "README_RELEASE.md" in EXCLUDED_FILES and "release_exclude.txt" in EXCLUDED_FILES
    assert (out / "README.md").read_text().startswith("# Instruction-order sensitivity")
    tasks = [json.loads(line) for line in (out / "data/benchmark_v1/tasks_main.jsonl").read_text().splitlines()]
    for t in tasks:
        if t["family"] in ("F2_CLASSIFICATION", "F3_SUMMARIZATION"):
            assert "input_text" not in t and "summary" not in t.get("gold", {})
        else:
            assert t["input_text"]
    prompts = [json.loads(line) for line in (out / "data/benchmark_v1/prompts_main.jsonl").read_text().splitlines()]
    assert all(("user_prompt" in p) == (p["family"] not in ("F2_CLASSIFICATION", "F3_SUMMARIZATION")) for p in prompts)
    assert len(prompts) == 2000 and all(p["prompt_sha256"] for p in prompts)
    assert scan(out) == [] and json.loads((out / "RELEASE_REDACTIONS.json").read_text())["redactions"] == report["redactions"]
    # wording-only changes of frozen files (release tree only): recorded with the manifest hash, no internal reference
    manifest = json.loads((REPO_ROOT / "data/benchmark_v1/manifest.json").read_text())["files_sha256"]
    rows = report["wording_redactions"]
    assert len(rows) == len(WORDING["files"]) == 13 and all(r["original_sha256"] == manifest[r["file"]] for r in rows)
    assert all(r["release_sha256"] != r["original_sha256"] for r in rows)
    assert term_hits(out) == [] and not (out / "release_wording.json").exists()
    # the release's freeze check accepts the documented wording changes; only the data files stripped of AG News and
    # XSum text differ until `make tasks prompts` rebuilds them
    res = subprocess.run([sys.executable, "scripts/freeze_manifest.py", "--check"], cwd=out, capture_output=True, text=True)
    assert set(report["texts_not_redistributed"]["files"]) <= set(manifest)
    for rel in report["texts_not_redistributed"]["files"]:
        assert rel in res.stdout
    for r in rows:
        assert r["file"] not in res.stdout.split("changed since the freeze:")[-1].split("\n")[0]
        assert f"{r['file']} (original SHA-256 {r['original_sha256']}" in res.stdout


def test_wording_change_guard():
    """A wording change may touch docstrings, comments and the listed string literals, never code or YAML values."""
    before = 'def f(x):\n    """Doc (old)."""\n    return x + 1  # comment (old)\n\nMSG = "report (old)"\n'
    check_wording_change("a.py", before, before.replace("Doc (old)", "Doc (new)").replace("comment (old)", "comment (new)"))
    check_wording_change("a.py", before, before.replace("report (old)", "report (new)"), literals_allowed=1)
    with pytest.raises(SystemExit):
        check_wording_change("a.py", before, before.replace("report (old)", "report (new)"))
    with pytest.raises(SystemExit):
        check_wording_change("a.py", before, before.replace("x + 1", "x + 2"))
    check_wording_change("a.yaml", "a: 1  # old\n", "a: 1  # new\n")
    with pytest.raises(SystemExit):
        check_wording_change("a.yaml", "a: 1  # old\n", "a: 2  # old\n")


def test_citation_and_source_attribution():
    """Source attribution, authors in D07 order, and no
    e-mail address or ORCID iD in the citation file."""
    import yaml

    from src.common import REPO_ROOT
    from src.privacy import find_personal_data

    cff = yaml.safe_load((REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    names = [(a["given-names"], a["family-names"]) for a in cff["authors"]]
    assert names == [("Songül", "ERDEM GÜLER"), ("Ali Kerem", "GÜLER"), ("Emel", "ARSLAN")]
    assert cff["preferred-citation"]["authors"] == cff["authors"] and cff["preferred-citation"]["year"] == 2026
    assert "license" not in cff
    assert not (REPO_ROOT / "LICENSE").exists()
    assert not (REPO_ROOT / "LICENSE-DATA.md").exists()
    for path in (REPO_ROOT / "CITATION.cff", RELEASE_README):
        assert find_personal_data(path.read_text(encoding="utf-8")) == []
    assert "rights in those excerpts remain with the original" in RELEASE_README.read_text(encoding="utf-8")
    text = " ".join(RELEASE_README.read_text(encoding="utf-8").split())
    assert "remain under their sources' terms." in text
    assert "SQuAD-derived texts remain under that licence." in text
