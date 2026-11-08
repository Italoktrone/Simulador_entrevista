"""Selección conservadora de episodios de apoyo, a partir del perfil de la sesión.

Reconoce formulaciones explícitas en español. La selección acota los hechos
disponibles; no certifica por sí sola la pertinencia de una respuesta libre.
"""

from copy import deepcopy
import re
import unicodedata


SELECTION_VERSION = "1.0.1"
RECEIVED = (
    r"\b(?:necesitaste|necesitabas|pediste|solicitaste|recibiste|requeriste|buscaste|dependiste)\b.{0,70}\b(?:ayuda|apoyo|orientacion)\b",
    r"\b(?:ayuda|apoyo|orientacion)\s+(?:que\s+)?(?:recibiste|recibido|recibida)\b",
    r"\bte\s+(?:ayudo|ayudaron|apoyo|apoyaron|orientaron|echaron una mano|prestaron ayuda)\b",
    r"\bte\s+(?:brindo|brindaron|presto|prestaron)\s+(?:ayuda|apoyo)\b",
    r"\b(?:acudiste|recurriste|consultaste)\b.{0,70}\b(?:companero|colega|equipo|desarrollador|analista|alguien)\b",
    r"\b(?:tuviste|has tenido|te toco)\b.{0,40}\b(?:pedir(?:le)?|solicitar|buscar)\b.{0,35}\b(?:ayuda|apoyo)\b",
    r"\b(?:fuiste tu|tu mismo|tu misma)\b.{0,40}\bnecesito\b.{0,20}\b(?:ayuda|apoyo)\b",
)
PROVIDED = (
    r"\b(?:ayudaste|apoyaste|orientaste)\b",
    r"\btu\s+(?:ayuda|apoyo|orientacion)\b",
    r"\b(?:prestaste|brindaste|diste|ofreciste)\b.{0,40}\b(?:ayuda|apoyo|orientacion)\b",
    r"\b(?:ayuda|apoyo)\s+(?:de ti|que prestaste|que brindaste)\b",
    r"\bte\s+(?:pidio|pidieron|solicito|solicitaron)\s+(?:ayuda|apoyo)\b",
    r"\bechaste una mano\b",
)
HYPOTHETICAL = r"\b(?:ayudarias|apoyarias|pedirias|solicitarias|harias|actuarias|recurririas)\b"
FOLLOWUP = r"\b(?:entonces|despues|ese caso|esa ocasion|eso|alli|lo resolviste|el resultado)\b"
STOP = frozenset("a al algo alguien aquel aquella antes caso como con cuando cuentame de del describeme el ella en equipo esa ese fue hiciste la lo los me momento ocasion para por que quien se sobre te tu un una y".split())
PERSON = r"\b(?:companer[oa]|colega|desarrollador[a]?|analista|encargad[oa]|coordinador[a]?|supervisor[a]?|equipo|jef[ea]|alguien|persona)\b"


def _normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def _direct_intents(text):
    text = _normalized(text)
    if re.search(HYPOTHETICAL, text):
        return ()
    # Una corrección como «no cuándo ayudaste; quiero saber cuándo pediste»
    # excluye la primera intención; no convierte la negación en otro pedido.
    if re.search(r"\bno\b", text):
        parts = re.split(r"\bsino(?: que)?\b|\bquiero saber\b|\bme interesa saber\b", text)
        if len(parts) > 1:
            text = parts[-1]
    return tuple(direction for direction, patterns in (("received", RECEIVED), ("provided", PROVIDED))
                 if any(re.search(pattern, text) for pattern in patterns))


def _intent(question, history):
    directions = _direct_intents(question)
    if directions or re.search(HYPOTHETICAL, _normalized(question)):
        return directions, False, question
    if not re.search(FOLLOWUP, _normalized(question)):
        return (), False, question
    # Solo preguntas del entrevistador; una respuesta anterior no añade hechos
    # ni puede imponer quién recibió ayuda. Detenerse ante un cambio de tema.
    for message in reversed((history or [])[-8:]):
        if message["role"] != "user":
            continue
        previous = message["content"]
        directions = _direct_intents(previous)
        if directions:
            return directions, True, previous
        if not re.search(FOLLOWUP, _normalized(previous)):
            break
    return (), False, question


def _evidence(situation):
    """Las anotaciones se respaldan con citas exactas de campos originales."""
    result = []
    title = _normalized(situation["title"])
    if re.search(r"\b(?:pedir|solicitar|recibir)\s+(?:ayuda|apoyo|orientacion)\b", title):
        result.append(("received", 3, [{"field": "title", "quote": situation["title"]}]))
    for index, action in enumerate(situation["actions"]):
        text = _normalized(action)
        if re.search(r"\b(?:consulto|pidio|solicito|recurrio)\b", text) and re.search(PERSON, text):
            result.append(("received", 2, [{"field": "actions", "index": index, "quote": action}]))
        if re.search(r"\b(?:ayudo|apoyo|oriento)\s+a\b", text):
            result.append(("provided", 3, [{"field": "actions", "index": index, "quote": action}]))
    context = _normalized(situation["context"])
    if re.search(r"\b(?:un|una|otro|otra)\s+companer[oa]\b.{0,70}\b(?:no pudo|necesitaba|tenia dificultades)\b", context):
        for index, action in enumerate(situation["actions"]):
            if re.search(r"\b(?:reviso|corrigio|explico|ayudo)\b", _normalized(action)):
                result.append(("provided", 2, [{"field": "context", "quote": situation["context"]},
                                               {"field": "actions", "index": index, "quote": action}]))
                break
    return result


def select_support_evidence(candidate, question, history=None):
    """Elegir por dirección, evidencia y tema; nunca por ID o nombre de NPC.

    La ausencia de episodios elegibles no significa que la persona nunca haya
    ayudado o recibido ayuda. Las relaciones no documentadas siguen ausentes.
    """
    directions, inherited, topic = _intent(question, history)
    if not directions:
        return None
    terms = set(re.findall(r"[a-z0-9]+", _normalized(topic))) - STOP
    projects = {p["project_id"]: p for p in candidate["projects"]}
    named_projects = {pid for pid, p in projects.items()
                      if re.search(r"(?<!\w)" + re.escape(_normalized(p["name"])) + r"(?!\w)", _normalized(topic))}
    selected = []
    missing = []
    for direction in directions:
        eligible = []
        for index, situation in enumerate(candidate["behavioral_situations"]):
            if named_projects and situation.get("project_id") not in named_projects:
                continue
            words = set(re.findall(r"[a-z0-9]+", _normalized(_situation_text(situation))))
            for role, strength, evidence in _evidence(situation):
                if role == direction:
                    eligible.append((strength, len(terms & words), -index, situation, evidence))
        if not eligible:
            missing.append(direction)
            continue
        _, _, _, situation, evidence = max(eligible, key=lambda item: item[:3])
        project = projects.get(situation.get("project_id"))
        selected.append({"direction": direction, "situation_id": situation["situation_id"],
                         "project_id": situation.get("project_id"), "project_name": project["name"] if project else None,
                         "evidence": evidence, "action_roles": _action_roles(situation)})
    return {"selection_version": SELECTION_VERSION, "candidate_id": candidate["candidate_id"],
            "requested_directions": list(directions), "selected": selected,
            "missing_directions": missing, "history_used": inherited}


def _situation_text(situation):
    return " ".join([situation["title"], situation["context"], *situation["actions"], situation["outcome"]])


def _action_roles(situation):
    result = []
    for index, action in enumerate(situation["actions"]):
        text = _normalized(action)
        verb = text.split()[0].strip(".,:;")
        plural = re.fullmatch(r"[a-z]+(?:aron|ieron|eron)", verb) is not None
        joint_review = bool(re.match(r"(?:reviso|acordo)\b", text)
                            and re.search(r"\b(?:junto|con)\b", text) and re.search(PERSON, text))
        involvement = "shared_action" if plural or joint_review else "candidate_action"
        if re.match(r"consulto\b", text) and re.search(PERSON, text):
            involvement = "candidate_consulted_other"
        elif re.match(r"(?:pidio|solicito)\b", text) and re.search(PERSON, text):
            involvement = "candidate_requested_other_action"
        result.append({"index": index, "quote": action, "documented_involvement": involvement})
    return result


def support_profile_view(candidate, selection):
    """Vista de trabajo: preservar archivos y mantener cada hecho seleccionado."""
    view = deepcopy(candidate)
    if selection is None:
        return view
    if selection["candidate_id"] != candidate["candidate_id"]:
        raise ValueError("La selección no corresponde al candidato.")
    ids = {item["situation_id"] for item in selection["selected"]}
    if not ids <= {s["situation_id"] for s in candidate["behavioral_situations"]}:
        raise ValueError("La selección contiene un episodio ajeno al perfil.")
    view["behavioral_situations"] = [s for s in view["behavioral_situations"] if s["situation_id"] in ids]
    for field in ("achievements", "professional_competencies", "strengths", "improvement_areas"):
        kept = []
        for item in view[field]:
            if "situation_id" in item and item["situation_id"] not in ids:
                continue
            if "situation_ids" in item:
                item["situation_ids"] = [sid for sid in item["situation_ids"] if sid in ids]
                if not item["situation_ids"]:
                    continue
            kept.append(item)
        view[field] = kept
    return view


def audit_support_selection(selection):
    """Metadatos del turno, sin copiar citas privadas al log público."""
    if selection is None:
        return None
    return {key: deepcopy(selection[key]) for key in ("selection_version", "candidate_id", "requested_directions", "missing_directions", "history_used")} | {
        "selected": [{"direction": s["direction"], "situation_id": s["situation_id"]} for s in selection["selected"]]
    }
