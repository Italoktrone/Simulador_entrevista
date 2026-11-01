"""Diagnóstico de tokens informados frente a un presupuesto explícito.

No tokeniza texto, predice solicitudes futuras ni modifica una conversación.
Recibe registros ya validados por el módulo de sesiones.
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ContextBudget:
    """Capacidad de comparación; no acredita la capacidad de un modelo."""

    context_size: int
    max_output_tokens: int
    safety_margin: int = 256

    def __post_init__(self) -> None:
        for field in ("context_size", "max_output_tokens", "safety_margin"):
            value = getattr(self, field)
            minimum = 0 if field == "safety_margin" else 1
            if type(value) is not int or value < minimum:
                raise ValueError(f"{field} debe ser un entero mayor o igual que {minimum}.")
        if self.max_output_tokens + self.safety_margin >= self.context_size:
            raise ValueError("La reserva de salida y el margen deben dejar espacio para la entrada.")

    @property
    def input_limit(self) -> int:
        return self.context_size - self.max_output_tokens - self.safety_margin

    def assess(self, input_tokens: int | None) -> dict:
        """Medir una llamada pasada; None significa métrica no disponible."""
        if input_tokens is not None and (type(input_tokens) is not int or input_tokens < 0):
            raise ValueError("input_tokens debe ser un entero no negativo o None.")
        remaining = None if input_tokens is None else self.input_limit - input_tokens
        if remaining is None:
            status = "unknown"
        elif remaining > 0:
            status = "within_budget"
        elif remaining == 0:
            status = "at_limit"
        else:
            status = "over_budget"
        return {
            "reported_input_tokens": input_tokens,
            "remaining_input_tokens": remaining,
            "budget_status": status,
        }


def build_context_report(session: dict, budget: ContextBudget) -> dict:
    """Proyectar métricas de un registro validado, sin copiar sus textos.

    Incluye intentos fallidos y respuestas parciales si tienen métricas.
    Los tokens reutilizados no se restan de la entrada: no son espacio libre.
    El presupuesto lo aporta el llamador; no se infiere del nombre del modelo.
    """
    attempts = []
    for attempt in session["attempts"]:
        response = attempt["response"]
        usage = budget.assess(None if response is None else response["input_tokens"])
        attempts.append({
            "question_number": attempt["question_number"],
            "attempt_status": attempt["status"],
            **usage,
        })
    known = [item["reported_input_tokens"] for item in attempts if item["reported_input_tokens"] is not None]
    return {
        "session_id": session["session_id"],
        "requested_provider": session["requested_provider"],
        "requested_model": session["requested_model"],
        "budget": {**asdict(budget), "input_limit": budget.input_limit},
        "attempts": attempts,
        "peak_reported_input_tokens": max(known, default=None),
        "unknown_attempts": sum(item["budget_status"] == "unknown" for item in attempts),
    }
