"""Eldornia – Server (FastAPI).

REST:  Registrierung, Login, Charakterverwaltung, statische Zonendaten
WS:    /ws – Echtzeitverbindung zur Spielwelt
Statisch: der Browser-Client aus /client
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import auth, config
from .db import SessionLocal, get_session, init_db
from .game.content import world as W
from .game.content.abilities import ABILITIES
from .game.content.classes import CLASSES, PLANNED_CLASSES
from .game.content.items import ITEMS, RARITY_NAMES, SLOT_NAMES, SUB_NAMES, item_client_info
from .game.entities import Player
from .game.terrain import zone_static_data
from .game.world import World
from .models import Character, User

log = logging.getLogger("eldornia")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

CLIENT_DIR = Path(__file__).resolve().parents[2] / "client"
NAME_RE = re.compile(r"^[A-Za-zÄÖÜäöüß]{3,16}$")
USER_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
RESERVED = {n["name"].split()[-1].lower() for n in __import__("app.game.content.npcs", fromlist=["NPCS"]).NPCS.values()}

world = World()
login_limiter = auth.RateLimiter(10, 60)
register_limiter = auth.RateLimiter(5, 300)
_zone_cache: dict[str, bytes] = {}


# ============================================================================== Speichern
def _write_character(char_id: int, data: dict):
    with SessionLocal() as s:
        c = s.get(Character, char_id)
        if not c:
            return
        for k, v in data.items():
            setattr(c, k, v)
        s.commit()


def save_player(p: Player):
    data = world.save_data(p)
    loop = asyncio.get_running_loop() if _has_loop() else None
    if loop:
        loop.run_in_executor(None, _write_character, p.char_id, data)
    else:
        _write_character(p.char_id, data)


def _has_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


world.save_callback = save_player


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    for zid in W.ZONES:
        _zone_cache[zid] = json.dumps(zone_static_data(zid), separators=(",", ":")).encode()
    task = asyncio.create_task(world.run())
    log.info("Eldornia-Server gestartet (Version %s)", config.VERSION)
    yield
    world.running = False
    for p in list(world.players.values()):
        _write_character(p.char_id, world.save_data(p))
    task.cancel()


app = FastAPI(title="Eldornia", version=config.VERSION, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============================================================================== Hilfen
def current_user(authorization: str = Header(default=""), db: Session = Depends(get_session)) -> User:
    token = authorization.removeprefix("Bearer ").strip()
    payload = auth.decode_token(token) if token else None
    if not payload:
        raise HTTPException(401, "Nicht angemeldet.")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "Account nicht gefunden.")
    return user


def char_summary(c: Character) -> dict:
    return {"id": c.id, "name": c.name, "cls": c.class_id, "cls_name": CLASSES[c.class_id]["name"], "level": c.level,
            "zone": W.ZONES.get(c.zone, W.ZONES["gruenmark"])["name"], "look": c.look or {},
            "gear": c.equipment or {}, "online": c.id in world.by_char}


class Credentials(BaseModel):
    username: str
    password: str
    email: str | None = None


class NewCharacter(BaseModel):
    name: str
    cls: str
    look: dict = {}


# ============================================================================== REST
@app.get("/api/status")
def status():
    return {"name": W.WORLD_NAME, "version": config.VERSION, "online": len(world.players)}


@app.post("/api/register")
def register(cred: Credentials, request: Request, db: Session = Depends(get_session)):
    ip = request.client.host if request.client else "?"
    if not register_limiter.allow(ip):
        raise HTTPException(429, "Zu viele Versuche. Bitte warte ein paar Minuten.")
    if not USER_RE.match(cred.username):
        raise HTTPException(400, "Benutzername: 3–20 Zeichen, nur Buchstaben, Zahlen und _.")
    if len(cred.password) < 6 or len(cred.password) > 128:
        raise HTTPException(400, "Das Passwort muss mindestens 6 Zeichen lang sein.")
    exists = db.scalar(select(User).where(User.username.ilike(cred.username)))
    if exists:
        raise HTTPException(400, "Dieser Benutzername ist bereits vergeben.")
    user = User(username=cred.username, email=(cred.email or None), password_hash=auth.hash_password(cred.password))
    db.add(user)
    db.commit()
    return {"token": auth.create_token(user.id, user.username), "username": user.username}


@app.post("/api/login")
def login(cred: Credentials, request: Request, db: Session = Depends(get_session)):
    ip = request.client.host if request.client else "?"
    if not login_limiter.allow(ip):
        raise HTTPException(429, "Zu viele Anmeldeversuche. Bitte warte kurz.")
    user = db.scalar(select(User).where(User.username.ilike(cred.username)))
    if not user or not auth.verify_password(cred.password, user.password_hash):
        raise HTTPException(401, "Benutzername oder Passwort ist falsch.")
    return {"token": auth.create_token(user.id, user.username), "username": user.username}


@app.get("/api/classes")
def classes():
    out = []
    for cid, c in CLASSES.items():
        out.append({"id": cid, "name": c["name"], "role": c["role"], "desc": c["desc"], "color": c["color"],
                    "resource": c["resource"], "playable": True,
                    "abilities": [{"name": ABILITIES[a]["name"], "icon": ABILITIES[a]["icon"],
                                   "color": ABILITIES[a]["color"], "level": ABILITIES[a]["level"]}
                                  for a in c["abilities"]]})
    for pc in PLANNED_CLASSES:
        out.append({**pc, "playable": False, "desc": "Kommt in einem späteren Update.", "abilities": []})
    return out


@app.get("/api/characters")
def list_characters(user: User = Depends(current_user), db: Session = Depends(get_session)):
    chars = db.scalars(select(Character).where(Character.user_id == user.id).order_by(Character.id)).all()
    return {"username": user.username, "characters": [char_summary(c) for c in chars], "max": config.MAX_CHARACTERS}


def _clean_look(look: dict) -> dict:
    allowed = {"skin", "hair", "hair_style", "body", "beard", "eyes"}
    out = {}
    for k, v in (look or {}).items():
        if k in allowed and isinstance(v, (str, int)) and len(str(v)) <= 16:
            out[k] = v
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
    count = len(db.scalars(select(Character).where(Character.user_id == user.id)).all())
    if count >= config.MAX_CHARACTERS:
        raise HTTPException(400, f"Maximal {config.MAX_CHARACTERS} Charaktere pro Account.")
    if db.scalar(select(Character).where(Character.name.ilike(name))):
        raise HTTPException(400, "Dieser Name ist bereits vergeben.")
    cls = CLASSES[data.cls]
    sx, sz, sr = W.ZONES["gruenmark"]["start"]
    bags = [[i, n] for i, n in cls["start_items"]["bags"]]
    c = Character(user_id=user.id, name=name, class_id=data.cls, level=1, xp=0, copper=0, zone="gruenmark",
                  x=sx, y=0.0, z=sz, rot=sr, hp=-1, res=-1, look=_clean_look(data.look),
                  inventory=bags, equipment=dict(cls["start_items"]["equip"]), quests={"active": {}, "done": []})
    db.add(c)
    db.commit()
    return char_summary(c)


@app.delete("/api/characters/{char_id}")
def delete_character(char_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    c = db.get(Character, char_id)
    if not c or c.user_id != user.id:
        raise HTTPException(404, "Charakter nicht gefunden.")
    if c.id in world.by_char:
        raise HTTPException(400, "Der Charakter ist gerade online.")
    db.delete(c)
    db.commit()
    return {"ok": True}


@app.get("/api/content")
def content():
    return {
        "items": {i: item_client_info(i) for i in ITEMS},
        "rarity": RARITY_NAMES, "slots": SLOT_NAMES, "subs": SUB_NAMES,
        "zones": {k: {"name": v["name"], "type": v["type"]} for k, v in W.ZONES.items()},
    }


@app.get("/api/zone/{zone_id}")
def zone_data(zone_id: str):
    data = _zone_cache.get(zone_id)
    if data is None:
        if zone_id not in W.ZONES:
            raise HTTPException(404, "Unbekannte Zone.")
        data = json.dumps(zone_static_data(zone_id), separators=(",", ":")).encode()
        _zone_cache[zone_id] = data
    return Response(content=data, media_type="application/json", headers={"Cache-Control": "public, max-age=300"})


# ============================================================================== WebSocket
class GameSession:
    def __init__(self, ws: WebSocket, username: str):
        self.ws = ws
        self.username = username
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=2000)
        self.closed = False
        self.kick_reason: str | None = None

    def send(self, msg: dict):
        if self.closed:
            return
        try:
            self.queue.put_nowait(json.dumps(msg, separators=(",", ":"), ensure_ascii=False))
        except asyncio.QueueFull:
            self.kick("Verbindung zu langsam.")

    def kick(self, reason: str):
        if self.closed:
            return
        self.kick_reason = reason
        try:
            self.queue.put_nowait(json.dumps({"t": "kick", "text": reason}, ensure_ascii=False))
            self.queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
        self.closed = True

    async def writer(self):
        while True:
            item = await self.queue.get()
            if item is None:
                await self.ws.close()
                return
            await self.ws.send_text(item)


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
        # Doppelte Anmeldung: alte Verbindung trennen und deren Stand zuerst sichern
        world.remove_player(old)
        if old.session:
            old.session.kick("Dieser Charakter wurde an anderer Stelle angemeldet.")
        await asyncio.get_running_loop().run_in_executor(None, _write_character, old.char_id, world.save_data(old))
    with SessionLocal() as db:
        rec = db.get(Character, char_id)
        if not rec or rec.user_id != int(payload["sub"]):
            await ws.send_text(json.dumps({"t": "kick", "text": "Charakter nicht gefunden."}))
            await ws.close()
            return
        rec.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
        db.expunge(rec)
    session = GameSession(ws, payload.get("name", "?"))
    player = Player(rec, session)
    world.add_player(player)
    writer = asyncio.create_task(session.writer())
    log.info("%s (%s) betritt die Welt", player.name, session.username)
    try:
        while True:
            raw = await ws.receive_text()
            if len(raw) > 4000:
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
            await asyncio.get_running_loop().run_in_executor(None, _write_character, player.char_id,
                                                             world.save_data(player))
        writer.cancel()
        log.info("%s verlässt die Welt", player.name)


# ============================================================================== Client
if CLIENT_DIR.exists():
    @app.get("/")
    def index():
        return FileResponse(CLIENT_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    app.mount("/", StaticFiles(directory=CLIENT_DIR), name="client")
