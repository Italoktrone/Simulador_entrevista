"""Aritmética y comparación de clasificación; los dobles no son mediciones reales."""

from copy import deepcopy

import pytest

from harness.classification_evaluation import (
    assess_case, exclusive_metrics, grouped_metrics, multilabel_metrics, semantic_projection, operation_metrics,
)
from harness.classification_references import load_classification_references
from harness.llm.client import LLMProviderError
from harness.llm_question_classifier import LLMQuestionClassifier


@pytest.fixture(scope="module")
def suite():
    return load_classification_references()


def observed(case, statuses=("validada",)):
    result = deepcopy(case["expected"])
    result.update(method="llm", rule_ids=[], technical_error=None, validation_status="pendiente")
    for unit in result["units"]:
        unit.update(method="llm", rule_ids=[])
    return {"route": "llm", "result": result, "trace": {
        "local": {"status": "abstencion", "reason": "Doble sintético para probar métricas."},
        "llm": {"attempts": [{"status": s} for s in statuses]}}}


def test_operation_includes_repair_and_reports_missing_measurements_explicitly():
    result = operation_metrics([{"input_tokens": 12, "output_tokens": 7, "elapsed_seconds": 2.5},
                                {"input_tokens": 15, "output_tokens": None, "elapsed_seconds": 4.0}])
    assert result["generations"] == 2
    assert result["input_tokens"]["known_total"] == 27
    assert result["output_tokens"] == {"known_total": 7, "reported_generations": 1, "total_generations": 2}
    assert result["elapsed_seconds"]["known_total"] == 6.5
    assert operation_metrics([{}])["input_tokens"]["known_total"] is None
    assert operation_metrics([])["input_tokens"]["known_total"] == 0


def test_exclusive_counts_macro_denominators_and_failure_column():
    result = exclusive_metrics(["a", "a", "b", "b"], ["a", "b", "b", "__abstencion__"], ["a", "b", "unused"])
    assert result["accuracy"] == {"numerator": 2, "denominator": 4, "value": 0.5}
    assert result["per_label"]["a"]["f1"] == pytest.approx(2 / 3)
    assert result["per_label"]["b"]["f1"] == 0.5
    assert result["per_label"]["unused"]["f1"] is None
    assert result["macro_f1"] == pytest.approx(7 / 12)
    assert result["macro_labels"] == ["a", "b"]
    assert result["confusion"]["column_labels"][-1] == "__abstencion__"
    assert sum(map(sum, result["confusion"]["matrix"])) == 4


def test_multilabel_counts_do_not_count_missing_empty_attributes_as_success():
    result = multilabel_metrics([["a"], ["a", "b"], [], ["b"]], [["a"], ["a"], None, []], ["a", "b"])
    assert result["exact_set_match"]["value"] == 0.25
    assert result["macro_f1"] == 0.5
    assert result["micro"]["precision"] == 1
    assert result["micro"]["recall"] == 0.5
    assert result["micro"]["f1"] == pytest.approx(2 / 3)
    assert result["missing_predictions"] == 1


def test_empty_metrics_remain_unknown_instead_of_inventing_zero_or_perfect_score():
    assert exclusive_metrics([], [], ["a"])["accuracy"]["value"] is None
    assert multilabel_metrics([], [], ["a"])["macro_f1"] is None
    metrics = grouped_metrics([])
    assert metrics["all"]["llm_delegation_rate"]["value"] is None
    assert metrics["comprobacion_conocida"]["semantic_exact_all"]["value"] is None


def test_prose_and_order_are_not_semantic_errors_and_inputs_are_copied(suite):
    case = next(c for c in suite.to_dict()["cases"] if len(c["expected"]["units"]) > 1)
    request = suite.input_for(case["case_id"], split=case["split"])
    report = observed(case)
    original = deepcopy(report)
    report["result"]["rationale"] = "Justificación distinta pero válida."
    report["result"]["classification"]["approaches"].reverse()
    report["result"]["classification"]["forms"].reverse()
    entry = assess_case(case, request, report)
    assert entry["exact_semantic_match"] and entry["discrepancy"] is None
    assert semantic_projection(report["result"]) == semantic_projection(original["result"])
    entry["prediction"]["original_text"] = "Modificación de una copia."
    assert report["result"]["original_text"] == case["input"]["text"]


def test_clear_compound_without_principal_is_a_valid_target_not_a_missing_prediction(suite):
    case = next(c for c in suite.to_dict()["cases"] if c["expected"]["classification"] is not None
                and c["expected"]["classification"]["main_approach"] is None)
    entry = assess_case(case, suite.input_for(case["case_id"], split=case["split"]), observed(case))
    result = grouped_metrics([entry])["all"]["exclusive"]["main_approach"]
    assert result["accuracy"]["value"] == 1
    assert result["per_label"]["__sin_principal__"]["support"] == 1


def test_valid_but_wrong_attribute_generates_pending_discrepancy_without_changing_reference(suite):
    case = suite.cases()[0]
    before = deepcopy(case)
    raw = observed(case)
    for labels in [raw["result"]["classification"], raw["result"]["units"][0]["classification"]]:
        labels["attributes"] = ["sugestiva"] if "sugestiva" not in labels["attributes"] else []
    entry = assess_case(case, suite.input_for(case["case_id"]), raw)
    assert not entry["exact_semantic_match"]
    assert entry["discrepancy"]["review_status"] == "pending_human_review"
    assert "interpretacion_llm" in entry["discrepancy"]["categories"]
    assert any(d["path"].endswith("/attributes") for d in entry["differences"])
    assert entry["discrepancy"]["possible_cause"].startswith("Hipótesis")
    assert case == before
    assert entry["segmentation_exact"] is True
    assert entry["unit_labels_exact"] is False
    metrics = grouped_metrics([entry])["all"]
    assert metrics["segmentation_exact_on_classified_evaluable"]["value"] == 1
    assert metrics["unit_labels_exact_on_matching_segmentation"]["value"] == 0


def test_forged_validated_source_is_rejected_and_raw_result_is_not_preserved(suite):
    case = suite.cases()[0]
    raw = observed(case)
    raw["result"].update(validation_status="validada", original_text="Fuente falsificada.")
    entry = assess_case(case, suite.input_for(case["case_id"]), raw)
    assert entry["outcome"] == "resultado_invalido"
    assert entry["prediction"] is entry["observation"] is None
    metrics = grouped_metrics([entry])["all"]
    assert metrics["semantic_exact_all"]["value"] == 0
    assert metrics["invalid_result_rate"]["value"] == 1


def test_abstention_is_not_hidden_by_conditional_accuracy_or_empty_attributes(suite):
    case = suite.cases()[0]
    entry = assess_case(case, suite.input_for(case["case_id"]),
                        {"status": "abstencion", "result": None, "reason": "Fuera de las plantillas."})
    metrics = grouped_metrics([entry])["all"]
    assert metrics["semantic_exact_on_classified"]["value"] is None
    assert metrics["semantic_exact_all"]["value"] == 0
    assert metrics["multilabel"]["attributes"]["exact_set_match"]["value"] == 0
    assert metrics["local_abstention_rate"]["value"] == 1
    assert metrics["llm_delegation_rate"]["value"] == 0


@pytest.mark.parametrize("statuses", [("json_invalido", "validada"), ("contrato_invalido", "validada")])
def test_repair_generation_rates_use_generations_not_cases(suite, statuses):
    case = suite.cases()[0]
    entry = assess_case(case, suite.input_for(case["case_id"]), observed(case, statuses))
    metrics = grouped_metrics([entry])["all"]
    assert metrics["llm_generations"] == 2
    assert metrics["llm_delegation_rate"]["numerator"] == 1
    assert metrics["invalid_structured_generation_rate"] == {"numerator": 1, "denominator": 2, "value": 0.5}
    assert metrics["repaired_cases"] == 1


def test_non_evaluable_cases_only_enter_evaluability_and_global_denominators(suite):
    case = next(c for c in suite.cases() if c["expected"]["evaluability"] == "no_evaluable")
    entry = assess_case(case, suite.input_for(case["case_id"]), observed(case))
    metrics = grouped_metrics([entry])["all"]
    assert metrics["exclusive"]["evaluability"]["n"] == 1
    assert metrics["exclusive"]["main_approach"]["n"] == 0
    assert metrics["multilabel"]["attributes"]["n"] == 0
    assert metrics["semantic_exact_all"]["value"] == 1


def test_technical_fallback_is_not_scored_as_genuine_indeterminacy(suite):
    case = suite.cases()[0]
    request = suite.input_for(case["case_id"])
    class FailingClient:
        def generate(self, messages):
            raise LLMProviderError("Fallo ficticio.")
    semantic = LLMQuestionClassifier(FailingClient()).classify(**request).to_dict()
    result = semantic.pop("result")
    raw = {"route": "llm", "result": result, "trace": {
        "local": {"status": "abstencion", "reason": "Doble sintético."}, "llm": semantic}}
    metrics = grouped_metrics([assess_case(case, request, raw)])["all"]
    assert metrics["technical_fallback_rate"]["value"] == 1
    assert "__error_tecnico__" in metrics["exclusive"]["certainty"]["confusion"]["column_labels"]
    assert metrics["exclusive"]["certainty"]["per_label"]["indeterminada"]["predicted_positive"] == 0
    assert metrics["invalid_structured_generation_rate"]["value"] == 0
