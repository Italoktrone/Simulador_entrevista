"""Vistas de texto de la consola: sin llamadas al modelo ni cambios de sesión."""

import textwrap

from harness.feedback import LABELS


WIDTH = 78


def paragraph(text: str, *, indent: str = "", width: int = WIDTH) -> str:
    """Ajusta líneas sin recortar contenido ni unir los párrafos originales."""
    return "\n".join(
        textwrap.fill(line, width=width, initial_indent=indent,
                      subsequent_indent=indent, break_on_hyphens=False)
        if line.strip() else ""
        for line in text.splitlines()
    )


def panel(title: str, body: str, *, major: bool = False) -> str:
    rule = ("=" if major else "-") * WIDTH
    return f"\n{rule}\n{title}\n{rule}\n{body}\n"


def subsection(title: str, body: str) -> str:
    return f"{title}\n\n{body}"


def bullets(items) -> str:
    return "\n".join(textwrap.fill(str(item), width=WIDTH, initial_indent="  - ",
                                 subsequent_indent="    ", break_on_hyphens=False)
                     for item in items)


def format_menu(*, started: bool = False) -> str:
    commands = (
        ("/iniciar", "Continuar la entrevista" if started else "Comenzar la entrevista"),
        ("/cv", "Consultar el currículum del candidato"),
        ("/puesto", "Consultar la oferta y sus requisitos"),
        ("/sesion", "Ver el estado y los contadores"),
        ("/respuestas", "Ver el índice de preguntas enviadas"),
        ("/respuesta N", "Leer la respuesta y evaluación de la pregunta N"),
        ("/ayuda o /menu", "Mostrar este menú"),
        ("/salir", "Finalizar y guardar la sesión"),
    )
    body = "\n".join(f"  {command:<17} {description}" for command, description in commands)
    body += "\n\n" + paragraph(
        "Escribe una pregunta para continuar." if started else
        "Puedes revisar el CV y el puesto antes de escribir /iniciar."
    )
    return panel("MENÚ DE LA ENTREVISTA", body)


def format_provider_menu() -> str:
    return panel("SIMULADOR DE ENTREVISTA | SELECCIÓN DEL MODELO", "\n\n".join((
        subsection("1. MODELO LOCAL | OLLAMA (predeterminado)",
                   "  Procesa la entrevista en este equipo."),
        subsection("2. API | UNAB IA", paragraph(
            "Envía el escenario y la conversación al servicio externo.", indent="  ")),
        "Pulsa Enter para usar el modelo local.",
    )), major=True)


def format_question(question: str, intervention_number: int) -> str:
    return panel(f"INTERVENCIÓN {intervention_number:02d}",
                 subsection("PREGUNTA DEL ENTREVISTADOR", paragraph(question, indent="  ")),
                 major=True)


def format_candidate_response(text: str, *, number: int, maximum: int,
                              elapsed_seconds: float, provider: str,
                              input_tokens=None, output_tokens=None) -> str:
    body = paragraph(text, indent="  ")
    body += f"\n\nTiempo de respuesta: {elapsed_seconds:.2f} s"
    if provider == "unab":
        known = lambda value: "no informado" if value is None else str(value)
        body += (f"\nTokens informados por UNAB IA: entrada={known(input_tokens)}, "
                 f"salida={known(output_tokens)}.")
    return panel(f"RESPUESTA DEL CANDIDATO | PREGUNTA {number:02d}/{maximum:02d}", body)


def format_evaluation(record: dict) -> str:
    """Presenta niveles ya calculados; no vuelve a puntuar la pregunta."""
    titles = {"parcial": "Evaluación parcial, sin nivel global", "no_evaluable": "No evaluable",
              "no_ejecutada": "Evaluación no ejecutada", "no_disponible": "Evaluación no disponible"}
    number = record["question_number"]
    heading = (f"EVALUACIÓN DE LA PREGUNTA {number:02d} | PROVISIONAL" if number is not None
               else "EVALUACIÓN DE LA INTERVENCIÓN | PROVISIONAL")
    title = record["visible_level"] if record["status"] == "evaluada" else titles[record["status"]]
    sections = [paragraph("Resultado: " + title)]
    analysis = record.get("analysis")
    if analysis is not None and analysis["applicability"] != "no_evaluable":
        levels = []
        for key, label in LABELS.items():
            level = analysis["criteria"][key]["level"]
            value = f"{level}/4" if level is not None else "Sin evidencia suficiente"
            levels.append(f"  {label}: {value}")
        sections.append(subsection("CRITERIOS", "\n".join(levels)))
    if record["explanation"].rstrip(".") != title:
        sections.append(subsection("RETROALIMENTACIÓN", paragraph(record["explanation"], indent="  ")))
    if record["suggestion"]:
        sections.append(subsection("SUGERENCIA", paragraph(record["suggestion"], indent="  ")))
    if record["reformulation"]:
        sections.append(subsection("POSIBLE REFORMULACIÓN", paragraph(record["reformulation"], indent="  ")))
    sections.append(f"Tiempo adicional de evaluación: {record['elapsed_seconds']:.2f} s")
    return panel(heading, "\n\n".join(sections))


ATTEMPT_STATUS = {"completed": "Respuesta completa", "error": "Sin respuesta válida",
                  "incomplete": "Respuesta incompleta", "interrupted": "Interrumpida",
                  "pending": "En espera"}


def format_response_index(session: dict) -> str:
    attempts = session["attempts"]
    if not attempts:
        body = "Todavía no se han enviado preguntas al candidato."
    else:
        rows = [f"Pregunta {item['question_number']:02d} | {ATTEMPT_STATUS[item['status']]}\n"
                + paragraph(item["question"], indent="  ") for item in attempts]
        body = "\n\n".join(rows)
        body += "\n\nEscribe /respuesta N para consultar una entrada; por ejemplo, /respuesta 1."
    return panel("ÍNDICE DE PREGUNTAS Y RESPUESTAS", body)


def format_saved_response(session: dict, number: int) -> str:
    """Consulta solo respuestas completas y evaluaciones de la misma pregunta."""
    attempt = next((item for item in session["attempts"] if item["question_number"] == number), None)
    if attempt is None:
        return panel("CONSULTA DE RESPUESTAS", "No existe esa pregunta. Usa /respuestas para ver el índice.")
    result = panel(f"CONSULTA | PREGUNTA {number:02d}",
                   subsection("PREGUNTA DEL ENTREVISTADOR", paragraph(attempt["question"], indent="  ")),
                   major=True)
    response = attempt["response"]
    if attempt["status"] == "completed" and response is not None:
        result += format_candidate_response(
            response["text"], number=number, maximum=session["configuration"]["max_questions"],
            elapsed_seconds=response["elapsed_seconds"], provider=response["provider"],
            input_tokens=response.get("input_tokens"), output_tokens=response.get("output_tokens"))
    else:
        result += panel("ESTADO DE LA RESPUESTA", ATTEMPT_STATUS[attempt["status"]]
                        + ". No hay una respuesta completa disponible para consultar.")
    evaluation = next((item for item in session.get("evaluations", [])
                       if item["question_number"] == number), None)
    if evaluation is not None:
        result += format_evaluation(evaluation)
    return result
