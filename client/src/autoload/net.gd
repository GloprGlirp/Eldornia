extends Node
## Verbindung zum Eldornia-Server: REST (Accounts, Charaktere, Inhalte, Zonen) und WebSocket (Spielwelt).

signal message(m: Dictionary)
signal connected
signal disconnected(reason: String)

var token := ""
var ws: WebSocketPeer
var ws_open := false
var _closing_reason := ""
var _out: Array = []
var ping_ms := 0.0
var _ping_t := 0.0
var server_tick_ms := 0.0
var online := 0
var bytes_in := 0
var _zone_cache: Dictionary = {}


func base_url() -> String:
	var s: String = Settings.server.strip_edges()
	if s.ends_with("/"):
		s = s.substr(0, s.length() - 1)
	if not s.begins_with("http"):
		s = "https://" + s
	return s


func ws_url() -> String:
	var b := base_url()
	if b.begins_with("https://"):
		return "wss://" + b.substr(8)
	return "ws://" + b.substr(7)


# ============================================================================== REST
## Führt eine HTTP-Anfrage aus. callback(ok: bool, status: int, data: Variant)
func api(method: int, path: String, body = null, callback: Callable = Callable(), timeout := 25.0) -> void:
	var req := HTTPRequest.new()
	req.timeout = timeout
	req.accept_gzip = true
	add_child(req)
	var headers := PackedStringArray(["Content-Type: application/json", "Accept: application/json"])
	if token != "":
		headers.append("Authorization: Bearer " + token)
	req.request_completed.connect(func(result: int, code: int, _h: PackedStringArray, raw: PackedByteArray):
		req.queue_free()
		var data = null
		if raw.size() > 0:
			data = JSON.parse_string(raw.get_string_from_utf8())
		var ok := result == HTTPRequest.RESULT_SUCCESS and code >= 200 and code < 300
		if callback.is_valid():
			callback.call(ok, code if result == HTTPRequest.RESULT_SUCCESS else 0, data)
	)
	var payload := "" if body == null else JSON.stringify(body)
	var err := req.request(base_url() + path, headers, method, payload)
	if err != OK:
		req.queue_free()
		if callback.is_valid():
			callback.call(false, 0, null)


func get_json(path: String, callback: Callable) -> void:
	api(HTTPClient.METHOD_GET, path, null, callback, 60.0)


func post_json(path: String, body: Dictionary, callback: Callable) -> void:
	api(HTTPClient.METHOD_POST, path, body, callback)


static func error_text(code: int, data) -> String:
	if code == 0:
		return "Der Server ist nicht erreichbar. Prüfe die Serveradresse oder deine Internetverbindung."
	if data is Dictionary and data.has("detail"):
		var d = data["detail"]
		if d is String:
			return d
		if d is Array and d.size() > 0 and d[0] is Dictionary:
			return "Ungültige Eingabe."
	return "Fehler %d" % code


## Lädt die Zonendaten (zwischengespeichert, auch auf der Festplatte).
func load_zone(zone_id: String, callback: Callable) -> void:
	if _zone_cache.has(zone_id):
		callback.call(_zone_cache[zone_id])
		return
	get_json("/api/zone/" + zone_id, func(ok: bool, code: int, data):
		if ok and data is Dictionary:
			_zone_cache[zone_id] = data
			callback.call(data)
		else:
			callback.call(null)
	)


# ============================================================================== WebSocket
func connect_world(char_id: int) -> void:
	close_world("")
	ws = WebSocketPeer.new()
	ws.inbound_buffer_size = 1 << 23
	ws.outbound_buffer_size = 1 << 20
	ws.max_queued_packets = 8192
	var err := ws.connect_to_url("%s/ws?token=%s&char=%d" % [ws_url(), token.uri_encode(), char_id])
	if err != OK:
		disconnected.emit("Verbindung fehlgeschlagen.")
		ws = null
	ws_open = false
	_closing_reason = ""


func close_world(reason := "") -> void:
	if ws:
		_closing_reason = reason
		ws.close()
		ws = null
	ws_open = false


func send(m: Dictionary) -> void:
	if ws and ws_open:
		ws.send_text(JSON.stringify(m))
	elif ws:
		_out.append(m)


func _process(delta: float) -> void:
	if ws == null:
		return
	ws.poll()
	var st := ws.get_ready_state()
	if st == WebSocketPeer.STATE_OPEN:
		if not ws_open:
			ws_open = true
			connected.emit()
			for m in _out:
				ws.send_text(JSON.stringify(m))
			_out.clear()
		var n := 0
		while ws.get_available_packet_count() > 0 and n < 400:
			n += 1
			var pkt := ws.get_packet()
			bytes_in += pkt.size()
			var m = JSON.parse_string(pkt.get_string_from_utf8())
			if m is Dictionary:
				if m.get("t") == "pong":
					ping_ms = (Time.get_ticks_msec() - float(m.get("c", 0))) * 1.0
					server_tick_ms = float(m.get("s", 0))
					online = int(m.get("n", 0))
				else:
					message.emit(m)
			if ws == null:
				return
		_ping_t -= delta
		if _ping_t <= 0.0:
			_ping_t = 3.0
			ws.send_text(JSON.stringify({"t": "ping", "c": Time.get_ticks_msec()}))
	elif st == WebSocketPeer.STATE_CLOSED:
		var reason := _closing_reason
		if reason == "":
			reason = "Die Verbindung zum Server wurde getrennt."
			if ws.get_close_reason() != "":
				reason += " (" + ws.get_close_reason() + ")"
		ws = null
		var was_open := ws_open
		ws_open = false
		if was_open or reason != "":
			disconnected.emit(reason)
		else:
			disconnected.emit("Der Spielserver ist nicht erreichbar.")
