"""Mostrar preguntas y criterios humanos, sin consultar al modelo ni evaluar."""

import argparse
import json
from pathlib import Path

from harness.reference_cases import DEFAULT_SUITE_PATH, load_reference_suite


def format_reference_suite(suite) -> str:
    data = suite.to_dict()
    cases = suite.resolved_cases()
    lines = [
        "REFERENCIAS DE CONSISTENCIA - REVISIÓN HUMANA",
        f"Conjunto: {suite.suite_id}. Versión: {data['suite_version']}.",
        f"Candidato: {data['candidate_id']}. Fecha del escenario: {data['scenario_reference_date']}.",
        f"Casos: {len(cases)}. Entradas de pregunta: {sum(len(c['steps']) for c in cases)}.",
        "Cada caso usará una sesión nueva; sus pasos compartirán esa sesión.",
    ]
    for case in cases:
        lines.extend(["", f"{case['case_id']} — {case['title']}"])
        facts = {fact["fact_id"]: fact for fact in case["reference_facts"]}
        for step in case["steps"]:
            lines.append(f"  Paso {step['step_number']}: {step['question']}")
            for identifier in step["expected_fact_ids"]:
                fact = facts[identifier]
                kind = "contenido esperado" if fact["criterion"] == "required_content" else "límite de consistencia"
                value = json.dumps(fact["value"], ensure_ascii=False, allow_nan=False)
                lines.append(f"    {fact['label']} ({kind}): {value}")
        lines.extend(f"  Revisar: {note}" for note in case["review_notes"])
    lines.extend(["", "Casos preparados. Ejecuciones y revisión de respuestas pendientes.",
                  "Referencias de desarrollo: no son una prueba independiente ni una puntuación educativa.",
                  "No se consultó un modelo y no se evaluaron respuestas."])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Comprobar los casos de referencia del candidato.")
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE_PATH)
    args = parser.parse_args(argv)
    try:
        suite = load_reference_suite(args.suite)
    except ValueError as error:
        print(f"No se pudieron preparar los casos: {error}")
        return 1
    print(format_reference_suite(suite))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
