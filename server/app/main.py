"""Eldornia – Server (FastAPI).

REST:      Registrierung, E-Mail-Bestätigung, Login, Charakterverwaltung, Spielinhalte, Zonendaten
WebSocket: /ws – Echtzeitverbindung zur Spielwelt (serverseitig simuliert, GDD 12)
Statisch:  /play – Web-Version des Godot-Clients (falls exportiert), /download – Installer
"""
from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
import secrets
import smtplib
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from . import auth, config
from .content import world as W
from .content.abilities import ABILITIES, SCHOOL_NAMES, ability_client_info, class_abilities
from .content.classes import CLASSES, PLANNED_CLASSES, RESOURCES, SPEC_NAMES, base_stats
from .content.collections import MOUNTS, PETS, TITLES
from .content.factions import CURRENCIES, FACTIONS, STANDINGS
from .content.items import ITEMS, RARITY_COLORS, RARITY_NAMES, SLOT_NAMES, STAT_NAMES, WEAPON_NAMES, ARMOR_NAMES, item_client_info
from .content.professions import PROFESSIONS
from .content.talents import client_trees
from .db import SessionLocal, engine, get_session, init_db
from .game.world import World
from .game.zone import static_zone
from .models import (BossDrop, Character, CharacterQuest, ClassDef, DungeonDef, Equipment, InventoryItem, ItemDef, QuestDef,
                     RegionDef, User)

log = logging.getLogger("eldornia")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "client" / "export" / "web"
NAME_RE = re.compile(r"^[A-Za-zÄÖÜäöüß]{3,16}$")
USER_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RESERVED = {n["name"].split()[-1].lower() for n in W.NPCS.values()} | {"admin", "gm", "eldornia", "system"}
LOOK_KEYS = {"skin": 16, "hair": 16, "hair_style": 16, "body": 2, "beard": 16, "beard_style": 12, "eyes": 12, "eye_color": 16,
             "face": 12, "kind": 8, "scar": 8, "tattoo": 16, "height": 6}

world = World()
login_limiter = auth.RateLimiter(10, 60)
register_limiter = auth.RateLimiter(5, 300)
_zone_cache: dict[str, bytes] = {}
_save_locks: dict[int, threading.Lock] = {}


# ============================================================================== Speichern & Laden
def _lock(char_id: int) -> threading.Lock:
    lk = _save_locks.get(char_id)
    if lk is None:
        lk = _save_locks[char_id] = threading.Lock()
    return lk


def write_character(char_id: int, data: dict):
    """Speichert einen Charakter vollständig in einer Transaktion (Charakter, Inventar, Ausrüstung, Quests)."""
    with _lock(char_id), SessionLocal() as s:
        c = s.get(Character, char_id)
        if not c:
            return
        for k in ("level", "xp", "copper", "zone", "x", "y", "z", "rot", "look", "talents", "action_bars", "professions",
                  "reputation", "currencies", "achievements", "collections", "discovered", "cooldowns", "misc",
                  "played_seconds", "arena_rating"):
            if k in data:
                setattr(c, k, data[k])
        s.execute(delete(InventoryItem).where(InventoryItem.character_id == char_id))
        s.execute(delete(Equipment).where(Equipment.character_id == char_id))
        s.execute(delete(CharacterQuest).where(CharacterQuest.character_id == char_id))
        for i, inst in enumerate(data["bags"]):
            if inst:
                s.add(InventoryItem(character_id=char_id, item_id=inst["i"], quantity=inst["n"], slot=i, bound=bool(inst.get("b")),
                                    extra={k: v for k, v in inst.items() if k not in ("i", "n", "b")}))
        for slot, inst in data["equipment"].items():
            if inst:
                s.add(Equipment(character_id=char_id, slot=slot, item_id=inst["i"], extra={k: v for k, v in inst.items() if k != "i"}))
        for qid, prog in data["quests_active"].items():
            s.add(CharacterQuest(character_id=char_id, quest_id=qid, status="active", progress=list(prog)))
        for qid, ts in data["quests_done"].items():
            if qid not in data["quests_active"]:
                s.add(CharacterQuest(character_id=char_id, quest_id=qid, status="done", progress=[], completed_at=float(ts)))
        s.commit()


def load_character(c: Character, s: Session) -> dict:
    bags: list = []
    for it in s.execute(select(InventoryItem).where(InventoryItem.character_id == c.id).order_by(InventoryItem.slot)).scalars():
        if it.item_id not in ITEMS:
            continue
        while len(bags) <= it.slot:
            bags.append(None)
        inst = {"i": it.item_id, "n": it.quantity}
        if it.bound:
            inst["b"] = 1
        inst.update(it.extra or {})
        bags[it.slot] = inst
    eq = {}
    for e in s.execute(select(Equipment).where(Equipment.character_id == c.id)).scalars():
        if e.item_id in ITEMS:
            eq[e.slot] = {"i": e.item_id, **(e.extra or {})}
    qa, qd = {}, {}
    for q in s.execute(select(CharacterQuest).where(CharacterQuest.character_id == c.id)).scalars():
        if q.quest_id not in W.QUESTS:
            continue
        if q.status == "active":
            n = len(W.QUESTS[q.quest_id]["objectives"])
            qa[q.quest_id] = (list(q.progress or []) + [0] * n)[:n]
        else:
            qd[q.quest_id] = q.completed_at or 0.0
    user = s.get(User, c.user_id)
    return {"id": c.id, "user_id": c.user_id, "username": user.username if user else "", "name": c.name, "class_id": c.class_id,
            "level": c.level, "xp": c.xp, "copper": c.copper, "zone": c.zone, "x": c.x, "y": c.y, "z": c.z, "rot": c.rot,
            "look": c.look or {}, "bags": bags, "equipment": eq, "quests_active": qa, "quests_done": qd, "talents": c.talents or {},
            "action_bars": c.action_bars or [], "professions": c.professions or {}, "reputation": c.reputation or {},
            "currencies": c.currencies or {}, "achievements": c.achievements or {}, "collections": c.collections or {},
            "discovered": c.discovered or {}, "cooldowns": c.cooldowns or {}, "misc": dict(c.misc or {}, arena_rating=c.arena_rating),
            "played_seconds": c.played_seconds, "is_admin": bool(user and (user.is_admin or user.username.lower() in config.ADMIN_USERS))}


def save_player(p, sync: bool = False):
    data = json.loads(json.dumps(world.save_data(p), default=list))     # Momentaufnahme (entkoppelt vom Spielzustand)
    p.save_dirty = False
    if sync:
        write_character(p.char_id, data)
        return
    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, write_character, p.char_id, data)
    except RuntimeError:
        write_character(p.char_id, data)


world.save_callback = save_player


def seed_static_tables():
    """Statische Spieldefinitionen in die Datenbank schreiben (GDD 13: classes, items, regions, quests, dungeons, boss_drops)."""
    with SessionLocal() as s:
        if s.execute(select(func.count()).select_from(ItemDef)).scalar() == len(ITEMS) and \
                s.execute(select(func.count()).select_from(QuestDef)).scalar() == len(W.QUESTS):
            return
        for model in (BossDrop, DungeonDef, QuestDef, RegionDef, ItemDef, ClassDef):
            s.execute(delete(model))
        for cid, c in CLASSES.items():
            s.add(ClassDef(id=cid, name=c["name"], base_stats=base_stats(cid, 1), description=c["desc"]))
        s.add_all([ItemDef(id=i, name=it["name"], item_type=it["type"], rarity=it["q"], stats=it.get("stats", {}),
                           bind_type=it.get("bind"), level=it.get("lvl", 1)) for i, it in ITEMS.items()])
        for zid, z in W.ZONES.items():
            if z.get("region"):
                s.add(RegionDef(id=zid, name=z["name"], level_min=z["levels"][0], level_max=z["levels"][1]))
            elif z["type"] == "dungeon" and not z.get("arena"):
                s.add(DungeonDef(id=zid, name=z["name"], recommended_level=z.get("recommended", z["levels"][0]),
                                 max_players=z.get("max_players", 5)))
        for qid, q in W.QUESTS.items():
            s.add(QuestDef(id=qid, name=q["title"], requirements={"level": q["min_level"], "prev": q.get("prev"), "cls": q.get("cls")},
                           rewards=json.loads(json.dumps(q["rewards"]))))
        for mid, m in W.MOBS.items():
            for l in m.get("loot", []):
                s.add(BossDrop(boss_id=mid, item_id=l["item"], drop_chance=l["chance"])) if m.get("boss") or m.get("rare") else None
            bl = m.get("boss_loot")
            if bl:
                pool = bl.get("pool", [])
                for i in pool:
                    s.add(BossDrop(boss_id=mid, item_id=i, drop_chance=round(bl.get("n", 1) / max(1, len(pool)), 3)))
                if bl.get("legendary"):
                    s.add(BossDrop(boss_id=mid, item_id=bl["legendary"], drop_chance=bl.get("legendary_chance", 0.01)))
        s.commit()
    log.info("Statische Definitionen in die Datenbank geschrieben (%d Gegenstände, %d Quests).", len(ITEMS), len(W.QUESTS))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_static_tables()
    t = time.time()
    world.boot()
    for zid in W.ZONES:
        _zone_cache[zid] = json.dumps(static_zone(zid).client_data(), separators=(",", ":")).encode()
    log.info("Welt erzeugt in %.1f s", time.time() - t)
    task = asyncio.create_task(world.run())
    log.info("Eldornia-Server gestartet (Version %s)", config.VERSION)
    yield
    world.running = False
    for p in list(world.players.values()):
        save_player(p, sync=True)
    task.cancel()


app = FastAPI(title="Eldornia", version=config.VERSION, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ============================================================================== Hilfen
def current_user(authorization: str = Header(default=""), db: Session = Depends(get_session)) -> User:
    token = authorization.removeprefix("Bearer ").strip()
    payload = auth.decode_token(token) if token else None
    if not payload:
        raise HTTPException(401, "Nicht angemeldet.")
    user = db.get(User, int(payload["sub"]))
    if not user or user.banned:
        raise HTTPException(401, "Account nicht gefunden.")
    return user


def char_summary(c: Character, eq: dict | None = None) -> dict:
    gear = {}
    for slot, inst in (eq or {}).items():
        it = ITEMS.get(inst["i"])
        if it:
            gear[slot] = {"sub": it.get("sub"), "q": it["q"], "vis": it.get("vis", {}), "id": inst["i"], "two": it.get("two_hand", False)}
    return {"id": c.id, "name": c.name, "cls": c.class_id, "cls_name": CLASSES[c.class_id]["name"], "level": c.level,
            "zone": W.ZONES.get(c.zone, W.ZONES["gruenmark"])["name"], "look": dict(c.look or {}, gear=gear, cls=c.class_id),
            "online": c.id in world.by_char, "played": c.played_seconds}


class Credentials(BaseModel):
    username: str
    password: str
    email: str | None = None


class VerifyBody(BaseModel):
    code: str


class NewCharacter(BaseModel):
    name: str
    cls: str
    look: dict = {}


def send_verification_mail(to: str, code: str) -> bool:
    if not config.SMTP_HOST:
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = "Eldornia – Bestätige deine E-Mail-Adresse"
        msg["From"] = config.SMTP_FROM
        msg["To"] = to
        msg.set_content(f"Willkommen in Eldornia!\n\nDein Bestätigungscode lautet: {code}\n\nGib ihn im Spiel ein, um deinen Account zu aktivieren.")
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if config.SMTP_USER:
                smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception:  # pragma: no cover
        log.exception("E-Mail-Versand fehlgeschlagen")
        return False


# ============================================================================== REST: Accounts
@app.get("/api/status")
def status():
    return {"name": W.WORLD_NAME, "version": config.VERSION, "online": len(world.players), "tick_ms": round(world.tick_ms, 2),
            "uptime": int(time.time() - world.started), "zones": len(world.zones)}


@app.post("/api/register")
def register(cred: Credentials, request: Request, db: Session = Depends(get_session)):
    ip = request.client.host if request.client else "?"
    if not config.TESTING and not register_limiter.allow(ip):
        raise HTTPException(429, "Zu viele Versuche. Bitte warte ein paar Minuten.")
    if not USER_RE.match(cred.username):
        raise HTTPException(400, "Benutzername: 3–20 Zeichen, nur Buchstaben, Zahlen und _.")
    if len(cred.password) < 6 or len(cred.password) > 128:
        raise HTTPException(400, "Das Passwort muss mindestens 6 Zeichen lang sein.")
    email = (cred.email or "").strip() or None
    if email and not EMAIL_RE.match(email):
        raise HTTPException(400, "Ungültige E-Mail-Adresse.")
    if db.scalar(select(User).where(User.username.ilike(cred.username))):
        raise HTTPException(400, "Dieser Benutzername ist bereits vergeben.")
    code = f"{secrets.randbelow(1000000):06d}"
    user = User(username=cred.username, email=email, password_hash=auth.hash_password(cred.password), verify_code=code)
    mail_sent = bool(email) and send_verification_mail(email, code)
    user.email_verified = not mail_sent      # ohne Mailserver: automatisch bestätigt
    if cred.username.lower() in config.ADMIN_USERS:
        user.is_admin = True
    db.add(user)
    db.commit()
    return {"token": auth.create_token(user.id, user.username), "username": user.username, "verify": mail_sent}


@app.post("/api/verify")
def verify(body: VerifyBody, user: User = Depends(current_user), db: Session = Depends(get_session)):
    if user.email_verified:
        return {"ok": True}
    if body.code.strip() != (user.verify_code or ""):
        raise HTTPException(400, "Der Code ist falsch.")
    user.email_verified = True
    user.verify_code = None
    db.merge(user)
    db.commit()
    return {"ok": True}


@app.post("/api/login")
def login(cred: Credentials, request: Request, db: Session = Depends(get_session)):
    ip = request.client.host if request.client else "?"
    if not config.TESTING and not login_limiter.allow(ip):
        raise HTTPException(429, "Zu viele Anmeldeversuche. Bitte warte kurz.")
    user = db.scalar(select(User).where(User.username.ilike(cred.username)))
    if not user or not auth.verify_password(cred.password, user.password_hash):
        raise HTTPException(401, "Benutzername oder Passwort ist falsch.")
    if user.banned:
        raise HTTPException(403, "Dieser Account ist gesperrt.")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    return {"token": auth.create_token(user.id, user.username), "username": user.username, "verify": not user.email_verified}


# ============================================================================== REST: Charaktere
@app.get("/api/characters")
def list_characters(user: User = Depends(current_user), db: Session = Depends(get_session)):
    chars = db.scalars(select(Character).where(Character.user_id == user.id).order_by(Character.id)).all()
    out = []
    for c in chars:
        eq = {e.slot: {"i": e.item_id} for e in db.scalars(select(Equipment).where(Equipment.character_id == c.id))}
        out.append(char_summary(c, eq))
    return {"username": user.username, "characters": out, "max": config.MAX_CHARACTERS, "verify": not user.email_verified}


def _clean_look(look: dict) -> dict:
    out = {}
    for k, v in (look or {}).items():
        if k in LOOK_KEYS and isinstance(v, (str, int, float)) and len(str(v)) <= LOOK_KEYS[k]:
            out[k] = v
    if out.get("kind") not in (None, "human", "dwarf", "elf"):
        out.pop("kind", None)
    return out


@app.post("/api/characters")
def create_character(data: NewCharacter, user: User = Depends(current_user), db: Session = Depends(get_session)):
    name = data.name.strip()
    if not NAME_RE.match(name):
        raise HTTPException(400, "Name: 3–16 Buchstaben, keine Zahlen oder Leerzeichen.")
    name = name[0].upper() + name[1:].lower()
    if name.lower() in RESERVED:
        raise HTTPException(400, "Dieser Name ist reserviert.")
    if data.cls not in CLASSES:
        raise HTTPException(400, "Diese Klasse ist noch nicht spielbar.")
    if db.scalar(select(func.count()).where(Character.user_id == user.id)) >= config.MAX_CHARACTERS:
        raise HTTPException(400, f"Maximal {config.MAX_CHARACTERS} Charaktere pro Account.")
    if db.scalar(select(Character).where(Character.name.ilike(name))):
        raise HTTPException(400, "Dieser Name ist bereits vergeben.")
    cls = CLASSES[data.cls]
    sx, sz, sr = W.ZONES["gruenmark"]["start"]
    c = Character(user_id=user.id, name=name, class_id=data.cls, level=1, xp=0, copper=0, zone="gruenmark",
                  x=sx, y=0.0, z=sz, rot=sr, look=_clean_look(data.look), misc={"bagslots": []},
                  collections={"mounts": [], "pets": [], "titles": [], "skins": []},
                  discovered={"stones": [], "subzones": [], "zones": []})
    db.add(c)
    db.flush()
    slot = 0
    for iid, n in list(cls["start"]["bags"]) + [("ruhestein", 1)]:
        db.add(InventoryItem(character_id=c.id, item_id=iid, quantity=n, slot=slot, bound=ITEMS[iid].get("bind") == "bop"))
        slot += 1
    for s_name, iid in cls["start"]["equip"].items():
        db.add(Equipment(character_id=c.id, slot=s_name, item_id=iid, extra={"d": 100}))
    db.commit()
    eq = {k: {"i": v} for k, v in cls["start"]["equip"].items()}
    return char_summary(c, eq)


@app.delete("/api/characters/{char_id}")
def delete_character(char_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    c = db.get(Character, char_id)
    if not c or c.user_id != user.id:
        raise HTTPException(404, "Charakter nicht gefunden.")
    if c.id in world.by_char:
        raise HTTPException(400, "Der Charakter ist gerade online.")
    for model in (InventoryItem, Equipment, CharacterQuest):
        db.execute(delete(model).where(model.character_id == c.id))
    db.delete(c)
    db.commit()
    return {"ok": True}


# ============================================================================== REST: Inhalte
_content_cache: bytes | None = None


@app.get("/api/content")
def content():
    """Statische Definitionen, die der Client zum Anzeigen braucht (Klassen, Fähigkeiten, Talente, Regionen ...)."""
    global _content_cache
    if _content_cache is None:
        classes = {}
        for cid, c in CLASSES.items():
            classes[cid] = {
                "id": cid, "name": c["name"], "role": c["role"], "difficulty": c["difficulty"], "desc": c["desc"],
                "color": c["color"], "icon": c["icon"], "resource": c["resource"], "armor": c["armor"], "weapons": c["weapons"],
                "offhand": c["offhand"], "specs": [{"id": s, "name": SPEC_NAMES[s][0], "role": SPEC_NAMES[s][1]} for s in c["specs"]],
                "abilities": [ability_client_info(a, max(1, ABILITIES[a]["level"])) for a in class_abilities(c and cid, True)],
                "talents": client_trees(cid), "start": c["start"], "class_slot_name": c["class_slot_name"],
            }
        data = {
            "world": W.WORLD_NAME, "version": config.VERSION, "classes": classes, "planned": PLANNED_CLASSES,
            "resources": RESOURCES, "rarity": RARITY_NAMES, "rarity_colors": RARITY_COLORS, "slots": SLOT_NAMES,
            "stats": STAT_NAMES, "weapons": WEAPON_NAMES, "armor": ARMOR_NAMES, "schools": SCHOOL_NAMES,
            "factions": FACTIONS, "currencies": CURRENCIES, "standings": STANDINGS, "professions": PROFESSIONS,
            "mounts": MOUNTS, "pets": PETS, "titles": TITLES, "modes": W.MODES, "affixes": W.AFFIXES,
            "zones": {k: {"name": v["name"], "type": v["type"], "levels": v.get("levels"), "theme": v.get("theme"),
                          "region": bool(v.get("region")), "hidden": bool(v.get("hidden"))} for k, v in W.ZONES.items()},
            "start_items": {i: item_client_info(i) for c in CLASSES.values() for i in list(c["start"]["equip"].values())},
        }
        _content_cache = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode()
    return Response(content=_content_cache, media_type="application/json")


@app.get("/api/items")
def items(ids: str = ""):
    out = {}
    for i in ids.split(",")[:200]:
        if i in ITEMS:
            out[i] = item_client_info(i)
    return out


@app.get("/api/zone/{zone_id}")
def zone_data(zone_id: str):
    data = _zone_cache.get(zone_id)
    if data is None:
        if zone_id not in W.ZONES:
            raise HTTPException(404, "Unbekannte Zone.")
        data = json.dumps(static_zone(zone_id).client_data(), separators=(",", ":")).encode()
        _zone_cache[zone_id] = data
    return Response(content=data, media_type="application/json", headers={"Cache-Control": "public, max-age=600"})


# ============================================================================== WebSocket
class GameSession:
    def __init__(self, ws: WebSocket, username: str):
        self.ws = ws
        self.username = username
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=4000)
        self.closed = False

    def send(self, msg: dict):
        if self.closed:
            return
        try:
            self.queue.put_nowait(json.dumps(msg, separators=(",", ":"), ensure_ascii=False, default=list))
        except asyncio.QueueFull:
            self.kick("Verbindung zu langsam.")

    def kick(self, reason: str):
        if self.closed:
            return
        try:
            self.queue.put_nowait(json.dumps({"t": "kick", "text": reason}, ensure_ascii=False))
            self.queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
        self.closed = True

    async def writer(self):
        try:
            while True:
                item = await self.queue.get()
                if item is None:
                    await self.ws.close()
                    return
                await self.ws.send_text(item)
        except Exception:
            self.closed = True


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    token = ws.query_params.get("token", "")
    try:
        char_id = int(ws.query_params.get("char", "0"))
    except ValueError:
        char_id = 0
    payload = auth.decode_token(token)
    if not payload:
        await ws.send_text(json.dumps({"t": "kick", "text": "Bitte melde dich erneut an."}))
        await ws.close()
        return
    old = world.by_char.get(char_id)
    if old and old.user_id == int(payload["sub"]):
        if old.session:
            old.session.kick("Dieser Charakter wurde an anderer Stelle angemeldet.")
        world.remove_player(old)
    loop = asyncio.get_running_loop()

    def _load():
        with SessionLocal() as db:
            rec = db.get(Character, char_id)
            if not rec or rec.user_id != int(payload["sub"]):
                return None
            rec.last_login = datetime.now(timezone.utc)
            db.commit()
            return load_character(rec, db)
    data = await loop.run_in_executor(None, _load)
    if not data:
        await ws.send_text(json.dumps({"t": "kick", "text": "Charakter nicht gefunden."}))
        await ws.close()
        return
    session = GameSession(ws, payload.get("name", "?"))
    player = world.add_player(data, session)
    writer = asyncio.create_task(session.writer())
    world.send_welcome(player)
    log.info("%s (%s) betritt die Welt", player.name, session.username)
    try:
        while True:
            raw = await ws.receive_text()
            if len(raw) > 6000:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(msg, dict) and not session.closed:
                world.handle(player, msg)
            if session.closed:
                break
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        session.closed = True
        if world.by_char.get(player.char_id) is player:
            world.remove_player(player)
        writer.cancel()
        log.info("%s verlässt die Welt", player.name)


# ============================================================================== Web-Client & Download
@app.get("/", response_class=HTMLResponse)
def index():
    online = len(world.players)
    web = (WEB_DIR / "index.html").exists()
    return HTMLResponse(f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eldornia</title><style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 50% 30%,#3a2a1a,#0d0a08);color:#f0e0c0;
font-family:Georgia,serif;text-align:center}}h1{{font-size:64px;letter-spacing:6px;margin:0;color:#ffd27a;text-shadow:0 4px 20px #000}}
p{{opacity:.85}}a{{display:inline-block;margin:10px;padding:14px 28px;border:2px solid #c9a040;border-radius:6px;color:#ffe9b0;
text-decoration:none;background:linear-gradient(#5a3a1a,#2a1a0a)}}a:hover{{background:#7a4a1a}}</style></head><body><div>
<h1>ELDORNIA</h1><p>Ein Fantasy-MMORPG im Stil von World of Warcraft und RuneScape</p><p>{online} Abenteurer online</p>
<a href="/download">Für Windows herunterladen</a>{'<a href="/play/">Im Browser spielen</a>' if web else ''}
<p style="font-size:13px;opacity:.6">Server-Version {config.VERSION}</p></div></body></html>""")


@app.get("/download")
def download():
    return RedirectResponse(config.DOWNLOAD_URL)


if WEB_DIR.exists():
    app.mount("/play", StaticFiles(directory=WEB_DIR, html=True), name="play")
