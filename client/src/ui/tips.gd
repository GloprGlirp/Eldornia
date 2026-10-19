class_name Tips
extends RefCounted
## Tooltips für Gegenstände, Fähigkeiten, Talente und Auren (WoW-artig).

const STAT_ORDER := ["str", "agi", "sta", "int", "spi", "ap", "sp", "heal", "crit", "haste", "block", "dodge", "parry", "mp5",
	"fire_res", "frost_res", "nature_res", "shadow_res", "arcane_res"]
const PCT := ["crit", "haste", "block", "dodge", "parry"]
const SLOT_TXT := {"head": "Kopf", "neck": "Hals", "shoulders": "Schultern", "back": "Rücken", "chest": "Brust", "hands": "Hände",
	"legs": "Beine", "feet": "Füße", "ring": "Finger", "main_hand": "Waffenhand", "off_hand": "Schildhand", "class": "Klassenslot"}
const SUB_TXT := {"stoff": "Stoff", "leder": "Leder", "kette": "Kette", "platte": "Platte", "schild": "Schild", "umhang": "Umhang",
	"buch": "Foliant", "kugel": "Kugel", "schaedel": "Schädel", "schwert": "Schwert", "zweihandschwert": "Zweihandschwert",
	"axt": "Axt", "zweihandaxt": "Zweihandaxt", "streitkolben": "Streitkolben", "kriegshammer": "Kriegshammer", "dolch": "Dolch",
	"katana": "Katana", "bogen": "Bogen", "stab": "Stab", "zauberstab": "Zauberstab", "schmuck": ""}


static func panel(bb: String, width := 300) -> Control:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UiSkin.tooltip_box())
	var r := UiSkin.rich(bb)
	r.custom_minimum_size.x = width
	r.add_theme_font_size_override("normal_font_size", 16)
	r.add_theme_font_size_override("bold_font_size", 17)
	p.add_child(r)
	return p


static func stat_name(k: String) -> String:
	var names: Dictionary = Content.defs.get("stats", {})
	return str(names.get(k, k))


static func item_bb(id: String, inst = null, compare := true) -> String:
	var it := Content.item(id)
	if it.is_empty():
		return "[color=#9d9d9d]%s[/color]" % id
	var q := int(it.get("q", 1))
	var col: String = Content.RARITY_COLORS[clampi(q, 0, 6)]
	var s := "[font_size=19][color=%s]%s[/color][/font_size]\n" % [col, it.get("name", id)]
	var bind = it.get("bind")
	if inst is Dictionary and inst.get("b"):
		s += "Seelengebunden\n"
	elif bind == "bop":
		s += "Wird beim Aufheben gebunden\n"
	elif bind == "boe":
		s += "Wird beim Anlegen gebunden\n"
	if it.get("unique"):
		s += "Einzigartig\n"
	var t := str(it.get("type", ""))
	if t in ["weapon", "armor", "jewelry"]:
		var slot := str(it.get("slot", ""))
		var slot_txt: String = SLOT_TXT.get(slot, slot)
		if it.get("two_hand"):
			slot_txt = "Zweihändig"
		var sub: String = SUB_TXT.get(str(it.get("sub", "")), str(it.get("sub", "")))
		s += "%s%s%s\n" % [slot_txt, "        " if sub != "" else "", sub]
		if t == "weapon":
			var dmg: Array = it.get("dmg", [1, 2])
			var sp := float(it.get("speed", 2.0))
			s += "%d – %d Schaden        Tempo %.2f\n" % [int(dmg[0]), int(dmg[1]), sp]
			s += "(%.1f Schaden pro Sekunde)\n" % ((float(dmg[0]) + float(dmg[1])) * 0.5 / sp)
		if it.get("armor"):
			s += "%d Rüstung\n" % int(it["armor"])
		var stats: Dictionary = it.get("stats", {})
		for k in STAT_ORDER:
			if stats.has(k):
				var v = stats[k]
				if k in ["str", "agi", "sta", "int", "spi"]:
					s += "+%d %s\n" % [int(v), stat_name(k)]
		for k in STAT_ORDER:
			if stats.has(k) and not k in ["str", "agi", "sta", "int", "spi"]:
				var v = stats[k]
				if k in PCT:
					s += "[color=#1eff00]Anlegen: Erhöht %s um %s %%.[/color]\n" % [stat_name(k), str(v)]
				else:
					s += "[color=#1eff00]Anlegen: +%d %s.[/color]\n" % [int(v), stat_name(k)]
		if inst is Dictionary and inst.get("e"):
			s += "[color=#1eff00]Verzaubert: %s[/color]\n" % str(inst["e"])
		if it.get("proc"):
			var pr: Dictionary = it["proc"]
			s += "[color=#1eff00]Treffer: %d %% Chance auf %s.[/color]\n" % [int(float(pr.get("chance", 0.1)) * 100), str(pr.get("name", "einen Zusatzeffekt"))]
		if inst is Dictionary and inst.has("d"):
			var d := int(inst["d"])
			s += ("[color=#ff4040]" if d <= 0 else "") + "Haltbarkeit %d / 100%s\n" % [d, "[/color]" if d <= 0 else ""]
		if it.get("set"):
			s += "\n[color=#ffd100]Teil eines Sets[/color]\n"
		var lvl := int(it.get("lvl", 1))
		if lvl > 1:
			var c := "#ffffff" if Game.level >= lvl else "#ff4040"
			s += "[color=%s]Benötigt Stufe %d[/color]\n" % [c, lvl]
		if it.get("cls"):
			var names: Array = []
			for cid in it["cls"]:
				names.append(Content.class_name_of(cid))
			s += "Klassen: %s\n" % ", ".join(names)
		if it.get("req_rep"):
			var rr: Array = it["req_rep"]
			s += "[color=#ff8040]Benötigt %s: %s[/color]\n" % [Content.defs.get("factions", {}).get(rr[0], {}).get("name", rr[0]), rr[1]]
		s += "[color=#888]Gegenstandsstufe %d[/color]\n" % int(it.get("ilvl", lvl))
	elif t == "consumable":
		var lvl := int(it.get("lvl", 1))
		if lvl > 1:
			s += "[color=%s]Benötigt Stufe %d[/color]\n" % ["#ffffff" if Game.level >= lvl else "#ff4040", lvl]
	elif t == "quest":
		s += "Questgegenstand\n"
	elif t == "material":
		s += "[color=#66bbff]Handwerkswaren[/color]\n"
	if it.get("desc"):
		var d := str(it["desc"])
		if d.begins_with("Benutzen:"):
			s += "[color=#1eff00]%s[/color]\n" % d
		else:
			s += "[color=#ffd100]\"%s\"[/color]\n" % d
	if it.get("starts_quest"):
		s += "[color=#ffd100]Dieser Gegenstand beginnt eine Quest.[/color]\n"
	var stack := int(it.get("stack", 1))
	if stack > 1:
		s += "[color=#888]Stapelbar bis %d[/color]\n" % stack
	if int(it.get("sell", 0)) > 0:
		var n := int(inst.get("n", 1)) if inst is Dictionary else 1
		s += "Verkaufspreis: %s\n" % Content.money_bb(int(it["sell"]) * n)
	if compare and t in ["weapon", "armor", "jewelry"]:
		var cmp := compare_bb(it)
		if cmp != "":
			s += "\n" + cmp
	return s.strip_edges()


static func compare_bb(it: Dictionary) -> String:
	var slot := str(it.get("slot", ""))
	var eq_slot := slot
	if slot == "ring":
		eq_slot = "ring1"
	var cur = Game.equipment.get(eq_slot)
	if not (cur is Dictionary):
		return ""
	var other := Content.item(str(cur.get("i")))
	if other.is_empty() or str(other.get("id", "")) == str(it.get("id", "")):
		return ""
	var a: Dictionary = it.get("stats", {})
	var b: Dictionary = other.get("stats", {})
	var keys := {}
	for k in a:
		keys[k] = true
	for k in b:
		keys[k] = true
	var lines: Array = []
	for k in STAT_ORDER:
		if not keys.has(k):
			continue
		var d := float(a.get(k, 0)) - float(b.get(k, 0))
		if absf(d) < 0.01:
			continue
		var c := "#1eff00" if d > 0 else "#ff4040"
		lines.append("[color=%s]%s%s %s[/color]" % [c, "+" if d > 0 else "", ("%.1f" % d) if k in PCT else str(int(d)), stat_name(k)])
	var da := float(it.get("armor", 0)) - float(other.get("armor", 0))
	if absf(da) > 0.5:
		lines.append("[color=%s]%s%d Rüstung[/color]" % ["#1eff00" if da > 0 else "#ff4040", "+" if da > 0 else "", int(da)])
	if lines.is_empty():
		return ""
	return "[color=#888]Im Vergleich zu %s:[/color]\n" % other.get("name", "") + "\n".join(lines)


static func ability_bb(ab: Dictionary) -> String:
	var s := "[font_size=19][color=#ffffff]%s[/color][/font_size]\n" % ab.get("name", "")
	var cost := int(ab.get("cost", 0))
	var pct := float(ab.get("cost_pct", 0.0))
	var left := ""
	if pct > 0:
		var mana := int(Game.stats.get("int", 10)) * 12 * 0.4 + 40 + 15 * Game.level
		left = "%d Mana" % int(pct * mana)
	elif cost > 0:
		left = "%d %s" % [cost, Content.POWER_NAMES.get(Game.power_type, "")]
	var rng := ""
	if ab.get("melee"):
		rng = "Nahkampfreichweite"
	elif float(ab.get("range", 0)) > 0 and str(ab.get("target")) != "self":
		rng = "%d m Reichweite" % int(ab["range"])
	if left != "" or rng != "":
		s += "%s%s%s\n" % [left, "        " if left != "" and rng != "" else "", rng]
	var cast := float(ab.get("cast", 0))
	var ct := "Spontanzauber"
	if cast > 0:
		ct = ("Kanalisiert (%.1f Sek.)" % cast) if ab.get("channel") else ("Zauberzeit: %.1f Sek." % cast)
	var cd := float(ab.get("cd", 0))
	s += "%s%s\n" % [ct, ("        Abklingzeit: %s" % _cd_text(cd)) if cd > 0 else ""]
	s += "[color=#ffd100]%s[/color]" % ab.get("desc", "")
	if ab.get("talent"):
		s += "\n[color=#a0a0ff]Talentfähigkeit[/color]"
	if int(ab.get("level", 1)) > Game.level:
		s += "\n[color=#ff4040]Erlernbar ab Stufe %d[/color]" % int(ab["level"])
	return s


static func _cd_text(cd: float) -> String:
	if cd >= 60:
		var m := cd / 60.0
		return ("%d Min." % int(m)) if absf(m - round(m)) < 0.01 else ("%.1f Min." % m)
	return "%s Sek." % (str(int(cd)) if absf(cd - round(cd)) < 0.01 else "%.1f" % cd)


static func aura_bb(a: Array) -> String:
	# [id, name, left, dur, icon, debuff, stacks, src]
	var s := "[color=%s]%s[/color]" % ["#ff6060" if int(a[5]) == 1 else "#ffffff", a[1]]
	if int(a[6]) > 1:
		s += " (%d)" % int(a[6])
	if float(a[3]) > 0 and float(a[3]) < 7200:
		s += "\nVerbleibend: %s" % Content.fmt_time(float(a[2]))
	return s
