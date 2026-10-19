"""Soziales (GDD 10): Chat, Gruppen & Raids, Gruppenfinder, Gilden, Freunde, Handel, Duelle und Arena."""
from __future__ import annotations

import itertools
import logging
import math
import random
import re
import time

from sqlalchemy import delete, select

from .. import config
from ..content import world as W
from ..content.classes import CLASSES
from ..content.items import ITEMS
from ..db import SessionLocal
from ..models import ArenaMatch, Character, Friend, Guild, GuildBankItem, GuildLog, GuildMember, Transaction
from .entities import Mob, Npc, Player, now

log = logging.getLogger("eldornia.social")

PARTY_MAX = 5
RAID_MAX = 10
GUILD_COST = 100000          # 10 Gold
GUILD_NAME_RE = re.compile(r"^[A-Za-zÄÖÜäöüß' ]{3,24}$")
GUILD_BANK_SLOTS = 98
MEMBER_WITHDRAW_PER_DAY = 5
CHAT_LIMIT = 6              # Nachrichten pro 10 Sekunden
DUEL_RANGE = 60.0
EMOTES = {
    "tanzen": ("dance", "tanzt."), "winken": ("wave", "winkt."), "verbeugen": ("bow", "verbeugt sich."),
    "lachen": ("laugh", "lacht."), "jubeln": ("cheer", "jubelt."), "sitzen": ("sit", "setzt sich."),
    "weinen": ("cry", "weint."), "zeigen": ("point", "zeigt nach vorn."), "salutieren": ("salute", "salutiert."),
    "klatschen": ("clap", "klatscht Beifall."), "schlafen": ("sleep", "legt sich schlafen."), "knien": ("kneel", "kniet nieder."),
}
GUILD_GOALS = [
    {"id": "kills", "name": "Monsterjagd", "desc": "Besiegt gemeinsam 1000 Gegner.", "counter": "kills", "n": 1000},
    {"id": "dungeons", "name": "Dungeonwoche", "desc": "Schließt gemeinsam 15 Dungeons ab.", "counter": "dungeons", "n": 15},
    {"id": "gather", "name": "Ernte der Gilde", "desc": "Sammelt gemeinsam 300 Erze und Kräuter.", "counter": "gathered", "n": 300},
    {"id": "quests", "name": "Auftragsbuch", "desc": "Schließt gemeinsam 120 Quests ab.", "counter": "quests", "n": 120},
    {"id": "crafts", "name": "Werkstattwoche", "desc": "Stellt gemeinsam 150 Gegenstände her.", "counter": "crafts", "n": 150},
]
RANK_NAMES = {"leiter": "Gildenleiter", "offizier": "Offizier", "mitglied": "Mitglied", "rekrut": "Rekrut"}
RANK_ORDER = ["rekrut", "mitglied", "offizier", "leiter"]


class Party:
    _ids = itertools.count(1)

    def __init__(self, leader: Player):
        self.id = next(Party._ids)
        self.leader = leader.id
        self.members: list[int] = [leader.id]
        self.raid = False
        self.loot = "personal"

    @property
    def max(self) -> int:
        return RAID_MAX if self.raid else PARTY_MAX


class GuildState:
    def __init__(self, g: Guild):
        self.id = g.id
        self.name = g.name
        self.tag = g.tag
        self.leader = g.leader_character_id
        self.motd = g.motd
        self.copper = g.copper
        self.weekly = dict(g.weekly or {})
        self.level = g.level
        self.xp = g.xp
        self.members: dict[int, dict] = {}
        self.bank: list = [None] * GUILD_BANK_SLOTS
        self.log: list[str] = []


class SocialMixin:
    # ================================================================== Chat
    def chat(self, p: Player, m: dict):
        text = str(m.get("text", ""))[:255].strip()
        if not text:
            return
        t = now()
        p.chat_times = [x for x in p.chat_times if t - x < 10]
        if len(p.chat_times) >= CHAT_LIMIT:
            self.err(p, "Ihr sprecht zu schnell.")
            return
        p.chat_times.append(t)
        if text.startswith("."):
            self.admin_command(p, text)
            return
        if text.startswith("/"):
            self.slash_command(p, text)
            return
        ch = m.get("ch", "say")
        payload = {"t": "chat", "ch": ch, "from": p.name, "fid": p.id, "text": text, "cls": p.class_id, "gm": p.gm}
        if ch == "say":
            for o in p.zone.players_near(p.x, p.z, 40):
                self.send(o, payload)
            p.zone.emit_fx(p.x, p.z, {"k": "say", "id": p.id, "text": text[:120]})
        elif ch == "yell":
            for o in p.zone.players_near(p.x, p.z, 160):
                self.send(o, payload)
        elif ch in ("party", "raid"):
            if not p.party:
                self.err(p, "Ihr seid in keiner Gruppe.")
                return
            for o in self.party_players(p.party):
                self.send(o, payload)
        elif ch == "guild":
            if not p.guild_id:
                self.err(p, "Ihr seid in keiner Gilde.")
                return
            g = self.guilds.get(p.guild_id)
            for cid in g.members if g else []:
                o = self.by_char.get(cid)
                if o:
                    self.send(o, payload)
        elif ch in ("world", "trade", "lfg"):
            for o in self.players.values():
                if not self.is_ignored(o, p):
                    self.send(o, payload)
        elif ch == "whisper":
            to = self.by_name.get(str(m.get("to", "")).lower())
            if not to:
                self.err(p, f"Spieler '{m.get('to')}' ist nicht online.")
                return
            if self.is_ignored(to, p):
                self.err(p, f"{to.name} ignoriert Euch.")
                return
            self.send(to, {**payload, "to": to.name})
            self.send(p, {**payload, "to": to.name, "out": True})
            to.misc["_last_whisper"] = p.name

    def slash_command(self, p: Player, text: str):
        parts = text[1:].split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        if cmd in ("w", "flüstern", "fl", "whisper"):
            to, _, msg = arg.partition(" ")
            self.chat(p, {"ch": "whisper", "to": to, "text": msg})
        elif cmd in ("r", "antworten") and p.misc.get("_last_whisper"):
            self.chat(p, {"ch": "whisper", "to": p.misc["_last_whisper"], "text": arg})
        elif cmd in ("s", "sagen"):
            self.chat(p, {"ch": "say", "text": arg})
        elif cmd in ("y", "rufen", "schreien"):
            self.chat(p, {"ch": "yell", "text": arg})
        elif cmd in ("p", "gruppe"):
            self.chat(p, {"ch": "party", "text": arg})
        elif cmd in ("g", "gilde"):
            self.chat(p, {"ch": "guild", "text": arg})
        elif cmd in ("1", "welt"):
            self.chat(p, {"ch": "world", "text": arg})
        elif cmd in ("2", "handel"):
            self.chat(p, {"ch": "trade", "text": arg})
        elif cmd in ("einladen", "inv", "invite"):
            self.invite(p, arg.strip())
        elif cmd in ("wer", "who"):
            self.who(p, arg)
        elif cmd in ("duell", "duel"):
            o = self.by_name.get(arg.strip().lower()) or (p.zone.entities.get(p.target) if p.target else None)
            if isinstance(o, Player):
                self.duel_request(p, o.id)
        elif cmd in ("würfeln", "roll", "random"):
            hi = int(arg) if arg.strip().isdigit() else 100
            r = random.randint(1, max(1, hi))
            for o in p.zone.players_near(p.x, p.z, 40):
                self.sys(o, f"{p.name} würfelt eine {r} (1–{hi}).")
        elif cmd in ("verlassen", "leave"):
            self.leave_party(p)
        elif cmd in ("hilfe", "help"):
            self.sys(p, "Befehle: /s /y /p /g /1 /2 /w Name, /r, /einladen Name, /wer, /duell, /würfeln, /verlassen, /tanzen, /winken …")
        elif cmd in EMOTES:
            self.emote(p, cmd)
        else:
            self.err(p, f"Unbekannter Befehl: /{cmd}")

    def emote(self, p: Player, e: str):
        if e not in EMOTES:
            return
        anim, text = EMOTES[e]
        p.emote = anim
        p.mark("emote")
        if anim == "sit":
            p.sitting = True
            p.mark("st")
        tgt = p.zone.entities.get(p.target) if p.target else None
        line = f"{p.name} {text}" if not tgt or tgt is p else f"{p.name} {text[:-1]} {tgt.name} zu." if e in ("winken", "jubeln") else f"{p.name} {text}"
        for o in p.zone.players_near(p.x, p.z, 40):
            self.send(o, {"t": "chat", "ch": "emote", "from": p.name, "fid": p.id, "text": line})
        if isinstance(tgt, Npc) and p.dist(tgt) < 15:
            self.quest_emote(p, e, tgt.npc_id)

    def admin_command(self, p: Player, text: str):
        if not (p.gm or config.DEBUG_COMMANDS):
            self.err(p, "Unbekannter Befehl.")
            return
        parts = text[1:].split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:]
        try:
            if cmd == "stufe":
                lvl = max(1, min(50, int(args[0])))
                while p.level < lvl:
                    from ..content.classes import xp_to_next
                    self.add_xp(p, xp_to_next(p.level) - p.xp)
            elif cmd == "gold":
                p.copper += int(float(args[0]) * 10000)
                self.send_stats(p)
            elif cmd == "item":
                n = int(args[1]) if len(args) > 1 else 1
                if args[0] in ITEMS:
                    self.give_items(p, [(args[0], n)])
            elif cmd == "tp" and len(args) >= 2:
                x, z = float(args[0]), float(args[1])
                if len(args) >= 3 and args[2] in self.zones:
                    self.move_player(p, self.zones[args[2]], x, z, p.r)
                else:
                    self.teleport(p, x, z)
            elif cmd == "zone" and args and args[0] in W.ZONES and not W.ZONES[args[0]]["type"] == "dungeon":
                sx, sz, sr = W.ZONES[args[0]]["start"]
                self.move_player(p, self.zones[args[0]], sx, sz, sr)
            elif cmd == "heilen":
                p.hp = p.max_hp
                p.power = p.max_power
                p.mark("hp", "pw")
            elif cmd == "ruf" and len(args) >= 2:
                self.add_rep(p, args[0], int(args[1]))
            elif cmd == "beruf" and len(args) >= 2:
                pr = p.professions.get(args[0])
                if pr:
                    pr["skill"] = min(pr["max"], int(args[1]))
                    self.send_professions(p)
            elif cmd == "pos":
                self.sys(p, f"{p.zone.id}: x={p.x:.1f} z={p.z:.1f} y={p.y:.1f} r={p.r:.2f}")
            elif cmd == "unsichtbar":
                p.misc["gm_invisible"] = not p.misc.get("gm_invisible")
            elif cmd == "spawn" and args and args[0] in W.MOBS:
                m = Mob(W.MOBS[args[0]], p.x + 4, p.z, 0.0)
                m.y = p.zone.height(m.x, m.z)
                m.respawn_at = 0
                p.zone.add(m)
            elif cmd == "quest" and args and args[0] in W.QUESTS:
                p.quests_done[args[0]] = time.time()
                p.quests_active.pop(args[0], None)
                self.send_quests(p)
            elif cmd == "reset":
                p.misc["lockouts"] = {}
                self.sys(p, "Sperren zurückgesetzt.")
            else:
                self.sys(p, "Admin: .stufe n, .gold n, .item id [n], .tp x z [zone], .zone id, .heilen, .ruf f n, .beruf b n, .pos, .spawn mob, .quest id, .reset")
        except (ValueError, IndexError):
            self.err(p, "Falsche Parameter.")

    def who(self, p: Player, arg: str = ""):
        q = arg.strip().lower()
        out = []
        for o in sorted(self.players.values(), key=lambda x: -x.level):
            if o.misc.get("gm_invisible"):
                continue
            if q and q not in o.name.lower() and q not in CLASSES[o.class_id]["name"].lower():
                continue
            g = self.guilds.get(o.guild_id) if o.guild_id else None
            out.append({"name": o.name, "lvl": o.level, "cls": o.class_id, "zone": o.zone.cfg["name"] if o.zone else "",
                        "guild": g.name if g else None})
        self.send(p, {"t": "who", "list": out[:50], "total": len(out)})

    # ================================================================== Freunde & Ignorieren
    def load_friends(self, p: Player):
        with SessionLocal() as s:
            rows = s.execute(select(Friend, Character.name).join(Character, Character.id == Friend.friend_id)
                             .where(Friend.character_id == p.char_id)).all()
        p.misc["_friends"] = {f.friend_id: name for f, name in rows if not f.ignore}
        p.misc["_ignore"] = {f.friend_id: name for f, name in rows if f.ignore}

    def is_ignored(self, receiver: Player, sender: Player) -> bool:
        return sender.char_id in receiver.misc.get("_ignore", {})

    def send_friends(self, p: Player):
        out = []
        for cid, name in p.misc.get("_friends", {}).items():
            o = self.by_char.get(cid)
            out.append({"id": cid, "name": name, "online": bool(o), "lvl": o.level if o else None,
                        "cls": o.class_id if o else None, "zone": o.zone.cfg["name"] if o and o.zone else None})
        self.send(p, {"t": "friends", "list": out, "ignore": list(p.misc.get("_ignore", {}).values())})

    def friend_add(self, p: Player, name: str, ignore: bool = False):
        with SessionLocal() as s:
            c = s.execute(select(Character).where(Character.name.ilike(name.strip()))).scalar_one_or_none()
            if not c or c.id == p.char_id:
                self.err(p, "Spieler nicht gefunden.")
                return
            s.execute(delete(Friend).where(Friend.character_id == p.char_id, Friend.friend_id == c.id))
            s.add(Friend(character_id=p.char_id, friend_id=c.id, ignore=ignore))
            s.commit()
            cname = c.name
        self.load_friends(p)
        self.sys(p, f"{cname} wurde {'ignoriert' if ignore else 'als Freund hinzugefügt'}.")
        self.send_friends(p)

    def friend_remove(self, p: Player, cid: int):
        with SessionLocal() as s:
            s.execute(delete(Friend).where(Friend.character_id == p.char_id, Friend.friend_id == int(cid)))
            s.commit()
        self.load_friends(p)
        self.send_friends(p)

    def notify_friends(self, p: Player, online: bool):
        for o in self.players.values():
            if p.char_id in o.misc.get("_friends", {}):
                self.sys(o, f"{p.name} ist jetzt {'online' if online else 'offline'}.")

    # ================================================================== Gruppen & Raids
    def party_players(self, party: Party) -> list[Player]:
        return [self.players[m] for m in party.members if m in self.players]

    def invite(self, p: Player, name_or_id):
        o = self.by_name.get(str(name_or_id).lower()) if isinstance(name_or_id, str) else self.players.get(name_or_id)
        if isinstance(name_or_id, str) and name_or_id.isdigit():
            o = self.players.get(int(name_or_id)) or o
        if not o or o is p:
            self.err(p, "Spieler nicht gefunden.")
            return
        if p.party and p.party.leader != p.id:
            self.err(p, "Nur der Gruppenleiter kann einladen.")
            return
        if o.party:
            self.err(p, f"{o.name} ist bereits in einer Gruppe.")
            return
        if p.party and len(p.party.members) >= p.party.max:
            self.err(p, "Die Gruppe ist voll." + ("" if p.party.raid else " Wandelt sie in einen Schlachtzug um (bis zu 10 Spieler)."))
            return
        if self.is_ignored(o, p):
            return
        o.invite_from = p.id
        self.send(o, {"t": "party_invite", "from": p.name, "fid": p.id})
        self.sys(p, f"Ihr habt {o.name} in Eure Gruppe eingeladen.")

    def party_accept(self, p: Player):
        inv = self.players.get(p.invite_from) if p.invite_from else None
        p.invite_from = None
        if not inv or p.party:
            return
        party = inv.party
        if party is None:
            party = Party(inv)
            self.parties[party.id] = party
            inv.party = party
        if len(party.members) >= party.max:
            self.err(p, "Die Gruppe ist voll.")
            return
        party.members.append(p.id)
        p.party = party
        for m in self.party_players(party):
            self.sys(m, f"{p.name} hat sich der Gruppe angeschlossen.")
        self.send_party(party)

    def party_decline(self, p: Player):
        inv = self.players.get(p.invite_from) if p.invite_from else None
        p.invite_from = None
        if inv:
            self.sys(inv, f"{p.name} hat Eure Einladung abgelehnt.")

    def leave_party(self, p: Player, silent: bool = False):
        party = p.party
        if not party:
            return
        p.party = None
        if p.id in party.members:
            party.members.remove(p.id)
        self.send(p, {"t": "party", "members": [], "leader": None})
        rest = self.party_players(party)
        if len(rest) <= 1:
            for m in rest:
                m.party = None
                self.send(m, {"t": "party", "members": [], "leader": None})
                if not silent:
                    self.sys(m, "Eure Gruppe wurde aufgelöst.")
            self.parties.pop(party.id, None)
            return
        if party.leader == p.id:
            party.leader = rest[0].id
            self.sys(rest[0], "Ihr seid jetzt Gruppenleiter.")
        for m in rest:
            if not silent:
                self.sys(m, f"{p.name} hat die Gruppe verlassen.")
        self.send_party(party)

    def party_kick(self, p: Player, pid: int):
        party = p.party
        if not party or party.leader != p.id or pid not in party.members or pid == p.id:
            return
        o = self.players.get(pid)
        if o:
            self.sys(o, "Ihr wurdet aus der Gruppe entfernt.")
            self.leave_party(o)

    def party_promote(self, p: Player, pid: int):
        party = p.party
        if party and party.leader == p.id and pid in party.members:
            party.leader = pid
            self.send_party(party)

    def party_raid(self, p: Player):
        party = p.party
        if party and party.leader == p.id and not party.raid:
            party.raid = True
            for m in self.party_players(party):
                self.sys(m, "Die Gruppe ist jetzt ein Schlachtzug (bis zu 10 Spieler).")
            self.send_party(party)

    def send_party(self, party: Party):
        members = []
        for mid in party.members:
            m = self.players.get(mid)
            if not m:
                continue
            members.append({"id": m.id, "name": m.name, "cls": m.class_id, "lvl": m.level, "hp": m.hp, "mhp": m.max_hp,
                            "pw": int(m.power), "mpw": m.max_power, "pt": m.power_type, "dead": m.dead,
                            "zone": m.zone.cfg["name"] if m.zone else "", "zid": m.zone.key if m.zone else "",
                            "x": round(m.x, 1), "z": round(m.z, 1), "role": m.misc.get("role", "dps"),
                            "au": [a.client(now())[:6] for a in m.auras if a.debuff][:6]})
        for m in self.party_players(party):
            self.send(m, {"t": "party", "members": members, "leader": party.leader, "raid": party.raid})

    # ================================================================== Gruppenfinder (GDD 10)
    def queue_dungeon(self, p: Player, zone_id: str, mode: str, role: str):
        z = W.ZONES.get(zone_id)
        if not z or z["type"] != "dungeon" or z.get("hidden") or z.get("arena"):
            return
        if p.party:
            self.err(p, "Der Gruppenfinder ist nur für Einzelspieler (Gruppen betreten das Portal direkt).")
            return
        need = z["levels"][0] + (0 if mode == "normal" else (5 if mode == "heroisch" else 8))
        if p.level < need:
            self.err(p, f"Dafür braucht Ihr Stufe {need}.")
            return
        if role not in ("tank", "heiler", "dps"):
            return
        p.queue = {"zone": zone_id, "mode": mode, "role": role, "t": now()}
        p.misc["role"] = role
        self.send(p, {"t": "queue", "zone": zone_id, "name": z["name"], "mode": mode, "role": role, "state": "searching"})
        self.sys(p, f"Ihr sucht eine Gruppe für {z['name']} ({W.MODES[mode]['name']}) als {role.capitalize()}.")
        self.try_match_queue(zone_id, mode)

    def leave_queue(self, p: Player):
        if p.queue:
            p.queue = None
            self.send(p, {"t": "queue", "state": "none"})

    def try_match_queue(self, zone_id: str, mode: str):
        z = W.ZONES[zone_id]
        size = min(5, z.get("max_players", 5))
        q = sorted([o for o in self.players.values() if o.queue and o.queue["zone"] == zone_id and o.queue["mode"] == mode],
                   key=lambda o: o.queue["t"])
        if len(q) < size:
            # Wer schon lange wartet, bekommt nach 90 Sek. auch eine kleinere Gruppe (mind. 2) – oder solo bei Dungeons bis 2 Spieler
            if q and now() - q[0].queue["t"] > 90 and len(q) >= max(1, min(2, size)):
                group = q
            else:
                return
        else:
            tanks = [o for o in q if o.queue["role"] == "tank"]
            heals = [o for o in q if o.queue["role"] == "heiler"]
            dps = [o for o in q if o.queue["role"] == "dps"]
            if size >= 5:
                if not tanks or not heals or len(dps) < size - 2:
                    if now() - q[0].queue["t"] < 120:
                        return
                    group = q[:size]
                else:
                    group = [tanks[0], heals[0]] + dps[: size - 2]
            else:
                group = q[:size]
        leader = group[0]
        for o in group:
            o.queue = None
            if o.party:
                self.leave_party(o, silent=True)
        party = Party(leader)
        self.parties[party.id] = party
        leader.party = party
        for o in group[1:]:
            party.members.append(o.id)
            o.party = party
        for o in group:
            o.finder_group = True
            self.send(o, {"t": "queue", "state": "found", "zone": zone_id, "name": z["name"], "mode": mode})
            self.sys(o, f"Gruppe gefunden für {z['name']}! Ihr werdet teleportiert.")
        self.send_party(party)
        zone = self.instance_for(leader, zone_id, mode)
        if zone:
            sx, sz, sr = z["start"]
            for o in group:
                o.misc["instance_return"] = [o.zone.id, round(o.x, 1), round(o.z, 1), round(o.r, 2)] if not o.zone.is_instance else o.misc.get("instance_return")
                self.move_player(o, zone, sx + random.uniform(-1.5, 1.5), sz + random.uniform(-1, 1), sr)

    # ================================================================== Gilden
    def load_guilds(self):
        self.guilds: dict[int, GuildState] = {}
        with SessionLocal() as s:
            for g in s.execute(select(Guild)).scalars():
                self.guilds[g.id] = GuildState(g)
            for gm, name, cls, lvl in s.execute(select(GuildMember, Character.name, Character.class_id, Character.level)
                                                .join(Character, Character.id == GuildMember.character_id)).all():
                g = self.guilds.get(gm.guild_id)
                if g:
                    g.members[gm.character_id] = {"name": name, "rank": gm.rank, "cls": cls, "lvl": lvl, "note": gm.note,
                                                  "contrib": gm.contribution}
            for b in s.execute(select(GuildBankItem)).scalars():
                g = self.guilds.get(b.guild_id)
                if g and 0 <= b.slot < GUILD_BANK_SLOTS:
                    g.bank[b.slot] = {"i": b.item_id, "n": b.quantity, **(b.extra or {})}
            for lg in s.execute(select(GuildLog).order_by(GuildLog.id.desc()).limit(2000)).scalars():
                g = self.guilds.get(lg.guild_id)
                if g and len(g.log) < 40:
                    g.log.append(lg.text)

    def _glog(self, g: GuildState, text: str):
        g.log.insert(0, text)
        del g.log[40:]
        with SessionLocal() as s:
            s.add(GuildLog(guild_id=g.id, text=text[:200]))
            s.commit()

    def guild_broadcast(self, gid: int, text: str, exclude: int | None = None):
        g = self.guilds.get(gid)
        if not g:
            return
        for cid in g.members:
            o = self.by_char.get(cid)
            if o and o.id != exclude:
                self.send(o, {"t": "chat", "ch": "guild_sys", "from": "", "text": text})

    def guild_create(self, p: Player, name: str, tag: str = ""):
        npc = p.zone.entities.get(p.misc.get("_gossip_npc"))
        if not isinstance(npc, Npc) or "guild" not in npc.tpl.get("services", []) or p.dist(npc) > 8:
            self.err(p, "Sprecht mit einem Gildenmeister.")
            return
        name = re.sub(r"\s+", " ", str(name)).strip()
        if not GUILD_NAME_RE.match(name):
            self.err(p, "Ungültiger Gildenname (3–24 Buchstaben).")
            return
        if p.guild_id:
            self.err(p, "Ihr seid bereits in einer Gilde.")
            return
        if p.copper < GUILD_COST:
            self.err(p, f"Eine Gilde kostet {self.fmt_money(GUILD_COST)}.")
            return
        tag = re.sub(r"[^A-Za-z]", "", str(tag))[:5].upper()
        with SessionLocal() as s:
            if s.execute(select(Guild).where(Guild.name.ilike(name))).scalar_one_or_none():
                self.err(p, "Diesen Namen gibt es schon.")
                return
            g = Guild(name=name, tag=tag, leader_character_id=p.char_id, motd="Willkommen in der Gilde!")
            s.add(g)
            s.flush()
            s.add(GuildMember(guild_id=g.id, character_id=p.char_id, rank="leiter"))
            s.commit()
            gs = GuildState(g)
        p.copper -= GUILD_COST
        p.save_dirty = True
        gs.members[p.char_id] = {"name": p.name, "rank": "leiter", "cls": p.class_id, "lvl": p.level, "note": "", "contrib": 0}
        self.guilds[gs.id] = gs
        self.set_player_guild(p, gs.id, "leiter")
        self._glog(gs, f"{p.name} hat die Gilde gegründet.")
        self.toast(p, "Gilde gegründet", f"<{name}>", "guild")
        self.progress_counter(p, "guild_joined", 1)
        self.send_guild(p)
        self.send_stats(p)

    def set_player_guild(self, p: Player, gid: int | None, rank: str | None):
        p.guild_id = gid
        p.guild_rank = rank
        g = self.guilds.get(gid) if gid else None
        p.look["guild_name"] = g.name if g else None
        p.mark("look")
        p.save_dirty = True

    def guild_invite(self, p: Player, name: str):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g:
            return
        if RANK_ORDER.index(g.members[p.char_id]["rank"]) < RANK_ORDER.index("offizier"):
            self.err(p, "Nur Offiziere und der Leiter können einladen.")
            return
        o = self.by_name.get(str(name).lower())
        if not o:
            self.err(p, "Spieler nicht online.")
            return
        if o.guild_id:
            self.err(p, f"{o.name} ist bereits in einer Gilde.")
            return
        o.guild_invite = g.id
        self.send(o, {"t": "guild_invite", "from": p.name, "guild": g.name})

    def guild_accept(self, p: Player):
        gid = p.guild_invite
        p.guild_invite = None
        g = self.guilds.get(gid) if gid else None
        if not g or p.guild_id:
            return
        with SessionLocal() as s:
            s.add(GuildMember(guild_id=g.id, character_id=p.char_id, rank="rekrut"))
            s.commit()
        g.members[p.char_id] = {"name": p.name, "rank": "rekrut", "cls": p.class_id, "lvl": p.level, "note": "", "contrib": 0}
        self.set_player_guild(p, g.id, "rekrut")
        self._glog(g, f"{p.name} ist der Gilde beigetreten.")
        self.guild_broadcast(g.id, f"{p.name} ist der Gilde beigetreten.")
        self.progress_counter(p, "guild_joined", 1)
        self.send_guild(p)

    def guild_leave(self, p: Player):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g:
            return
        if g.leader == p.char_id and len(g.members) > 1:
            self.err(p, "Übergebt die Leitung zuerst an ein anderes Mitglied.")
            return
        self._remove_member(g, p.char_id)
        self._glog(g, f"{p.name} hat die Gilde verlassen.")
        self.guild_broadcast(g.id, f"{p.name} hat die Gilde verlassen.")
        self.set_player_guild(p, None, None)
        if not g.members:
            with SessionLocal() as s:
                s.execute(delete(Guild).where(Guild.id == g.id))
                s.commit()
            self.guilds.pop(g.id, None)
        self.send(p, {"t": "guild", "guild": None})

    def _remove_member(self, g: GuildState, cid: int):
        with SessionLocal() as s:
            s.execute(delete(GuildMember).where(GuildMember.character_id == cid))
            s.commit()
        g.members.pop(cid, None)

    def guild_kick(self, p: Player, cid: int):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g or cid not in g.members or cid == p.char_id:
            return
        my = RANK_ORDER.index(g.members[p.char_id]["rank"])
        their = RANK_ORDER.index(g.members[cid]["rank"])
        if my < RANK_ORDER.index("offizier") or their >= my:
            self.err(p, "Dazu fehlen Euch die Rechte.")
            return
        name = g.members[cid]["name"]
        self._remove_member(g, cid)
        o = self.by_char.get(cid)
        if o:
            self.set_player_guild(o, None, None)
            self.sys(o, "Ihr wurdet aus der Gilde entfernt.")
            self.send(o, {"t": "guild", "guild": None})
        self._glog(g, f"{p.name} hat {name} entfernt.")
        self.guild_broadcast(g.id, f"{name} wurde aus der Gilde entfernt.")
        self.send_guild(p)

    def guild_set_rank(self, p: Player, cid: int, up: bool):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g or cid not in g.members or cid == p.char_id:
            return
        my = RANK_ORDER.index(g.members[p.char_id]["rank"])
        cur = RANK_ORDER.index(g.members[cid]["rank"])
        new = cur + (1 if up else -1)
        if new < 0 or new >= len(RANK_ORDER):
            return
        if RANK_ORDER[new] == "leiter":
            if my != RANK_ORDER.index("leiter"):
                return
            # Leitung übergeben
            g.members[p.char_id]["rank"] = "offizier"
            g.leader = cid
            self._db_rank(p.char_id, "offizier")
            with SessionLocal() as s:
                gg = s.get(Guild, g.id)
                gg.leader_character_id = cid
                s.commit()
            p.guild_rank = "offizier"
        elif my <= max(cur, new):
            self.err(p, "Dazu fehlen Euch die Rechte.")
            return
        g.members[cid]["rank"] = RANK_ORDER[new]
        self._db_rank(cid, RANK_ORDER[new])
        o = self.by_char.get(cid)
        if o:
            o.guild_rank = RANK_ORDER[new]
        self._glog(g, f"{g.members[cid]['name']} ist jetzt {RANK_NAMES[RANK_ORDER[new]]}.")
        self.guild_broadcast(g.id, f"{g.members[cid]['name']} ist jetzt {RANK_NAMES[RANK_ORDER[new]]}.")
        self.send_guild(p)

    def _db_rank(self, cid: int, rank: str):
        with SessionLocal() as s:
            gm = s.execute(select(GuildMember).where(GuildMember.character_id == cid)).scalar_one_or_none()
            if gm:
                gm.rank = rank
                s.commit()

    def guild_motd(self, p: Player, text: str):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g or RANK_ORDER.index(g.members[p.char_id]["rank"]) < RANK_ORDER.index("offizier"):
            return
        g.motd = str(text)[:200]
        with SessionLocal() as s:
            gg = s.get(Guild, g.id)
            gg.motd = g.motd
            s.commit()
        self.guild_broadcast(g.id, f"Nachricht des Tages: {g.motd}")

    def guild_goal(self, g: GuildState) -> dict:
        week = int(self.next_weekly_reset())
        if g.weekly.get("week") != week:
            idx = (week // (7 * 86400) + g.id) % len(GUILD_GOALS)
            g.weekly = {"week": week, "goal": GUILD_GOALS[idx]["id"], "progress": 0, "done": False, "contrib": {}}
        return next(x for x in GUILD_GOALS if x["id"] == g.weekly["goal"])

    def guild_progress(self, p: Player, counter: str, n: int):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g:
            return
        goal = self.guild_goal(g)
        if goal["counter"] != counter or g.weekly.get("done"):
            return
        g.weekly["progress"] = g.weekly.get("progress", 0) + n
        c = g.weekly.setdefault("contrib", {})
        c[str(p.char_id)] = c.get(str(p.char_id), 0) + n
        if g.weekly["progress"] >= goal["n"]:
            g.weekly["done"] = True
            g.xp += 1000
            g.copper += 50000
            for cid_s, amount in c.items():
                if amount >= max(1, goal["n"] // 50):
                    self.mail_system(int(cid_s), f"Gildenziel: {goal['name']}", "Danke für Euren Beitrag zum Wochenziel der Gilde!",
                                     [], 5000, currency={"dungeonmarken": 5})
            self.guild_broadcast(g.id, f"Wochenziel erreicht: {goal['name']}! Belohnungen kamen per Post. Die Gildenbank erhält 5 Gold.")
            self._glog(g, f"Wochenziel erreicht: {goal['name']}")
        self._save_guild_meta(g)

    def _save_guild_meta(self, g: GuildState):
        if now() - getattr(g, "_last_save", 0) < 20 and not g.weekly.get("done"):
            return
        g._last_save = now()
        with SessionLocal() as s:
            gg = s.get(Guild, g.id)
            if gg:
                gg.weekly = dict(g.weekly)
                gg.copper = g.copper
                gg.xp = g.xp
                gg.level = 1 + g.xp // 5000
                s.commit()

    def send_guild(self, p: Player):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g:
            self.send(p, {"t": "guild", "guild": None})
            return
        goal = self.guild_goal(g)
        members = []
        for cid, m in g.members.items():
            o = self.by_char.get(cid)
            members.append({"id": cid, "name": m["name"], "rank": m["rank"], "rank_name": RANK_NAMES[m["rank"]], "cls": m["cls"],
                            "lvl": o.level if o else m["lvl"], "online": bool(o), "zone": o.zone.cfg["name"] if o and o.zone else None,
                            "note": m.get("note", "")})
        members.sort(key=lambda x: (not x["online"], -RANK_ORDER.index(x["rank"]), x["name"]))
        ids = [b["i"] for b in g.bank if b]
        self.send(p, {"t": "guild", "guild": {
            "id": g.id, "name": g.name, "tag": g.tag, "motd": g.motd, "level": 1 + g.xp // 5000, "xp": g.xp % 5000,
            "copper": g.copper, "members": members, "my_rank": g.members.get(p.char_id, {}).get("rank"),
            "goal": {**goal, "progress": g.weekly.get("progress", 0), "done": g.weekly.get("done", False)},
            "log": g.log[:20], "bank": g.bank, "items": self.item_info_for(p, ids)}})

    def guild_bank_deposit(self, p: Player, slot: int):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g or not self.near_bank(p):
            self.err(p, "Dafür müsst Ihr bei einem Gildenmeister oder Briefkasten sein.")
            return
        if not (0 <= slot < len(p.bags)) or not p.bags[slot]:
            return
        inst = p.bags[slot]
        if inst.get("b") or ITEMS[inst["i"]].get("quest"):
            self.err(p, "Gebundene Gegenstände können nicht eingelagert werden.")
            return
        free = next((i for i, b in enumerate(g.bank) if b is None), None)
        if free is None:
            self.err(p, "Die Gildenbank ist voll.")
            return
        p.bags[slot] = None
        g.bank[free] = inst
        p.save_dirty = True
        self.save_player_now(p)
        with SessionLocal() as s:
            s.add(GuildBankItem(guild_id=g.id, slot=free, item_id=inst["i"], quantity=inst["n"],
                                extra={k: v for k, v in inst.items() if k not in ("i", "n")}))
            s.add(Transaction(seller_id=p.char_id, kind="guildbank", item_id=inst["i"], quantity=inst["n"]))
            s.commit()
        self._glog(g, f"{p.name} hat {ITEMS[inst['i']]['name']} ×{inst['n']} eingelagert.")
        self.send_inventory(p)
        self.send_guild(p)

    def guild_bank_withdraw(self, p: Player, slot: int):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g or not self.near_bank(p) or not (0 <= slot < GUILD_BANK_SLOTS) or not g.bank[slot]:
            return
        rank = g.members[p.char_id]["rank"]
        day = int(time.time() // 86400)
        wd = p.misc.setdefault("guild_withdraw", {})
        if wd.get("day") != day:
            wd.clear()
            wd["day"] = day
        if RANK_ORDER.index(rank) < RANK_ORDER.index("offizier") and wd.get("n", 0) >= (MEMBER_WITHDRAW_PER_DAY if rank == "mitglied" else 1):
            self.err(p, "Ihr habt heute schon genug entnommen.")
            return
        inst = g.bank[slot]
        extra = {k: v for k, v in inst.items() if k not in ("i", "n", "b")}
        if not p.add_items([(inst["i"], inst["n"], False, extra or None)]):
            self.err(p, "Eure Taschen sind voll.")
            return
        g.bank[slot] = None
        wd["n"] = wd.get("n", 0) + 1
        with SessionLocal() as s:
            s.execute(delete(GuildBankItem).where(GuildBankItem.guild_id == g.id, GuildBankItem.slot == slot))
            s.add(Transaction(buyer_id=p.char_id, kind="guildbank", item_id=inst["i"], quantity=inst["n"]))
            s.commit()
        self.save_player_now(p)
        self._glog(g, f"{p.name} hat {ITEMS[inst['i']]['name']} ×{inst['n']} entnommen.")
        self.send_inventory(p)
        self.send_guild(p)

    def guild_bank_money(self, p: Player, amount: int):
        g = self.guilds.get(p.guild_id) if p.guild_id else None
        if not g or not self.near_bank(p):
            return
        amount = int(amount)
        rank = g.members[p.char_id]["rank"]
        if amount > 0:
            if p.copper < amount:
                return
            p.copper -= amount
            g.copper += amount
            self._glog(g, f"{p.name} hat {self.fmt_money(amount)} eingezahlt.")
        elif amount < 0:
            if RANK_ORDER.index(rank) < RANK_ORDER.index("offizier") or g.copper < -amount:
                self.err(p, "Dazu fehlen Euch die Rechte oder das Gold.")
                return
            g.copper += amount
            p.copper -= amount
            self._glog(g, f"{p.name} hat {self.fmt_money(-amount)} entnommen.")
        g._last_save = 0
        self._save_guild_meta(g)
        self.save_player_now(p)
        self.send_stats(p)
        self.send_guild(p)

    def near_bank(self, p: Player) -> bool:
        from .entities import GameObj
        for e in p.zone.entities.values():
            if p.dist(e) < 8 and ((isinstance(e, GameObj) and e.obj_kind == "mailbox")
                                  or (isinstance(e, Npc) and any(s in e.tpl.get("services", []) for s in ("guild", "auction", "bank")))):
                return True
        return False

    # ================================================================== Handel zwischen Spielern
    def trade_request(self, p: Player, tid: int):
        o = self.players.get(tid)
        if not o or o is p or o.zone is not p.zone or p.dist(o) > 10:
            self.err(p, "Zu weit entfernt.")
            return
        if p.trade or o.trade:
            self.err(p, "Ein Handel läuft bereits.")
            return
        if p.combat or o.combat or p.dead or o.dead:
            self.err(p, "Jetzt nicht.")
            return
        tr = {"a": p.id, "b": o.id, "items": {p.id: [], o.id: []}, "copper": {p.id: 0, o.id: 0},
              "lock": {p.id: False, o.id: False}, "ok": {p.id: False, o.id: False}, "pending": True}
        p.trade = tr
        o.trade = tr
        self.send(o, {"t": "trade_request", "from": p.name, "fid": p.id})
        self.sys(p, f"Handelsanfrage an {o.name} gesendet.")

    def trade_answer(self, p: Player, accept: bool):
        tr = p.trade
        if not tr or tr["b"] != p.id or not tr["pending"]:
            return
        if not accept:
            self.cancel_trade(p, f"{p.name} hat den Handel abgelehnt.")
            return
        tr["pending"] = False
        self.send_trade(tr)

    def _trade_other(self, p: Player) -> Player | None:
        tr = p.trade
        if not tr:
            return None
        return self.players.get(tr["b"] if tr["a"] == p.id else tr["a"])

    def trade_set(self, p: Player, slots: list, copper: int):
        tr = p.trade
        if not tr or tr["pending"]:
            return
        clean = []
        for s in slots[:6]:
            if isinstance(s, int) and 0 <= s < len(p.bags) and p.bags[s] and s not in clean:
                inst = p.bags[s]
                if inst.get("b") or ITEMS[inst["i"]].get("quest"):
                    self.err(p, "Gebundene Gegenstände können nicht gehandelt werden.")
                    continue
                clean.append(s)
        tr["items"][p.id] = clean
        tr["copper"][p.id] = max(0, min(int(copper or 0), p.copper))
        tr["lock"] = {k: False for k in tr["lock"]}
        tr["ok"] = {k: False for k in tr["ok"]}
        self.send_trade(tr)

    def trade_lock(self, p: Player):
        tr = p.trade
        if not tr or tr["pending"]:
            return
        tr["lock"][p.id] = True
        self.send_trade(tr)

    def trade_confirm(self, p: Player):
        tr = p.trade
        if not tr or tr["pending"] or not all(tr["lock"].values()):
            return
        tr["ok"][p.id] = True
        if all(tr["ok"].values()):
            self.execute_trade(tr)
        else:
            self.send_trade(tr)

    def execute_trade(self, tr: dict):
        a, b = self.players.get(tr["a"]), self.players.get(tr["b"])
        if not a or not b:
            return
        if a.dist(b) > 12:
            self.cancel_trade(a, "Zu weit entfernt.")
            return
        give_a = [a.bags[s] for s in tr["items"][a.id] if a.bags[s]]
        give_b = [b.bags[s] for s in tr["items"][b.id] if b.bags[s]]
        ca, cb = tr["copper"][a.id], tr["copper"][b.id]
        if a.copper < ca or b.copper < cb:
            self.cancel_trade(a, "Nicht genug Geld.")
            return
        # Atomar: Kopien prüfen, dann beide Seiten übernehmen (GDD 9: keine Duplikation)
        bags_a = [dict(s) if s else None for s in a.bags]
        bags_b = [dict(s) if s else None for s in b.bags]
        for s in tr["items"][a.id]:
            bags_a[s] = None
        for s in tr["items"][b.id]:
            bags_b[s] = None

        def put(bags, insts):
            for inst in insts:
                for i in range(len(bags)):
                    if bags[i] is None:
                        bags[i] = dict(inst)
                        break
                else:
                    return False
            return True
        if not put(bags_a, give_b) or not put(bags_b, give_a):
            self.cancel_trade(a, "Nicht genug Platz in den Taschen.")
            return
        a.bags, b.bags = bags_a, bags_b
        a.copper += cb - ca
        b.copper += ca - cb
        a.trade = b.trade = None
        a.save_dirty = b.save_dirty = True
        self.save_player_now(a)
        self.save_player_now(b)
        with SessionLocal() as s:
            for inst in give_a:
                s.add(Transaction(seller_id=a.char_id, buyer_id=b.char_id, kind="trade", item_id=inst["i"], quantity=inst["n"]))
            for inst in give_b:
                s.add(Transaction(seller_id=b.char_id, buyer_id=a.char_id, kind="trade", item_id=inst["i"], quantity=inst["n"]))
            if ca or cb:
                big = max(ca, cb) > 5_000_000
                s.add(Transaction(seller_id=a.char_id, buyer_id=b.char_id, kind="trade", price=ca - cb, flagged=big))
            s.commit()
        for x in (a, b):
            self.send(x, {"t": "trade_done"})
            self.sys(x, "Handel abgeschlossen.")
            self.progress_counter(x, "trades", 1)
            self.send_inventory(x)
            self.send_stats(x)

    def cancel_trade(self, p: Player, reason: str = "Handel abgebrochen."):
        tr = p.trade
        if not tr:
            return
        for pid in (tr["a"], tr["b"]):
            o = self.players.get(pid)
            if o:
                o.trade = None
                self.send(o, {"t": "trade_cancel", "reason": reason})

    def send_trade(self, tr: dict):
        a, b = self.players.get(tr["a"]), self.players.get(tr["b"])
        if not a or not b:
            return
        for me, other in ((a, b), (b, a)):
            mine = [me.bags[s] for s in tr["items"][me.id] if me.bags[s]]
            theirs = [other.bags[s] for s in tr["items"][other.id] if other.bags[s]]
            self.send(me, {"t": "trade", "with": other.name, "mine": mine, "my_slots": tr["items"][me.id], "theirs": theirs,
                           "my_copper": tr["copper"][me.id], "their_copper": tr["copper"][other.id],
                           "my_lock": tr["lock"][me.id], "their_lock": tr["lock"][other.id],
                           "my_ok": tr["ok"][me.id], "their_ok": tr["ok"][other.id],
                           "items": self.item_info_for(me, [i["i"] for i in theirs])})

    # ================================================================== Duelle
    def duel_request(self, p: Player, tid: int):
        o = self.players.get(tid)
        if not o or o is p or o.zone is not p.zone or p.dist(o) > 30:
            self.err(p, "Ungültiges Ziel.")
            return
        if p.duel_with or o.duel_with or p.zone.is_instance:
            self.err(p, "Jetzt nicht.")
            return
        o.duel_invite = p.id
        self.send(o, {"t": "duel_request", "from": p.name, "fid": p.id})
        self.sys(p, f"Ihr habt {o.name} zum Duell herausgefordert.")

    def duel_answer(self, p: Player, accept: bool):
        o = self.players.get(p.duel_invite) if p.duel_invite else None
        p.duel_invite = None
        if not o:
            return
        if not accept:
            self.sys(o, f"{p.name} lehnt das Duell ab.")
            return
        p.duel_with, o.duel_with = o.id, p.id
        fx, fz = (p.x + o.x) / 2, (p.z + o.z) / 2
        p.misc["_duel_flag"] = o.misc["_duel_flag"] = (fx, fz)
        for x in (p, o):
            self.send(x, {"t": "duel_start", "with": (o if x is p else p).name, "in": 3, "x": round(fx, 1), "z": round(fz, 1)})
        p.zone.emit_fx(fx, fz, {"k": "duelflag", "x": round(fx, 2), "z": round(fz, 2)})

        def go():
            if p.duel_with == o.id and o.duel_with == p.id:
                p.duel_active = o.duel_active = True
                for x in (p, o):
                    self.sys(x, "Das Duell beginnt!")
                    x.mark("team")
        p.zone.schedule(3.0, go)

    def end_duel(self, winner: Player, loser: Player, fled: bool = False):
        for x in (winner, loser):
            x.duel_with = None
            x.duel_active = False
            x.misc.pop("_duel_flag", None)
            x.auto_attack = False
            x.mark("team")
            for a in list(x.auras):
                if a.debuff:
                    x.auras.remove(a)
            x.mark("au")
        loser.hp = max(1, loser.hp)
        msg = f"{winner.name} hat das Duell gegen {loser.name} gewonnen" + (" (Flucht)." if fled else ".")
        for o in winner.zone.players_near(winner.x, winner.z, 60):
            self.sys(o, msg)
        self.progress_counter(winner, "duels_won", 1)
        loser.emote = "kneel"
        loser.mark("emote")

    def duel_tick(self, p: Player):
        if getattr(p, "duel_active", False):
            fl = p.misc.get("_duel_flag")
            o = self.players.get(p.duel_with)
            if not o or not fl or math.hypot(p.x - fl[0], p.z - fl[1]) > DUEL_RANGE or o.zone is not p.zone:
                if o:
                    self.end_duel(o, p, fled=True)
                else:
                    p.duel_with = None
                    p.duel_active = False

    # ================================================================== PvP & Arena
    def on_pvp_kill(self, killer: Player, victim: Player):
        if killer.zone and killer.zone.in_pvp_area(killer.x, killer.z):
            self.progress_counter(killer, "pvp_kills", 1)
            killer.add_currency("ehrenabzeichen", 1 if abs(killer.level - victim.level) < 8 else 0)

    def arena_queue(self, p: Player, bracket: str):
        if bracket not in ("1v1", "2v2", "3v3"):
            return
        if p.zone.is_instance:
            return
        size = int(bracket[0])
        if size > 1 and (not p.party or len(p.party.members) != size or p.party.leader != p.id):
            self.err(p, f"Für {bracket} braucht Ihr eine Gruppe mit genau {size} Spielern (Ihr als Leiter).")
            return
        team = [p] if size == 1 else self.party_players(p.party)
        for m in team:
            m.misc["arena_q"] = {"bracket": bracket, "t": now(), "team": [x.id for x in team]}
            self.send(m, {"t": "arena_queue", "state": "searching", "bracket": bracket})
        self.try_arena_match(bracket)

    def arena_leave_queue(self, p: Player):
        q = p.misc.pop("arena_q", None)
        if q:
            for pid in q["team"]:
                o = self.players.get(pid)
                if o:
                    o.misc.pop("arena_q", None)
                    self.send(o, {"t": "arena_queue", "state": "none"})

    def try_arena_match(self, bracket: str):
        teams = {}
        for o in self.players.values():
            q = o.misc.get("arena_q")
            if q and q["bracket"] == bracket:
                teams[tuple(q["team"])] = q["t"]
        if len(teams) < 2 or "arena" not in W.ZONES:
            return
        ordered = sorted(teams, key=lambda k: teams[k])
        t1, t2 = ordered[0], ordered[1]
        from .zone import Zone
        key = f"arena:{next(Party._ids)}"
        zone = Zone(self, "arena", key)
        zone.arena_teams = {1: list(t1), 2: list(t2)}
        zone.arena_bracket = bracket
        zone.arena_over = False
        self.zones[key] = zone
        spawns = W.ZONES["arena"]["team_spawns"]
        for team_no, ids in ((1, t1), (2, t2)):
            for i, pid in enumerate(ids):
                o = self.players.get(pid)
                if not o:
                    continue
                o.misc.pop("arena_q", None)
                o.misc["instance_return"] = [o.zone.id, round(o.x, 1), round(o.z, 1), round(o.r, 2)]
                sx, sz, sr = spawns[team_no - 1]
                self.move_player(o, zone, sx + i * 2.0, sz, sr)
                o.team = team_no
                o.hp, o.power = o.max_hp, (o.max_power if o.power_type in ("mana", "energy", "concentration") else 0)
                o.mark("team", "hp", "pw")
                self.send(o, {"t": "arena_queue", "state": "found", "bracket": bracket})
                self.send(o, {"t": "arena_start", "in": 10})
        zone.arena_gate_t = now() + 10
        zone.schedule(10.0, lambda: [self.sys(o, "Die Tore öffnen sich! Kämpft!") for o in zone.players.values()])

    def arena_player_died(self, p: Player):
        zone = p.zone
        if getattr(zone, "arena_over", True):
            return
        alive = {1: 0, 2: 0}
        for o in zone.players.values():
            if not o.dead and o.team in alive:
                alive[o.team] += 1
        for team, n in alive.items():
            if n == 0:
                self.finish_arena(zone, winner=2 if team == 1 else 1)
                return

    def finish_arena(self, zone, winner: int):
        zone.arena_over = True
        loser = 2 if winner == 1 else 1
        win_ids = zone.arena_teams[winner]
        lose_ids = zone.arena_teams[loser]
        wr = [self.players[i].misc.get("arena_rating", 1500) for i in win_ids if i in self.players] or [1500]
        lr = [self.players[i].misc.get("arena_rating", 1500) for i in lose_ids if i in self.players] or [1500]
        wa, la = sum(wr) / len(wr), sum(lr) / len(lr)
        exp = 1 / (1 + 10 ** ((la - wa) / 400))
        delta = max(4, int(32 * (1 - exp)))
        for pid in win_ids + lose_ids:
            o = self.players.get(pid)
            if not o:
                continue
            won = pid in win_ids
            o.misc["arena_rating"] = max(0, o.misc.get("arena_rating", 1500) + (delta if won else -delta))
            o.add_currency("arenapunkte", 25 if won else 8)
            if won:
                self.progress_counter(o, "arena_wins", 1)
            self.set_counter_max(o, "arena_rating", o.misc["arena_rating"])
            self.send(o, {"t": "arena_end", "won": won, "rating": o.misc["arena_rating"], "delta": delta if won else -delta})
        with SessionLocal() as s:
            s.add(ArenaMatch(bracket=zone.arena_bracket, winners=win_ids, losers=lose_ids))
            s.commit()

        def leave():
            for o in list(zone.players.values()):
                o.team = None
                o.dead = False
                o.hp = o.max_hp
                o.mark("team", "hp", "st")
                self.leave_instance(o)
        zone.schedule(6.0, leave)
