"""Comprobación aislada del contexto: no reanuda ni modifica la entrevista fuente."""

import argparse
from pathlib import Path

from harness.history_summary import build_summary_source, generate_summary
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMError, LLMInvalidResponseError
from harness.llm.factory import create_client
from harness.prompt_builder import load_instructions
from harness.session_log import SessionLogError, load_session
from harness.summary_context import prepare_summary_context


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consultar al candidato con contexto derivado de una sesión guardada.")
    parser.add_argument("session_path", type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--keep-recent-pairs", type=int, default=2)
    args = parser.parse_args(argv)
    setup = None
    exit_code = 1
    try:
        setup = load_interview_setup()
        instructions = load_instructions()
        session = load_session(args.session_path)
        build_summary_source(session, keep_recent_pairs=args.keep_recent_pairs)
        # Comprobar vínculos y entrada antes de crear un cliente o gastar una llamada.
        initial, _ = generate_summary(session, None, keep_recent_pairs=20)
        prepare_summary_context(setup, args.question, instructions=instructions, session=session, summary=initial)
        with create_client() as client:
            print(f"COMPROBACIÓN AISLADA DE CONTEXTO. Proveedor: {client.provider}. Modelo: {client.settings.model}.", flush=True)
            summary, _ = generate_summary(session, client, keep_recent_pairs=args.keep_recent_pairs)
            prepared = prepare_summary_context(setup, args.question, instructions=instructions, session=session, summary=summary)
            mode = "resumen extractivo" if prepared["mode"] == "extractive_summary" else "historial completo"
            print(f"Contexto elegido: {mode}. Motivo: {prepared['reason']}.", flush=True)
            print(f"Bytes de mensajes: {prepared['full_message_bytes']} → {prepared['selected_message_bytes']}. No es un conteo de tokens.", flush=True)
            setup.candidate.assert_source_unchanged()
            try:
                response = client.generate(prepared["messages"])
            finally:
                setup.candidate.assert_source_unchanged()
            if response.finish_reason == "length":
                raise LLMInvalidResponseError("La respuesta quedó cortada y no se acepta como comprobación completa.")
            print(f"Respuesta de comprobación: {response.text}")
            print(f"Tiempo de respuesta: {response.elapsed_seconds:.2f} s")
            print("La sesión fuente y sus contadores permanecen sin cambios.")
            exit_code = 0
    except (SessionLogError, ValueError, LLMError) as error:
        print(f"No se pudo completar la comprobación: {error}")
    except KeyboardInterrupt:
        print("\nComprobación interrumpida.")
    finally:
        if setup is not None:
            try:
                setup.candidate.assert_source_unchanged()
            except ValueError as error:
                print(f"Error de integridad: {error}")
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
