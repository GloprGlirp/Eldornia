"""Zentrale Konfiguration des Eldornia-Servers (über Umgebungsvariablen steuerbar)."""
import os


def _normalize_db_url(url: str) -> str:
    # Render & Co. liefern "postgres://..." – SQLAlchemy braucht einen Treiber-Namen.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalize_db_url(os.environ.get("DATABASE_URL", "sqlite:///./eldornia.db"))
# Eigenes Postgres-Schema, damit sich Eldornia eine Datenbank mit anderen Projekten teilen kann
DB_SCHEMA = os.environ.get("DB_SCHEMA", "eldornia" if DATABASE_URL.startswith("postgresql") else "")
SECRET_KEY = os.environ.get("SECRET_KEY", "eldornia-dev-secret-bitte-aendern")
TOKEN_HOURS = int(os.environ.get("TOKEN_HOURS", "24"))

# Accounts mit Admin-Rechten (Chatbefehle wie .stufe, .gold, .tp) – kommagetrennt
ADMIN_USERS = {u.strip().lower() for u in os.environ.get("ADMIN_USERS", "").split(",") if u.strip()}
# Im Entwicklungsmodus darf jeder Admin-Befehle nutzen
DEBUG_COMMANDS = os.environ.get("ELDORNIA_DEBUG", "0") == "1"
TESTING = os.environ.get("ELDORNIA_TESTING", "0") == "1"

TICK_RATE = 10            # Simulationsschritte pro Sekunde
SAVE_INTERVAL = 60.0      # Sekunden zwischen automatischen Speicherungen
MAX_CHARACTERS = 10
VERSION = "0.3.0"

# E-Mail-Bestätigung (optional). Ohne SMTP-Server werden Accounts automatisch bestätigt.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "Eldornia <noreply@eldornia.example>")

DOWNLOAD_URL = os.environ.get("DOWNLOAD_URL", "https://github.com/GloprGlirp/Eldornia/releases/latest")
