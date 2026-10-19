extends Node
## Globaler Spielzustand: Account, Charaktere und alle Daten des eigenen Charakters in der Welt.
## Leitet Servernachrichten weiter (Signal "msg") und hält die zuletzt empfangenen Zustände.

signal msg(t: String, m: Dictionary)
signal state_changed(what: String)
signal chat_line(ch: String, from: String, text: String, extra: Dictionary)
signal system_text(text: String, kind: String)

var username := ""
var characters: Array = []
var max_characters := 10
var char_id := 0
var in_world := false

# Eigener Charakter
var me_id := 0
var me_name := ""
var me_cls := ""
var level := 1
var xp := 0
var xp_next := 400
var copper := 0
var stats: Dictionary = {}
var power_type := "mana"
var currencies: Dictionary = {}
var title := ""
var spec := ""
var gm := false

var bags: Array = []
var equipment: Dictionary = {}
var capacity := 24
var bagslots: Array = []
var repair_cost := 0

var abilities: Dictionary = {}       # id -> info
var ability_order: Array = []
var future_abilities: Array = []
var bars: Array = []                 # 36 Plätze: {"ab": id} | {"item": id} | {"mount": id} | {"emote": e} | null
var cooldowns: Dictionary = {}       # id -> Ende (Sekunden, Time.get_ticks_msec()/1000)
var cd_total: Dictionary = {}
var gcd_end := 0.0
var gcd_total := 1.5
var combo := 0
var combo_target := 0
var reactive_until: Dictionary = {}

var quests: Array = []
var quests_done_count := 0
var talents: Dictionary = {}
var professions: Dictionary = {}
var collections: Dictionary = {}
var reputation: Array = []
var party: Dictionary = {}
var guild = null
var friends: Array = []
var ignore: Array = []
var mail_unread := 0
var achievements: Dictionary = {}
var zone_id := ""
var zone_name := ""
var zone_inst := false
var zone_mode := ""
var subzone := ""
var weekly = null
var affixes: Array = []
var queue_state = null


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


func reset_world() -> void:
	in_world = false
	me_id = 0
	bags = []
	equipment = {}
	abilities = {}
	bars = []
	cooldowns = {}
	quests = []
	party = {}
	guild = null


func _ready() -> void:
	Net.message.connect(_on_message)


func _on_message(m: Dictionary) -> void:
	var t: String = str(m.get("t", ""))
	match t:
		"welcome":
			in_world = true
			me_id = int(m["id"])
			me_name = str(m["name"])
			me_cls = str(m["cls"])
			level = int(m["lvl"])
			xp = int(m["xp"])
			xp_next = int(m["next"])
			power_type = str(m.get("pt", "mana"))
			zone_id = str(m["zone"])
			zone_name = str(m["zone_name"])
			zone_inst = bool(m.get("inst", false))
			gm = bool(m.get("gm", false))
			weekly = m.get("weekly")
			affixes = m.get("affixes", [])
		"stats":
			stats = m.get("st", {})
			level = int(m.get("lvl", level))
			xp = int(m.get("xp", xp))
			xp_next = int(m.get("next", xp_next))
			copper = int(m.get("copper", copper))
			currencies = m.get("cur", currencies)
			power_type = str(m.get("pt", power_type))
			title = str(m.get("title", ""))
			spec = str(m.get("spec", "")) if m.get("spec") != null else ""
			state_changed.emit("stats")
		"xp":
			xp = int(m.get("xp", xp))
			xp_next = int(m.get("next", xp_next))
			state_changed.emit("xp")
		"xpbar":
			xp = int(m.get("xp", xp))
			xp_next = int(m.get("next", xp_next))
			level = int(m.get("lvl", level))
			state_changed.emit("xp")
		"levelup":
			level = int(m.get("lvl", level))
			state_changed.emit("level")
		"inv":
			bags = m.get("bags", [])
			equipment = m.get("eq", {})
			copper = int(m.get("copper", copper))
			capacity = int(m.get("cap", 24))
			bagslots = m.get("bagslots", [])
			currencies = m.get("cur", currencies)
			repair_cost = int(m.get("repair", 0))
			Content.add_items(m.get("items", {}))
			state_changed.emit("inventory")
		"abilities":
			abilities.clear()
			ability_order.clear()
			for a in m.get("list", []):
				abilities[a["id"]] = a
				ability_order.append(a["id"])
			future_abilities = m.get("future", [])
			var cds: Dictionary = m.get("cds", {})
			for k in cds:
				cooldowns[k] = now() + float(cds[k])
				cd_total[k] = maxf(float(cds[k]), float(abilities.get(k, {}).get("cd", cds[k])))
			var b: Array = m.get("bars", [])
			if not b.is_empty() or bars.is_empty():
				bars = b
			while bars.size() < 36:
				bars.append(null)
			state_changed.emit("abilities")
		"cd":
			var ab := str(m.get("ab", ""))
			var cd := float(m.get("cd", 0))
			if cd > 0:
				cooldowns[ab] = now() + cd
				cd_total[ab] = maxf(cd, float(abilities.get(ab, {}).get("cd", cd)))
			var g := float(m.get("gcd", 0))
			if g > 0:
				gcd_end = now() + g
				gcd_total = g
			state_changed.emit("cooldowns")
		"combo":
			combo = int(m.get("n", 0))
			combo_target = int(m.get("tg", 0)) if m.get("tg") != null else 0
			state_changed.emit("combo")
		"reactive":
			reactive_until[str(m.get("k"))] = now() + 5.0
			state_changed.emit("reactive")
		"quests":
			quests = m.get("quests", [])
			quests_done_count = int(m.get("done", 0))
			state_changed.emit("quests")
		"talents":
			talents = m
			state_changed.emit("talents")
		"professions":
			professions = m.get("list", {})
			Content.add_items(m.get("items", {}))
			state_changed.emit("professions")
		"collections":
			collections = m
			state_changed.emit("collections")
		"reputation":
			reputation = m.get("list", [])
			currencies = m.get("cur", currencies)
			state_changed.emit("reputation")
		"party":
			party = m
			state_changed.emit("party")
		"guild":
			guild = m.get("guild")
			if guild is Dictionary:
				Content.add_items(guild.get("items", {}))
			state_changed.emit("guild")
		"friends":
			friends = m.get("list", [])
			ignore = m.get("ignore", [])
			state_changed.emit("friends")
		"mail_notify":
			mail_unread = int(m.get("unread", 0))
			state_changed.emit("mail")
		"achievements":
			achievements = m
			state_changed.emit("achievements")
		"zone":
			zone_id = str(m["zone"])
			zone_name = str(m["name"])
			zone_inst = bool(m.get("inst", false))
			zone_mode = str(m.get("mode_name", "")) if m.get("mode_name") != null else ""
			affixes = m.get("affixes", [])
			subzone = ""
		"subzone":
			subzone = str(m.get("name", ""))
			state_changed.emit("subzone")
		"queue":
			queue_state = m if m.get("state") != "none" else null
			state_changed.emit("queue")
		"chat":
			chat_line.emit(str(m.get("ch", "say")), str(m.get("from", "")), str(m.get("text", "")), m)
		"sys":
			system_text.emit(str(m.get("text", "")), "sys")
		"err":
			system_text.emit(str(m.get("text", "")), "err")
		"loot_msg":
			Content.add_items(m.get("items", {}))
			var it := Content.item(str(m.get("i")))
			var n := int(m.get("n", 1))
			chat_line.emit("loot", "", "Ihr erhaltet Beute: [%s]%s" % [str(m.get("name", "")), (" ×%d" % n) if n > 1 else ""],
				{"q": int(m.get("q", 1)), "i": m.get("i")})
		"vendor", "loot", "market", "market_mine", "mail", "trade", "inspect", "prof_trainer":
			for key in ["items", "defs"]:
				if m.has(key):
					Content.add_items(m[key])
		"quest_detail":
			var q: Dictionary = m.get("q", {})
			Content.add_items(q.get("items", {}))
		"rep":
			system_text.emit("Ruf bei %s %s um %d (%s)." % [str(m.get("name")), "erhöht" if int(m.get("a", 0)) >= 0 else "verringert",
				absi(int(m.get("a", 0))), str(m.get("st", ""))], "rep")
		"skillup":
			system_text.emit("Eure Fertigkeit in %s hat sich auf %d erhöht." % [str(m.get("name")), int(m.get("skill"))], "skill")
			if professions.has(str(m.get("prof"))):
				professions[str(m.get("prof"))]["skill"] = int(m.get("skill"))
			state_changed.emit("professions")
	msg.emit(t, m)


# ============================================================================== Hilfen
func send(m: Dictionary) -> void:
	Net.send(m)


func cd_left(id: String) -> float:
	return maxf(0.0, float(cooldowns.get(id, 0.0)) - now())


func gcd_left() -> float:
	return maxf(0.0, gcd_end - now())


func count_item(id: String) -> int:
	var n := 0
	for s in bags:
		if s is Dictionary and str(s.get("i")) == id:
			n += int(s.get("n", 1))
	return n


func bag_slot_of(id: String) -> int:
	for i in bags.size():
		var s = bags[i]
		if s is Dictionary and str(s.get("i")) == id:
			return i
	return -1


func save_bars() -> void:
	send({"t": "bars", "bars": bars})
