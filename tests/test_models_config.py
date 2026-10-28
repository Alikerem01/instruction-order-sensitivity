"""Pinned models and phases, including the fourth model of decision D06 (Gemma 4 E4B)."""

import pytest

from src.common import load_experiment, load_models, read_jsonl
from src.generate import dedup_prompts, load_tokenizer, render

PINNED = {
    "smollm2": ("HuggingFaceTB/SmolLM2-1.7B-Instruct", "31b70e2e869a7173562077fd711b654946d38674"),
    "qwen25": ("Qwen/Qwen2.5-3B-Instruct", "aa8e72537993ba99e69dfaafa59ed015b17504d1"),
    "phi4mini": ("microsoft/Phi-4-mini-instruct", "cfbefacb99257ffa30c83adab238a50856ac3083"),
    "gemma4e4b": ("google/gemma-4-E4B-it", "ee0ef6023621cff504d758262d4e04895a5af4a2"),
}
MODELS = load_models()["models"]


def test_revisions_are_pinned_and_never_silently_changed():
    assert {k: (v["hf_id"], v["revision"]) for k, v in MODELS.items()} == PINNED
    for spec in MODELS.values():
        assert spec["trust_remote_code"] is False and spec["native_class_module"].startswith("transformers.models.")
        assert all(spec["chat_template_checks"].values())


def test_gemma_entry_records_the_facts_required_by_d06():
    g = MODELS["gemma4e4b"]
    assert g["license"] == "Apache-2.0" and g["hub_gated"] is False
    assert g["parameters_safetensors"] == 7_996_156_490 and "4.5B effective" in g["parameters_effective"]
    assert g["architecture"] == "Gemma4ForConditionalGeneration"
    assert g["eos_token_ids"] == [1, 106, 50] and g["pad_token_id"] == 0
    assert g["chat_template_kwargs"] == {"enable_thinking": False}
    assert {"<|think|>", "<|channel>"} <= set(g["thinking_markers"])
    assert g["chat_template_checks"]["system_message_in_its_own_turn"] is True
    assert g["chat_template_checks"]["no_thinking_markers_in_rendered_prompt"] is True


def test_phases_for_the_fourth_model():
    exp = load_experiment()
    ph = exp["phases"]
    assert ph["main"]["models"] == ["smollm2", "qwen25", "phi4mini", "gemma4e4b"]
    for name in ("smoke", "pilot", "pilot_bs1"):  # the three-model runs stay as they are
        assert ph[name]["models"] == ["smollm2", "qwen25", "phi4mini"]
    for name in ("smoke_gemma", "pilot_gemma"):
        assert ph[name]["models"] == ["gemma4e4b"] and ph[name]["experimental"] and not ph[name]["analysis_eligible"]
    assert ph["smoke_gemma"]["passes"] == 2
    assert exp["calibration_models"] == ["smollm2", "qwen25", "phi4mini"]


def test_batch_size_one_for_main_and_the_gemma_pilot_decision_g2():
    """Decision G2 §2.1-§2.2 (option B): main at batch size 1 for all four models and both arms; one Gemma pilot
    at batch size 1 with all 190 texts; pilot_bs1_gemma dropped; the batch-16 phases already run stay as they were."""
    exp = load_experiment()
    ph = exp["phases"]
    assert ph["main"]["batch_size"] == 1 and "prompt_arms" not in ph["main"]
    assert ph["pilot_gemma"]["batch_size"] == 1 and "prompt_arms" not in ph["pilot_gemma"]
    assert "pilot_bs1_gemma" not in ph and "pilot_bs1_gemma" not in exp["prompts"]["expected"]
    assert exp["generation"]["batch_size"] == 16 and "batch_size" not in ph["pilot"] and "batch_size" not in ph["smoke"]
    a6 = ph["main"]["determinism_check"]
    assert a6["prompts_file"] == "data/benchmark_v1/prompts_smoke.jsonl"
    assert a6["reference_phases"] == {"smollm2": "pilot_bs1", "qwen25": "pilot_bs1", "phi4mini": "pilot_bs1",
                                      "gemma4e4b": "pilot_gemma"}
    assert set(a6["reference_phases"]) == set(ph["main"]["models"])
    for ref_phase in set(a6["reference_phases"].values()):
        assert ph[ref_phase]["batch_size"] == 1  # A6 compares batch-1 outputs only


def _cached(spec) -> bool:
    from huggingface_hub import try_to_load_from_cache

    return isinstance(try_to_load_from_cache(spec["hf_id"], "tokenizer_config.json", revision=spec["revision"]), str)


def test_render_rejects_thinking_markers():
    spec = dict(MODELS["smollm2"])
    if not _cached(spec):
        pytest.skip("tokenizer not cached")
    tok = load_tokenizer(spec, "left")
    group = dedup_prompts(read_jsonl("data/benchmark_v1/prompts_smoke.jsonl"))[0]
    render(tok, group, spec)
    with pytest.raises(RuntimeError, match="thinking marker"):
        render(tok, group, {**spec, "thinking_markers": ["<|im_start|>"]})


def test_gemma_template_has_thinking_disabled_and_a_native_system_turn():
    spec = MODELS["gemma4e4b"]
    if not _cached(spec):
        pytest.skip("Gemma tokenizer not cached")
    tok = load_tokenizer(spec, "left")
    group = dedup_prompts(read_jsonl("data/benchmark_v1/prompts_smoke.jsonl"))[1]
    rendered, ids = render(tok, group, spec)
    assert rendered.startswith("<bos><|turn>system\n" + group["system_prompt"] + "<turn|>\n<|turn>user\n")
    assert rendered.endswith("<turn|>\n<|turn>model\n") and ids[0] == tok.bos_token_id
    with pytest.raises(RuntimeError, match="thinking marker"):
        render(tok, group, {**spec, "chat_template_kwargs": {"enable_thinking": True}})
