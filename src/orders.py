"""Instruction orders P01-P10: a Williams design for five instructions (brief §5.4).

Letters: A = T1 (FORMAT), B = T2 (LENGTH), C = T3 (CARDINALITY), D = T4, E = T5 (VERBATIM).
"""

from __future__ import annotations

from collections import Counter
from itertools import permutations

LETTER_TO_SLOT = {"A": "T1", "B": "T2", "C": "T3", "D": "T4", "E": "T5"}
LETTERS = tuple(LETTER_TO_SLOT)

# Hard-coded; never derived or re-ordered at runtime.
ORDERS: dict[str, str] = {
    "P01": "ABCDE",
    "P02": "BDAEC",
    "P03": "DEBCA",
    "P04": "ECDAB",
    "P05": "CAEBD",
    "P06": "EDCBA",
    "P07": "CEADB",
    "P08": "ACBED",
    "P09": "BADCE",
    "P10": "DBEAC",
}
ORDER_IDS = tuple(ORDERS)
CANONICAL_ORDER_ID = "P01"


def order_slots(order_id: str) -> list[str]:
    """Slots (T1..T5) in presentation order for one order id."""
    return [LETTER_TO_SLOT[letter] for letter in ORDERS[order_id]]


def verify_orders(orders: dict[str, str] = ORDERS) -> dict:
    """Check the Williams-design properties and return a summary; raise ValueError on any violation.

    1. Every order is a permutation of A-E.
    2. Every instruction appears in every position exactly twice.
    3. Every ordered adjacent pair (X immediately followed by Y, X != Y) appears exactly twice.
    4. For every pair, X precedes Y in exactly 5 of the 10 orders.
    """
    errors: list[str] = []
    n = len(orders)
    if n != 10:
        errors.append(f"expected 10 orders, found {n}")
    for oid, seq in orders.items():
        if sorted(seq) != sorted(LETTERS):
            errors.append(f"{oid}={seq} is not a permutation of {''.join(LETTERS)}")

    position_counts = Counter((letter, pos) for seq in orders.values() for pos, letter in enumerate(seq, 1))
    bad_positions = {k: v for k, v in position_counts.items() if v != 2}
    missing_positions = [(x, p) for x in LETTERS for p in range(1, 6) if (x, p) not in position_counts]
    if bad_positions or missing_positions:
        errors.append(f"position balance violated: {bad_positions or ''} missing={missing_positions}")

    adjacent = Counter((seq[i], seq[i + 1]) for seq in orders.values() for i in range(len(seq) - 1))
    all_pairs = [(x, y) for x, y in permutations(LETTERS, 2)]
    bad_adjacent = {p: adjacent.get(p, 0) for p in all_pairs if adjacent.get(p, 0) != 2}
    if bad_adjacent:
        errors.append(f"adjacency balance violated: {bad_adjacent}")

    precedes = {(x, y): sum(seq.index(x) < seq.index(y) for seq in orders.values()) for x, y in all_pairs}
    bad_precedes = {p: c for p, c in precedes.items() if c != 5}
    if bad_precedes:
        errors.append(f"precedence balance violated: {bad_precedes}")

    if errors:
        raise ValueError("Williams design check failed: " + "; ".join(errors))
    return {
        "n_orders": n,
        "position_counts": "every instruction appears in every position exactly 2 times",
        "adjacent_pairs": f"all {len(all_pairs)} ordered adjacent pairs appear exactly 2 times",
        "precedence": "X precedes Y in exactly 5 of 10 orders for every ordered pair",
    }


def e2_informative_positions(orders: dict[str, str] = ORDERS) -> dict[str, list[int]]:
    """Exploratory analysis E2 (decision D03 §3): for each instruction that refers to the JSON keys FORMAT
    introduces (B-E), the positions at which it occurs both before FORMAT (A) and after it across the orders.
    The E2 contrast is estimated only within these positions."""
    out = {}
    for letter in "BCDE":
        seen: dict[int, set[bool]] = {}
        for seq in orders.values():
            seen.setdefault(seq.index(letter) + 1, set()).add(seq.index(letter) < seq.index("A"))
        out[LETTER_TO_SLOT[letter]] = sorted(pos for pos, values in seen.items() if values == {True, False})
    return out


if __name__ == "__main__":
    import json

    print(json.dumps(verify_orders(), indent=2))
