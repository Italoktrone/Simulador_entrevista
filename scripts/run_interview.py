"""Ejecutar la consola: python -X utf8 -m scripts.run_interview."""

import argparse
import sys
import json
from contextlib import ExitStack

from harness.application.cli import run_console
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMError
from harness.llm.factory import create_client
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.live_context import LiveContextPolicy
from harness.session_log import SessionLogError, save_session
from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.llm_question_classifier import ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client
from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.scoring import CONFIG_PATH, load_rubric


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulador de entrevista con candidato ficticio.")
    parser.add_argument("--extractive-context", action="store_true", help="Activar la política de resumen verificable")
    parser.add_argument("--summary-trigger-tokens", type=int, help="Umbral de entrada informada; por defecto usa la reserva de contexto")
    parser.add_argument("--summary-context-size", type=int, help="Capacidad explícita si el cliente no la declara")
    parser.add_argument("--classify", action="store_true", help="Clasificar antes del candidato y aplicar política de respuesta")
    parser.add_argument("--classifier-model", help="Modelo opcional independiente para clasificar")
    parser.add_argument("--classifier-max-output-tokens", type=int, help="Presupuesto del clasificador; por defecto 2048")
    parser.add_argument("--no-classifier-examples", action="store_true", help="Desactivar demostraciones aprobadas para comparar el clasificador")
    parser.add_argument("--evaluate", action="store_true", help="Evaluar preguntas después del candidato; activa también clasificación")
    parser.add_argument("--evaluation-config", help="Ruta opcional a la configuración de rúbrica")
    parser.add_argument("--evaluator-model", help="Modelo opcional independiente para evaluar")
    parser.add_argument("--no-evaluator-examples", action="store_true", help="Desactivar demostraciones del evaluador para comparación")
    args = parser.parse_args([] if argv is None else argv)
    if args.evaluate:
        args.classify = True
    elif args.evaluation_config is not None or args.evaluator_model is not None or args.no_evaluator_examples:
        parser.error("Los ajustes de evaluación requieren --evaluate.")
    if not args.extractive_context and (args.summary_trigger_tokens is not None or args.summary_context_size is not None):
        parser.error("Los ajustes de resumen requieren --extractive-context.")
    if not args.classify and (args.classifier_model is not None or args.classifier_max_output_tokens is not None or args.no_classifier_examples):
        parser.error("Los ajustes del clasificador requieren --classify.")
    setup = None
    client = None
    classification_client = None
    evaluation_client = None
    runtime = None
    integrity_failed = False
    exit_code = 1
    try:
        setup = load_interview_setup()
        instructions = load_instructions()
        with ExitStack() as resources:
            client = resources.enter_context(create_client())
            runtime_options = {"provider": client.provider, "model": client.settings.model}
            if args.classify:
                settings = ClassificationLLMSettings(
                    model=args.classifier_model,
                    max_output_tokens=2048 if args.classifier_max_output_tokens is None else args.classifier_max_output_tokens,
                )
                classification_client = resources.enter_context(create_classification_client(settings=settings))
                runtime_options.update(
                    classifier=HybridQuestionClassifier(LLMQuestionClassifier(classification_client, few_shot=not args.no_classifier_examples)),
                    classification_info={"requested_provider": classification_client.provider,
                                         "requested_model": classification_client.settings.model,
                                         "max_output_tokens": classification_client.settings.max_output_tokens},
                )
            if args.extractive_context:
                size = args.summary_context_size
                if size is None:
                    size = getattr(client.settings, "context_size", None)
                if size is None:
                    raise ValueError("Indica --summary-context-size para un proveedor sin capacidad explícita.")
                if hasattr(client.settings, "context_size") and size != client.settings.context_size:
                    raise ValueError("La capacidad de resumen debe coincidir con la solicitada al cliente local.")
                runtime_options["context_policy"] = LiveContextPolicy(
                    context_size=size, max_output_tokens=client.settings.max_output_tokens,
                    trigger_input_tokens=args.summary_trigger_tokens,
                )
            if args.evaluate:
                rubric = load_rubric(args.evaluation_config or CONFIG_PATH)
                evaluation_client = resources.enter_context(create_evaluation_client(rubric=rubric, model=args.evaluator_model))
                runtime_options["evaluator"] = QuestionEvaluator(evaluation_client, rubric=rubric, few_shot=not args.no_evaluator_examples)
            runtime = InterviewRuntime(
                setup, instructions, client, **runtime_options
            )
            exit_code = run_console(runtime, provider=client.provider, model=client.settings.model)
    except ProfileIntegrityError as error:
        integrity_failed = True
        print(f"Error de integridad: {error}")
    except (ValueError, LLMError) as error:
        print(f"No se pudo iniciar o continuar la entrevista: {error}")
    except KeyboardInterrupt:
        if runtime is not None:
            runtime.close("interrupted")
        print("\nPrograma interrumpido por el usuario.")
        exit_code = 0
    finally:
        if setup is not None:
            try:
                if runtime is not None:
                    runtime.assert_source_unchanged()
                else:
                    setup.candidate.assert_source_unchanged()
            except ProfileIntegrityError as error:
                if not integrity_failed:
                    print(f"Error de integridad: {error}")
                integrity_failed = True
            if integrity_failed:
                exit_code = 1
            else:
                print("Archivo original del candidato intacto.")
        if runtime is not None:
            runtime.close()
            try:
                output = save_session(runtime.session_dict())
            except SessionLogError as error:
                print(f"No se pudo guardar la sesión: {error}")
                exit_code = 1
            except KeyboardInterrupt:
                print("\nGuardado interrumpido. No se confirmó un archivo de sesión guardado.")
                exit_code = 1
            else:
                print(f"Registro de sesión guardado: {output}")
                for role, active_client in (("candidate", client), ("classifier", classification_client), ("evaluator", evaluation_client)):
                    if getattr(active_client, "provider", None) != "unab" or not active_client.call_diagnostics:
                        continue
                    prefix = "unab-usage" if role == "candidate" else "unab-" + role + "-usage"
                    diagnostic_path = output.parent.parent / "results" / f"{prefix}-{runtime.session_id}.json"
                    try:
                        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
                        with diagnostic_path.open("x", encoding="utf-8") as target:
                            json.dump({"diagnostics_version": "1.0.0", "session_id": runtime.session_id,
                                       "provider": "unab", "requested_model": active_client.settings.model,
                                       "calls": active_client.call_diagnostics}, target, ensure_ascii=False, indent=2, allow_nan=False)
                            target.write("\n")
                    except OSError:
                        print("No se pudo guardar el diagnóstico de uso de UNAB IA.")
                        exit_code = 1
                    else:
                        print(f"Diagnóstico de uso de API guardado: {diagnostic_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
