"""Datenbanktabellen (GDD Abschnitt 13).

Statische Inhalte (Klassen, Gegenstände, Regionen, Quests, Dungeons, Bossbeute) werden beim Serverstart
aus den Inhaltsdateien in ihre Tabellen geschrieben – so bleibt das Datenmodell erweiterbar und die
Datenbank vollständig auswertbar. Spielerdaten (Inventar, Ausrüstung, Questfortschritt) liegen in eigenen
Tabellen und werden pro Charakter in einer einzigen Transaktion gespeichert (kein Item-Dupe durch halb
geschriebene Daten).
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _now():
    return datetime.now(timezone.utc)


# ============================================================================== Accounts & Charaktere
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verify_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    class_id: Mapped[str] = mapped_column(String(24))
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    copper: Mapped[int] = mapped_column(BigInteger, default=0)

    zone: Mapped[str] = mapped_column(String(32), default="gruenmark")
    x: Mapped[float] = mapped_column(Float, default=0.0)
    y: Mapped[float] = mapped_column(Float, default=0.0)
    z: Mapped[float] = mapped_column(Float, default=0.0)
    rot: Mapped[float] = mapped_column(Float, default=0.0)

    look: Mapped[dict] = mapped_column(JSON, default=dict)
    talents: Mapped[dict] = mapped_column(JSON, default=dict)
    action_bars: Mapped[list] = mapped_column(JSON, default=list)
    professions: Mapped[dict] = mapped_column(JSON, default=dict)
    reputation: Mapped[dict] = mapped_column(JSON, default=dict)
    currencies: Mapped[dict] = mapped_column(JSON, default=dict)
    achievements: Mapped[dict] = mapped_column(JSON, default=dict)
    collections: Mapped[dict] = mapped_column(JSON, default=dict)
    discovered: Mapped[dict] = mapped_column(JSON, default=dict)
    cooldowns: Mapped[dict] = mapped_column(JSON, default=dict)
    misc: Mapped[dict] = mapped_column(JSON, default=dict)

    arena_rating: Mapped[int] = mapped_column(Integer, default=1500)
    played_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ============================================================================== Statische Definitionen
class ClassDef(Base):
    __tablename__ = "classes"
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    base_stats: Mapped[dict] = mapped_column(JSON, default=dict)
    description: Mapped[str] = mapped_column(Text, default="")


class ItemDef(Base):
    __tablename__ = "items"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    item_type: Mapped[str] = mapped_column(String(24))
    rarity: Mapped[int] = mapped_column(Integer)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    bind_type: Mapped[str | None] = mapped_column(String(8), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)


class RegionDef(Base):
    __tablename__ = "regions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    level_min: Mapped[int] = mapped_column(Integer)
    level_max: Mapped[int] = mapped_column(Integer)


class QuestDef(Base):
    __tablename__ = "quests"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    requirements: Mapped[dict] = mapped_column(JSON, default=dict)
    rewards: Mapped[dict] = mapped_column(JSON, default=dict)


class DungeonDef(Base):
    __tablename__ = "dungeons"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    recommended_level: Mapped[int] = mapped_column(Integer)
    max_players: Mapped[int] = mapped_column(Integer, default=5)


class BossDrop(Base):
    __tablename__ = "boss_drops"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    boss_id: Mapped[str] = mapped_column(String(64), index=True)
    item_id: Mapped[str] = mapped_column(String(64))
    drop_chance: Mapped[float] = mapped_column(Float)


# ============================================================================== Spielerbesitz
class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    slot: Mapped[int] = mapped_column(Integer)
    bound: Mapped[bool] = mapped_column(Boolean, default=False)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)      # Haltbarkeit, Verzauberung ...


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (UniqueConstraint("character_id", "slot"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    slot: Mapped[str] = mapped_column(String(16))
    item_id: Mapped[str] = mapped_column(String(64))
    extra: Mapped[dict] = mapped_column(JSON, default=dict)


class CharacterQuest(Base):
    __tablename__ = "character_quests"
    __table_args__ = (UniqueConstraint("character_id", "quest_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    quest_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(12))              # active | done
    progress: Mapped[list] = mapped_column(JSON, default=list)
    completed_at: Mapped[float | None] = mapped_column(Float, nullable=True)


# ============================================================================== Gilden
class Guild(Base):
    __tablename__ = "guilds"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    tag: Mapped[str] = mapped_column(String(6), default="")
    leader_character_id: Mapped[int] = mapped_column(Integer)
    motd: Mapped[str] = mapped_column(String(200), default="")
    copper: Mapped[int] = mapped_column(BigInteger, default=0)
    emblem: Mapped[dict] = mapped_column(JSON, default=dict)
    weekly: Mapped[dict] = mapped_column(JSON, default=dict)      # Gildenquests & Wochenziele
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class GuildMember(Base):
    __tablename__ = "guild_members"
    __table_args__ = (UniqueConstraint("character_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    rank: Mapped[str] = mapped_column(String(12), default="mitglied")    # leiter | offizier | mitglied
    note: Mapped[str] = mapped_column(String(60), default="")
    contribution: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class GuildBankItem(Base):
    __tablename__ = "guild_bank"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), index=True)
    slot: Mapped[int] = mapped_column(Integer)
    item_id: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)


class GuildLog(Base):
    __tablename__ = "guild_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ============================================================================== Markt & Handel
class MarketListing(Base):
    __tablename__ = "market_listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    seller_name: Mapped[str] = mapped_column(String(24))
    item_id: Mapped[str] = mapped_column(String(64), index=True)
    item_name: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(24), index=True)
    rarity: Mapped[int] = mapped_column(Integer, index=True)
    level: Mapped[int] = mapped_column(Integer, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[int] = mapped_column(BigInteger)                 # Sofortkaufpreis (gesamt)
    bid: Mapped[int] = mapped_column(BigInteger, default=0)        # aktuelles Gebot (Auktion)
    start_bid: Mapped[int] = mapped_column(BigInteger, default=0)
    bidder_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    deposit: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(12), default="active", index=True)   # active | sold | cancelled | expired
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[float] = mapped_column(Float)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    seller_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    kind: Mapped[str] = mapped_column(String(12), default="market")     # market | trade | mail | guildbank
    item_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[int] = mapped_column(BigInteger, default=0)
    fee: Mapped[int] = mapped_column(BigInteger, default=0)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)       # ungewöhnliche Muster (GDD 9)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Mail(Base):
    __tablename__ = "mail"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    to_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    from_name: Mapped[str] = mapped_column(String(32))
    subject: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(Text, default="")
    items: Mapped[list] = mapped_column(JSON, default=list)
    copper: Mapped[int] = mapped_column(BigInteger, default=0)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    taken: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ============================================================================== Soziales
class Friend(Base):
    __tablename__ = "friends"
    __table_args__ = (UniqueConstraint("character_id", "friend_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    ignore: Mapped[bool] = mapped_column(Boolean, default=False)


class ArenaMatch(Base):
    __tablename__ = "arena_matches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bracket: Mapped[str] = mapped_column(String(8))
    winners: Mapped[list] = mapped_column(JSON, default=list)
    losers: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
