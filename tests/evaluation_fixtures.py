"""Datos sintéticos; no son valoraciones humanas ni llamadas a un proveedor."""

from copy import deepcopy
import json

from harness.scoring import CRITERIA
from harness.evaluation_contract import EVALUATION_VERSION
from harness.llm.client import LLMResponse


def draft(question="¿Has utilizado Git?", levels=None):
    levels = dict.fromkeys(CRITERIA, 3) if levels is None else levels
    return {"contract_version": "1.0.0", "applicability": "evaluable", "reason": "Pregunta de entrevista.",
            "criteria": {k: {"level": levels[k], "evidence": [] if levels[k] is None else [
                {"source": "question", "turn_number": None, "quote": question[:100]}],
                "reason": "Falta contexto para valorar el criterio." if levels[k] is None else "La formulación permite obtener información pertinente.",
                "suggestion": None if levels[k] in (None, 4) else "Precisa el objetivo de la pregunta.",
                "reformulation": None} for k in CRITERIA}, "discrepancies": []}


def compact(analysis):
    if analysis.get("contract_version") != "1.0.0":
        return deepcopy(analysis)
    result = {"contract_version": EVALUATION_VERSION, "applicability": analysis["applicability"], "reason": analysis["reason"],
              "evidence": [], "criteria": {}, "feedback": {"criterion": None, "suggestion": None, "reformulation": None},
              "discrepancies": deepcopy(analysis["discrepancies"])}
    for key, item in analysis["criteria"].items():
        ids = []
        for evidence in item["evidence"]:
            if evidence not in result["evidence"]:
                result["evidence"].append(deepcopy(evidence))
            ids.append(result["evidence"].index(evidence))
        result["criteria"][key] = {"level": item["level"], "evidence_ids": ids, "reason": item["reason"]}
    deficits = [k for k in CRITERIA if analysis["criteria"][k]["level"] in (1, 2, 3)]
    if deficits:
        key = max(deficits, key=lambda k: (4-analysis["criteria"][k]["level"])*dict(zip(CRITERIA,[35,30,20,15]))[k])
        item = analysis["criteria"][key]
        result["feedback"] = {"criterion": key, "suggestion": item["suggestion"], "reformulation": item["reformulation"]}
    return result


class EvaluationClient:
    def __init__(self, outcomes=None, events=None):
        self.outcomes = list(outcomes or [])
        self.requests = []
        self.events = [] if events is None else events

    def generate(self, messages):
        self.requests.append(deepcopy(messages))
        self.events.append("evaluation")
        request = json.loads(messages[1]["content"])["input"]
        value = self.outcomes.pop(0) if self.outcomes else draft(request["question"])
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, LLMResponse):
            return value
        return LLMResponse(value if isinstance(value, str) else json.dumps(compact(value)), "modelo-simulado", "ollama", 0.1,
                           input_tokens=100, output_tokens=50, finish_reason="stop")
