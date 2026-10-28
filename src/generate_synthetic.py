"""Deterministic synthetic records for F4 (controlled extraction) and F5 (controlled transformation).

Original plan §11-§12 and brief §5.2: fixed source lists in code, seed 20261003, 22 records per family
(20 main + 2 pilot), all records distinct, and no commas inside any field value (dates are written as
"14 March 2025"; amounts and budgets are digits, budgets followed by " USD"). Templates may contain commas;
field values never do, so the NO_COMMA constraint can be met without altering any value.

Each family uses a fresh ``random.Random(seed)``. Values are sampled without replacement, so every
person, organization, city, date, amount, project, owner, deadline and budget is unique within its family.
"""

from __future__ import annotations

import calendar
import random

MONTHS = [calendar.month_name[m] for m in range(1, 13)]

# ---- F4: controlled information extraction -------------------------------------------------------
F4_PERSONS = [
    "Daniel Reed", "Aisha Karimi", "Tomas Novak", "Lena Fischer", "Omar Haddad", "Priya Nair",
    "Jonas Berg", "Elena Rossi", "Kofi Mensah", "Hana Sato", "Lucas Moreau", "Ingrid Larsen",
    "Rafael Ortega", "Yusuf Demir", "Clara Weber", "Nikhil Rao", "Sofia Lindqvist", "Mateo Silva",
    "Grace Okafor", "Victor Lambert", "Nadia Petrova", "Samuel Brooks", "Leila Farouk", "Ethan Park",
]
F4_ORGANIZATIONS = [
    "Northbridge Labs", "Harbor Point Logistics", "Bluefield Analytics", "Cedar Grove Health",
    "Ironwood Systems", "Silverline Energy", "Maple Ridge Foods", "Quarry Lane Engineering",
    "Redstone Medical", "Brightwater Utilities", "Kestrel Aviation", "Larkspur Textiles",
    "Granite Peak Mining", "Willow Creek Pharma", "Summit Rail Services", "Oakmont Robotics",
    "Riverside Water Trust", "Falcon Crest Insurance", "Pinehurst Media", "Copperfield Chemicals",
    "Seaview Shipping", "Highgate Instruments", "Elmstead Construction", "Lakeshore Biotech",
]
F4_CITIES = [
    "Leeds", "Lyon", "Porto", "Gdansk", "Utrecht", "Graz", "Bergen", "Tampere", "Brno", "Malmo",
    "Bilbao", "Ghent", "Aarhus", "Krakow", "Seville", "Turin", "Lausanne", "Galway", "Dundee",
    "Rotterdam", "Bologna", "Antwerp", "Salzburg", "Tallinn",
]
# (plural noun, past participle); stored as event_type "<noun> <participle>" as in original plan §11.
F4_EVENT_TYPES = [
    ("devices", "inspected"),
    ("samples", "tested"),
    ("contracts", "signed"),
    ("parcels", "delivered"),
    ("applications", "reviewed"),
]
F4_TEMPLATES = {
    "T01": "On {date}, {person} from {organization} visited the {city} facility. During the visit, "
           "{amount} {noun} were {verb} before the team closed the report.",
    "T02": "{person} of {organization} reported that {amount} {noun} were {verb} at the {city} site on {date}.",
    "T03": "During a review held in {city} on {date}, {organization} confirmed through {person} that "
           "{amount} {noun} had been {verb}.",
    "T04": "A report filed by {person} states that {organization} had {amount} {noun} {verb} in {city} on {date}.",
    "T05": "According to {person}, the {city} office of {organization} recorded that {amount} {noun} were "
           "{verb} on {date}.",
}
F4_YEARS = (2024, 2025)
F4_AMOUNT_RANGE = (32, 980)  # above any day number, below any year; never 20 or 25 (numbers in T2)

# ---- F5: controlled structured transformation ----------------------------------------------------
F5_PROJECTS = [
    "Orion", "Helix", "Nimbus", "Cobalt", "Juniper", "Meridian", "Polaris", "Quartz", "Sable", "Tundra",
    "Vertex", "Zephyr", "Aurora", "Beacon", "Cascade", "Ember", "Lumen", "Mosaic", "Onyx", "Pioneer",
    "Solstice", "Trident", "Saffron", "Bastion",
]
F5_OWNERS = [
    "Mira Chen", "Arjun Mehta", "Freya Nilsson", "Diego Alvarez", "Amara Obi", "Felix Wagner",
    "Yara Saleh", "Henrik Dahl", "Lucia Romano", "Kenji Watanabe", "Bianca Costa", "Tobias Klein",
    "Selin Aydin", "Marcus Hale", "Ines Duarte", "Pavel Horak", "Chloe Martin", "Rohan Iyer",
    "Astrid Holm", "Emeka Nwosu", "Julia Kowalski", "Adrian Vos", "Noor Rahman", "Oscar Lindgren",
]
# "approved" is deliberately absent: every F5 input contains the label "Approved budget".
F5_STATUSES = ["delayed", "completed", "on hold", "in progress", "under review", "cancelled", "at risk", "on track"]
F5_TEMPLATE = (
    "Project: {project}.\n"
    "Owner: {owner}.\n"
    "Current status: {status}.\n"
    "Deadline: {deadline}.\n"
    "Approved budget: {budget}."
)
F5_YEARS = (2025, 2026, 2027)
F5_BUDGET_RANGE = (15000, 950000, 500)  # start, stop (inclusive), step


def _unique_dates(rng: random.Random, years: tuple[int, ...], n: int) -> list[str]:
    candidates = [(y, m, d) for y in years for m in range(1, 13) for d in range(1, 29)]
    picked = rng.sample(candidates, n)
    return [f"{d} {MONTHS[m - 1]} {y}" for (y, m, d) in picked]


def generate_f4(seed: int, n: int) -> list[dict]:
    rng = random.Random(seed)
    persons = rng.sample(F4_PERSONS, n)
    organizations = rng.sample(F4_ORGANIZATIONS, n)
    cities = rng.sample(F4_CITIES, n)
    dates = _unique_dates(rng, F4_YEARS, n)
    amounts = rng.sample(range(F4_AMOUNT_RANGE[0], F4_AMOUNT_RANGE[1] + 1), n)
    template_ids = list(F4_TEMPLATES)
    records = []
    for i in range(n):
        noun, verb = rng.choice(F4_EVENT_TYPES)
        template_id = template_ids[i % len(template_ids)]
        fields = {
            "person": persons[i],
            "organization": organizations[i],
            "city": cities[i],
            "date": dates[i],
            "amount": str(amounts[i]),
        }
        text = F4_TEMPLATES[template_id].format(noun=noun, verb=verb, **fields)
        records.append(
            {
                "gold": fields,
                "input_text": text,
                "metadata": {"template_id": template_id, "event_type": f"{noun} {verb}", "seed": seed},
            }
        )
    _check_records(records)
    return records


def generate_f5(seed: int, n: int) -> list[dict]:
    rng = random.Random(seed)
    projects = rng.sample(F5_PROJECTS, n)
    owners = rng.sample(F5_OWNERS, n)
    deadlines = _unique_dates(rng, F5_YEARS, n)
    start, stop, step = F5_BUDGET_RANGE
    budgets = rng.sample(range(start, stop + 1, step), n)
    records = []
    for i in range(n):
        fields = {
            "project": projects[i],
            "owner": owners[i],
            "status": rng.choice(F5_STATUSES),
            "deadline": deadlines[i],
            "budget": f"{budgets[i]} USD",
        }
        records.append(
            {
                "gold": fields,
                "input_text": F5_TEMPLATE.format(**fields),
                "metadata": {"template_id": "F5_T01", "seed": seed},
            }
        )
    _check_records(records)
    return records


def _check_records(records: list[dict]) -> None:
    texts = [r["input_text"] for r in records]
    if len(set(texts)) != len(texts):
        raise ValueError("synthetic records are not distinct")
    for r in records:
        for key, value in r["gold"].items():
            if "," in value or "，" in value:
                raise ValueError(f"comma in synthetic field {key}={value!r}")
            if value not in r["input_text"]:
                raise ValueError(f"field {key}={value!r} missing from input text")


if __name__ == "__main__":
    import json

    for name, fn in (("F4", generate_f4), ("F5", generate_f5)):
        for rec in fn(20261003, 22)[:2]:
            print(name, json.dumps(rec, ensure_ascii=False))
