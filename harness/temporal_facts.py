"""Hechos temporales derivados del perfil validado, sin archivos ni LLM."""

import json


def _months(start: str, end: str) -> set[int]:
    """Meses de un periodo ISO validado; ambos extremos están incluidos."""
    start_year, start_month = map(int, start.split("-"))
    end_year, end_month = map(int, end.split("-"))
    return set(range(start_year * 12 + start_month - 1, end_year * 12 + end_month))


def build_temporal_facts(candidate: dict) -> dict:
    """Contar meses distintos de empleo y ordenar términos de estudios/proyectos.

    Los roles concurrentes no duplican meses en el total calendario. Los
    periodos de jornada se conservan por rol; no se infieren horas ni jornada
    de una práctica que no las especifica. El trabajo académico no es empleo.
    """
    worked_months: set[int] = set()
    roles = []
    for experience in candidate["work_experience"]:
        for role in experience["roles"]:
            role_months = _months(role["start_month"], role["end_month"])
            worked_months.update(role_months)
            schedules = []
            scheduled_months: set[int] = set()
            for period in role.get("schedule_periods", []):
                months = _months(period["start_month"], period["end_month"])
                scheduled_months.update(months)
                schedules.append({
                    "schedule": period["schedule"],
                    "start_month": period["start_month"],
                    "end_month": period["end_month"],
                    "calendar_months": len(months),
                })
            roles.append({
                "role_id": role["role_id"],
                "title": role["title"],
                "organization": experience["organization"],
                "start_month": role["start_month"],
                "end_month": role["end_month"],
                "calendar_months": len(role_months),
                "schedule_periods": schedules,
                "months_without_recorded_schedule": len(role_months - scheduled_months),
            })

    completion_events = [
        {"event_type": "project_end", "record_id": project["project_id"],
         "name": project["name"], "month": project["end_month"]}
        for project in candidate["projects"]
    ]
    for study in candidate["education"]:
        for event_type, field in (("education_end", "end_month"), ("graduation", "graduation_month")):
            completion_events.append({
                "event_type": event_type, "record_id": study["education_id"],
                "name": study["degree"], "institution": study["institution"],
                "month": study[field],
            })
    completion_events.sort(key=lambda event: (event["month"], event["record_id"], event["event_type"]))
    return {
        "employment": {
            "distinct_calendar_months": len(worked_months),
            "roles": sorted(roles, key=lambda role: (role["start_month"], role["role_id"])),
            "counting_basis": "Meses calendario incluidos ambos extremos, sin duplicar empleos concurrentes.",
            "full_time_equivalent_months": None,
            "full_time_equivalent_note": "No calculable: no constan horas o fracciones de todas las jornadas.",
        },
        "completion_events": completion_events,
    }


def format_temporal_reference(facts: dict) -> str:
    """Presentar los mismos cálculos como datos legibles para el modelo."""
    employment = facts["employment"]
    lines = [
        f"Experiencia laboral total: {employment['distinct_calendar_months']} meses calendario distintos, contando todos los roles, incluida la práctica si figura entre ellos.",
        "No sumar los proyectos académicos como empleos ni volver a contar proyectos realizados dentro de un empleo.",
    ]
    for role in employment["roles"]:
        title = json.dumps(role["title"], ensure_ascii=False)
        organization = json.dumps(role["organization"], ensure_ascii=False)
        lines.append(f"- {title} en {organization}: {role['start_month']} a {role['end_month']}, {role['calendar_months']} meses calendario.")
        for period in role["schedule_periods"]:
            lines.append(f"  {period['schedule']}: {period['start_month']} a {period['end_month']}, {period['calendar_months']} meses.")
        unknown = role["months_without_recorded_schedule"]
        if unknown:
            lines.append(f"  Sin jornada especificada en el perfil: {unknown} meses de este rol.")
    lines.append(employment["full_time_equivalent_note"])
    lines.append("Finalización de TODOS los proyectos y estudios, por fecha de término (meses iguales no fijan orden dentro del mes):")
    labels = {"project_end": "Término de proyecto", "education_end": "Término de estudios", "graduation": "Titulación"}
    for event in facts["completion_events"]:
        name = json.dumps(event["name"], ensure_ascii=False)
        lines.append(f"- {event['month']}: {labels[event['event_type']]} {name}.")
    return "\n".join(lines)
