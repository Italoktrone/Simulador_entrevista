"""Revisar el uso registrado sin consultar al modelo ni escribir archivos."""

import argparse
from pathlib import Path

from harness.context_budget import ContextBudget, build_context_report
from harness.llm.config import OllamaSettings
from harness.session_log import SessionLogError, load_session


def format_context_report(report: dict) -> str:
    budget = report["budget"]
    lines = [
        "DIAGNÓSTICO DEL CONTEXTO REGISTRADO",
        f"Sesión: {report['session_id']}",
        f"Proveedor solicitado: {report['requested_provider'] or 'no registrado'}",
        f"Modelo solicitado: {report['requested_model'] or 'no registrado'}",
        "Parámetros de comparación elegidos; no son metadatos históricos del archivo:",
        f"  Capacidad: {budget['context_size']} tokens",
        f"  Reserva de salida: {budget['max_output_tokens']} tokens",
        f"  Margen adicional: {budget['safety_margin']} tokens",
        f"  Límite de entrada con reservas: {budget['input_limit']} tokens",
    ]
    labels = {
        "within_budget": "dentro del presupuesto",
        "at_limit": "en el límite del presupuesto",
        "over_budget": "sobre el presupuesto",
    }
    for attempt in report["attempts"]:
        prefix = f"Pregunta {attempt['question_number']} ({attempt['attempt_status']})"
        if attempt["budget_status"] == "unknown":
            lines.append(f"{prefix}: entrada no informada; margen desconocido.")
        else:
            lines.append(
                f"{prefix}: entrada informada={attempt['reported_input_tokens']}; "
                f"margen respecto al límite={attempt['remaining_input_tokens']}; "
                f"{labels[attempt['budget_status']]} (tokens)."
            )
    if not report["attempts"]:
        lines.append("Sin intentos registrados.")
    peak = report["peak_reported_input_tokens"]
    lines.append(f"Mayor entrada informada: {peak if peak is not None else 'no disponible'}")
    lines.append(f"Intentos sin métrica de entrada: {report['unknown_attempts']}")
    lines.append("La entrada incluye los tokens reutilizados; la caché no se resta del contexto.")
    lines.append("Son métricas de llamadas pasadas; no garantizan que la próxima pregunta quepa ni que el servidor conservara todo el texto enviado.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    defaults = OllamaSettings()
    parser = argparse.ArgumentParser(description="Comparar métricas de una sesión JSON con un presupuesto de contexto.")
    parser.add_argument("session_path", type=Path, help="Archivo de sesión cerrada")
    parser.add_argument("--context-size", type=int, default=defaults.context_size)
    parser.add_argument("--max-output-tokens", type=int, default=defaults.max_output_tokens)
    parser.add_argument("--safety-margin", type=int, default=256)
    args = parser.parse_args(argv)
    try:
        budget = ContextBudget(args.context_size, args.max_output_tokens, args.safety_margin)
        session = load_session(args.session_path)
        report = build_context_report(session, budget)
    except (SessionLogError, ValueError) as error:
        print(f"No se pudo revisar el contexto: {error}")
        return 1
    print(format_context_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
