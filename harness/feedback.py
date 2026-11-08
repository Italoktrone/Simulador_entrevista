"""Retroalimentación local derivada del análisis validado, sin una segunda llamada."""

from harness.scoring import CRITERIA

LABELS = {"pertinencia": "Pertinencia", "enfoque": "Adecuación metodológica", "claridad": "Claridad", "neutralidad": "Neutralidad"}
GUIDANCE = {
    "pertinencia": "Relaciona la pregunta con una responsabilidad o requisito del cargo.",
    "enfoque": "Precisa qué evidencia buscas y adapta la petición a ese objetivo.",
    "claridad": "Delimita la información solicitada y explicita el antecedente necesario.",
    "neutralidad": "Formula la pregunta sin imponer conclusiones ni juicios sobre el candidato.",
}


def build_feedback(analysis, scores, rubric):
    observed = {k: v for k, v in analysis["criteria"].items() if v["level"] is not None}
    if analysis["applicability"] == "no_evaluable":
        return {"explanation": analysis["reason"], "suggestion": None, "reformulation": None}
    if not observed:
        return {"explanation": "No hay evidencia suficiente para evaluar los criterios. " + analysis["reason"],
                "suggestion": "Aporta el contexto necesario para interpretar la pregunta.", "reformulation": None}
    deficits = [k for k in observed if observed[k]["level"] < 4]
    priority = max(deficits, key=lambda k: ((4 - observed[k]["level"]) * rubric["weights"][k], -CRITERIA.index(k))) if deficits else next(iter(observed))
    item = observed[priority]
    explanation = LABELS[priority] + ": " + item["reason"]
    if scores["visible_level"] is None:
        explanation = "Evaluación parcial, sin nivel global. " + explanation
    elif scores["critical_cap_applied"]:
        explanation += (" El nivel global se limita a En desarrollo porque existe un criterio en nivel 1; el porcentaje se conserva."
                        if rubric["rubric_version"] == "1.1.0" else
                        " No se asigna Destacado porque existe un criterio en nivel 1.")
    fallback = GUIDANCE[priority] if analysis["contract_version"] in {"1.1.0", "1.2.0"} and item["level"] < 4 else "Mantén la precisión y el alcance de esta formulación en la siguiente pregunta."
    if analysis["contract_version"] in {"1.1.0", "1.2.0"} and item["level"] == 3:
        fallback = "Puedes mantener esta pregunta para su objetivo y profundizar en otra intervención si lo necesitas."
    return {"explanation": explanation, "suggestion": item["suggestion"] or fallback,
            "reformulation": item["reformulation"] if item["level"] < 4 else None}


def format_feedback(record):
    titles = {"parcial": "Evaluación parcial, sin nivel global", "no_evaluable": "No evaluable",
              "no_ejecutada": "Evaluación no ejecutada", "no_disponible": "Evaluación no disponible"}
    title = record["visible_level"] if record["status"] == "evaluada" else titles[record["status"]]
    lines = ["Retroalimentación: " + title]
    if record["explanation"].rstrip(".") != title:
        lines.append(record["explanation"])
    if record["suggestion"]:
        lines.append("Sugerencia: " + record["suggestion"])
    if record["reformulation"]:
        lines.append("Reformulación: " + record["reformulation"])
    return "\n".join(lines)
