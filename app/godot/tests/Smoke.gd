extends SceneTree
## Recorre los controles reales contra la API; no prueba la calidad educativa.

var ui: Control
var report: Dictionary = {"checks": [], "ok": false}
var output := ""
var live := false
var wait_seconds := 40.0
var screenshot := ""
var candidate := "cand-001"
const PROFILES = {"cand-001": ["Nicolás Vera Soto", "MesaFaro"], "cand-002": ["Camila Rojas Medina", "TurnosBrújula"], "cand-003": ["Diego Muñoz Leiva", "ConciliaciónLadera"]}


func _init() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			output = argument.trim_prefix("--report=")
		elif argument == "--live":
			live = true
			wait_seconds = 600.0
		elif argument.begins_with("--screenshot="):
			screenshot = argument.trim_prefix("--screenshot=")
		elif argument.begins_with("--candidate="):
			candidate = argument.trim_prefix("--candidate=")
	call_deferred("_run")


func _expect(value: bool, description: String) -> bool:
	report.checks.append({"name": description, "passed": value})
	if not value:
		push_error(description)
		_finish(false)
	return value


func _settled() -> bool:
	var deadline := Time.get_ticks_msec() + int(wait_seconds * 1000)
	while ui.api.busy:
		if Time.get_ticks_msec() > deadline:
			return false
		await process_frame
	return true


func _idle() -> bool:
	return await _settled() and not ui.api.has_pending_request()


func _preview_ready() -> bool:
	var deadline := Time.get_ticks_msec() + 30000
	while ui.previewed_candidate.is_empty() or ui.api.busy:
		if Time.get_ticks_msec() > deadline or (ui.api.has_pending_request() and not ui.api.busy):
			return false
		await process_frame
	return true


func _complete(operation: String) -> bool:
	if live:
		return await _idle()
	if not await _settled():
		return false
	if not _expect(ui.api.has_pending_request() and ui.get_node("%Retry").visible and ui.send_button.disabled, "Reintento disponible tras respuesta perdida o inválida: " + operation):
		return false
	var pending: Dictionary = ui.api._pending.duplicate(true)
	ui.get_node("%Retry").pressed.emit()
	if not _expect(ui.api._pending == pending, "Reintento conserva UUID y contenido: " + operation):
		return false
	return await _idle()


func _run() -> void:
	ui = load("res://Main.tscn").instantiate()
	root.add_child(ui)
	await process_frame
	if not _expect(await _complete("health") and ui.connection_ready, "Conexión con la API desde Godot"):
		return
	if not _expect(await _preview_ready() and ui.candidate_buttons.size() == 3, "Catálogo de tres candidatos disponible"):
		return
	for identifier in PROFILES:
		ui.candidate_buttons[identifier].pressed.emit()
		if not _expect(await _idle() and ui.get_node("%CandidateName").text == PROFILES[identifier][0] and PROFILES[identifier][1] in ui.get_node("%Currículum").text, "Vista previa del CV correcto: " + identifier):
			return
		for other in PROFILES:
			if other != identifier:
				if not _expect(not PROFILES[other][1] in ui.get_node("%Currículum").text, "CV sin proyectos ajenos: " + identifier + " / " + other):
					return
	ui.candidate_buttons[candidate].pressed.emit()
	if not _expect(await _idle() and ui.previewed_candidate == candidate, "Perfil elegido antes de iniciar"):
		return
	report.candidate_id = candidate
	if not _expect(ui.send_button.disabled and ui.close_button.disabled, "Sin envíos antes de iniciar"):
		return
	if OS.get_environment("GODOT_SMOKE_NO_EVALUATION") == "1":
		ui.get_node("%Evaluate").button_pressed = false
	ui.start_button.pressed.emit()
	if not _expect(await _complete("start") and ui.session_active, "Inicio desde el botón"):
		return
	report.session_id = ui.api.session_id
	if not _expect(ui.candidate_buttons.values().all(func(button): return button.disabled), "Selección bloqueada durante la entrevista"):
		return
	if not _expect(not ui.get_node("%Currículum").text.is_empty() and not ui.get_node("%Puesto").text.is_empty(), "CV y puesto disponibles"):
		return
	var question := "¿Has utilizado Git?"
	ui.question_input.text = question
	ui.send_button.pressed.emit()
	if not _expect(ui.send_button.disabled and not ui.question_input.editable, "Controles bloqueados durante la petición"):
		return
	if not _expect(await _complete("run"), "Respuesta completa recibida"):
		return
	report.history = ui.history.get_parsed_text()
	report.evaluation = ui.evaluation_text.get_parsed_text()
	report.evaluation_level = ui.evaluation_level.text
	if not _expect(question in report.history and ui.history.get_parsed_text().count("Tú\n") == 1, "Pregunta visible una sola vez"):
		return
	if not _expect(ui.get_node("%Counter").text.begins_with("1 /"), "Contador actualizado"):
		return
	if not _expect(not ui.question_input.text, "Borrador limpiado tras la respuesta"):
		return
	if not live:
		if not _expect(PROFILES[candidate][0] in report.history and not "[resume." in report.history and not "[job." in report.history and not "[document_id:" in report.history and ui.get_node("%Sources").visible, "Respuesta del candidato elegido y fuentes separadas"):
			return
		if not _expect("[b]Texto literal[/b]" in report.history, "Respuesta del modelo tratada como texto literal"):
			return
		if not _expect(ui.evaluation_level.text == "Logrado" and "Pertinencia: 3 / 4" in report.evaluation, "Evaluación separada con cuatro criterios"):
			return
	if not screenshot.is_empty():
		await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		if not _expect(image != null and image.save_png(screenshot) == OK, "Captura de la interfaz renderizada"):
			return
		report.screenshot = screenshot
	ui.close_button.pressed.emit()
	if not _expect(await _complete("close") and ui.session_closed and not ui.session_active, "Cierre confirmado por la API"):
		return
	if not _expect(ui.send_button.disabled and not ui.start_button.disabled, "Nueva entrevista disponible tras cerrar"):
		return
	if not _expect(ui.candidate_buttons.values().all(func(button): return not button.disabled), "Selección disponible tras cerrar"):
		return
	_finish(true)


func _finish(ok: bool) -> void:
	report.ok = ok
	report.mode = "live" if live else "simulated"
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file == null:
			push_error("No se pudo guardar el informe de Godot.")
			quit(2)
			return
		file.store_string(JSON.stringify(report, "  "))
		file.close()
	print("GODOT_SMOKE_OK" if ok else "GODOT_SMOKE_FAILED")
	quit(0 if ok else 1)
