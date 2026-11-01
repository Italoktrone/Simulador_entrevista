"""Reservas y métricas ausentes: cálculos puros, sin tokenización aproximada."""

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from harness.context_budget import ContextBudget, build_context_report


@pytest.mark.parametrize(("input_tokens", "remaining", "status"), [
    (None, None, "unknown"), (0, 7424, "within_budget"),
    (6097, 1327, "within_budget"), (7423, 1, "within_budget"),
    (7424, 0, "at_limit"), (7425, -1, "over_budget"),
    (9000, -1576, "over_budget"),
])
def test_usage_keeps_unknown_zero_and_boundary_distinct(input_tokens, remaining, status):
    budget = ContextBudget(8192, 512)
    assert budget.input_limit == 7424
    assert budget.assess(input_tokens) == {
        "reported_input_tokens": input_tokens, "remaining_input_tokens": remaining, "budget_status": status,
    }


@pytest.mark.parametrize("changes", [
    {"context_size": 0}, {"context_size": True}, {"context_size": 8192.0},
    {"max_output_tokens": 0}, {"max_output_tokens": False},
    {"safety_margin": -1}, {"safety_margin": 1.5},
    {"context_size": 768}, {"context_size": 767},
])
def test_invalid_budgets_are_rejected(changes):
    settings = dict(context_size=8192, max_output_tokens=512, safety_margin=256)
    with pytest.raises(ValueError):
        ContextBudget(**(settings | changes))


@pytest.mark.parametrize("value", [-1, True, "6023", 1.5, float("nan"), float("inf")])
def test_invalid_reported_counts_are_rejected(value):
    with pytest.raises(ValueError, match="input_tokens"):
        ContextBudget(8192, 512).assess(value)


def test_custom_capacity_and_zero_extra_margin_are_explicit_and_immutable():
    budget = ContextBudget(1000, 100, 0)
    assert budget.input_limit == 900
    assert budget.assess(900)["budget_status"] == "at_limit"
    with pytest.raises(FrozenInstanceError):
        budget.context_size = 8192


def record(attempts):
    return {"session_id": "identificador-simulado", "requested_provider": None, "requested_model": None,
            "attempts": attempts}


def attempt(number, status, response):
    return {"question_number": number, "status": status, "response": response, "question": "TEXTO_RESERVADO"}


def test_report_includes_failed_partial_and_missing_metrics_without_copying_text_or_subtracting_cache():
    session = record([
        attempt(1, "error", None),
        attempt(2, "completed", {"input_tokens": 6097, "cached_input_tokens": 6075, "text": "TEXTO_RESERVADO"}),
        attempt(3, "incomplete", {"input_tokens": 7500}),
        attempt(4, "completed", {"input_tokens": None}),
    ])
    before = deepcopy(session)
    report = build_context_report(session, ContextBudget(8192, 512))
    assert report["unknown_attempts"] == 2
    assert report["peak_reported_input_tokens"] == 7500
    assert [a["budget_status"] for a in report["attempts"]] == ["unknown", "within_budget", "over_budget", "unknown"]
    assert report["attempts"][1]["remaining_input_tokens"] == 1327
    assert "TEXTO_RESERVADO" not in str(report)
    assert session == before
    report["attempts"][1]["reported_input_tokens"] = 0
    assert session == before


def test_no_attempts_have_no_known_peak():
    report = build_context_report(record([]), ContextBudget(8192, 512))
    assert report["attempts"] == [] and report["unknown_attempts"] == 0
    assert report["peak_reported_input_tokens"] is None
