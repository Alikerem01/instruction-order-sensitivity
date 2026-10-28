"""No personal data in project files or outputs (decisions D01, D02 §3, D03 §2.3, D04 §4).

The example strings below are assembled at runtime so that this file does not itself contain them.
"""

import json

from src.common import REPO_ROOT
from src.privacy import DEFAULT_DIRS, dataset_text_findings, find_personal_data, scan, scan_repository

AT = "@"
HOME = "/Us" + "ers/someone"
LINUX_HOME = "/ho" + "me/someone"
EMAIL = "name.surname" + AT + "example.org"
ORCID = "0000-0002-" + "1825-009X"


def kinds(text):
    return sorted({k for k, _ in find_personal_data(text)})


def test_patterns():
    assert kinds(f"python at {HOME}/project/.venv") == ["home_directory_path"]
    assert kinds(f"cache in {LINUX_HOME}/.cache") == ["home_directory_path"]
    assert kinds(f"write to {EMAIL} please") == ["email_address"]
    assert kinds(f"ORCID {ORCID}") == ["orcid_id"]
    assert kinds("<repo>/runs/dryrun and ~/.local/share are fine") == []
    assert kinds("dates 2026-10-04, hashes 7b6d24c440a3, /content/drive/MyDrive/Colab Notebooks") == []


def test_dataset_and_model_text_are_not_scanned(tmp_path):
    raw = tmp_path / "runs" / "generations.jsonl"
    raw.parent.mkdir(parents=True)
    raw.write_text(json.dumps({"output_text": f"contact {EMAIL}", "user_prompt": EMAIL, "model_key": "m"}) + "\n")
    assert scan([tmp_path / "runs"]) == []
    raw.write_text(json.dumps({"output_text": "ok", "note": f"{HOME}/x"}) + "\n")
    assert [k for _, k, _ in scan([tmp_path / "runs"])] == ["home_directory_path"]


def test_outputs_contain_no_personal_data():
    findings = scan([REPO_ROOT / d for d in DEFAULT_DIRS])
    assert findings == [], findings


def test_tracked_project_files_contain_no_personal_data():
    findings = scan_repository()
    assert findings == [], findings


def test_known_addresses_in_source_dataset_text():
    """Two XSum documents contain organizational addresses (a study contact, a BBC newsroom footer). They are
    dataset text, not the authors' data; their handling at release is decided by the study team (decision G2 §2.5)."""
    found = {(task_id, match) for task_id, kind, match in dataset_text_findings() if kind == "email_address"}
    assert found == {("sum_002", "vesuvius" + AT + "dundee.ac.uk"), ("sum_013", "entertainment.news" + AT + "bbc.co.uk")}
