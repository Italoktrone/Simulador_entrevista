"""Evaluación independiente y acotada; nunca recibe la respuesta del turno actual."""

from copy import deepcopy
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from harness.evaluation_contract import (RECORD_VERSION, EvaluationContractError,
                                         llm_evaluation_schema, evaluation_generation_schema,
                                         complete_evaluation, validate_record)
from harness.evaluator_few_shot import load_evaluator_examples, disabled_few_shot, canonical
from harness.feedback import build_feedback
from harness.json_loader import JsonTextError, parse_json_text
from harness.llm.client import LLMResponse
from harness.llm.config import OllamaSettings
from harness.llm.factory import create_client
from harness.llm.ollama_client import OllamaClient
from harness.scoring import CRITERIA, load_rubric, score_criteria, validate_rubric
from harness.session_state import describe_issue

PROMPT_PATH = Path(__file__).resolve().parents[1] / "agent/evaluator.md"


def create_evaluation_client(environ=None, *, rubric=None, model=None, transport=None):
    """Cliente propio con presupuesto propio, sin cargar claves desde archivos.

    La espera HTTP limita inactividad de lectura, no un plazo absoluto de pared.
    No se reintenta transporte ni se cambia de proveedor automáticamente.
    """
    rubric = load_rubric() if rubric is None else validate_rubric(rubric)
    values = os.environ if environ is None else environ
    provider = values.get("LLM_PROVIDER", "ollama")
    common = {"max_output_tokens": rubric["max_output_tokens"],
              "read_timeout_seconds": rubric["read_timeout_seconds"], "connection_retries": 0}
    if provider == "ollama":
        settings = OllamaSettings(model=model or values.get("OLLAMA_MODEL", OllamaSettings().model), temperature=0, **common)
        return OllamaClient(settings, transport=transport, output_schema=evaluation_generation_schema())
    # La fábrica comprueba consentimiento externo y credenciales. Crear no hace HTTP.
    return create_client(values, model=model, transport=transport, **common)


def select_evaluation_context(attempts, rubric):
    limit = rubric["context_characters"]
    result = []
    for turn in [a for a in attempts if a["status"] == "completed"][-rubric["context_pairs"]:]:
        question, answer = turn["question"], turn["response"]["text"]
        result.append({"turn_number": turn["question_number"], "question": question[:limit], "answer": answer[:limit],
                       "truncated": len(question) > limit or len(answer) > limit})
    return result


def classification_hint(classification):
    if classification is None:
        return None
    labels = classification.get("classification")
    return {"evaluability": classification.get("evaluability"), "technical_error": classification.get("technical_error"),
            "labels": None if labels is None else {k: deepcopy(labels.get(k)) for k in ("approaches", "forms", "attributes", "certainty")}}


class QuestionEvaluator:
    def __init__(self, client, *, rubric=None, instructions=None, few_shot=True):
        if not callable(getattr(client, "generate", None)):
            raise ValueError("El evaluador requiere un cliente LLM.")
        self._rubric = load_rubric() if rubric is None else validate_rubric(rubric)
        if type(few_shot) is not bool:
            raise ValueError("few_shot debe ser booleano.")
        self._examples, self._examples_job = "", None
        self._few_shot = disabled_few_shot()
        if few_shot and self._rubric["rubric_version"] == "1.1.0":
            self._examples, self._few_shot, self._examples_job = load_evaluator_examples(self._rubric)
        elif few_shot:
            self._few_shot = disabled_few_shot("rubric_incompatible")
        instructions = PROMPT_PATH.read_text(encoding="utf-8") if instructions is None else instructions
        if not isinstance(instructions, str) or not instructions.strip():
            raise ValueError("Faltan instrucciones de evaluación.")
        self._system = instructions + "\nRUBRICA:\n" + json.dumps(self._rubric["descriptors"], ensure_ascii=False, separators=(",", ":")) + "\nESQUEMA:\n" + json.dumps(llm_evaluation_schema(), ensure_ascii=False, separators=(",", ":"))
        self._prompt_sha256 = hashlib.sha256(self._system.encode("utf-8")).hexdigest()
        self._client = client

    @property
    def rubric(self):
        return deepcopy(self._rubric)

    def make_request(self, *, question, configuration, job, attempts, classification=None, competency=None, objective=None):
        if not isinstance(question, str):
            raise ValueError("La intervención debe ser texto.")
        if any(v is not None and (not isinstance(v, str) or not v.strip()) for v in (competency, objective)):
            raise ValueError("Competencia y objetivo deben ser texto o null.")
        return deepcopy({"question": question, "configuration": configuration, "job": job,
                         "competency": competency, "objective": objective,
                         "context_turns": select_evaluation_context(attempts, self._rubric),
                         "classification": classification_hint(classification)})

    def _record(self, request, session_id, intervention_id, question_number, status, reason_code):
        system, metadata = self._prompt_for(request)
        return {"evaluation_version": RECORD_VERSION, "evaluation_id": str(uuid4()), "session_id": session_id,
                "few_shot": metadata,
                "method": "unavailable",
                "intervention_id": intervention_id, "question_number": question_number, "status": status,
                "reason_code": reason_code, "request": deepcopy(request), "analysis": None,
                "weighted_score": None, "normalized_score": None, "visible_level": None,
                "critical_cap_applied": False, "explanation": "Evaluación no disponible.", "suggestion": None,
                "reformulation": None, "discrepancies": [], "attempts": [], "elapsed_seconds": 0,
                "prompt_sha256": hashlib.sha256(system.encode("utf-8")).hexdigest()}

    def _prompt_for(self, request):
        if self._few_shot["enabled"] and canonical(request["job"]) != self._examples_job:
            return self._system, disabled_few_shot("job_incompatible")
        return self._system + self._examples, deepcopy(self._few_shot)

    def skipped(self, request, *, session_id, intervention_id, question_number=None, action):
        status = "no_evaluable" if action == "no_evaluable" else "no_ejecutada"
        record = self._record(request, session_id, intervention_id, question_number, status, action)
        record["method"] = "policy"
        record["explanation"] = {
            "no_evaluable": "La política identificó una intervención sin pregunta de entrevista; no se asigna puntuación.",
            "aclarar": "La política solicitó una aclaración y no envió la pregunta al candidato; no se ejecutó la evaluación.",
            "error_tecnico": "El clasificador tuvo un fallo técnico y no envió la pregunta al candidato; no se asigna puntuación.",
            "candidate_error": "No se obtuvo una respuesta completa del candidato; la evaluación no se ejecutó.",
            "interrupted": "La evaluación fue interrumpida; se conserva la respuesta del candidato.",
        }.get(action, "La evaluación no se ejecutó; no se asigna puntuación.")
        return validate_record(record, self._rubric)

    def unavailable(self, request, *, session_id, intervention_id, question_number=None):
        record = self._record(request, session_id, intervention_id, question_number, "no_disponible", "error_evaluador")
        return validate_record(record, self._rubric)

    def evaluate(self, request, *, session_id, intervention_id, question_number=None):
        started = perf_counter()
        record = self._record(request, session_id, intervention_id, question_number, "no_disponible", "sin_resultado")
        system, _ = self._prompt_for(request)
        payload = json.dumps({"input": deepcopy(request)}, ensure_ascii=False, allow_nan=False)
        generation_schema = evaluation_generation_schema(
            allowed_context_turn_numbers=[t["turn_number"] for t in request["context_turns"]],
            classification_available=request["classification"] is not None)
        def finish():
            if record["status"] == "no_disponible" and record["analysis"] is None:
                record["explanation"] = {
                    "timeout": "El modelo superó el tiempo de espera; no se asigna una valoración.",
                    "json_invalido": "El modelo no devolvió JSON válido tras la única reparación permitida.",
                    "salida_incompleta": "El modelo no terminó la evaluación; no se asigna una valoración.",
                }.get(record["reason_code"], "No se obtuvo una evaluación válida; la respuesta del candidato se conserva.")
            record["elapsed_seconds"] = perf_counter() - started
            return validate_record(record, self._rubric)
        for number in (1, 2):
            repair = "" if number == 1 else "\nREPARACION: La salida previa incumplió " + record["reason_code"] + ". Devuelve un JSON nuevo desde los datos originales. Esta es la única reparación."
            if number == 2 and record["attempts"][-1]["validation"] is not None:
                repair += " Diagnóstico controlado: " + json.dumps(record["attempts"][-1]["validation"], ensure_ascii=False)
            audit = {"number": number, "status": "error_proveedor", "error_code": None,
                     "validation": None, "input_tokens": None, "output_tokens": None, "elapsed_seconds": None, "provider": None, "model": None}
            record["attempts"].append(audit)
            attempt_started = perf_counter()
            try:
                messages = [{"role": "system", "content": system + repair}, {"role": "user", "content": payload}]
                if isinstance(self._client, OllamaClient):
                    response = self._client.generate(messages, output_schema=generation_schema)
                else:
                    response = self._client.generate(messages)
                if not isinstance(response, LLMResponse):
                    raise ValueError("respuesta_invalida")
            except Exception as error:
                audit["error_code"] = describe_issue(error)["code"]
                audit["elapsed_seconds"] = perf_counter() - attempt_started
                record["reason_code"] = audit["error_code"]
                return finish()
            for key in ("input_tokens", "output_tokens"):
                value = getattr(response, key)
                audit[key] = value if type(value) is int and value >= 0 else None
            audit["elapsed_seconds"] = response.elapsed_seconds if type(response.elapsed_seconds) in (int, float) and isfinite(response.elapsed_seconds) and response.elapsed_seconds >= 0 else None
            audit["provider"], audit["model"] = response.provider, response.model
            if response.finish_reason not in (None, "stop", "completed"):
                audit.update(status="salida_incompleta", error_code="salida_incompleta")
                record["reason_code"] = "salida_incompleta"
                return finish()
            try:
                draft = parse_json_text(response.text)
            except JsonTextError:
                audit.update(status="json_invalido", error_code="json_invalido")
                record["reason_code"] = "json_invalido"
                continue
            try:
                analysis = complete_evaluation(draft, request)
            except EvaluationContractError as error:
                audit.update(status="contrato_invalido", error_code=error.code, validation=error.audit())
                record["reason_code"] = error.code
                continue
            scores = score_criteria({k: analysis["criteria"][k]["level"] for k in CRITERIA}, self._rubric)
            status = "no_evaluable" if analysis["applicability"] == "no_evaluable" else "evaluada" if scores["visible_level"] else "parcial" if any(c["level"] is not None for c in analysis["criteria"].values()) else "no_disponible"
            audit.update(status="validada", error_code=None)
            record.update(analysis=analysis, method="llm_python", status=status, reason_code="evidencia_suficiente" if status == "evaluada" else "fuera_de_rubrica" if status == "no_evaluable" else "informacion_insuficiente", **scores)
            record.update(build_feedback(analysis, scores, self._rubric))
            hint = request["classification"]
            for item in analysis["discrepancies"]:
                original = hint["evaluability"] if item["field"] == "evaluability" else None if hint["labels"] is None else hint["labels"][item["field"]]
                record["discrepancies"].append({**item, "original": deepcopy(original), "review_status": "pending"})
            return finish()
        return finish()
