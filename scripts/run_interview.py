"""Ejecutar la consola: python -X utf8 -m scripts.run_interview."""

import argparse
import sys
import json

from harness.application.cli import run_console
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMError
from harness.llm.factory import create_client
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.live_context import LiveContextPolicy
from harness.session_log import SessionLogError, save_session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulador de entrevista con candidato ficticio.")
    parser.add_argument("--extractive-context", action="store_true", help="Activar la política de resumen verificable")
    parser.add_argument("--summary-trigger-tokens", type=int, help="Umbral de entrada informada; por defecto usa la reserva de contexto")
    parser.add_argument("--summary-context-size", type=int, help="Capacidad explícita si el cliente no la declara")
    args = parser.parse_args([] if argv is None else argv)
    if not args.extractive_context and (args.summary_trigger_tokens is not None or args.summary_context_size is not None):
        parser.error("Los ajustes de resumen requieren --extractive-context.")
    setup = None
    client = None
    runtime = None
    integrity_failed = False
    exit_code = 1
    try:
        setup = load_interview_setup()
        instructions = load_instructions()
        with create_client() as client:
            runtime_options = {"provider": client.provider, "model": client.settings.model}
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
                if getattr(client, "provider", None) == "unab" and client.call_diagnostics:
                    diagnostic_path = output.parent.parent / "results" / f"unab-usage-{runtime.session_id}.json"
                    try:
                        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
                        with diagnostic_path.open("x", encoding="utf-8") as target:
                            json.dump({"diagnostics_version": "1.0.0", "session_id": runtime.session_id,
                                       "provider": "unab", "requested_model": client.settings.model,
                                       "calls": client.call_diagnostics}, target, ensure_ascii=False, indent=2, allow_nan=False)
                            target.write("\n")
                    except OSError:
                        print("No se pudo guardar el diagnóstico de uso de UNAB IA.")
                        exit_code = 1
                    else:
                        print(f"Diagnóstico de uso de API guardado: {diagnostic_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
