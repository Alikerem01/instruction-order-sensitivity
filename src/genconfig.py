"""Fail-fast checks of greedy generation (design decision G1, R4).

Two checks, both of which abort the run when they fail:

1. ``check_generation_config``: the *effective* configuration that ``generate()`` will use (after transformers
   merges its global defaults into unset fields) is compared with an allow-list: ``do_sample`` False,
   ``num_beams`` 1, ``repetition_penalty`` 1.0, ``max_new_tokens`` as configured (512, or 768 after the
   calibration rule), end-of-turn ids and pad id as in models.yaml, and every field that would add a logits
   processor, a stopping criterion or another decoding strategy inactive. The sampling-only fields temperature,
   top_p and top_k may hold transformers' global defaults (1.0, 1.0, 50), which are inert under greedy decoding;
   any other value (for example a Hub default such as temperature 0.7) fails, because it would reveal that the
   model's Hub generation config leaked in.
2. ``check_processors``: the logits processors and stopping criteria that ``generate()`` actually built for a
   batch (captured at runtime): no logits processor at all, and only MaxLengthCriteria and EosTokenCriteria.
"""

from __future__ import annotations

from typing import Any

REQUIRED_VALUES: dict[str, Any] = {"do_sample": False, "num_beams": 1, "repetition_penalty": 1.0}
ALLOWED_MAX_NEW_TOKENS = (512, 768)

# Fields that add a logits processor, a stopping criterion or another decoding strategy when set.
INACTIVE_VALUES: dict[str, tuple] = {
    "no_repeat_ngram_size": (None, 0),
    "encoder_no_repeat_ngram_size": (None, 0),
    "encoder_repetition_penalty": (None, 1.0),
    "bad_words_ids": (None,),
    "sequence_bias": (None,),
    "suppress_tokens": (None,),
    "begin_suppress_tokens": (None,),
    "forced_bos_token_id": (None,),
    "forced_eos_token_id": (None,),
    "min_length": (None, 0),
    "min_new_tokens": (None, 0),
    "exponential_decay_length_penalty": (None,),
    "remove_invalid_values": (None, False),
    "renormalize_logits": (None, False),
    "guidance_scale": (None, 1.0),
    "watermarking_config": (None,),
    "max_time": (None,),
    "stop_strings": (None,),
    "penalty_alpha": (None,),
    "dola_layers": (None,),
    "prompt_lookup_num_tokens": (None,),
    "assistant_early_exit": (None,),
    "num_beam_groups": (None, 1),
    "diversity_penalty": (None, 0.0),
    "num_return_sequences": (None, 1),
    "constraints": (None,),
    "force_words_ids": (None,),
    "cache_implementation": (None,),
}
# Sampling- or beam-only fields: inert under greedy decoding; allowed only at transformers' global defaults.
INERT_DEFAULTS: dict[str, tuple] = {
    "temperature": (None, 1.0),
    "top_p": (None, 1.0),
    "top_k": (None, 50),
    "typical_p": (None, 1.0),
    "min_p": (None,),
    "top_h": (None,),
    "epsilon_cutoff": (None, 0.0),
    "eta_cutoff": (None, 0.0),
    "length_penalty": (None, 1.0),
    "early_stopping": (None, False),
}
ALLOWED_STOPPING_CRITERIA = ("MaxLengthCriteria", "EosTokenCriteria")


def _as_list(value: Any) -> list | None:
    if value is None:
        return None
    return list(value) if isinstance(value, (list, tuple)) else [value]


def check_generation_config(cfg: dict, max_new_tokens: int, eos_token_ids: list[int], pad_token_id: int) -> list[str]:
    """Return every violation of the allow-list (an empty list means the configuration is accepted)."""
    problems = []
    for key, value in REQUIRED_VALUES.items():
        if cfg.get(key) != value:
            problems.append(f"{key}={cfg.get(key)!r} (required {value!r})")
    if max_new_tokens not in ALLOWED_MAX_NEW_TOKENS:
        problems.append(f"configured max_new_tokens={max_new_tokens} not in {ALLOWED_MAX_NEW_TOKENS}")
    if cfg.get("max_new_tokens") != max_new_tokens:
        problems.append(f"max_new_tokens={cfg.get('max_new_tokens')!r} (required {max_new_tokens})")
    if _as_list(cfg.get("eos_token_id")) != list(eos_token_ids):
        problems.append(f"eos_token_id={cfg.get('eos_token_id')!r} (models.yaml: {list(eos_token_ids)})")
    if cfg.get("pad_token_id") != pad_token_id:
        problems.append(f"pad_token_id={cfg.get('pad_token_id')!r} (models.yaml: {pad_token_id})")
    for table, label in ((INACTIVE_VALUES, "must be inactive"), (INERT_DEFAULTS, "only the inert global default")):
        for key, allowed in table.items():
            if cfg.get(key) not in allowed:
                problems.append(f"{key}={cfg.get(key)!r} ({label}: {allowed})")
    return problems


def check_processors(logits_processors: list[str] | None, stopping_criteria: list[str] | None) -> list[str]:
    """Check the class names of the processors and criteria generate() built for one batch."""
    if logits_processors is None or stopping_criteria is None:
        return ["could not observe the logits processors or stopping criteria used by generate()"]
    problems = []
    if logits_processors:
        problems.append(f"logits processors active: {logits_processors} (greedy decoding uses none)")
    extra = [c for c in stopping_criteria if c not in ALLOWED_STOPPING_CRITERIA]
    if extra:
        problems.append(f"unexpected stopping criteria: {extra}")
    missing = [c for c in ALLOWED_STOPPING_CRITERIA if c not in stopping_criteria]
    if missing:
        problems.append(f"missing stopping criteria: {missing}")
    return problems


MIN_TORCH = (2, 5)  # transformers 5.17.0 requires torch >= 2.5 (design decision G1, item 3)


def torch_version_ok(version: str, minimum: tuple[int, int] = MIN_TORCH) -> bool:
    """True if a torch version string such as "2.8.0+cu126" is at least ``minimum`` (major, minor)."""
    try:
        major_minor = tuple(int(x) for x in version.split("+")[0].split(".")[:2])
    except ValueError:
        return False
    return major_minor >= minimum
