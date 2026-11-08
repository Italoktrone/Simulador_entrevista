"""Presentación pública y entrada de preguntas; lógica del candidato en runtime."""

from collections.abc import Callable

from harness.llm.client import LLMContextLimitError, LLMError
from harness.profile import CandidateProfile
from harness.runtime import InterviewRuntime
from harness.response_policy import ResponsePolicyDecision
from harness.application.console_view import (
    bullets, format_candidate_response, format_evaluation, format_menu,
    format_question, format_response_index, format_saved_response, panel,
    paragraph, subsection,
)


MONTH_NAMES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def _format_month(value: str) -> str:
    """Presenta un mes ya validado, sin depender del idioma de Windows."""
    year, month = value.split("-")
    return f"{MONTH_NAMES[int(month) - 1]} de {year}"


def _period(record: dict) -> str:
    return f"{_format_month(record['start_month'])} a {_format_month(record['end_month'])}"


def format_resume(profile: CandidateProfile) -> str:
    """Devuelve texto legible usando únicamente la vista pública del perfil.

    No accede a archivos ni imprime por sí misma. Otra interfaz puede utilizar
    la vista pública sin depender de este formato de consola.
    """
    resume = profile.to_public_resume()
    sections = [resume["name"], subsection("RESUMEN PROFESIONAL", paragraph(resume["professional_summary"]))]
    studies = []
    for study in resume["education"]:
        studies.append("\n".join([
            paragraph(f"{study['degree']} | {study['institution']}"),
            paragraph(f"{_period(study)}.", indent="  "),
            paragraph(f"{study['status']}. Titulación: {_format_month(study['graduation_month'])}.", indent="  "),
        ]))
    sections.append(subsection("FORMACIÓN", "\n\n".join(studies)))
    employers = []
    for employer in resume["work_experience"]:
        roles = []
        for role in employer["roles"]:
            lines = [paragraph(role["title"]), paragraph(_period(role), indent="  ")]
            for period in role["schedule_periods"]:
                lines.append(paragraph(f"{period['schedule']}: {_period(period)}.", indent="  "))
            lines.append(bullets(role["responsibilities"]))
            roles.append("\n".join(lines))
        employers.append(paragraph(employer["organization"]) + "\n\n" + "\n\n".join(roles))
    sections.extend([
        subsection("EXPERIENCIA LABORAL", "\n\n".join(employers)),
        subsection("CONOCIMIENTOS TÉCNICOS", bullets(resume["technical_skills"])),
        subsection("HERRAMIENTAS", paragraph(", ".join(resume["tools_used"]))),
    ])
    projects = []
    for project in resume["projects"]:
        projects.append("\n".join([
            paragraph(f"{project['name']} | {project['kind']}"),
            paragraph(_period(project), indent="  "),
            paragraph(project["description"], indent="  "),
            paragraph(f"Tecnologías: {', '.join(project['technologies_used'])}.", indent="  "),
            paragraph(f"Aporte personal: {'; '.join(project['personal_contributions'])}.", indent="  "),
        ]))
    sections.append(subsection("PROYECTOS", "\n\n".join(projects)))
    return panel("CURRÍCULUM RESUMIDO - PERFIL FICTICIO", "\n\n".join(sections), major=True)


def format_job(job: dict) -> str:
    """Selecciona la información de la oferta que consulta el entrevistador."""

    sections = [paragraph(job["title"]), paragraph("Organización: " + job["organization"]),
                subsection("DESCRIPCIÓN", paragraph(job["summary"]))]
    for heading, field in (
        ("RESPONSABILIDADES", "responsibilities"),
        ("REQUISITOS", "requirements"),
        ("COMPETENCIAS A EXPLORAR", "competencies_to_explore"),
    ):
        sections.append(subsection(heading, bullets(job[field])))
    expectations = job["seniority_expectations"]
    sections.extend([
        subsection("NIVEL ESPERADO", paragraph(expectations["experience_level"])),
        subsection("NO REQUERIDO PARA EL PUESTO", bullets(expectations["not_required"])),
    ])
    return panel("PUESTO FICTICIO", "\n\n".join(sections), major=True)


def _print_line(text: str) -> None:
    print(text, flush=True)


def format_session(runtime: InterviewRuntime) -> str:
    """Resumen de sesión sin textos de respuestas ni detalles internos de errores."""
    session = runtime.session_dict()
    attempts = session["attempts"]
    completed = sum(attempt["status"] == "completed" for attempt in attempts)
    issues = len(session["issues"]) + sum(len(attempt["issues"]) for attempt in attempts)
    events = session.get("context_events", [])
    issues += sum(len(event["issues"]) for event in events)
    interventions = session.get("interventions", [])
    issues += sum(len(event["issues"]) for event in interventions if event["candidate_question_number"] is None)
    classifier_errors = [event["classification"]["result"]["technical_error"]
                         for event in interventions if event["classification"] is not None
                         and event["classification"]["result"]["technical_error"] is not None]
    # Los respaldos atendidos no generan issue: contar una vez por intervención,
    # nunca por generación o reparación interna del clasificador.
    classifier_issues = sum(len(event["issues"]) for event in interventions
                            if event["classification"] is not None
                            and event["classification"]["result"]["technical_error"] is not None
                            and event["candidate_question_number"] is None)
    other_issues = issues - classifier_issues
    evaluations = session.get("evaluations", [])
    evaluator_errors = sum(e["status"] == "no_disponible" and e["reason_code"] != "informacion_insuficiente" for e in evaluations)
    issues = other_issues + len(classifier_errors) + evaluator_errors
    state = "cerrada" if session["status"] == "closed" else "abierta"
    lines = [
        f"Identificador: {session['session_id']}",
        f"Creada (UTC): {session['created_at']}",
        f"Estado: {state}",
        "",
        "AVANCE DE LA ENTREVISTA",
        "",
        f"Preguntas enviadas: {len(attempts)}/{runtime.max_questions}",
        f"Preguntas disponibles: {runtime.max_questions - len(attempts)}",
        f"Respuestas completas: {completed}",
        f"Incidencias técnicas: {issues}",
    ]
    if "context_policy" in session:
        selections = sum(e["selector_status"] != "not_requested" for e in events)
        used = sum(e["preparation"] is not None and e["preparation"]["mode"] == "extractive_summary" for e in events)
        lines.extend(["", "MEMORIA DE LA ENTREVISTA", "", f"Selecciones de memoria: {selections}", f"Resúmenes usados: {used}"])
    if "classification_policy" in session:
        lines.extend([
            "", "CLASIFICACIÓN DE INTERVENCIONES", "",
            f"Intervenciones registradas: {len(interventions)}",
            f"Aclaraciones solicitadas: {sum(e['policy'] is not None and e['policy']['action'] == 'aclarar' for e in interventions)}",
            f"Entradas no evaluables: {sum(e['policy'] is not None and e['policy']['action'] == 'no_evaluable' for e in interventions)}",
            f"Fallos de clasificación: {len(classifier_errors)}",
            f"Fallos de contrato del clasificador: {classifier_errors.count('contrato_invalido')}",
            f"Fallos de JSON del clasificador: {classifier_errors.count('json_invalido')}",
            f"Fallos del proveedor del clasificador (incluye red/servidor): {classifier_errors.count('error_proveedor')}",
            f"Otras incidencias técnicas (candidato/memoria/sesión): {other_issues}",
        ])
    if "evaluation_policy" in session:
        lines.extend([
            "", "EVALUACIÓN DE PREGUNTAS", "",
            f"Preguntas con evaluación completa: {sum(e['status'] == 'evaluada' for e in evaluations)}",
            f"Evaluaciones parciales: {sum(e['status'] == 'parcial' for e in evaluations)}",
            f"Fallos técnicos del evaluador: {evaluator_errors}",
            f"Discrepancias de evaluación pendientes: {sum(len(e['discrepancies']) for e in evaluations)}",
        ])
    consultation = ("El registro completo se guarda al finalizar esta ejecución."
                    if session["status"] == "closed" else
                    "Usa /respuestas para ver el índice o /respuesta N para leer una entrada.")
    lines.extend(["", "REGISTRO" if session["status"] == "closed" else "CONSULTA", "", consultation])
    return panel("SESIÓN ACTUAL", "\n".join(lines), major=True)


def run_console(
    runtime: InterviewRuntime,
    *,
    provider: str,
    model: str,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], None] | None = None,
) -> int:
    """Consola de una ejecución, con entradas y salidas sustituibles en pruebas."""

    read = input if input_fn is None else input_fn
    write = _print_line if output_fn is None else output_fn
    started = False
    try:
        source = {"ollama": "Ollama (local)", "openai": "OpenAI (externo)", "unab": "UNAB IA (externo)"}.get(provider, "API externa")
        overview = [
            f"Candidato: {runtime.setup.candidate.to_public_resume()['name']}",
            f"Puesto: {runtime.setup.job_dict()['title']}",
            f"Proveedor: {source}. Modelo: {model}.",
            f"Sesión: {runtime.session_id}", "",
            "Las preguntas y respuestas completas se conservan durante esta entrevista.",
            "Al finalizar se guardará el registro de esta sesión en un archivo JSON local.",
        ]
        if runtime.classification_enabled:
            overview.extend(["", "Clasificación previa activa.",
                             "Solo las preguntas enviadas al candidato consumen el límite."])
        if runtime.evaluation_enabled:
            overview.extend(["", "Evaluación provisional activa: valora la pregunta del entrevistador.",
                             "Verás los criterios, la explicación y la sugerencia después de cada respuesta."])
        if "context_policy" in runtime.session_dict():
            overview.extend(["", "La memoria se preparará cuando sea necesario; se conserva el registro completo."])
        write(panel("SIMULADOR DE ENTREVISTA - PERFIL FICTICIO",
                    "\n".join(paragraph(line) for line in overview), major=True))
        write(format_menu())
        while not runtime.finished:
            prompt = f"Pregunta {runtime.questions_asked + 1}/{runtime.max_questions}> " if started else "Menú> "
            raw = read(prompt)
            runtime.assert_source_unchanged()
            command = raw.strip().lower()
            if not command:
                if not started or not runtime.classification_enabled:
                    write("Escribe una pregunta o /salir." if started else "Escribe un comando, por ejemplo /cv.")
                    continue
            if command == "/salir":
                runtime.close("user_exit")
                write("Finalizado por el usuario.")
                return 0
            if command in {"/ayuda", "/menu"}:
                write(format_menu(started=started))
                continue
            if command == "/cv":
                write(format_resume(runtime.setup.candidate))
                continue
            if command == "/puesto":
                write(format_job(runtime.setup.job_dict()))
                continue
            if command == "/sesion":
                write(format_session(runtime))
                continue
            if command == "/respuestas":
                write(format_response_index(runtime.session_dict()))
                continue
            if command.split(maxsplit=1)[:1] == ["/respuesta"]:
                parts = command.split()
                if len(parts) != 2 or not parts[1].isascii() or not parts[1].isdecimal() or len(parts[1]) > 2 or int(parts[1]) < 1:
                    write("Usa /respuesta N; por ejemplo, /respuesta 1. Consulta /respuestas para ver el índice.")
                else:
                    write(format_saved_response(runtime.session_dict(), int(parts[1])))
                continue
            if command == "/iniciar":
                if started:
                    write("La entrevista ya está iniciada; el contador se conserva.")
                else:
                    started = True
                    write(panel("ENTREVISTA INICIADA", "\n\n".join((
                        f"Máximo: {runtime.max_questions} preguntas enviadas al candidato.",
                        "Cada pregunta enviada cuenta, aunque falle la respuesta.",
                        "Escribe tu primera pregunta. Los comandos siguen disponibles.",
                        "La primera respuesta puede tardar mientras se prepara el modelo.",
                    )), major=True))
                continue
            if command.startswith("/"):
                write("Comando no reconocido. Usa /ayuda.")
                continue
            if not started:
                write("Usa /iniciar para comenzar a enviar preguntas.")
                continue
            number = (len(runtime.session_dict().get("interventions", [])) + 1
                      if runtime.classification_enabled else runtime.questions_asked + 1)
            write(format_question(raw, number))
            write("Procesando intervención..." if runtime.classification_enabled else "Esperando respuesta del candidato...")
            try:
                def show_candidate(answer):
                    write(format_candidate_response(
                        answer.text, number=runtime.questions_asked, maximum=runtime.max_questions,
                        elapsed_seconds=answer.elapsed_seconds, provider=provider,
                        input_tokens=answer.input_tokens, output_tokens=answer.output_tokens))
                    if runtime.evaluation_enabled:
                        write("Evaluando la pregunta...")
                response = runtime.ask(raw, on_candidate_response=show_candidate) if runtime.evaluation_enabled else runtime.ask(raw)
            except LLMError as error:
                write(panel("RESPUESTA NO DISPONIBLE", paragraph(f"No se obtuvo una respuesta válida: {error}")))
                if not runtime.finished:
                    if isinstance(error, LLMContextLimitError):
                        write("La pregunta se contabilizó y el historial completo se conserva. Puedes acortar la pregunta o usar /salir para guardarlo.")
                    else:
                        write("La pregunta se contabilizó. Puedes formular otra o usar /salir.")
            else:
                if isinstance(response, ResponsePolicyDecision):
                    write(panel("AVISO DEL SIMULADOR", paragraph(f"Simulador: {response.text}")
                                + "\n\nEsta intervención no consume una pregunta enviada al candidato."))
                    if runtime.evaluation_enabled:
                        write(format_evaluation(runtime.last_evaluation))
                    continue
                if runtime.evaluation_enabled:
                    write(format_evaluation(runtime.last_evaluation))
                else:
                    show_candidate(response)
                events = runtime.session_dict().get("context_events", [])
                if events and events[-1]["selector_status"] != "not_requested":
                    write(f"Tiempo adicional de preparación de memoria: {events[-1]['preparation_elapsed_seconds']:.2f} s")
        write(f"Límite de {runtime.max_questions} preguntas enviadas alcanzado. Entrevista finalizada.")
        return 0
    except EOFError:
        runtime.close("end_of_input")
        write("\nFin de la entrada. Programa finalizado.")
        return 0
    except KeyboardInterrupt:
        runtime.close("interrupted")
        write("\nEntrevista interrumpida por el usuario.")
        return 0
    finally:
        runtime.close()
        write(format_session(runtime))
