"""Datenbanktabellen.

Für den ersten spielbaren Kern werden Inventar, Ausrüstung und Questfortschritt als
JSON-Spalten am Charakter gespeichert. Das hält Speichern/Laden atomar (kein Item-Dupe
durch halb geschriebene Tabellen) und kann später in eigene Tabellen aufgeteilt werden.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    class_id: Mapped[str] = mapped_column(String(24))
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    copper: Mapped[int] = mapped_column(Integer, default=0)

    zone: Mapped[str] = mapped_column(String(32), default="gruenmark")
    x: Mapped[float] = mapped_column(Float, default=0.0)
    y: Mapped[float] = mapped_column(Float, default=0.0)
    z: Mapped[float] = mapped_column(Float, default=0.0)
    rot: Mapped[float] = mapped_column(Float, default=0.0)
    hp: Mapped[int] = mapped_column(Integer, default=-1)   # -1 = voll
    res: Mapped[int] = mapped_column(Integer, default=-1)

    look: Mapped[dict] = mapped_column(JSON, default=dict)
    inventory: Mapped[list] = mapped_column(JSON, default=list)
    equipment: Mapped[dict] = mapped_column(JSON, default=dict)
    quests: Mapped[dict] = mapped_column(JSON, default=dict)

    played_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
