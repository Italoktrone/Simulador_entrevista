"""Reglas locales conservadoras: resultado validado o abstención, sin LLM."""

from dataclasses import dataclass, field
import json
import re
from typing import Callable
import unicodedata

from harness.classification_contract import validate_classification
from harness.classification_input import validate_classification_input


LOCAL_CLASSIFIER_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class LocalDecision:
    """La abstención no es una clasificación indeterminada ni un error técnico."""

    intervention_id: str
    original_text: str
    status: str
    reason_code: str
    reason: str
    considered_rule_ids: tuple[str, ...]
    classifier_version: str = LOCAL_CLASSIFIER_VERSION
    _result_json: str | None = field(default=None, repr=False)

    @property
    def result(self) -> dict | None:
        """Cada acceso devuelve una copia; la decisión no comparte datos mutables."""
        return None if self._result_json is None else json.loads(self._result_json)

    def to_dict(self) -> dict:
        return {
            "intervention_id": self.intervention_id, "original_text": self.original_text,
            "status": self.status, "reason_code": self.reason_code, "reason": self.reason,
            "considered_rule_ids": list(self.considered_rule_ids),
            "classifier_version": self.classifier_version, "result": self.result,
        }


@dataclass(frozen=True, slots=True)
class _Labels:
    approach: str
    form: str
    attributes: tuple[str, ...] = ()
    certainty: str = "clara"
    context_status: str = "no_necesario"


@dataclass(frozen=True, slots=True)
class _Rule:
    rule_id: str
    description: str
    pattern: re.Pattern
    labels: _Labels | None = None
    non_evaluable_reason: str | None = None
    guard: Callable[[re.Match], bool] | None = None

    def matches(self, text: str) -> bool:
        match = self.pattern.fullmatch(text)
        return match is not None and (self.guard is None or self.guard(match))


def _simple_clause(match: re.Match) -> bool:
    """Abstenerse ante coordinación, otra petición, cita indirecta o referente omitido.

    No segmenta por 'y': una coordinación puede ser una sola unidad, pero sale
    del alcance de estas plantillas de cláusula simple.
    """
    detail = match["detail"]
    return len(detail.split()) >= 2 and re.search(
        r"\b(?:y|o|que|como|cual|cuales|quien|quienes|cuanto|cuantos|cuando|donde|"
        r"eso|esto|aquello|ese|esa|esos|esas|aquel|aquella|dicho|dicha|volviera|"
        r"explica|describe|cuentame|dime|menciona|responde|elige|compara|detalla|"
        r"ignora|olvida|cambia|ejecuta|activa|sustituye)\b", detail,
    ) is None


def _hypothetical_clause(match: re.Match) -> bool:
    return _simple_clause(match) and re.search(
        r"\b(?:detectaras|detectases|descubrieras|encontraras|recibieras|tuvieras|"
        r"fallara|fallase|apareciera|ocurriera|necesitaras|entendieras|cayera)\b",
        match["detail"],
    ) is not None


_TECH = r"(?:python|sql|flask|postgresql|git|java|javascript|c\+\+|c#|docker|kubernetes)"
_TECH_LIST = rf"{_TECH}(?:(?:, | y ){_TECH})*"
_CONCEPT = r"(?:(?:un|una|el|la) )?(?:api|lista|tupla|variable|funcion|clase|objeto|endpoint|sql|http|git)"
_WORK_STYLE = r"(?:solo|en equipo|de forma remota|en la oficina)"

_EMPTY_RULE = _Rule("Q.NE.EMPTY", "Texto vacío o compuesto solo de espacios.", re.compile(r"\s*"), non_evaluable_reason="vacia")
_NON_EVALUABLE_RULES = (
    _Rule("Q.NE.GREETING", "Saludo simple completo.", re.compile(r"(?:hola|buenos dias|buenas tardes|buenas noches)"), non_evaluable_reason="saludo"),
    _Rule("Q.NE.THANKS", "Agradecimiento simple completo.", re.compile(r"(?:gracias|muchas gracias|gracias por (?:tu|la) respuesta)"), non_evaluable_reason="agradecimiento"),
    _Rule("Q.NE.ACK", "Acuse de recibo simple completo.", re.compile(r"(?:entiendo|entendido|de acuerdo|ok)"), non_evaluable_reason="acuse"),
    _Rule("Q.NE.TRANSITION", "Transición simple sin petición de contenido.", re.compile(r"(?:continuemos|sigamos|pasemos a la siguiente pregunta)"), non_evaluable_reason="transicion"),
)
_CORE_RULES = (
    _Rule("Q.BEHAVIOR.EPISODE", "Petición explícita de una ocasión pasada con actuación, sin otra petición.", re.compile(
        r"(?:cuentame|describe|relata|(?:podrias|puedes) (?:contarme|describirme|relatarme)) "
        r"(?:una|alguna) (?:ocasion|situacion|experiencia) en (?:la )?que "
        r"(?P<detail>(?:resolviste|corregiste|pediste|aclaraste|comunicaste|aprendiste|colaboraste)\b.+)"
    ), _Labels("conductual", "abierta"), guard=_simple_clause),
    _Rule("Q.SITUATION.HYPOTHETICAL", "Actuación solicitada ante una condición hipotética explícita y autocontenida.", re.compile(
        r"(?:que harias|como actuarias|que medidas tomarias) si (?P<detail>.+)"
    ), _Labels("situacional", "abierta"), guard=_hypothetical_clause),
    _Rule("Q.FACT.TECH_CONFIRMATION", "Confirmación de conocimientos o experiencia declarada con tecnologías reconocidas.", re.compile(
        rf"(?:has (?:utilizado|usado|trabajado con)|conoces|tienes experiencia (?:con|en)) {_TECH_LIST}"
    ), _Labels("factual_tecnico", "cerrada")),
    _Rule("Q.FACT.INVENTORY", "Inventario de tecnologías, herramientas o lenguajes en un proyecto o práctica.", re.compile(
        r"(?:que|cuales) (?:tecnologias|herramientas|lenguajes) (?:utilizaste|usaste) "
        r"(?:en|durante) (?:tu|el) (?:ultimo |anterior )?(?:proyecto|practica)(?: academico| profesional)?"
    ), _Labels("factual_tecnico", "cerrada")),
    _Rule("Q.FACT.DEFINITION", "Definición o funcionamiento de un concepto reconocido, sin episodio o escenario.", re.compile(
        rf"(?:que es|como funciona|explica (?:que es|como funciona)|podrias explicar (?:que es|como funciona)) {_CONCEPT}(?: en {_TECH})?"
    ), _Labels("factual_tecnico", "abierta")),
    _Rule("Q.FACT.COMPARISON", "Comparación de dos conceptos técnicos; su 'y' no crea dos preguntas.", re.compile(
        rf"(?:explica la diferencia entre|cual es la diferencia entre|compara) {_CONCEPT} y {_CONCEPT}(?: en {_TECH})?"
    ), _Labels("factual_tecnico", "abierta")),
    _Rule("Q.FACT.YEAR", "Solicitud de fecha o año de formación o titulación.", re.compile(
        r"(?:en que ano|cuando) (?:te titulaste|terminaste tus estudios)"
    ), _Labels("factual_tecnico", "cerrada")),
    _Rule("Q.OTHER.WORK_PREFERENCE", "Preferencia laboral simple, sin anticipar la respuesta.", re.compile(
        rf"prefieres trabajar {_WORK_STYLE}"
    ), _Labels("otro", "cerrada")),
    _Rule("Q.OTHER.EXPLICIT_OPTIONS", "Elección de preferencia laboral entre dos alternativas explícitas diferentes.", re.compile(
        rf"prefieres trabajar (?P<first>{_WORK_STYLE}) o (?P<second>{_WORK_STYLE})"
    ), _Labels("otro", "opcion_multiple"), guard=lambda match: match["first"] != match["second"]),
    _Rule("Q.SUGGESTIVE.WORK_PREFERENCE", "Preferencia laboral anticipada mediante 'seguro que' y solicitud de confirmación.", re.compile(
        rf"seguro que prefieres trabajar {_WORK_STYLE},? (?:verdad|cierto)"
    ), _Labels("otro", "cerrada", ("sugestiva",))),
    _Rule("Q.CONTEXT.MISSING_ACTION", "Petición de acción posterior sin antecedente disponible: enfoque indeterminado.", re.compile(
        r"que (?:hiciste|ocurrio|paso) despues"
    ), _Labels("indeterminado", "abierta", certainty="indeterminada", context_status="insuficiente")),
)
_SCOPE_PREFIX = re.compile(r"centrate solo en (?:tu|tus) (?:practica|estudios|tareas|proyectos): ?(?P<body>.+)")
_YEAR_PREFIX = re.compile(r"responde (?:solo|unicamente) con el ano: ?(?P<body>.+)")
_PREFIX_DEFINITIONS = (
    ("Q.DIRECTIVE.SCOPE", "Delimitación explícita de ámbito; requiere una petición reconocida después de los dos puntos."),
    ("Q.DIRECTIVE.YEAR", "Formato exclusivamente de año; solo se aplica con Q.FACT.YEAR."),
)


def local_rule_definitions() -> list[dict[str, str]]:
    """Catálogo de reglas aplicadas; las condiciones detalladas están en la guía."""
    return [
        {"rule_id": rule.rule_id, "description": rule.description}
        for rule in (_EMPTY_RULE, *_NON_EVALUABLE_RULES, *_CORE_RULES)
    ] + [{"rule_id": key, "description": description} for key, description in _PREFIX_DEFINITIONS]


def _normalize(text: str) -> str:
    normalized = "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))
    normalized = normalized.replace("¿", "").replace("¡", "")
    return " ".join(normalized.split()).strip(" ?!.…")


def _accepted(intervention_id: str, text: str, rule: _Rule, rule_ids: tuple[str, ...], considered: tuple[str, ...], allowed_ids: tuple[int, ...]) -> LocalDecision:
    classification = None
    units = []
    directive = any(rule_id.startswith("Q.DIRECTIVE.") for rule_id in rule_ids)
    rationale = rule.description + (" Se aplica además una delimitación explícita de ámbito o formato." if directive else "")
    if rule.labels is not None:
        tags = rule.labels
        classification = {
            "approaches": [tags.approach], "main_approach": tags.approach,
            "secondary_approaches": [], "main_approach_reason": None,
            "forms": [tags.form], "main_form": tags.form, "main_form_reason": None,
            "attributes": list(tags.attributes) + (["directiva"] if directive else []),
            "certainty": tags.certainty, "rationale": rationale,
        }
        start, end = len(text) - len(text.lstrip()), len(text.rstrip())
        units = [{
            "unit_id": "u1", "text": text[start:end], "source_start": start, "source_end": end,
            "classification": classification, "method": "reglas", "rule_ids": list(rule_ids),
            "context_status": tags.context_status, "followup_of": None, "depends_on": None,
        }]
    result = validate_classification({
        "contract_version": "1.0.0", "intervention_id": intervention_id, "original_text": text,
        "evaluability": "no_evaluable" if rule.non_evaluable_reason else "evaluable",
        "non_evaluable_reason": rule.non_evaluable_reason, "classification": classification,
        "units": units, "context_turn_ids": [], "method": "reglas", "rule_ids": list(rule_ids),
        "technical_error": None, "validation_status": "pendiente", "rationale": rationale,
    }, expected_intervention_id=intervention_id, expected_text=text, allowed_context_turn_ids=allowed_ids)
    return LocalDecision(intervention_id, text, "clasificada", "regla_aplicada", rationale,
                         considered, _result_json=json.dumps(result, ensure_ascii=False, allow_nan=False))


def classify_local(
    text: str, *, intervention_id: str, configuration: dict | None = None,
    context_turns: list[dict] | tuple[dict, ...] | None = None, competency: str | None = None,
) -> LocalDecision:
    """Clasificar una petición simple o abstenerse sin llamar al LLM.

    El contexto es del llamador y se valida, pero este bloque aún no interpreta
    episodios ni segmenta compuestas. Las preferencias nunca fuerzan etiquetas.
    """
    turns = () if context_turns is None else context_turns
    allowed_ids = validate_classification_input(intervention_id, text, configuration, turns, competency)

    def abstain(code: str, reason: str, considered: tuple[str, ...] = ()) -> LocalDecision:
        return LocalDecision(intervention_id, text, "abstencion", code, reason, considered)

    if _EMPTY_RULE.matches(text):
        return _accepted(intervention_id, text, _EMPTY_RULE, (_EMPTY_RULE.rule_id,), (_EMPTY_RULE.rule_id,), allowed_ids)
    normalized = _normalize(text)
    terminal_ids = (_EMPTY_RULE.rule_id, *(rule.rule_id for rule in _NON_EVALUABLE_RULES))
    for rule in _NON_EVALUABLE_RULES:
        if rule.matches(normalized):
            return _accepted(intervention_id, text, rule, (rule.rule_id,), terminal_ids, allowed_ids)
    prefix_ids = ()
    body = normalized
    for pattern, rule_id in ((_SCOPE_PREFIX, "Q.DIRECTIVE.SCOPE"), (_YEAR_PREFIX, "Q.DIRECTIVE.YEAR")):
        match = pattern.fullmatch(normalized)
        if match:
            body, prefix_ids = match["body"], (rule_id,)
            break
    if (any(char in text.strip() for char in "\n\r\"'«»“”‘’`{}[]\\/")
            or any(char in body for char in ".;:?!") or text.count("?") > 1):
        return abstain("estructura_no_soportada", "Citas, instrucciones mezcladas o varias cláusulas requieren interpretación adicional.", terminal_ids + prefix_ids)
    considered = terminal_ids + prefix_ids + tuple(rule.rule_id for rule in _CORE_RULES)
    matches = [rule for rule in _CORE_RULES if rule.matches(body)]
    if len(matches) > 1:
        return abstain("conflicto_reglas", "Más de una regla propone una clasificación; no se elige por orden.", considered)
    if not matches:
        if turns:
            return abstain("contexto_requiere_interpretacion", "La petición no es autocontenida para estas reglas y necesita interpretación contextual.", considered)
        return abstain("sin_regla_segura", "Ninguna plantilla local permite una clasificación suficientemente defendible.", considered)
    rule = matches[0]
    if turns and rule.rule_id == "Q.CONTEXT.MISSING_ACTION":
        return abstain("contexto_requiere_interpretacion", "Hay antecedentes disponibles; estas reglas no pueden resolver a qué episodio se refiere la repregunta.", considered)
    if prefix_ids == ("Q.DIRECTIVE.YEAR",) and rule.rule_id != "Q.FACT.YEAR":
        return abstain("restriccion_incompatible", "La restricción de año no coincide con el dato solicitado.", considered)
    return _accepted(intervention_id, text, rule, (*prefix_ids, rule.rule_id), considered, allowed_ids)
