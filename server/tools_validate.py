"""Prüft alle Inhaltsreferenzen (Items, Gegner, NPCs, Quests, Zonen)."""
import sys
sys.path.insert(0, ".")
from app.content import world as W
from app.content.items import ITEMS, SETS
from app.content import professions as P, achievements as A, collections as COL, factions as F
from app.content.abilities import ABILITIES
from app.content.classes import CLASSES
errs = []
def chk_item(i, where):
    if i not in ITEMS: errs.append(f"item {i!r} fehlt ({where})")
def chk_mob(m, where):
    if m not in W.MOBS: errs.append(f"mob {m!r} fehlt ({where})")
for mid, m in W.MOBS.items():
    for l in m.get("loot", []): chk_item(l["item"], "loot "+mid)
    bl = m.get("boss_loot")
    if bl:
        for i in bl.get("pool", []): chk_item(i, "boss_loot "+mid)
        if bl.get("legendary"): chk_item(bl["legendary"], "legendary "+mid)
    for k in ("hide", "cloth"):
        if m.get(k): chk_item(m[k], k+" "+mid)
    abl = list(m.get("abilities", []))
    for ph in m.get("phases", []) or []:
        abl += ph.get("abilities", []); abl += ph.get("on_enter", [])
    for a in abl:
        if a.get("summon"): chk_mob(a["summon"], "summon "+mid)
for zid, sp in W.SPAWNS.items():
    for s in sp: chk_mob(s["mob"], "spawn "+zid)
for zid, obs in W.OBJECTS.items():
    for o in obs:
        if o.get("item"): chk_item(o["item"], "obj "+zid)
        if o.get("node") and o["node"] not in P.NODES: errs.append(f"node {o['node']} fehlt")
        for it in o.get("loot", []): chk_item(it[0], "chest "+zid)
for nid, n in W.NPCS.items():
    for i in n.get("vendor", []): chk_item(i, "vendor "+nid)
    if n.get("trainer") and n["trainer"] not in CLASSES: errs.append(f"trainer {n['trainer']}")
for qid, q in W.QUESTS.items():
    for k in ("giver", "ender"):
        v = q[k]
        if v in ("item",) or v.startswith("board:"): continue
        if v not in W.NPCS: errs.append(f"npc {v!r} fehlt (quest {qid} {k})")
    if q.get("prev") and q["prev"] not in W.QUESTS: errs.append(f"prev {q['prev']} fehlt ({qid})")
    if q.get("start_item"): chk_item(q["start_item"], "start_item "+qid)
    for o in q["objectives"]:
        t = o["type"]
        if t == "kill":
            for mm in (o["mob"] if isinstance(o["mob"], list) else [o["mob"]]): chk_mob(mm, "quest "+qid)
        elif t == "collect": chk_item(o["item"], "quest "+qid)
        elif t in ("talk", "emote") and o["npc"] not in W.NPCS: errs.append(f"npc {o['npc']} fehlt (obj {qid})")
        elif t == "explore" and o.get("zone") and o["zone"] not in W.ZONES: errs.append(f"zone {o['zone']} fehlt ({qid})")
    r = q["rewards"]
    for it in r.get("items", []): chk_item(it[0], "reward "+qid)
    for it in r.get("choice", []): chk_item(it, "choice "+qid)
    for f in r.get("rep", {}):
        if f not in F.FACTIONS: errs.append(f"faction {f} ({qid})")
    if r.get("title") and r["title"] not in COL.TITLES: errs.append(f"title {r['title']} ({qid})")
    if q.get("dungeon") and q["dungeon"] not in W.ZONES: errs.append(f"dungeon {q['dungeon']} ({qid})")
for zid, z in W.ZONES.items():
    for p in z.get("portals", []):
        if p["to"] not in W.ZONES: errs.append(f"portal {zid}->{p['to']} (Zone fehlt)")
for sid, s in SETS.items():
    for i in s["items"]: chk_item(i, "set "+sid)
for cid, c in CLASSES.items():
    for slot, i in c["start"]["equip"].items(): chk_item(i, "start "+cid)
    for i, n in c["start"]["bags"]: chk_item(i, "start "+cid)
    if c["trainer"] not in W.NPCS: errs.append(f"trainer npc {c['trainer']} fehlt")
for rid, r in P.RECIPES.items():
    chk_item(r["result"], "recipe "+rid)
    for i, n in r["mats"]: chk_item(i, "recipe mats "+rid)
from collections import Counter
for e in sorted(set(errs)): print(e)
print(len(set(errs)), "Fehler |", len(W.ZONES), "Zonen", len(W.MOBS), "Gegner", len(W.NPCS), "NPCs", len(W.QUESTS), "Quests", len(ITEMS), "Items")
