"""Relaciones del registro educativo con la entrevista y el contexto anterior."""

from harness.evaluation_contract import validate_record
from harness.question_evaluator import classification_hint, select_evaluation_context
from harness.scoring import validate_rubric


def validate_evaluations(data):
    if data["session_version"] != "1.3.0":
        return
    rubric = validate_rubric(data["evaluation_policy"])
    events = data["interventions"]
    records = data["evaluations"]
    if len(records) != len(events):
        raise ValueError("Cada intervención requiere un resultado de evaluación o un motivo de omisión.")
    seen = set()
    for event, record in zip(events, records):
        validate_record(record, rubric)
        if record["evaluation_id"] in seen:
            raise ValueError("Identificador de evaluación repetido.")
        seen.add(record["evaluation_id"])
        if (record["session_id"] != data["session_id"] or record["intervention_id"] != event["intervention_id"]
                or record["question_number"] != event["candidate_question_number"]):
            raise ValueError("Evaluación vinculada a otra intervención o pregunta.")
        request = record["request"]
        if request["question"] != event["text"] or request["configuration"] != data["configuration"]:
            raise ValueError("La pregunta o configuración evaluadas no corresponden a la sesión.")
        if request["job"]["job_id"] != data["job_id"]:
            raise ValueError("El puesto evaluado no corresponde a la sesión.")
        previous = data["attempts"][:event["before_question_number"] - 1]
        if request["context_turns"] != select_evaluation_context(previous, rubric):
            raise ValueError("La evaluación debe usar exclusivamente fragmentos de turnos completos anteriores.")
        report = event["classification"]
        expected_hint = None if report is None else classification_hint(report["result"])
        if request["classification"] != expected_hint:
            raise ValueError("La clasificación auxiliar no coincide con el registro original.")
        policy = event["policy"]
        if policy is not None and policy["action"] != "responder":
            status = "no_evaluable" if policy["action"] == "no_evaluable" else "no_ejecutada"
            if record["status"] != status or record["analysis"] is not None or record["attempts"]:
                raise ValueError("Una intervención no enviada no puede contener una evaluación ejecutada.")
        if event["status"] != "completed" and record["analysis"] is not None:
            raise ValueError("No puede haber análisis sin respuesta completa del candidato.")
