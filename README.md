# Eldornia

Ein Fantasy-MMORPG im Stil von World of Warcraft und RuneScape – mit stilisierter, handgemalt wirkender 3D-Grafik,
WoW-artigem Kampfsystem, Quests, Dungeons, Berufen, Markt, Gilden und Gruppen.

## Spielen

| Plattform | Download |
|-----------|----------|
| Windows   | **EldorniaSetup.exe** unter [Releases](https://github.com/GloprGlirp/Eldornia/releases/latest) – Installer mit Startmenü- und Desktopverknüpfung |
| macOS     | `Eldornia-macos.zip` (Rechtsklick → Öffnen beim ersten Start, da nicht signiert) |
| Linux     | `Eldornia-linux.tar.gz` |
| Browser   | `https://<server>/play` |

Beim ersten Start fragt der Client nach Benutzername und Passwort (Registrierung mit E-Mail-Bestätigung direkt im Spiel).
Die Serveradresse lässt sich im Anmeldebildschirm ändern.

### Steuerung (frei belegbar unter Esc → Einstellungen → Tastenbelegung)

| Taste | Aktion |
|-------|--------|
| W A S D | Bewegen (A/D drehen, mit rechter Maustaste seitwärts) |
| Q / R | Seitwärts gehen |
| Maus | Kamera drehen (rechte Taste: Blickrichtung), Mausrad: Zoom |
| Linksklick / Rechtsklick | Ziel wählen / Angreifen, Sprechen, Plündern |
| 1–6 (bis 0, ß, ´) | Fähigkeiten, Leiste 2: Z X C V T |
| Leertaste | Springen / Ausweichen |
| E | Interagieren |
| Tab | Nächster Gegner (optionale Zielhilfe in den Einstellungen) |
| I | Inventar · **M** Weltkarte · **J** Questlog · **G** Gilde |
| K Charakter · P Zauberbuch · N Talente · U Berufe · Y Erfolge · H Sammlung · O Gruppenfinder | |
| Enter | Chat (/s /y /p /g /1 /2 /w Name …) |

## Welt Eldornia

| Region | Stufe | |
|--------|-------|---|
| Grünmark | 1–10 | Startgebiet: Eichenau, Burg Eldenstein (Simon der zweiäugige Herrscher), Vergessene Krypta |
| Frostklamm | 10–25 | Zwergenfestungen, Eisriesen, verlassene Minen, Schwarze Schmiede |
| Mondhain | 20–35 | Feenwälder, Druidenruinen, Naturbosse |
| Aschenlande | 30–50 | Vulkane, Dämonen, Varkor der Aschendrache, Kathedrale der Verdammten |
| Himmelsbruch | Endgame | Schwebende Inseln, Thron des Weltenbrechers (Schlachtzug) |

8 Klassen mit je 3 Spezialisierungen und Talentbäumen: Ritter, Magier, Räuber, Samurai, Bogenschütze, Barbar, Druide,
Totenbeschwörer.

## Technik

- **Client:** Godot 4 (GDScript), prozedurale stilisierte Modelle, Shader und Vegetation – `client/`
- **Server:** Python 3.12, FastAPI (REST + WebSocket), autoritative Weltsimulation mit 10 Ticks/s – `server/`
- **Datenbank:** PostgreSQL (Produktion) bzw. SQLite (Entwicklung) über SQLAlchemy
- **Installer:** Inno Setup (`installer/eldornia.iss`), gebaut von GitHub Actions (`.github/workflows/build.yml`)

### Server lokal starten

```bash
pip install -r requirements.txt
cd server
uvicorn app.main:app --reload --ws-ping-interval 30 --ws-ping-timeout 180
```

Umgebungsvariablen: `DATABASE_URL`, `SECRET_KEY`, `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM`
(E-Mail-Bestätigung; ohne SMTP werden Konten direkt freigeschaltet), `ADMIN_USERS` (GM-Befehle wie `.stufe 20`).

Tests: `pip install -r requirements-dev.txt && cd server && pytest`

### Client

Godot 4.7 öffnen → `client/project.godot`. Start mit eigenem Server: `godot --path client -- --server=http://127.0.0.1:8000`.

### Hosting (Render)

`render.yaml` richtet Webdienst + PostgreSQL ein. Beim Build wird die Web-Version des Clients aus dem neuesten Release
geladen und unter `/play` bereitgestellt; `/download` leitet zum Windows-Installer.

## Lizenzen

Symbole: [game-icons.net](https://game-icons.net) (Lorc, Delapouite u. a.), CC BY 3.0.
Schriften: Cinzel, Cinzel Decorative, Alegreya Sans (SIL Open Font License).
