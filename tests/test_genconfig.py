"""R4 (design decision G1): fail-fast checks of the effective generation config and of the processors."""

import pytest
from transformers import GenerationConfig

from src.genconfig import INACTIVE_VALUES, check_generation_config, check_processors, torch_version_ok

EOS, PAD = [151645, 151643], 151643


def effective(**overrides) -> dict:
    """Mimic generate(): our from-scratch config, then transformers' global defaults merged into unset fields."""
    cfg = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=512, repetition_penalty=1.0,
                           eos_token_id=list(EOS), pad_token_id=PAD)
    for k, v in overrides.items():
        setattr(cfg, k, v)
    cfg.update(**GenerationConfig._get_default_generation_params(), defaults_only=True)
    return cfg.to_dict()


def test_greedy_config_with_inert_global_defaults_passes():
    d = effective()
    assert (d["temperature"], d["top_p"], d["top_k"]) == (1.0, 1.0, 50)  # inert global defaults
    assert check_generation_config(d, 512, EOS, PAD) == []


def test_768_after_calibration_passes_only_when_configured():
    assert check_generation_config(effective(max_new_tokens=768), 768, EOS, PAD) == []
    assert check_generation_config(effective(max_new_tokens=768), 512, EOS, PAD)
    assert check_generation_config(effective(max_new_tokens=600), 600, EOS, PAD)


@pytest.mark.parametrize(
    "overrides",
    [
        {"do_sample": True},
        {"num_beams": 4},
        {"repetition_penalty": 1.05},
        {"max_new_tokens": 256},
        {"eos_token_id": [151645]},
        {"pad_token_id": 0},
        {"temperature": 0.7},   # a Hub default leaking in (Qwen2.5)
        {"top_k": 20},
        {"top_p": 0.8},
    ],
)
def test_violations_are_reported(overrides):
    assert check_generation_config(effective(**overrides), 512, EOS, PAD)


def test_qwen_hub_defaults_merged_into_unset_fields_are_caught():
    """What would happen without replacing model.generation_config: Hub values fill the unset fields."""
    cfg = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=512, repetition_penalty=1.0,
                           eos_token_id=list(EOS), pad_token_id=PAD)
    hub = {"do_sample": True, "temperature": 0.7, "top_p": 0.8, "top_k": 20, "repetition_penalty": 1.05}
    cfg.update(**hub, defaults_only=True)
    problems = check_generation_config(cfg.to_dict(), 512, EOS, PAD)
    assert any("temperature" in p for p in problems) and any("top_k" in p for p in problems)


ACTIVE_EXAMPLES = {
    "no_repeat_ngram_size": 3, "encoder_no_repeat_ngram_size": 2, "encoder_repetition_penalty": 1.2,
    "bad_words_ids": [[5]], "sequence_bias": {(5,): -1.0}, "suppress_tokens": [5], "begin_suppress_tokens": [5],
    "forced_bos_token_id": 1, "forced_eos_token_id": 2, "min_length": 10, "min_new_tokens": 5,
    "exponential_decay_length_penalty": (10, 1.5), "remove_invalid_values": True, "renormalize_logits": True,
    "guidance_scale": 1.5, "watermarking_config": {"greenlist_ratio": 0.25}, "max_time": 10.0,
    "stop_strings": ["}"], "penalty_alpha": 0.6, "dola_layers": "high", "prompt_lookup_num_tokens": 10,
    "assistant_early_exit": 4, "num_beam_groups": 2, "diversity_penalty": 0.5, "num_return_sequences": 2,
    "constraints": ["c"], "force_words_ids": [[5]], "cache_implementation": "static",
}


@pytest.mark.parametrize("key", sorted(INACTIVE_VALUES))
def test_every_inactive_field_is_enforced(key):
    d = effective()
    d[key] = ACTIVE_EXAMPLES[key]
    assert any(p.startswith(key) for p in check_generation_config(d, 512, EOS, PAD))


def test_processor_check():
    ok = ["MaxLengthCriteria", "EosTokenCriteria"]
    assert check_processors([], ok) == []
    assert check_processors(["RepetitionPenaltyLogitsProcessor"], ok)
    assert check_processors([], ok + ["StopStringCriteria"])
    assert check_processors([], ["MaxLengthCriteria"])
    assert check_processors(None, ok) and check_processors([], None)


def test_torch_version_rule():
    assert torch_version_ok("2.8.0+cu126") and torch_version_ok("2.5.0") and torch_version_ok("3.0.1")
    assert not torch_version_ok("2.4.1+cu121") and not torch_version_ok("") and not torch_version_ok("dev")
