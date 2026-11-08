extends Control
## Presentación de una sesión: las respuestas del modelo siempre se muestran como texto.

const ThemeFactory = preload("res://InterviewTheme.gd")
const CRITERIA = {"pertinencia": "Pertinencia", "enfoque": "Adecuación metodológica", "claridad": "Claridad", "neutralidad": "Neutralidad"}
const HEADINGS = {"education": "Formación", "work_experience": "Experiencia", "projects": "Proyectos", "technical_skills": "Conocimientos", "tools_used": "Herramientas", "responsibilities": "Responsabilidades", "requirements": "Requisitos", "competencies_to_explore": "Competencias", "seniority_expectations": "Nivel del cargo"}

@onready var api = %Api
@onready var start_button: Button = %Start
@onready var close_button: Button = %Close
@onready var question_input: LineEdit = %Question
@onready var send_button: Button = %Send
@onready var history: RichTextLabel = %History
@onready var evaluation_text: RichTextLabel = %EvaluationText
@onready var evaluation_level: Label = %EvaluationLevel
@onready var notice: Label = %Notice

var connection_ready := false
var session_active := false
var session_closed := false
var _pending_question := ""
var _quit_after_close := false
var _seen_requests: Dictionary = {}


func _ready() -> void:
	theme = ThemeFactory.build()
	ThemeFactory.primary(start_button)
	ThemeFactory.primary(send_button)
	get_tree().auto_accept_quit = false
	api.received.connect(_received)
	api.failed.connect(_failed)
	api.request_started.connect(_started)
	start_button.pressed.connect(start_interview)
	close_button.pressed.connect(close_interview)
	send_button.pressed.connect(send_question)
	question_input.text_submitted.connect(func(_text: String): send_question())
	question_input.text_changed.connect(func(_text: String): _controls())
	%Retry.pressed.connect(api.retry_request)
	%Reconnect.pressed.connect(reconnect)
	%ExitConfirm.confirmed.connect(func(): get_tree().quit())
	_controls()
	reconnect.call_deferred()


func reconnect() -> void:
	if api.busy:
		return
	if api.has_pending_request():
		if api.pending_operation() == "health":
			api.retry_request()
		return
	api.check_health()


func start_interview() -> void:
	if not connection_ready or session_active or api.busy or api.has_pending_request():
		return
	var evaluate: bool = %Evaluate.button_pressed
	api.start_session(evaluate, evaluate)


func send_question() -> void:
	if not session_active or api.busy or api.has_pending_request():
		return
	var text := question_input.text.strip_edges()
	if text.is_empty():
		return
	_pending_question = text
	_append("Tú", text, ThemeFactory.ACCENT)
	api.ask(text)


func close_interview() -> void:
	if session_active and not api.busy and not api.has_pending_request():
		api.close_session()


func _started(operation: String) -> void:
	var messages := {"health": "Comprobando el servicio…", "start": "Preparando la entrevista…", "run": "Esperando la respuesta y su análisis. El modelo local puede tardar unos minutos…", "close": "Guardando la entrevista…"}
	_set_notice(str(messages.get(operation, "Esperando al servicio…")))
	_controls()


func _received(operation: String, payload: Dictionary) -> void:
	match operation:
		"health":
			connection_ready = payload.get("status") == "ok" and payload.get("api_version") == "1.0.0"
			%Connection.text = "Servicio conectado" if connection_ready else "Servicio incompatible"
			%Connection.modulate = ThemeFactory.ACCENT if connection_ready else Color("f3b96c")
			_set_notice("Listo para iniciar. La disponibilidad del modelo se comprobará al preguntar." if connection_ready else "Revisa que esté funcionando la API del proyecto.", not connection_ready)
		"start":
			session_active = true
			session_closed = false
			_seen_requests.clear()
			history.clear()
			question_input.clear()
			_pending_question = ""
			var resume: Dictionary = payload.get("resume", {})
			var job: Dictionary = payload.get("job", {})
			%CandidateName.text = str(resume.get("name", "Candidato"))
			%JobTitle.text = str(job.get("title", "Puesto de práctica"))
			%Currículum.text = _resume(resume)
			%Puesto.text = _job(job)
			_counter(payload)
			_render_evaluation(null)
			_append("Entrevista iniciada", "Consulta el currículum y el puesto antes de formular tu primera pregunta.", ThemeFactory.MUTED)
			_set_notice("Escribe una pregunta y pulsa Enviar o Enter.")
		"run":
			_counter(payload)
			var request_id := str(payload.get("request_id", ""))
			if not _seen_requests.has(request_id):
				_seen_requests[request_id] = true
				if payload.get("reply") is String:
					_append(str(%CandidateName.text) if payload.get("status") == "completed" else "Orientación", payload.reply, ThemeFactory.INK)
				_render_evaluation(payload.get("evaluation"))
				if payload.get("status") != "error":
					question_input.clear()
					_pending_question = ""
			if payload.get("closed", false):
				_closed()
			elif payload.get("status") == "error":
				_set_notice(_error_message(str(payload.get("error_code", "model_error"))), true)
			else:
				_set_notice("Respuesta recibida. Puedes continuar la entrevista.")
		"close":
			_closed()
			if _quit_after_close:
				get_tree().quit()
	_controls()
	if session_active and not api.has_pending_request():
		question_input.grab_focus()


func _failed(operation: String, code: String) -> void:
	if operation == "health":
		connection_ready = false
		%Connection.text = "Servicio no disponible"
		%Connection.modulate = Color("f3b96c")
	if code in ["session_not_found", "session_closed"]:
		session_active = false
		session_closed = true
	_set_notice(_error_message(code), true)
	_controls()
	if _quit_after_close:
		_quit_after_close = false
		%ExitConfirm.popup_centered()


func _closed() -> void:
	session_active = false
	session_closed = true
	_set_notice("Entrevista cerrada. El registro quedó guardado.")


func _controls() -> void:
	var pending: bool = api.has_pending_request()
	var locked: bool = api.busy or pending
	start_button.disabled = not connection_ready or session_active or locked
	start_button.text = "Nueva entrevista" if session_closed else "Iniciar entrevista"
	close_button.disabled = not session_active or locked
	question_input.editable = session_active and not locked
	send_button.disabled = not session_active or locked or question_input.text.strip_edges().is_empty()
	%Evaluate.disabled = session_active or locked
	%Retry.visible = pending and not api.busy
	%Retry.disabled = api.busy
	%Reconnect.disabled = api.busy or (pending and api.pending_operation() != "health")
	%Waiting.visible = api.busy


func _counter(payload: Dictionary) -> void:
	%Counter.text = "%d / %d preguntas" % [int(payload.get("questions_asked", 0)), int(payload.get("max_questions", 20))]


func _append(speaker: String, text: String, color: Color) -> void:
	history.push_color(color)
	history.push_bold()
	history.add_text(speaker + "\n")
	history.pop()
	history.pop()
	history.add_text(text + "\n\n")


func _set_notice(text: String, error: bool = false) -> void:
	notice.text = text
	notice.modulate = Color("f3b96c") if error else Color.WHITE


func _render_evaluation(value: Variant) -> void:
	evaluation_text.clear()
	if not value is Dictionary:
		evaluation_level.text = "Sin evaluar"
		evaluation_text.add_text("El análisis aparecerá después de la respuesta si activaste Analizar mis preguntas.")
		return
	var titles := {"parcial": "Evaluación parcial", "no_evaluable": "No evaluable", "no_ejecutada": "No ejecutada", "no_disponible": "No disponible"}
	evaluation_level.text = str(value.get("visible_level") if value.get("visible_level") != null else titles.get(value.get("status"), "Sin nivel global"))
	var analysis: Variant = value.get("analysis")
	if analysis is Dictionary:
		var criteria: Dictionary = analysis.get("criteria", {})
		for key in CRITERIA:
			var criterion: Dictionary = criteria.get(key, {})
			var level: Variant = criterion.get("level")
			evaluation_text.add_text("%s: %s\n" % [CRITERIA[key], "%d / 4" % int(level) if level != null else "Sin evidencia suficiente"])
			if not str(criterion.get("reason", "")).is_empty():
				evaluation_text.add_text(str(criterion.reason) + "\n\n")
	for entry in [["explanation", ""], ["suggestion", "Sugerencia: "], ["reformulation", "Reformulación: "]]:
		if value.get(entry[0]) is String and not str(value[entry[0]]).is_empty():
			evaluation_text.add_text(str(entry[1]) + str(value[entry[0]]) + "\n\n")
	evaluation_text.scroll_to_line(0)


func _resume(data: Dictionary) -> String:
	var text := str(data.get("professional_summary", "")) + "\n"
	for key in ["education", "work_experience", "technical_skills", "tools_used", "projects"]:
		text += "\n" + str(HEADINGS[key]) + "\n" + _details(data.get(key, []))
	return text


func _job(data: Dictionary) -> String:
	var text := str(data.get("organization", "")) + "\n\n" + str(data.get("summary", "")) + "\n"
	for key in ["responsibilities", "requirements", "competencies_to_explore", "seniority_expectations"]:
		text += "\n" + str(HEADINGS[key]) + "\n" + _details(data.get(key, []))
	return text


func _details(value: Variant, indent: String = "") -> String:
	var text := ""
	if value is Array:
		for item in value:
			text += _details(item, indent) if item is Dictionary else indent + "• " + str(item) + "\n"
	elif value is Dictionary:
		for key in value:
			if str(key).ends_with("_id"):
				continue
			if value[key] is Array or value[key] is Dictionary:
				text += _details(value[key], indent + "  ")
			else:
				text += indent + str(value[key]) + "\n"
	else:
		text = indent + str(value) + "\n"
	return text


func _error_message(code: String) -> String:
	var messages := {"connection_error": "No se pudo conectar. Inicia la API y pulsa Reintentar.", "transport_error": "No se confirmó la respuesta. Reintentar conserva la misma petición y evita duplicarla.", "invalid_json": "El servicio devolvió una respuesta ilegible. Revisa la API y reintenta.", "invalid_response": "La respuesta del servicio es incompatible. Revisa la API y reintenta.", "unauthorized": "El servicio requiere una credencial de acceso. Configura la conexión antes de continuar.", "session_busy": "La sesión todavía está ocupada. Espera un momento y reintenta.", "session_not_found": "La sesión ya no está disponible. Inicia una nueva entrevista.", "session_closed": "Esta entrevista ya está cerrada. Puedes iniciar otra.", "model_error": "El modelo no pudo responder. La pregunta se conserva para que puedas enviarla de nuevo.", "fallo_clasificacion": "No se pudo interpretar la pregunta. Puedes revisarla y enviarla de nuevo.", "execution_error": "La entrevista se interrumpió. Puedes iniciar una nueva sesión.", "session_capacity": "El servicio alcanzó su capacidad de sesiones. Reinícialo antes de continuar."}
	return str(messages.get(code, "La operación no se pudo confirmar. Revisa el servicio y vuelve a intentarlo."))


func _notification(what: int) -> void:
	if what != NOTIFICATION_WM_CLOSE_REQUEST or not is_node_ready():
		return
	if not session_active and not api.busy and not api.has_pending_request():
		get_tree().quit()
	elif api.busy or api.has_pending_request():
		%ExitConfirm.popup_centered()
	else:
		_quit_after_close = true
		close_interview()
