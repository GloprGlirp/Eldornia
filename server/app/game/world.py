"""Die Spielwelt von Eldornia: Zonen, Simulationsschleife und Verarbeitung aller Client-Nachrichten.

Alles Spielrelevante passiert serverseitig (GDD 12): Schaden, Lebenspunkte, Fähigkeiten, Abklingzeiten,
Gegnerbewegungen, Bossphasen, Beute, Inventar, Gold, Handel, Questfortschritt und Erfahrung.
Der Client stellt dar und schickt Eingaben.
"""
from __future__ import annotations

import asyncio
import logging
import math
import time

from .. import config
from ..content import world as W
from ..content.abilities import ABILITIES
from ..content.classes import CLASSES
from ..content.items import EQUIP_SLOTS, ITEMS
from .abilities import AbilityMixin
from .ai import AIMixin
from .core import CoreMixin
from .crafting import CraftingMixin
from .economy import EconomyMixin
from .entities import BACK_SPEED, RUN_SPEED, SPRINT_MULT, GameObj, Mob, Npc, Pet, Player, now
from .inventory import INTERACT_RANGE, InventoryMixin
from .progress import ProgressMixin
from .quests import QuestMixin
from .social import Party, SocialMixin
from .stats import recalc
from .zone import Zone, static_zone

log = logging.getLogger("eldornia.world")

INSTANCE_IDLE_TIMEOUT = 900.0
SAVE_FIELDS_SKIP = ("_",)


class World(CoreMixin, AbilityMixin, AIMixin, QuestMixin, ProgressMixin, InventoryMixin, CraftingMixin, SocialMixin, EconomyMixin):
    def __init__(self):
        self.zones: dict[str, Zone] = {}
        self.players: dict[int, Player] = {}
        self.by_name: dict[str, Player] = {}
        self.by_char: dict[int, Player] = {}
        self.parties: dict[int, Party] = {}
        self.guilds = {}
        self.last_tick = now()
        self.next_party_update = 0.0
        self.next_autosave = now() + config.SAVE_INTERVAL
        self.next_market = now() + 30
        self.next_queue = now() + 5
        self.save_callback = None      # wird von main.py gesetzt
        self.running = False
        self.tick_ms = 0.0
        self.started = time.time()

    def boot(self):
        for zid, cfg in W.ZONES.items():
            if cfg["type"] != "dungeon":
                t = time.time()
                self.zones[zid] = Zone(self, zid, zid)
                log.info("Zone %s bereit (%.1f s, %d Einheiten)", zid, time.time() - t, len(self.zones[zid].entities))
        for zid, cfg in W.ZONES.items():
            if cfg["type"] == "dungeon":
                static_zone(zid)
        try:
            self.load_guilds()
        except Exception:  # pragma: no cover
            log.exception("Gilden konnten nicht geladen werden")

    # ================================================================== Hauptschleife
    async def run(self):
        self.running = True
        interval = 1.0 / config.TICK_RATE
        while self.running:
            start = now()
            try:
                self.tick()
            except Exception:  # pragma: no cover
                log.exception("Fehler im Welt-Tick")
            elapsed = now() - start
            self.tick_ms = self.tick_ms * 0.95 + elapsed * 1000 * 0.05
            await asyncio.sleep(max(0.0, interval - elapsed))

    def tick(self):
        t = now()
        dt = min(0.5, t - self.last_tick)
        self.last_tick = t
        for zone in list(self.zones.values()):
            zone.run_timers(t)
            self.zone_tick(zone, t, dt)
        for p in list(self.players.values()):
            if p.duel_with:
                self.duel_tick(p)
        for zone in list(self.zones.values()):
            self.broadcast(zone)
        if t >= self.next_party_update:
            self.next_party_update = t + 0.5
            for party in list(self.parties.values()):
                self.send_party(party)
        for key, zone in list(self.zones.items()):
            if zone.is_instance and not zone.players and t - zone.empty_since > (60 if zone.is_arena else INSTANCE_IDLE_TIMEOUT):
                del self.zones[key]
        if t >= self.next_queue:
            self.next_queue = t + 5
            seen = set()
            for p in list(self.players.values()):
                if p.queue and (p.queue["zone"], p.queue["mode"]) not in seen:
                    seen.add((p.queue["zone"], p.queue["mode"]))
                    self.try_match_queue(p.queue["zone"], p.queue["mode"])
            for b in ("1v1", "2v2", "3v3"):
                self.try_arena_match(b)
        if t >= self.next_market:
            self.next_market = t + 30
            try:
                self.market_expire()
            except Exception:  # pragma: no cover
                log.exception("Markt-Abwicklung fehlgeschlagen")
        if t >= self.next_autosave:
            self.next_autosave = t + config.SAVE_INTERVAL
            for p in list(self.players.values()):
                self.save_player(p)

    # ================================================================== Spieler betreten/verlassen
    def add_player(self, data: dict, session) -> Player:
        p = Player(data, session)
        p.recalc_cb = recalc
        p.misc.setdefault("bagslots", [])
        p.misc["_known_items"] = set()
        if not p.action_bars:
            self.default_bars(p)
        zid = data["zone"] if data["zone"] in self.zones else "gruenmark"
        zone = self.zones[zid]
        if zone.is_instance:
            zone = self.zones["gruenmark"]
        self.fit_bags(p)
        recalc(p, full=True)
        if data.get("hp", -1) > 0:
            p.hp = min(p.max_hp, data["hp"])
        p.title = p.misc.get("title_text", "")
        x, z = data["x"], data["z"]
        if not zone.walkable(x, z):
            x, z = zone.walkable_clamp(x, z)
        p.x, p.z = x, z
        p.y = zone.height(x, z)
        p.zone_id = zone.id
        zone.add(p)
        if p.guild_id and p.guild_id in self.guilds:
            g = self.guilds[p.guild_id]
            p.guild_rank = g.members.get(p.char_id, {}).get("rank")
            p.look["guild_name"] = g.name
            if p.char_id in g.members:
                g.members[p.char_id]["lvl"] = p.level
        else:
            p.guild_id = None
            for g in self.guilds.values():
                if p.char_id in g.members:
                    p.guild_id = g.id
                    p.guild_rank = g.members[p.char_id]["rank"]
                    p.look["guild_name"] = g.name
        self.update_gear_look(p)
        if p.misc.get("pet"):
            self.summon_companion(p, p.misc["pet"])
        self.players[p.id] = p
        self.by_name[p.name.lower()] = p
        self.by_char[p.char_id] = p
        try:
            self.load_friends(p)
        except Exception:  # pragma: no cover
            log.exception("Freunde laden")
        self.notify_friends(p, True)
        return p

    def remove_player(self, p: Player):
        if p.trade:
            self.cancel_trade(p, f"{p.name} ist offline gegangen.")
        if p.duel_with:
            o = self.players.get(p.duel_with)
            if o and getattr(o, "duel_active", False):
                self.end_duel(o, p, fled=True)
        self.arena_leave_queue(p)
        self.leave_party(p, silent=False)
        if p.zone:
            for pet in self.pets_of(p):
                p.zone.remove(pet)
            if p.zone.is_instance:
                ret = p.misc.get("instance_return")
                if ret:
                    p.zone_id, p.x, p.z = ret[0], ret[1], ret[2]
                else:
                    ex = p.zone.cfg.get("exit") or ["gruenmark", 0, 0, 0]
                    p.zone_id, p.x, p.z = ex[0], ex[1], ex[2]
            p.zone.remove(p)
        self.save_player(p)
        self.players.pop(p.id, None)
        if self.by_name.get(p.name.lower()) is p:
            del self.by_name[p.name.lower()]
        if self.by_char.get(p.char_id) is p:
            del self.by_char[p.char_id]
        self.notify_friends(p, False)

    def save_data(self, p: Player) -> dict:
        t = now()
        zone_id = p.zone_id
        x, z, y = p.x, p.z, p.y
        if p.zone and p.zone.is_instance:
            ret = p.misc.get("instance_return")
            if ret:
                zone_id, x, z = ret[0], ret[1], ret[2]
                y = 0.0
        misc = {k: v for k, v in p.misc.items() if not k.startswith(SAVE_FIELDS_SKIP)}
        return {
            "level": p.level, "xp": p.xp, "copper": p.copper, "zone": zone_id, "x": round(x, 2), "y": round(y, 2),
            "z": round(z, 2), "rot": round(p.r, 3),
            "look": {k: v for k, v in p.look.items() if k not in ("gear", "cls", "mount", "form", "companion", "guild_name", "poly")},
            "bags": p.bags, "equipment": p.equipment, "quests_active": p.quests_active, "quests_done": p.quests_done,
            "talents": p.talents, "action_bars": p.action_bars, "professions": p.professions, "reputation": p.reputation,
            "currencies": p.currencies, "achievements": p.achievements, "collections": p.collections, "discovered": p.discovered,
            "cooldowns": {k: round(v - t, 1) for k, v in p.cooldowns.items() if v - t > 5},
            "misc": misc, "played_seconds": int(p.played_seconds + (t - p.login_time)),
            "arena_rating": int(p.misc.get("arena_rating", 1500)),
        }

    def save_player(self, p: Player):
        if self.save_callback:
            self.save_callback(p)

    def save_player_now(self, p: Player):
        """Sofort und synchron speichern (nach Wirtschaftsvorgängen, damit Datenbank und Speicher übereinstimmen)."""
        if self.save_callback:
            self.save_callback(p, sync=True)

    # ================================================================== Startdaten
    def send_welcome(self, p: Player):
        from ..content.classes import xp_to_next
        self.send(p, {"t": "welcome", "id": p.id, "char": p.char_id, "name": p.name, "cls": p.class_id, "lvl": p.level,
                      "xp": p.xp, "next": xp_to_next(p.level), "zone": p.zone.id, "zone_name": p.zone.cfg["name"],
                      "inst": p.zone.is_instance, "p": [round(p.x, 2), round(p.y, 2), round(p.z, 2), round(p.r, 3)],
                      "look": p.look, "pt": p.power_type, "server_time": time.time(), "gm": p.gm,
                      "guild": self.guilds[p.guild_id].name if p.guild_id in self.guilds else None,
                      "weekly": self.weekly_challenge(), "affixes": self.current_affixes(),
                      "motd": "Willkommen in Eldornia! Drückt H für die Hilfe."})
        self.send_stats(p)
        self.send_inventory(p)
        self.send_abilities(p)
        self.send_quests(p)
        self.send_talents(p)
        self.send_professions(p)
        self.send_collections(p)
        self.send_reputation(p)
        if p.guild_id:
            self.send_guild(p)
            g = self.guilds.get(p.guild_id)
            if g and g.motd:
                self.send(p, {"t": "chat", "ch": "guild_sys", "from": "", "text": f"Gilde: {g.motd}"})
        self.send_friends(p)
        self.mail_notify(p.char_id)
        if p.dead:
            self.send(p, {"t": "died"})

    # ================================================================== Nachrichten
    def handle(self, p: Player, msg: dict):
        t = msg.get("t")
        h = getattr(self, f"on_{t}", None) if isinstance(t, str) and t.isidentifier() else None
        if h is None:
            return
        try:
            h(p, msg)
        except Exception:  # pragma: no cover - fehlerhafte Eingaben dürfen den Server nicht stoppen
            log.exception("Fehler bei Nachricht %s von %s", t, p.name)

    def on_ready(self, p: Player, m: dict):
        p.ready = True
        p.known = set()
        p.flag_cache = {}

    def on_ping(self, p: Player, m: dict):
        self.send(p, {"t": "pong", "c": m.get("c"), "s": round(self.tick_ms, 1), "n": len(self.players)})

    # ------------------------------------------------------------------ Bewegung (serverseitig geprüft)
    def on_mv(self, p: Player, m: dict):
        if p.dead or not p.ready:
            return
        pos = m.get("p")
        if not isinstance(pos, list) or len(pos) < 4:
            return
        try:
            x, y, z, r = (float(v) for v in pos[:4])
        except (TypeError, ValueError):
            return
        if not all(math.isfinite(v) for v in (x, y, z, r)):
            return
        t = now()
        zone = p.zone
        moving = bool(m.get("m"))
        p.sprinting = bool(m.get("sp"))
        dist = math.hypot(x - p.x, z - p.z)
        if p.rooted or p.incapacitated:
            if dist > 0.05:
                self.teleport(p, p.x, p.z, p.r, "root")
            p.r = r
            p.mark("p")
            return
        # Geschwindigkeitsbudget (Token-Bucket)
        speed = RUN_SPEED * p.speed_mult() * (p.mount_speed if p.mounted else 1.0) * (SPRINT_MULT if p.sprinting else 1.0)
        elapsed = t - p.move_budget_t
        p.move_budget_t = t
        p.move_budget = min(speed * 2.5, p.move_budget + elapsed * speed * 1.25)
        if dist > p.move_budget + 0.6 and not p.gm:
            self.teleport(p, p.x, p.z, p.r, "speed")
            return
        p.move_budget -= dist
        if dist > 0.01 and not zone.walkable(x, z):
            # an Kanten entlanggleiten statt hart zurücksetzen
            nx, nz = zone.try_move(p.x, p.z, x, z, for_mob=False)
            if (nx, nz) == (p.x, p.z) and not zone.walkable(p.x, p.z):
                nx, nz = zone.walkable_clamp(*p.last_safe)
            self.teleport(p, nx, nz, r, "block")
            return
        if zone.walkable(x, z):
            p.last_safe = (x, z)
        ground = zone.height(x, z)
        wl = zone.water_level(x, z)
        if wl is not None and ground < wl - 1.2:
            ground = wl - 1.15        # schwimmen
        if y < ground - 1.5 or y > ground + 6.0:
            y = ground
        if dist > 0.01:
            p.last_move_t = t
            if p.cast and p.cast.get("kind") in ("ability", "gather", "craft", "hearth", "mount", "use"):
                ab = ABILITIES.get(p.cast.get("ab", ""))
                if not (ab and ab.get("tags") and "move_cast" in ab["tags"]):
                    self.interrupt(p)
            if p.eating:
                self.stop_eating(p)
            if p.sitting:
                p.sitting = False
                p.mark("st")
            if p.emote:
                p.emote = None
                p.mark("emote")
            if p.loot_open:
                p.loot_open = None
        p.moving = moving
        p.x, p.y, p.z, p.r = x, y, z, r
        p.mark("p")
        p.jumping = bool(m.get("j"))

    def on_jump(self, p: Player, m: dict):
        if not p.dead:
            p.zone.emit_fx(p.x, p.z, {"k": "jump", "id": p.id})

    # ------------------------------------------------------------------ Ziel & Kampf
    def on_tg(self, p: Player, m: dict):
        tid = m.get("id")
        if tid is None:
            p.target = None
            p.auto_attack = False
        elif isinstance(tid, int) and tid in p.zone.entities:
            p.target = tid
        p.mark("tg")

    def on_atk(self, p: Player, m: dict):
        tid = m.get("id", p.target)
        tgt = p.zone.entities.get(tid) if isinstance(tid, int) else None
        if not tgt or tgt.dead or not self.is_enemy(p, tgt):
            self.err(p, "Ungültiges Ziel.")
            return
        p.target = tgt.id
        p.mark("tg")
        if p.mounted:
            self.dismount(p)
        if p.stealthed and not p.mods.get("stealth_attack"):
            pass
        p.auto_attack = True
        if p.swing_ready < now():
            p.swing_ready = now() + 0.1
        if isinstance(tgt, Mob) and tgt.state == "idle" and not tgt.look.get("dummy"):
            pass

    def on_satk(self, p: Player, m: dict):
        p.auto_attack = False

    def on_ab(self, p: Player, m: dict):
        ab = m.get("ab")
        if not isinstance(ab, str):
            return
        gp = m.get("gp")
        if gp is not None and not (isinstance(gp, list) and len(gp) == 2):
            gp = None
        tid = m.get("tid")
        self.use_ability(p, ab, tid if isinstance(tid, int) else None, gp)

    def on_stopcast(self, p: Player, m: dict):
        if p.cast:
            p.cast = None
            p.mark("cast")

    def on_release(self, p: Player, m: dict):
        self.release_spirit(p)

    def on_leave_instance(self, p: Player, m: dict):
        if p.zone.is_instance and not p.zone.is_arena:
            self.leave_instance(p)

    def on_sit(self, p: Player, m: dict):
        if p.dead or p.combat:
            return
        p.sitting = not p.sitting
        if not p.sitting and p.eating:
            self.stop_eating(p)
        p.mark("st")

    def on_emote(self, p: Player, m: dict):
        e = str(m.get("e", ""))
        if p.dead:
            return
        self.emote(p, e)

    def on_mount(self, p: Player, m: dict):
        mid = m.get("m")
        if mid is None:
            mid = p.misc.get("fav_mount") or (p.collections.get("mounts") or [None])[0]
        if p.mounted:
            self.dismount(p)
        elif mid:
            p.misc["fav_mount"] = mid
            self.summon_mount(p, mid)
        else:
            self.err(p, "Ihr besitzt kein Reittier. Stallmeister Fritz in Eichenau verkauft welche.")

    def on_companion(self, p: Player, m: dict):
        self.summon_companion(p, m.get("pet"))

    def on_title(self, p: Player, m: dict):
        self.set_title(p, m.get("id"))

    def on_transmog(self, p: Player, m: dict):
        npc = p.zone.entities.get(p.misc.get("_gossip_npc"))
        if not isinstance(npc, Npc) or "transmog" not in npc.tpl.get("services", []) or p.dist(npc) > 8:
            self.err(p, "Sprecht mit einer Schneiderin.")
            return
        self.set_transmog(p, str(m.get("slot")), m.get("skin"))

    def on_bars(self, p: Player, m: dict):
        bars = m.get("bars")
        if not isinstance(bars, list) or len(bars) > 48:
            return
        clean = []
        for b in bars:
            if isinstance(b, dict) and (isinstance(b.get("ab"), str) and b["ab"] in ABILITIES or
                                        isinstance(b.get("item"), str) and b["item"] in ITEMS or
                                        isinstance(b.get("mount"), str) or isinstance(b.get("emote"), str)):
                clean.append({k: v for k, v in b.items() if k in ("ab", "item", "mount", "emote") and isinstance(v, str)})
            else:
                clean.append(None)
        p.action_bars = clean
        p.save_dirty = True

    # ------------------------------------------------------------------ Interaktion
    def on_interact(self, p: Player, m: dict):
        e = p.zone.entities.get(m.get("id"))
        if e is None or p.dead:
            return
        rng = INTERACT_RANGE + e.radius
        if p.dist(e) > rng + 1.0:
            self.err(p, "Ihr seid zu weit entfernt.")
            return
        if isinstance(e, Npc):
            self.open_gossip(p, e)
        elif isinstance(e, Mob) and not isinstance(e, Pet):
            if e.dead and e.loot.get(p.id):
                self.open_loot(p, e)
        elif isinstance(e, Player) and e is not p:
            self.send(p, {"t": "inspect", "id": e.id, "name": e.name, "lvl": e.level, "cls": e.class_id,
                          "eq": e.equipment, "items": self.item_info_for(p, [s["i"] for s in e.equipment.values() if s]),
                          "guild": self.guilds[e.guild_id].name if e.guild_id in self.guilds else None,
                          "ach": sum(1 for k in e.achievements if not k.startswith("_")),
                          "title": e.title})
        elif isinstance(e, GameObj):
            self.use_object(p, e)

    def use_object(self, p: Player, o: GameObj):
        k = o.obj_kind
        if k in ("node", "quest"):
            self.start_gather(p, o)
        elif k == "chest":
            opened = p.misc.setdefault("_opened", set())
            if o.id in opened:
                return
            if o.spec.get("needs_item") and p.count_item(o.spec["needs_item"]) < 1:
                self.err(p, f"Verschlossen. Benötigt: {ITEMS[o.spec['needs_item']]['name']}")
                return
            persist = p.misc.get("chests")
            if not isinstance(persist, dict):
                persist = p.misc["chests"] = {}
            ckey = f"{p.zone.id}:{o.spec['pos'][0]}:{o.spec['pos'][1]}"
            if not p.zone.is_instance and time.time() - persist.get(ckey, 0) < 20 * 3600:
                self.err(p, "Diese Truhe habt Ihr heute schon geöffnet.")
                return
            if not p.zone.is_instance:
                persist[ckey] = time.time()
            opened.add(o.id)
            if o.spec.get("needs_item"):
                p.remove_item(o.spec["needs_item"], 1)
            loot = {"items": [list(x) for x in o.spec.get("loot", [])], "copper": o.spec.get("copper", 0)}
            tier = o.spec.get("tier", 1)
            from ..content.items import world_drop_pool
            import random as _r
            lvl = max(1, p.level if not p.zone.is_instance else p.zone.cfg.get("recommended", p.level))
            pool = world_drop_pool(lvl, 3 if tier >= 2 else 2)
            if pool:
                loot["items"].append([_r.choice(pool), 1])
            loot["copper"] += _r.randint(20, 60) * lvl * tier
            o.loot = {p.id: loot}
            p.loot_open = o.id
            self.send(p, {"t": "loot", "id": o.id, "name": o.name, "items": loot["items"], "copper": loot["copper"],
                          "defs": self.item_info_for(p, [i[0] for i in loot["items"]])})
            if o.spec.get("hidden"):
                self.progress_counter(p, "chests", 1)
            if o.spec.get("event"):
                self.quest_event(p, o.spec["event"], 1)
            p.zone.emit_fx(o.x, o.z, {"k": "chest", "id": o.id})
        elif k == "stone":
            p.misc["_stone_obj"] = o.id
            self.activate_stone(p, o)
        elif k == "mailbox":
            self.mail_open(p)
        elif k == "board":
            self.open_board(p, p.zone.id, o.id)
        elif k in ("forge", "alchemy", "anvil"):
            self.send_professions(p)
            self.send(p, {"t": "open", "w": "professions"})

    def on_gossip(self, p: Player, m: dict):
        npc = p.zone.entities.get(m.get("npc"))
        if not isinstance(npc, Npc) or p.dist(npc) > INTERACT_RANGE + 3:
            return
        opt = m.get("opt")
        svc = npc.tpl.get("services", [])
        if opt == "vendor" and "vendor" in svc:
            self.open_vendor(p, npc)
        elif opt == "trainer" and "trainer" in svc:
            self.send_talents(p)
            self.send(p, {"t": "trainer", "npc": npc.id, "name": npc.name, "cls": npc.tpl.get("trainer"),
                          "mine": npc.tpl.get("trainer") == p.class_id})
        elif opt == "prof_trainer" and "prof_trainer" in svc:
            self.open_prof_trainer(p, npc)
        elif opt == "innkeeper" and "innkeeper" in svc:
            self.set_hearth(p, npc.tpl.get("bind_stone", "stein_eichenau"), npc.name)
        elif opt == "auction" and "auction" in svc:
            self.send(p, {"t": "open", "w": "market"})
            self.market_search(p, {"q": ""})
        elif opt == "mail" and "mail" in svc:
            self.mail_open(p)
        elif opt == "guild" and "guild" in svc:
            self.send(p, {"t": "open", "w": "guild_create" if not p.guild_id else "guild"})
            if p.guild_id:
                self.send_guild(p)
        elif opt == "spirit" and "spirit" in svc:
            self.sys(p, "Bruder Anselm segnet Euch.")
        elif opt == "stable" and "stable" in svc:
            self.send_collections(p)
            self.send(p, {"t": "open", "w": "collections"})
        elif opt == "transmog" and "transmog" in svc:
            self.send_collections(p)
            self.send(p, {"t": "open", "w": "transmog"})
        elif opt == "repair" and "repair" in svc:
            self.repair(p, {"npc": npc.id})
        elif opt == "finder" and "finder" in svc:
            self.send(p, {"t": "open", "w": "finder"})
        elif opt == "arena" and "arena" in svc:
            self.send(p, {"t": "open", "w": "arena", "rating": p.misc.get("arena_rating", 1500)})

    def _giver(self, p: Player, m: dict) -> str | None:
        g = m.get("giver")
        if g == "item":
            return "item"
        if isinstance(g, str) and g.startswith("board:"):
            for e in p.zone.entities.values():
                if isinstance(e, GameObj) and e.obj_kind == "board" and p.dist(e) < 10:
                    return g
            return None
        npc = p.zone.npcs.get(g) if isinstance(g, str) else None
        if not npc or p.dist(npc) > INTERACT_RANGE + 3:
            return None
        return g

    def on_quest_view(self, p: Player, m: dict):
        g = self._giver(p, m)
        if g:
            self.show_quest(p, g, str(m.get("q")))

    def on_quest_accept(self, p: Player, m: dict):
        g = self._giver(p, m)
        if g:
            self.accept_quest(p, g, str(m.get("q")))

    def on_quest_complete(self, p: Player, m: dict):
        g = self._giver(p, m)
        if g:
            self.complete_quest(p, g, str(m.get("q")), m.get("choice"))

    def on_quest_abandon(self, p: Player, m: dict):
        self.abandon_quest(p, str(m.get("q")))

    def on_quest_share(self, p: Player, m: dict):
        qid = str(m.get("q"))
        if qid not in p.quests_active or not p.party:
            return
        for o in self.party_players(p.party):
            if o is not p and o.dist(p) < 40 and self.quest_available(o, qid):
                self.send(o, {"t": "quest_detail", "mode": "offer", "giver": W.QUESTS[qid]["giver"], "shared": p.name,
                              "q": self.quest_payload(W.QUESTS[qid], o)})

    def on_quest_accept_shared(self, p: Player, m: dict):
        qid = str(m.get("q"))
        q = W.QUESTS.get(qid)
        if q and self.quest_available(p, qid):
            self.accept_quest(p, q["giver"], qid)

    def on_dungeon_enter(self, p: Player, m: dict):
        zid = m.get("zone")
        mode = m.get("mode", "normal")
        for portal in p.zone.cfg.get("portals", []):
            if portal["to"] == zid and (p.x - portal["x"]) ** 2 + (p.z - portal["z"]) ** 2 <= (portal["r"] + 6) ** 2:
                p.portal_lock = 0
                self.enter_portal(p, portal, mode)
                return

    # ------------------------------------------------------------------ Beute & Gegenstände
    def on_loot_take(self, p: Player, m: dict):
        self.loot_take(p, m)

    def on_loot_all(self, p: Player, m: dict):
        self.loot_all(p, m)

    def on_loot_close(self, p: Player, m: dict):
        self.loot_close(p)

    def on_buy(self, p: Player, m: dict):
        self.buy(p, m)

    def on_sell(self, p: Player, m: dict):
        self.sell(p, m)

    def on_buyback(self, p: Player, m: dict):
        self.buyback(p, m)

    def on_sell_junk(self, p: Player, m: dict):
        self.sell_junk(p, m)

    def on_repair(self, p: Player, m: dict):
        self.repair(p, m)

    def on_use(self, p: Player, m: dict):
        slot = m.get("slot")
        if isinstance(slot, int):
            self.use_item(p, slot, m.get("tid"))
        elif isinstance(m.get("item"), str):
            iid = m["item"]
            for i, s in enumerate(p.bags):
                if s and s["i"] == iid:
                    self.use_item(p, i, m.get("tid"))
                    return
            self.err(p, "Davon habt Ihr nichts mehr.")

    def on_equip(self, p: Player, m: dict):
        if isinstance(m.get("slot"), int):
            self.equip(p, m["slot"], m.get("to"))

    def on_unequip(self, p: Player, m: dict):
        if m.get("s") in EQUIP_SLOTS:
            self.unequip(p, m["s"], m.get("to"))

    def on_swap(self, p: Player, m: dict):
        a, b = m.get("a"), m.get("b")
        if isinstance(a, int) and isinstance(b, int):
            self.swap(p, a, b)

    def on_split(self, p: Player, m: dict):
        if isinstance(m.get("slot"), int):
            self.split(p, m["slot"], m.get("n", 1))

    def on_sort(self, p: Player, m: dict):
        self.sort_bags(p)

    def on_destroy(self, p: Player, m: dict):
        if isinstance(m.get("slot"), int):
            self.destroy(p, m["slot"])

    # ------------------------------------------------------------------ Talente, Berufe
    def on_talent(self, p: Player, m: dict):
        self.learn_talent(p, str(m.get("id")))

    def on_talent_reset(self, p: Player, m: dict):
        npc = p.zone.entities.get(m.get("npc"))
        if not isinstance(npc, Npc) or npc.tpl.get("trainer") != p.class_id or p.dist(npc) > 8:
            self.err(p, "Sprecht mit Eurem Klassenlehrer.")
            return
        self.reset_talents(p)

    def _npc_near(self, p: Player, m: dict) -> Npc | None:
        npc = p.zone.entities.get(m.get("npc"))
        if isinstance(npc, Npc) and p.dist(npc) <= 8:
            return npc
        return None

    def on_prof_learn(self, p: Player, m: dict):
        npc = self._npc_near(p, m)
        if npc:
            self.learn_profession(p, npc, str(m.get("prof")))

    def on_prof_rank(self, p: Player, m: dict):
        npc = self._npc_near(p, m)
        if npc:
            self.upgrade_rank(p, npc, str(m.get("prof")))

    def on_prof_recipe(self, p: Player, m: dict):
        npc = self._npc_near(p, m)
        if npc:
            self.train_recipe(p, npc, str(m.get("r")))

    def on_prof_unlearn(self, p: Player, m: dict):
        self.unlearn_profession(p, str(m.get("prof")))

    def on_craft(self, p: Player, m: dict):
        self.craft(p, str(m.get("r")), m.get("n", 1))

    def on_disenchant(self, p: Player, m: dict):
        if isinstance(m.get("slot"), int):
            self.disenchant(p, m["slot"])

    def on_get(self, p: Player, m: dict):
        """Fenster-Daten anfordern."""
        w = m.get("w")
        {"achievements": self.send_achievements, "reputation": self.send_reputation, "collections": self.send_collections,
         "professions": self.send_professions, "talents": self.send_talents, "guild": self.send_guild,
         "friends": self.send_friends, "quests": self.send_quests, "stats": self.send_stats, "inventory": self.send_inventory,
         "abilities": self.send_abilities}.get(w, lambda _p: None)(p)
        if w == "map":
            self.send_map(p)
        elif w == "finder":
            self.send_finder(p)

    def send_map(self, p: Player):
        z = p.zone
        party = []
        if p.party:
            party = [{"name": o.name, "x": round(o.x, 1), "z": round(o.z, 1), "cls": o.class_id}
                     for o in self.party_players(p.party) if o.zone is z and o is not p]
        npcs = [{"name": n.name, "title": n.title, "x": n.x, "z": n.z, "svc": n.tpl.get("services", []),
                 "q": self.quest_marker(p, n.npc_id)} for n in z.npcs.values()]
        self.send(p, {"t": "map", "zone": z.id, "name": z.cfg["name"], "party": party, "npcs": npcs,
                      "discovered": [s.split(":", 1)[1] for s in p.discovered.get("subzones", []) if s.startswith(z.id + ":")],
                      "regions": [{"id": zid, "name": W.ZONES[zid]["name"], "levels": W.ZONES[zid].get("levels"),
                                   "known": zid in p.discovered.get("zones", [])} for zid in W.REGIONS],
                      "stones": p.discovered.get("stones", [])})

    def send_finder(self, p: Player):
        out = []
        for zid, z in W.DUNGEONS.items():
            if z.get("hidden") or z.get("arena"):
                continue
            out.append({"id": zid, "name": z["name"], "levels": z["levels"], "players": z.get("players_text", ""),
                        "modes": [{"id": md, "name": W.MODES[md]["name"]} for md in z.get("modes", ["normal"])],
                        "locks": self.lockout_info(p, zid)})
        self.send(p, {"t": "finder", "list": out, "queue": p.queue, "weekly": self.weekly_challenge(),
                      "affixes": [{"id": a, **W.AFFIXES[a]} for a in self.current_affixes()], "role": p.misc.get("role", "dps"),
                      "arena_rating": p.misc.get("arena_rating", 1500)})

    # ------------------------------------------------------------------ Reisen
    def on_travel(self, p: Player, m: dict):
        self.travel_to_stone(p, str(m.get("stone")))

    def on_waypoint(self, p: Player, m: dict):
        """Schnellreise innerhalb von Städten (Wegpunkte)."""
        wps = {w["id"]: w for w in p.zone.cfg.get("waypoints", [])}
        to = wps.get(m.get("to"))
        if not to or p.combat:
            return
        near = any(math.hypot(p.x - w["pos"][0], p.z - w["pos"][1]) < 6 for w in wps.values())
        if not near:
            self.err(p, "Ihr müsst an einem Wegweiser stehen.")
            return
        self.teleport(p, to["pos"][0] + 1.5, to["pos"][1] + 1.5, p.r, "tele")

    def on_hearth(self, p: Player, m: dict):
        if p.count_item("ruhestein") < 1:
            self.err(p, "Ihr habt keinen Ruhestein.")
            return
        self.use_hearth(p)

    # ------------------------------------------------------------------ Soziales
    def on_chat(self, p: Player, m: dict):
        self.chat(p, m)

    def on_who(self, p: Player, m: dict):
        self.who(p, str(m.get("q", "")))

    def on_invite(self, p: Player, m: dict):
        self.invite(p, m.get("name") if m.get("name") is not None else m.get("id"))

    def on_party_accept(self, p: Player, m: dict):
        self.party_accept(p)

    def on_party_decline(self, p: Player, m: dict):
        self.party_decline(p)

    def on_party_leave(self, p: Player, m: dict):
        self.leave_party(p)

    def on_party_kick(self, p: Player, m: dict):
        self.party_kick(p, m.get("id"))

    def on_party_lead(self, p: Player, m: dict):
        self.party_promote(p, m.get("id"))

    def on_party_raid(self, p: Player, m: dict):
        self.party_raid(p)

    def on_role(self, p: Player, m: dict):
        if m.get("role") in ("tank", "heiler", "dps"):
            p.misc["role"] = m["role"]

    def on_queue(self, p: Player, m: dict):
        self.queue_dungeon(p, str(m.get("zone")), str(m.get("mode", "normal")), str(m.get("role", "dps")))

    def on_queue_leave(self, p: Player, m: dict):
        self.leave_queue(p)

    def on_arena_queue(self, p: Player, m: dict):
        self.arena_queue(p, str(m.get("bracket", "1v1")))

    def on_arena_leave(self, p: Player, m: dict):
        self.arena_leave_queue(p)

    def on_friend_add(self, p: Player, m: dict):
        self.friend_add(p, str(m.get("name", "")), bool(m.get("ignore")))

    def on_friend_remove(self, p: Player, m: dict):
        self.friend_remove(p, m.get("id"))

    def on_guild_create(self, p: Player, m: dict):
        self.guild_create(p, str(m.get("name", "")), str(m.get("tag", "")))

    def on_guild_invite(self, p: Player, m: dict):
        self.guild_invite(p, str(m.get("name", "")))

    def on_guild_accept(self, p: Player, m: dict):
        self.guild_accept(p)

    def on_guild_decline(self, p: Player, m: dict):
        p.guild_invite = None

    def on_guild_leave(self, p: Player, m: dict):
        self.guild_leave(p)

    def on_guild_kick(self, p: Player, m: dict):
        self.guild_kick(p, m.get("id"))

    def on_guild_rank(self, p: Player, m: dict):
        self.guild_set_rank(p, m.get("id"), bool(m.get("up")))

    def on_guild_motd(self, p: Player, m: dict):
        self.guild_motd(p, str(m.get("text", "")))

    def on_guild_deposit(self, p: Player, m: dict):
        if isinstance(m.get("slot"), int):
            self.guild_bank_deposit(p, m["slot"])

    def on_guild_withdraw(self, p: Player, m: dict):
        if isinstance(m.get("slot"), int):
            self.guild_bank_withdraw(p, m["slot"])

    def on_guild_money(self, p: Player, m: dict):
        self.guild_bank_money(p, m.get("amount", 0))

    def on_trade_request(self, p: Player, m: dict):
        self.trade_request(p, m.get("id"))

    def on_trade_answer(self, p: Player, m: dict):
        self.trade_answer(p, bool(m.get("ok")))

    def on_trade_set(self, p: Player, m: dict):
        self.trade_set(p, m.get("slots") or [], m.get("copper", 0))

    def on_trade_lock(self, p: Player, m: dict):
        self.trade_lock(p)

    def on_trade_confirm(self, p: Player, m: dict):
        self.trade_confirm(p)

    def on_trade_cancel(self, p: Player, m: dict):
        self.cancel_trade(p, f"{p.name} hat den Handel abgebrochen.")

    def on_duel(self, p: Player, m: dict):
        self.duel_request(p, m.get("id"))

    def on_duel_answer(self, p: Player, m: dict):
        self.duel_answer(p, bool(m.get("ok")))

    # ------------------------------------------------------------------ Markt & Post
    def on_market_search(self, p: Player, m: dict):
        self.market_search(p, m)

    def on_market_price(self, p: Player, m: dict):
        self.market_price_info(p, str(m.get("i")))

    def on_market_post(self, p: Player, m: dict):
        self.market_post(p, m)

    def on_market_buy(self, p: Player, m: dict):
        self.market_buy(p, m.get("id"))

    def on_market_bid(self, p: Player, m: dict):
        self.market_bid(p, m.get("id"), m.get("amount", 0))

    def on_market_cancel(self, p: Player, m: dict):
        self.market_cancel(p, m.get("id"))

    def on_market_mine(self, p: Player, m: dict):
        self.market_mine(p)

    def on_mail_open(self, p: Player, m: dict):
        self.mail_open(p)

    def on_mail_take(self, p: Player, m: dict):
        self.mail_take(p, m.get("id"))

    def on_mail_send(self, p: Player, m: dict):
        self.mail_send(p, m)
