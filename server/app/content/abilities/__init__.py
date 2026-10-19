"""Alle Spielerfähigkeiten."""
from . import barbar, bogenschuetze, druide, magier, raeuber, ritter, samurai, totenbeschwoerer
from ._base import GCD, GCD_FAST, SCHOOL_COLORS, SCHOOL_NAMES

ABILITIES: dict[str, dict] = {}
for _mod in (ritter, magier, raeuber, samurai, bogenschuetze, barbar, druide, totenbeschwoerer):
    for _a in _mod.ABILITIES:
        ABILITIES[_a["id"]] = _a

FAST_GCD_CLASSES = {"raeuber", "samurai"}


def class_abilities(class_id: str, include_talents: bool = False) -> list[str]:
    out = [a["id"] for a in ABILITIES.values() if a["cls"] == class_id and (include_talents or not a["talent"])]
    return sorted(out, key=lambda i: (ABILITIES[i]["level"], ABILITIES[i]["slot"] or 99))


def scaled(pair, level: int) -> float:
    if pair is None:
        return 0.0
    return pair[0] + pair[1] * level


def scaled_range(spec, level: int) -> tuple[int, int]:
    return int(spec[0] + spec[1] * level), int(spec[2] + spec[3] * level)


def ability_range(ab: dict) -> float:
    rng = ab["range"]
    return 5.0 if rng == "melee" else float(rng)


def first_effect(ab: dict, t: str):
    for e in ab["effects"]:
        if e.get("t") == t:
            return e
        if e.get("t") == "trap":
            for e2 in e["trap"].get("on_trigger", []):
                if e2.get("t") == t:
                    return e2
        if e.get("t") == "ground_dot":
            for e2 in e.get("effects", []):
                if e2.get("t") == t:
                    return e2
    return None


def describe(ab_id: str, level: int) -> str:
    ab = ABILITIES[ab_id]
    text = ab["desc"]
    d = first_effect(ab, "dmg")
    if d and "{dmg}" in text:
        if d.get("per_cp"):
            lo, hi = scaled_range(d["base"], level)
            extra = scaled(d["per_cp"], level)
            text = text.replace("{dmg}", f"{int(lo + extra)}–{int(hi + extra)}")
        else:
            lo, hi = scaled_range(d["base"], level)
            text = text.replace("{dmg}", f"{lo}–{hi}")
    elif "{dmg}" in text:
        ex = first_effect(ab, "explode_pet")
        if ex:
            lo, hi = scaled_range(ex["base"], level)
            text = text.replace("{dmg}", f"{lo}–{hi}")
    w = first_effect(ab, "weapon")
    if w and "{bonus}" in text:
        text = text.replace("{bonus}", str(int(scaled(w["bonus"], level))))
    h = first_effect(ab, "heal")
    if h and "{heal}" in text:
        lo, hi = scaled_range(h["base"], level)
        text = text.replace("{heal}", f"{lo}–{hi}")
    a = first_effect(ab, "aura")
    if a:
        for stat, pair in a["aura"].get("stats", {}).items():
            text = text.replace("{" + stat + "}", str(int(scaled(pair, level))))
    return text


def ability_client_info(ab_id: str, level: int, mods: dict | None = None) -> dict:
    ab = ABILITIES[ab_id]
    mods = mods or {}
    cd = max(0.0, ab["cd"] + mods.get("cd:" + ab_id, 0.0))
    cast = max(0.0, ab["cast"] + mods.get("cast:" + ab_id, 0.0)) if ab["cast"] else 0.0
    return {
        "id": ab_id, "name": ab["name"], "level": ab["level"], "icon": ab["icon"], "school": ab["school"],
        "color": ab["color"], "cost": ab["cost"], "cost_pct": ab["cost_pct"], "cast": round(cast, 2),
        "channel": ab["channel"], "cd": round(cd, 1), "gcd": ab["gcd"], "range": ability_range(ab),
        "min_range": ab["min_range"], "melee": ab["range"] == "melee", "target": ab["target"],
        "desc": describe(ab_id, level), "talent": ab["talent"], "form": ab["form"], "ground": ab["ground"],
        "area": ab["area"], "slot": ab["slot"], "tags": ab["tags"], "req": {k: v for k, v in ab["req"].items() if k != "weapon"},
    }
