"""User-prompt rendering: the canonical template (V01), the format variants V02-V10, and canonicalize().

Canonical user message (brief §5.3)::

    INSTRUCTIONS:
    - {instruction_1}
    ...
    - {instruction_5}

    TASK:
    {task_directive}

    INPUT:
    {input_text}

Lines are joined with "\\n", blocks with "\\n\\n"; no trailing whitespace, no trailing newline.
The format variants change only bullets, whitespace, header case and colons (brief §5.5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

HEADERS = ("INSTRUCTIONS", "TASK", "INPUT")


@dataclass(frozen=True)
class FormatSpec:
    bullet: str = "- "
    header_case: str = "upper"  # upper | title | lower
    header_colon: bool = True
    block_sep: str = "\n\n"
    instruction_sep: str = "\n"

    def header(self, name: str) -> str:
        text = {"upper": name.upper(), "title": name.title(), "lower": name.lower()}[self.header_case]
        return text + (":" if self.header_colon else "")


FORMAT_VARIANTS: dict[str, FormatSpec] = {
    "V01": FormatSpec(),
    "V02": FormatSpec(bullet="* "),
    "V03": FormatSpec(bullet="• "),
    "V04": FormatSpec(header_case="title"),
    "V05": FormatSpec(header_case="lower"),
    "V06": FormatSpec(block_sep="\n\n\n"),
    "V07": FormatSpec(instruction_sep="\n\n"),
    "V08": FormatSpec(bullet="  - "),
    "V09": FormatSpec(header_colon=False),
    "V10": FormatSpec(bullet="* ", header_case="title"),
}
VARIANT_IDS = tuple(FORMAT_VARIANTS)
CANONICAL_VARIANT_ID = "V01"


def render_user_prompt(
    instructions: list[str], task_directive: str, input_text: str, spec: FormatSpec = FORMAT_VARIANTS["V01"]
) -> str:
    """Render one user message. ``instructions`` are already in presentation order."""
    if not instructions:
        raise ValueError("at least one instruction is required")
    for part in [*instructions, task_directive, input_text]:
        if part != part.strip():
            raise ValueError(f"prompt part has leading or trailing whitespace: {part[:60]!r}")
    instruction_block = spec.header("INSTRUCTIONS") + "\n" + spec.instruction_sep.join(
        spec.bullet + text for text in instructions
    )
    task_block = spec.header("TASK") + "\n" + task_directive
    input_block = spec.header("INPUT") + "\n" + input_text
    return spec.block_sep.join([instruction_block, task_block, input_block])


def render_canonical(instructions: list[str], task_directive: str, input_text: str) -> str:
    return render_user_prompt(instructions, task_directive, input_text, FORMAT_VARIANTS[CANONICAL_VARIANT_ID])


def _header_re(name: str) -> re.Pattern:
    variants = "|".join(re.escape(v) for v in (name.upper(), name.title(), name.lower()))
    return re.compile(rf"^(?:{variants}):?$")


_HEADER_RES = {name: _header_re(name) for name in HEADERS}
_BULLET_RE = re.compile(r"^(?:  )?(?:- |\* |• )(.+)$")


@dataclass(frozen=True)
class ParsedPrompt:
    instructions: list[str]
    task: str
    input: str


def parse_user_prompt(prompt: str) -> ParsedPrompt:
    """Parse any rendered variant into (instructions, task block content, input block content).

    The INPUT block content is everything after the INPUT header line, verbatim.
    """
    lines = prompt.split("\n")
    if not lines or not _HEADER_RES["INSTRUCTIONS"].match(lines[0]):
        raise ValueError("prompt does not start with an INSTRUCTIONS header")
    i = 1
    instructions: list[str] = []
    while i < len(lines):
        line = lines[i]
        if line == "":
            i += 1
            continue
        m = _BULLET_RE.match(line)
        if m:
            instructions.append(m.group(1))
            i += 1
            continue
        if _HEADER_RES["TASK"].match(line):
            break
        raise ValueError(f"unexpected line in INSTRUCTIONS block: {line!r}")
    if i >= len(lines) or not instructions:
        raise ValueError("no TASK header or no instructions found")
    i += 1  # skip the TASK header
    j = i
    while j < len(lines):
        if lines[j] == "":
            k = j
            while k < len(lines) and lines[k] == "":
                k += 1
            if k < len(lines) and _HEADER_RES["INPUT"].match(lines[k]):
                task = "\n".join(lines[i:j])
                return ParsedPrompt(instructions, task, "\n".join(lines[k + 1 :]))
            j = k
            continue
        j += 1
    raise ValueError("no INPUT header found after the TASK block")


def canonicalize(prompt: str) -> str:
    """Map any format variant back to the canonical V01 rendering."""
    parsed = parse_user_prompt(prompt)
    return render_canonical(parsed.instructions, parsed.task, parsed.input)


def instruction_lines_removed(prompt: str) -> str:
    """The prompt with every instruction (bullet) line removed; used by integrity test 6."""
    parsed_lines = prompt.split("\n")
    instruction_header = parsed_lines[0]
    out = [instruction_header]
    in_instructions = True
    for line in parsed_lines[1:]:
        if in_instructions and _BULLET_RE.match(line):
            continue
        if in_instructions and _HEADER_RES["TASK"].match(line):
            in_instructions = False
        out.append(line)
    return "\n".join(out)
