"""Bausteine für Fähigkeiten (Kampfsystem im Stil von World of Warcraft).

Eine Fähigkeit besteht aus Kosten, Zauberzeit, Abklingzeit, Reichweite, Zielart und einer Liste von
Effekten. Die Effekte werden serverseitig von game/abilities.py ausgeführt.

Skalierung: Werte der Form (a, b) bedeuten a + b * Stufe. Schadensbereiche (a, b, c, d) bedeuten
min = a + b * Stufe, max = c + d * Stufe.
"""

GCD = 1.5
GCD_FAST = 1.0          # Energie- und Fokusklassen


def ab(aid, name, cls, level, icon, *, school="physical", cost=0, cost_pct=0.0, cast=0.0, cd=0.0, gcd=True,
       rng="melee", min_range=0.0, target="enemy", effects=(), area=None, req=None, proj=None, channel=False,
       ticks=0, desc="", color=None, tags=(), talent=False, form=None, off_gcd=False, charges=0, slot=0,
       requires_target_alive=True, no_move=False, ground=False):
    """Erzeugt eine Fähigkeitsdefinition."""
    return {
        "id": aid, "name": name, "cls": cls, "level": level, "icon": icon, "school": school,
        "cost": cost, "cost_pct": cost_pct, "cast": cast, "cd": cd, "gcd": gcd and not off_gcd,
        "range": rng, "min_range": min_range, "target": target, "effects": list(effects), "area": area,
        "req": req or {}, "proj": proj, "channel": channel, "ticks": ticks, "desc": desc,
        "color": color or SCHOOL_COLORS.get(school, "#ffffff"), "tags": list(tags), "talent": talent,
        "form": form, "charges": charges, "slot": slot, "no_move": no_move, "ground": ground,
    }


SCHOOL_COLORS = {
    "physical": "#d9c8a0", "fire": "#ff7a1a", "frost": "#7fd0ff", "arcane": "#d58cff", "nature": "#7ad04a",
    "shadow": "#9a5ad0", "holy": "#ffe080", "blood": "#d03030",
}

SCHOOL_NAMES = {
    "physical": "Körperlich", "fire": "Feuer", "frost": "Frost", "arcane": "Arkan", "nature": "Natur",
    "shadow": "Schatten", "holy": "Heilig", "blood": "Blut",
}


# ----------------------------------------------------------------------------- Effekte
def W(mult=1.0, bonus=(0, 0), threat=0, crit_bonus=0.0, behind_bonus=0.0, per_cp=None, ignore_armor=0.0,
      offhand=False, rage_scale=0.0, cp_finish=False, marked_bonus=0.0):
    """Waffenschlag: Waffenschaden * mult + bonus."""
    return {"t": "weapon", "mult": mult, "bonus": bonus, "threat": threat, "crit_bonus": crit_bonus,
            "behind_bonus": behind_bonus, "per_cp": per_cp, "ignore_armor": ignore_armor, "offhand": offhand,
            "rage_scale": rage_scale, "cp_finish": cp_finish, "marked_bonus": marked_bonus}


def D(school, base, coef=0.0, stat="sp", threat=1.0, per_cp=None, cp_finish=False, bonus_vs=None,
      execute_bonus=0.0, range_bonus=None, marked_bonus=0.0, crit_bonus=0.0):
    """Direkter Schaden einer Schule (base = (min_a, min_b, max_a, max_b))."""
    return {"t": "dmg", "school": school, "base": base, "coef": coef, "stat": stat, "threat": threat,
            "per_cp": per_cp, "cp_finish": cp_finish, "bonus_vs": bonus_vs, "execute_bonus": execute_bonus,
            "range_bonus": range_bonus, "marked_bonus": marked_bonus, "crit_bonus": crit_bonus}


def H(base, coef=0.0, on="target", stat="sp", pct_max=0.0):
    """Heilung."""
    return {"t": "heal", "base": base, "coef": coef, "on": on, "stat": stat, "pct_max": pct_max}


def A(aura, on="target"):
    """Aura (Buff/Debuff) auf Ziel, sich selbst, Gruppe oder Begleiter."""
    return {"t": "aura", "aura": aura, "on": on}


def AURA(aid, name, dur, icon=None, debuff=False, **kw):
    a = {"id": aid, "name": name, "dur": dur, "icon": icon, "debuff": debuff}
    a.update(kw)
    return a


def CC(kind, dur, **kw):
    """Kontrolleffekt: stun, root, fear, poly, silence, slow, sleep."""
    d = {"t": "cc", "kind": kind, "dur": dur}
    d.update(kw)
    return d


def TAUNT(dur=3.0):
    return {"t": "taunt", "dur": dur}


def INTERRUPT(lock=4.0):
    return {"t": "interrupt", "lock": lock}


def GAIN(amount):
    return {"t": "gain", "amount": amount}


def CP(n=1):
    return {"t": "combo", "n": n}


def CHARGE(stun=1.0):
    return {"t": "charge", "stun": stun}


def LEAP(dist=20.0):
    return {"t": "leap", "dist": dist}


def BLINK(dist=15.0):
    return {"t": "blink", "dist": dist}


def DISENGAGE(dist=12.0):
    return {"t": "disengage", "dist": dist}


def DASH(dist=12.0):
    return {"t": "dash", "dist": dist}


def SUMMON(pet, max_n=1, dur=0.0, count=1):
    return {"t": "summon", "pet": pet, "max": max_n, "dur": dur, "count": count}


def TRAP(trap):
    return {"t": "trap", "trap": trap}


def DISPEL(kinds=("magic",), on="target", n=1):
    return {"t": "dispel", "kinds": list(kinds), "on": on, "n": n}


def DROP_THREAT():
    return {"t": "drop_threat"}


def STEALTH():
    return {"t": "stealth"}


def REZ(pct=0.5):
    return {"t": "rez", "pct": pct}


def FORM(form):
    return {"t": "form", "form": form}


def EXPLODE_PET(base, coef=0.5, radius=8.0):
    return {"t": "explode_pet", "base": base, "coef": coef, "radius": radius}


def PET_CMD(cmd):
    return {"t": "pet_cmd", "cmd": cmd}


def AREA(shape="circle", radius=8.0, center="self", max_targets=10, angle=90.0):
    return {"shape": shape, "radius": radius, "center": center, "max": max_targets, "angle": angle}
