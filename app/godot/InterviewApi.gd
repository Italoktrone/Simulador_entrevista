class_name InterviewApi
extends Node
## Nodo de transporte para conectar las escenas de Godot 4 con Python.

signal received(operation: String, payload: Dictionary)
signal failed(operation: String, code: String)
signal request_started(operation: String)

@export var base_url: String = "http://127.0.0.1:8000"
@export var timeout_seconds: float = 600.0
var session_id: String = ""
var token: String = ""
var busy: bool = false
var _http: HTTPRequest
var _pending: Dictionary = {}


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = timeout_seconds
	add_child(_http)
	_http.body_size_limit = 2097152
	_http.request_completed.connect(_completed)
	if OS.has_environment("INTERVIEW_API_URL"):
		base_url = OS.get_environment("INTERVIEW_API_URL")
	token = OS.get_environment("INTERVIEW_API_TOKEN")


func has_pending_request() -> bool:
	return not _pending.is_empty()


func pending_operation() -> String:
	return str(_pending.get("operation", ""))


func new_request_id() -> String:
	var data := Crypto.new().generate_random_bytes(16)
	data[6] = (data[6] & 0x0f) | 0x40
	data[8] = (data[8] & 0x3f) | 0x80
	var hex := data.hex_encode()
	return "%s-%s-%s-%s-%s" % [hex.substr(0, 8), hex.substr(8, 4), hex.substr(12, 4), hex.substr(16, 4), hex.substr(20, 12)]


func check_health() -> void:
	_send("health", "/health", HTTPClient.METHOD_GET, {})


func metadata() -> void:
	_send("metadata", "/metadata", HTTPClient.METHOD_GET, {})


func start_session(classify: bool = true, evaluate: bool = true) -> void:
	_send("start", "/sessions", HTTPClient.METHOD_POST, {
		"request_id": new_request_id(), "classify": classify, "evaluate": evaluate
	})


func ask(question: String, use_rag: bool = true) -> void:
	if session_id.is_empty():
		failed.emit("run", "session_required")
		return
	_send("run", "/run", HTTPClient.METHOD_POST, {
		"session_id": session_id, "request_id": new_request_id(),
		"question": question, "use_rag": use_rag
	})


func close_session() -> void:
	if session_id.is_empty():
		failed.emit("close", "session_required")
		return
	_send("close", "/sessions/" + session_id + "/close", HTTPClient.METHOD_POST, {})


func get_logs() -> void:
	if session_id.is_empty():
		failed.emit("logs", "session_required")
		return
	_send("logs", "/logs?session_id=" + session_id, HTTPClient.METHOD_GET, {})


func search_documents(query: String) -> void:
	_send("search", "/tools/search_documents", HTTPClient.METHOD_POST, {"query": query, "limit": 3})


func retry_request() -> void:
	if _pending.is_empty() or busy:
		failed.emit("retry", "no_retry_available")
		return
	_dispatch()


func _send(operation: String, path: String, method: int, body: Dictionary) -> void:
	if busy or not _pending.is_empty():
		failed.emit(operation, "request_pending")
		return
	_pending = {"operation": operation, "path": path, "method": method, "body": body}
	_dispatch()


func _dispatch() -> void:
	var headers := PackedStringArray(["Content-Type: application/json"])
	if not token.is_empty():
		headers.append("Authorization: Bearer " + token)
	busy = true
	_http.timeout = timeout_seconds if _pending.operation == "run" else 10.0
	request_started.emit(str(_pending.operation))
	var body := "" if _pending.method == HTTPClient.METHOD_GET else JSON.stringify(_pending.body)
	var error := _http.request(base_url.trim_suffix("/") + _pending.path, headers, _pending.method, body)
	if error != OK:
		busy = false
		failed.emit(_pending.operation, "connection_error")


func _completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	busy = false
	var operation: String = _pending.operation
	if result != HTTPRequest.RESULT_SUCCESS:
		failed.emit(operation, "transport_error")
		return
	var decoded: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not decoded is Dictionary:
		failed.emit(operation, "invalid_json")
		return
	if response_code >= 400:
		var detail: Variant = decoded.get("error", {})
		var code := "http_error"
		if detail is Dictionary:
			code = str(detail.get("code", code))
		if code != "session_busy" and response_code < 500:
			_pending = {}
		failed.emit(operation, code)
		return
	if not _valid_response(operation, decoded):
		failed.emit(operation, "invalid_response")
		return
	_pending = {}
	if operation == "start":
		session_id = decoded.session_id
	received.emit(operation, decoded)


func _valid_response(operation: String, payload: Dictionary) -> bool:
	match operation:
		"health":
			return payload.get("status") is String and payload.get("api_version") is String
		"start":
			return payload.get("session_id") is String and not payload.session_id.is_empty() and payload.get("status") == "open" and payload.get("resume") is Dictionary and payload.get("job") is Dictionary
		"run":
			return payload.get("session_id") == session_id and payload.get("request_id") == _pending.body.request_id and payload.get("status") in ["completed", "handled", "error"] and payload.get("closed") is bool and (payload.get("reply") == null or payload.get("reply") is String) and (payload.get("evaluation") == null or payload.get("evaluation") is Dictionary)
		"close":
			return payload.get("session_id") == session_id and payload.get("status") == "closed"
	return true
