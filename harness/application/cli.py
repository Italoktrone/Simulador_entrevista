"""Presentación pública y entrada de preguntas; lógica del candidato en runtime."""

from collections.abc import Callable

from harness.llm.client import LLMContextLimitError, LLMError
from harness.profile import CandidateProfile
from harness.runtime import InterviewRuntime


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
    lines = [
        "CURRÍCULUM RESUMIDO - PERFIL FICTICIO",
        resume["name"],
        "",
        "RESUMEN PROFESIONAL",
        resume["professional_summary"],
        "",
        "FORMACIÓN",
    ]
    for study in resume["education"]:
        lines.extend([
            f"- {study['degree']} - {study['institution']}",
            f"  {_period(study)}.",
            f"  {study['status']}. Titulación: {_format_month(study['graduation_month'])}.",
        ])
    lines.extend(["", "EXPERIENCIA LABORAL"])
    for employer in resume["work_experience"]:
        lines.append(employer["organization"])
        for role in employer["roles"]:
            lines.append(f"- {role['title']} ({_period(role)})")
            for period in role["schedule_periods"]:
                lines.append(f"  {period['schedule']}: {_period(period)}.")
            lines.extend(f"  - {item}" for item in role["responsibilities"])
    lines.extend(["", "CONOCIMIENTOS TÉCNICOS"])
    lines.extend(f"- {skill}" for skill in resume["technical_skills"])
    lines.extend(["", "HERRAMIENTAS", ", ".join(resume["tools_used"]), "", "PROYECTOS"])
    for project in resume["projects"]:
        lines.extend([
            f"- {project['name']} ({project['kind']}; {_period(project)})",
            f"  {project['description']}",
            f"  Tecnologías: {', '.join(project['technologies_used'])}.",
            f"  Aporte personal: {'; '.join(project['personal_contributions'])}.",
        ])
    return "\n".join(lines)


def format_job(job: dict) -> str:
    """Selecciona la información de la oferta que consulta el entrevistador."""

    lines = ["PUESTO FICTICIO", job["title"], job["organization"], "", job["summary"]]
    for heading, field in (
        ("RESPONSABILIDADES", "responsibilities"),
        ("REQUISITOS", "requirements"),
        ("COMPETENCIAS A EXPLORAR", "competencies_to_explore"),
    ):
        lines.extend(["", heading])
        lines.extend(f"- {item}" for item in job[field])
    expectations = job["seniority_expectations"]
    lines.extend(["", "NIVEL ESPERADO", expectations["experience_level"], "", "NO REQUERIDO PARA EL PUESTO"])
    lines.extend(f"- {item}" for item in expectations["not_required"])
    return "\n".join(lines)


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
    state = "cerrada" if session["status"] == "closed" else "abierta"
    lines = [
        "SESIÓN ACTUAL",
        f"Identificador: {session['session_id']}",
        f"Creada (UTC): {session['created_at']}",
        f"Estado: {state}",
        f"Preguntas enviadas: {len(attempts)}/{runtime.max_questions}",
        f"Respuestas completas: {completed}",
        f"Incidencias técnicas: {issues}",
    ]
    if "context_policy" in session:
        selections = sum(e["selector_status"] != "not_requested" for e in events)
        used = sum(e["preparation"] is not None and e["preparation"]["mode"] == "extractive_summary" for e in events)
        lines.extend([f"Selecciones de memoria: {selections}", f"Resúmenes usados: {used}"])
    return "\n".join(lines)


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
    help_text = "Comandos: /cv, /puesto, /sesion, /iniciar, /ayuda, /salir."
    try:
        write("SIMULADOR DE ENTREVISTA - PERFIL FICTICIO")
        write(f"Sesión: {runtime.session_id}")
        write(f"Candidato: {runtime.setup.candidate.to_public_resume()['name']}")
        write(f"Puesto: {runtime.setup.job_dict()['title']}")
        source = {"ollama": "Ollama (local)", "openai": "OpenAI (externo)", "unab": "UNAB IA (externo)"}.get(provider, "API externa")
        write(f"Proveedor: {source}. Modelo: {model}.")
        write(help_text)
        write("Las preguntas y respuestas completas se conservan durante esta entrevista.")
        write("Al finalizar se guardará el registro de esta sesión en un archivo JSON local.")
        if "context_policy" in runtime.session_dict():
            write("La memoria se preparará cuando sea necesario y se conservará el registro completo.")
        while not runtime.finished:
            prompt = f"Pregunta {runtime.questions_asked + 1}/{runtime.max_questions}> " if started else "Menú> "
            raw = read(prompt)
            runtime.assert_source_unchanged()
            command = raw.strip().lower()
            if not command:
                write("Escribe una pregunta o /salir." if started else "Escribe un comando, por ejemplo /cv.")
                continue
            if command == "/salir":
                runtime.close("user_exit")
                write("Finalizado por el usuario.")
                return 0
            if command == "/ayuda":
                write(help_text)
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
            if command == "/iniciar":
                if started:
                    write("La entrevista ya está iniciada; el contador se conserva.")
                else:
                    started = True
                    write(f"Entrevista iniciada. Máximo: {runtime.max_questions} preguntas enviadas.")
                    write("Cada pregunta enviada cuenta, aunque falle la respuesta.")
                    write("La primera respuesta puede tardar mientras se prepara el modelo.")
                continue
            if command.startswith("/"):
                write("Comando no reconocido. Usa /ayuda.")
                continue
            if not started:
                write("Usa /iniciar para comenzar a enviar preguntas.")
                continue
            write("Esperando respuesta del candidato...")
            try:
                response = runtime.ask(raw)
            except LLMError as error:
                write(f"No se obtuvo una respuesta válida: {error}")
                if not runtime.finished:
                    if isinstance(error, LLMContextLimitError):
                        write("La pregunta se contabilizó y el historial completo se conserva. Puedes acortar la pregunta o usar /salir para guardarlo.")
                    else:
                        write("La pregunta se contabilizó. Puedes formular otra o usar /salir.")
            else:
                write(f"Candidato: {response.text}")
                write(f"Tiempo de respuesta: {response.elapsed_seconds:.2f} s")
                if provider == "unab":
                    write(f"Tokens informados por UNAB IA: entrada={response.input_tokens}, salida={response.output_tokens}.")
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
