"""Una pregunta con el proveedor seleccionado; Ollama local por defecto."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from harness.interview_config import load_interview_setup
from harness.llm.client import LLMError
from harness.llm.factory import create_client
from harness.prompt_builder import build_messages, load_instructions


ROOT = Path(__file__).resolve().parents[1]
QUESTION = "¿Dónde estudiaste y qué título obtuviste?"


def _format_seconds(value: float | None) -> str:
    return "no informado" if value is None else f"{value:.2f} s"


def main() -> int:
    started = perf_counter()
    setup = None
    provider = "llm"
    evidence: dict = {
        "test_id": "llm-single-question-001",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "question": QUESTION,
        "status": "error",
        "profile_unchanged": None,
        "semantic_review": "pendiente de revisión humana",
    }
    exit_code = 1
    try:
        with create_client() as client:
            provider = client.provider
            evidence["provider"] = provider
            evidence["settings"] = asdict(client.settings)
            setup = load_interview_setup()
            evidence["candidate_source_sha256"] = setup.candidate.source_sha256
            instructions = load_instructions()
            messages = build_messages(setup, QUESTION, instructions=instructions)
            evidence["instructions_text_sha256"] = hashlib.sha256(instructions.encode("utf-8")).hexdigest().upper()
            evidence["system_message_sha256"] = hashlib.sha256(messages[0]["content"].encode("utf-8")).hexdigest().upper()
            label = "Modelo local" if provider == "ollama" else "Modelo externo"
            provider_name = {"ollama": "Ollama", "openai": "OpenAI", "unab": "UNAB IA"}[provider]
            print(f"{label}: {client.settings.model}", flush=True)
            print(f"Pregunta: {QUESTION}", flush=True)
            print(f"Esperando respuesta de {provider_name}...", flush=True)
            result = client.generate(messages)
        evidence["response"] = asdict(result)
        truncated = result.finish_reason == "length"
        evidence["status"] = "incomplete" if truncated else "completed"
        if truncated:
            print("\nSe alcanzó el límite de salida. La respuesta no se acepta como prueba completada.")
        else:
            print(f"\nCandidato: {result.text}")
        print(f"\nTiempo de la llamada: {result.elapsed_seconds:.2f} s")
        print(f"Tokens informados por {provider_name}: entrada={result.input_tokens}, salida={result.output_tokens}")
        print(f"Motivo de finalización: {result.finish_reason}")
        if provider == "ollama":
            print("Desglose informado por Ollama:")
            for label, value in (
                ("Carga del modelo", result.load_seconds),
                ("Procesamiento del contexto", result.prompt_eval_seconds),
                ("Generación de la respuesta", result.eval_seconds),
                ("Total del servidor", result.server_total_seconds),
            ):
                print(f"  {label}: {_format_seconds(value)}")
            cached = "no informado" if result.cached_input_tokens is None else str(result.cached_input_tokens)
            print(f"  Tokens de contexto reutilizados: {cached}")
        exit_code = 1 if truncated else 0
    except (LLMError, ValueError) as exc:
        evidence["error_type"] = type(exc).__name__
        evidence["error"] = str(exc)
        print(f"No se completó la prueba: {exc}")
    except KeyboardInterrupt:
        evidence["error_type"] = "KeyboardInterrupt"
        evidence["error"] = "Prueba interrumpida por el usuario."
        print("\nPrueba interrumpida.")
    finally:
        if setup is not None:
            try:
                setup.candidate.assert_source_unchanged()
                evidence["profile_unchanged"] = True
                print("Archivo original del candidato intacto.")
            except ValueError as exc:
                evidence["profile_unchanged"] = False
                evidence["status"] = "error"
                evidence["integrity_error"] = str(exc)
                exit_code = 1
                print(f"Error de integridad: {exc}")

    evidence["test_elapsed_seconds"] = perf_counter() - started
    output = ROOT / "outputs" / "results" / f"{provider}-smoke-{uuid4().hex}.json"
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"No se pudo guardar la evidencia ({type(exc).__name__}).")
        return 1
    print(f"Evidencia: {output}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
