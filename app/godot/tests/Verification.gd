extends SceneTree
## Fallos provocados y límite desde los mismos controles que usa el entrevistador.

var ui: Control
var report: Dictionary = {"checks": [], "observations": [], "errors": [], "ok": false}
var output := ""
var screenshot := ""
var candidate := "cand-001"
var scenario := ""


func _init() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			output = argument.trim_prefix("--report=")
		elif argument.begins_with("--screenshot="):
			screenshot = argument.trim_prefix("--screenshot=")
		elif argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
		elif argument.begins_with("--scenario="):
			scenario = argument.trim_prefix("--scenario=")
	call_deferred("_run")


func _expect(value: bool, description: String) -> bool:
	report.checks.append({"name": description, "passed": value})
	if not value:
		push_error(description)
		_finish(false)
	return value


func _settled() -> bool:
	var deadline := Time.get_ticks_msec() + 30000
	while ui.api.busy:
		if Time.get_ticks_msec() > deadline:
			return false
		await process_frame
	return true


func _idle() -> bool:
	return await _settled() and not ui.api.has_pending_request()


func _observe(label: String) -> void:
	report.observations.append({"step": label, "notice": ui.notice.text,
		"history": ui.history.get_parsed_text(), "evaluation": ui.evaluation_text.get_parsed_text(),
		"evaluation_level": ui.evaluation_level.text, "counter": ui.get_node("%Counter").text,
		"retry_visible": ui.get_node("%Retry").visible, "input_editable": ui.question_input.editable})


func _capture() -> void:
	if screenshot.is_empty():
		return
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if _expect(image != null and image.save_png(screenshot) == OK, "Captura de la pantalla verificada"):
		report.screenshot = screenshot


func _ask() -> void:
	ui.question_input.text = "Cuéntame una ocasión en que necesitaste ayuda de un compañero y cómo trabajaron juntos." if scenario == "unsupported_claim" else "¿Has utilizado Git?"
	ui.send_button.pressed.emit()


func _run() -> void:
	ui = load("res://Main.tscn").instantiate()
	root.add_child(ui)
	ui.api.failed.connect(func(operation: String, code: String): report.errors.append({"operation": operation, "code": code}))
	var deadline := Time.get_ticks_msec() + 30000
	while ui.previewed_candidate.is_empty() or ui.api.busy:
		if Time.get_ticks_msec() > deadline:
			_expect(false, "Conexión y catálogo disponibles")
			return
		await process_frame
	ui.candidate_buttons[candidate].pressed.emit()
	if not _expect(await _idle() and ui.previewed_candidate == candidate, "CV seleccionado antes de iniciar"):
		return
	ui.start_button.pressed.emit()
	if not _expect(await _idle() and ui.session_active, "Entrevista iniciada desde Godot"):
		return
	report.session_id = ui.api.session_id
	report.candidate_id = candidate
	report.scenario = scenario
	if scenario == "limit":
		await _limit()
		return
	if scenario == "timeout":
		ui.api.timeout_seconds = 0.3
	_ask()
	if not _expect(await _settled(), "La espera de red termina sin bloquear la interfaz"):
		return
	_observe("fallo provocado")
	if scenario == "timeout":
		if not _expect(ui.api.has_pending_request() and ui.get_node("%Retry").visible and "tiempo de espera" in ui.notice.text, "Timeout visible y reintento disponible"):
			return
		if not _expect(ui.send_button.disabled and not ui.question_input.editable and ui.question_input.text == "¿Has utilizado Git?", "Borrador conservado y envíos nuevos bloqueados mientras hay una petición pendiente"):
			return
		await _capture()
		var pending: Dictionary = ui.api._pending.duplicate(true)
		await create_timer(2.2).timeout
		ui.api.timeout_seconds = 30.0
		ui.get_node("%Retry").pressed.emit()
		if not _expect(ui.api._pending == pending and await _idle(), "Reintento resuelve el mismo UUID y contenido"):
			return
		if not _expect(ui.history.get_parsed_text().count("Tú\n") == 1 and ui.get_node("%Counter").text == "1 / 20 preguntas", "Timeout resuelto sin duplicar pregunta ni contador"):
			return
	elif scenario in ["ollama_unavailable", "unsupported_claim"]:
		var expected_notice := "antecedentes del candidato" if scenario == "unsupported_claim" else "modelo no pudo responder"
		if not _expect(not ui.api.has_pending_request() and ui.question_input.editable and not ui.send_button.disabled and expected_notice in ui.notice.text, "Error confirmado visible y controles recuperados: " + scenario):
			return
		if not _expect(not ui.question_input.text.is_empty() and ui.get_node("%Counter").text == "1 / 20 preguntas", "Fallo del modelo conserva el borrador y registra el intento consumido"):
			return
		if scenario == "unsupported_claim" and not _expect(not "cambiamos la consulta" in ui.history.get_parsed_text(), "La atribución rechazada no aparece en la conversación"):
			return
		await _capture()
		if scenario == "unsupported_claim":
			ui.question_input.text = "¿Has utilizado Git?"
		ui.send_button.pressed.emit()
		if not _expect(await _idle() and ui.get_node("%Counter").text == "2 / 20 preguntas", "Nuevo envío tras recuperar el modelo"):
			return
	elif scenario == "evaluation_unavailable":
		if not _expect(not ui.api.has_pending_request() and ui.evaluation_level.text == "No disponible" and "análisis no está disponible" in ui.notice.text, "Fallo de evaluación visible sin perder la respuesta"):
			return
		var previous: String = ui.history.get_parsed_text()
		if not _expect(previous.count("Tú\n") == 1 and "He utilizado Git" in previous and ui.question_input.editable, "Respuesta del candidato conservada y entrevista disponible"):
			return
		await _capture()
		_ask()
		if not _expect(await _idle() and ui.evaluation_level.text == "Logrado" and ui.history.get_parsed_text().begins_with(previous), "La evaluación se recupera en el siguiente turno sin borrar el anterior"):
			return
	else:
		_expect(false, "Escenario conocido")
		return
	_observe("recuperación")
	ui.close_button.pressed.emit()
	if not _expect(await _idle() and ui.session_closed and not ui.start_button.disabled, "Sesión guardada y nueva entrevista disponible"):
		return
	_finish(true)


func _limit() -> void:
	for number in range(1, 21):
		_ask()
		if not _expect(await _idle() and ui.get_node("%Counter").text == "%d / 20 preguntas" % number, "Envío y contador %d de 20" % number):
			return
		if number < 20 and not _expect(ui.session_active and ui.question_input.editable, "La entrevista continúa antes del límite: %d" % number):
			return
	if not _expect(ui.session_closed and not ui.session_active and ui.send_button.disabled and not ui.question_input.editable, "El turno 20 cierra la entrevista y bloquea envíos"):
		return
	if not _expect(ui.evaluation_level.text == "No disponible" and ui.history.get_parsed_text().count("Tú\n") == 20 and ui.history.get_parsed_text().count("He utilizado Git") == 20, "El fallo del evaluador en el turno 20 conserva las veinte respuestas"):
		return
	_observe("límite de veinte preguntas")
	await _capture()
	var previous: String = ui.history.get_parsed_text()
	ui.question_input.text = "Pregunta 21 que debe rechazarse"
	ui.send_button.pressed.emit()
	ui.question_input.text_submitted.emit(ui.question_input.text)
	if not _expect(not ui.api.busy and not ui.api.has_pending_request() and ui.history.get_parsed_text() == previous, "Enviar y Enter no despachan la pregunta 21 desde la interfaz"):
		return
	# Verificar también el rechazo del servidor aunque se omita la protección visual.
	ui.api.ask("Pregunta 21 que debe rechazarse")
	if not _expect(await _idle() and ui.session_closed and ui.history.get_parsed_text() == previous, "La API rechaza el turno 21 y conserva el historial"):
		return
	if not _expect(report.errors.any(func(error): return error.operation == "run" and error.code == "session_closed"), "Rechazo explícito session_closed para el turno 21"):
		return
	if not _expect(not ui.start_button.disabled and ui.candidate_buttons.values().all(func(button): return not button.disabled), "Selector y nueva entrevista disponibles tras el límite"):
		return
	_finish(true)


func _finish(ok: bool) -> void:
	report.ok = ok
	report.mode = "fault_injection_simulated_models"
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file != null:
			file.store_string(JSON.stringify(report, "  "))
			file.close()
	print("GODOT_VERIFICATION_OK" if ok else "GODOT_VERIFICATION_FAILED")
	quit(0 if ok else 1)
