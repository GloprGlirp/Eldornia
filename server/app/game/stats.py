"""Werteberechnung für Spielercharaktere: Grundwerte + Ausrüstung + Sets + Verzauberungen + Talente + Auren."""
from __future__ import annotations

from ..content.classes import base_hp, base_stats
from ..content.enchants import ENCHANTS
from ..content.items import ITEMS, SETS
from ..content.talents import talent_mods
from .entities import Player, resource_max

PRIMARY = ("str", "agi", "sta", "int", "spi")
RESISTS = ("fire_res", "frost_res", "nature_res", "shadow_res", "arcane_res")


def set_counts(p: Player) -> dict[str, int]:
    counts: dict[str, int] = {}
    for slot, inst in p.equipment.items():
        it = ITEMS.get(inst["i"]) if inst else None
        if it and it.get("set"):
            counts[it["set"]] = counts.get(it["set"], 0) + 1
    return counts


def active_set_bonuses(p: Player) -> list[dict]:
    out = []
    for sid, n in set_counts(p).items():
        s = SETS.get(sid)
        if not s:
            continue
        for need, bonus in s["bonuses"].items():
            if n >= need:
                out.append(bonus)
    return out


def recalc(p: Player, full: bool = False):
    cls = p.cls
    lvl = p.level
    st = {k: float(v) for k, v in base_stats(p.class_id, lvl).items()}
    for k in ("armor", "ap", "sp", "heal", "crit", "haste", "block", "dodge", "parry", "mp5", *RESISTS):
        st[k] = 0.0
    # --- Ausrüstung
    two_hand = False
    for slot, inst in p.equipment.items():
        if not inst:
            continue
        it = ITEMS.get(inst["i"])
        if not it:
            continue
        if inst.get("d", 100) <= 0:
            continue   # kaputte Gegenstände geben keine Werte
        if slot == "main_hand" and it.get("two_hand"):
            two_hand = True
        for k, v in it.get("stats", {}).items():
            st[k] = st.get(k, 0.0) + v
        st["armor"] += it.get("armor", 0)
        ench = ENCHANTS.get(inst.get("e") or "")
        if ench:
            for k, v in ench.get("stats", {}).items():
                st[k] = st.get(k, 0.0) + v
    # --- Sets
    pct_extra: dict[str, float] = {}
    school_extra: dict[str, float] = {}
    procs = []
    for bonus in active_set_bonuses(p):
        for k, v in bonus.get("stats", {}).items():
            st[k] = st.get(k, 0.0) + v
        for k, v in bonus.get("pct", {}).items():
            pct_extra[k] = pct_extra.get(k, 0.0) + v
        for k, v in bonus.get("school_pct", {}).items():
            school_extra[k] = school_extra.get(k, 0.0) + v
        if bonus.get("proc"):
            procs.append(bonus["proc"])
    # --- Talente
    mods, grants = talent_mods(p.class_id, p.talents)
    for k, v in school_extra.items():
        mods["school_pct:" + k] = mods.get("school_pct:" + k, 0.0) + v
    for k, v in pct_extra.items():
        key = {"dmg_done": "dmg_pct", "heal_done": "heal_pct", "dmg_taken": "dmg_taken_pct"}.get(k, k)
        mods[key] = mods.get(key, 0.0) + v
    # --- Auren
    for a in p.auras:
        for k, v in a.stats.items():
            st[k] = st.get(k, 0.0) + v
    # Prozentwerte auf Primärattribute
    for k in PRIMARY:
        if mods.get(k + "_pct"):
            st[k] *= 1.0 + mods[k + "_pct"] / 100.0
    form = p.form()
    # --- Abgeleitete Werte
    ap_def = cls.get("ap", {"str": 1.0})
    st["ap"] += st["str"] * ap_def.get("str", 0) + st["agi"] * ap_def.get("agi", 0) + lvl * 2
    if form == "baer":
        st["ap"] += st["str"] * 1.0 + st["agi"] * 0.5 + lvl * 3
    st["sp"] += st["int"] * cls.get("sp_int", 0.0)
    st["heal"] += st["sp"]
    agi_k = 4.0 + lvl * 0.6
    int_k = 6.0 + lvl * 0.9
    st["crit"] += 5.0 + st["agi"] / agi_k + mods.get("crit", 0.0)
    st["spell_crit"] = 5.0 + st["int"] / int_k + mods.get("crit", 0.0) + mods.get("spell_crit", 0.0) + (st["crit"] - 5.0 - st["agi"] / agi_k)
    st["dodge"] += 3.0 + st["agi"] / (5.0 + lvl * 0.8) + mods.get("dodge", 0.0)
    has_weapon = p.item_def("main_hand") is not None
    st["parry"] += (cls.get("parry", 0.0) if has_weapon else 0.0) + mods.get("parry", 0.0)
    st["block"] = (st["block"] + cls.get("block", 0.0) + mods.get("block", 0.0)) if p.has_shield() else 0.0
    st["block_value"] = int(5 + st["str"] / 2 + lvl)
    haste_aura = p.aura_pct("haste")
    st["haste"] += mods.get("haste", 0.0) + haste_aura
    armor = st["armor"] + st["agi"] * 2.0
    armor *= 1.0 + mods.get("armor_pct", 0.0) / 100.0
    if form == "baer":
        armor *= 2.8
    st["armor"] = armor
    hp_pct = mods.get("hp_pct", 0.0) + p.aura_pct("max_hp") + (25.0 if form == "baer" else 0.0)
    old_max_hp, old_max_pw = p.max_hp, p.max_power
    p.max_hp = int((base_hp(p.class_id, lvl) + st["sta"] * 10) * (1.0 + hp_pct / 100.0))
    rmax = resource_max(p.power_type)
    if p.power_type == "mana":
        p.max_power = int((40 + 15 * lvl + st["int"] * 12) * (1.0 + mods.get("mana_pct", 0.0) / 100.0))
    else:
        p.max_power = rmax or 100
    st["hp_regen"] = 0.5 + st["spi"] * 0.15 + lvl * 0.12
    st["mp_regen"] = (st["spi"] * 0.3 + lvl * 0.6 + st["mp5"] / 5.0) * (1.0 + mods.get("regen_pct", 0.0) / 100.0)
    w = p.weapon()
    speed = w["speed"] / (1.0 + st["haste"] / 100.0)
    if form == "baer":
        w = {"min": 4 + lvl * 2, "max": 8 + lvl * 3, "speed": 2.5, "sub": "klaue"}
        speed = 2.5 / (1.0 + st["haste"] / 100.0)
    bonus = st["ap"] / 14.0 * w["speed"]
    st["dmg_min"] = int(w["min"] + bonus)
    st["dmg_max"] = int(w["max"] + bonus)
    st["speed"] = round(speed, 2)
    st["wspeed"] = w["speed"]
    if p.dual_wielding():
        ow = p.weapon(off=True)
        ob = st["ap"] / 14.0 * ow["speed"]
        off_mult = 0.5 * (1.0 + mods.get("offhand_pct", 0.0) / 100.0)
        st["oh_min"] = int((ow["min"] + ob) * off_mult)
        st["oh_max"] = int((ow["max"] + ob) * off_mult)
        st["oh_speed"] = round(ow["speed"] / (1.0 + st["haste"] / 100.0), 2)
    st["two_hand"] = two_hand
    st["ranged"] = p.ranged()
    p.stats = st
    p.mods = mods
    p.granted = grants
    p.set_procs = procs
    p.resist = {"fire": st["fire_res"], "frost": st["frost_res"], "nature": st["nature_res"],
                "shadow": st["shadow_res"], "arcane": st["arcane_res"]}
    if full:
        p.hp = p.max_hp
        p.power = p.max_power if p.power_type in ("mana", "energy", "concentration") else 0
    else:
        if p.max_hp > old_max_hp and old_max_hp > 1:
            p.hp = min(p.max_hp, p.hp + (p.max_hp - old_max_hp))
        p.hp = min(p.hp, p.max_hp)
        if p.power_type == "mana" and p.max_power > old_max_pw and old_max_pw > 0:
            p.power = min(p.max_power, p.power + (p.max_power - old_max_pw))
        p.power = min(p.power, p.max_power)
    p.mark("hp", "pw")


def client_stats(p: Player) -> dict:
    st = p.stats
    keys = ("str", "agi", "sta", "int", "spi", "armor", "ap", "sp", "heal", "crit", "spell_crit", "haste", "dodge",
            "parry", "block", "dmg_min", "dmg_max", "speed", "hp_regen", "mp_regen", *RESISTS)
    out = {}
    for k in keys:
        v = st.get(k, 0)
        out[k] = round(v, 1) if isinstance(v, float) else v
    return out
