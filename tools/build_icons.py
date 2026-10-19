"""Sammelt alle im Spiel verwendeten Symbolnamen und schreibt deren SVG-Pfade nach client/assets/icons.json.

Symbole: game-icons.net (Lorc, Delapouite & Mitwirkende), Lizenz CC BY 3.0.
Aufruf: python3 tools/build_icons.py <pfad/zu/@iconify-json/game-icons/icons.json>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.content import world as W  # noqa: E402
from app.content.abilities import ABILITIES  # noqa: E402
from app.content.achievements import ACHIEVEMENTS  # noqa: E402
from app.content.classes import CLASSES  # noqa: E402
from app.content.factions import CURRENCIES, FACTIONS  # noqa: E402
from app.content.items import ITEMS  # noqa: E402
from app.content.professions import PROFESSIONS  # noqa: E402
from app.content.talents import TALENTS  # noqa: E402

src = json.load(open(sys.argv[1]))
icons = src["icons"]
aliases = src.get("aliases", {})

names = set()
for d in (ABILITIES, ITEMS, ACHIEVEMENTS, TALENTS, PROFESSIONS, FACTIONS, CURRENCIES, CLASSES):
    for v in d.values():
        if isinstance(v.get("icon"), str):
            names.add(v["icon"])
# Symbole der Benutzeroberfläche
names |= {"backpack", "scroll-unfurled", "spell-book", "skills", "treasure-map", "medal", "family-tree", "crossed-swords",
          "envelope", "shop", "two-coins", "cog", "help", "exit-door", "magnifying-glass", "trophy-cup", "horse-head",
          "paw", "crown", "heart-plus", "shield", "sword-wound", "anvil-impact", "round-bottom-flask", "mining",
          "herbs-bundle", "leather-vest", "magic-swirl", "skull-crossed-bones", "chat-bubble", "person", "team-idea",
          "dungeon-gate", "portal", "stone-tablet", "padlock", "open-treasure-chest", "chest", "gold-bar", "wooden-sign",
          "warlord-helmet", "abdominal-armor", "shoulder-armor", "gauntlet", "leg-armor", "boots", "cape", "necklace",
          "ring", "broadsword", "checked-shield", "bolt", "fist", "healing", "warn", "gathering", "hourglass",
          "battle-gear", "barbute", "pointy-hat", "rune-stone", "party-popper", "laurels", "world", "compass",
          "sun", "moon", "fire", "frozen-orb", "earth-crack", "vortex", "angel-wings", "meat", "water-flask", "sleepy",
          "cloak-dagger", "bear-head", "enrage", "rock", "skull", "drop", "lightning-arc", "sprint", "jump-across"}
# alle Symbolnamen, die im Client-Quelltext als Zeichenkette vorkommen
for f in (ROOT / "client" / "src").rglob("*.gd"):
    for lit in re.findall(r'"([a-z0-9]+(?:-[a-z0-9]+)*)"', f.read_text(encoding="utf-8")):
        if lit in icons:
            names.add(lit)
# Zonen-/Mob-/NPC-Symbole aus den Inhalten
for coll in (getattr(W, "MOBS", {}), getattr(W, "NPCS", {})):
    for v in coll.values():
        if isinstance(v, dict) and isinstance(v.get("icon"), str):
            names.add(v["icon"])
ALIAS = {"badge": "police-badge", "bolt": "bolt-spell-cast", "crypt": "crypt-entrance", "drain": "marrow-drain",
         "gathering": "flower-pot", "last-stand": "standing-potion", "monocle": "spectacles", "pelt": "fur-shirt",
         "resurrected": "angel-outfit", "seal": "wax-seal", "skull": "death-skull", "thistle": "thorny-vine",
         "warn": "hazard-sign"}
out = {}
missing = []
for n in sorted(names):
    key = ALIAS.get(n, n)
    if key not in icons and key in aliases:
        key = aliases[key]["parent"]
    if key in icons:
        body = icons[key]["body"]
        m = re.findall(r'd="([^"]+)"', body)
        out[n] = m
    else:
        missing.append(n)
dst = ROOT / "client" / "assets" / "icons.json"
dst.write_text(json.dumps(out, separators=(",", ":")))
print(len(out), "Symbole geschrieben,", len(missing), "fehlen:", missing[:80])
