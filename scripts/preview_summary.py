"""Generar una propuesta para revisión; no modifica ni reanuda entrevistas."""

import argparse
from pathlib import Path

from harness.history_summary import build_summary_source, generate_summary
from harness.llm.client import LLMError
from harness.llm.factory import create_client
from harness.session_log import SessionLogError, load_session


def format_summary_preview(summary: dict) -> str:
    stats = summary["statistics"]
    lines = ["PROPUESTA DE RESUMEN EXTRACTIVO - PENDIENTE DE REVISIÓN",
             f"Sesión de origen: {summary['source_session_id']}",
             "Las citas son afirmaciones previas del candidato; el perfil conserva su prioridad."]
    for turn in summary["older_turns"]:
        lines.append(f"Pregunta antigua {turn['question_number']}: {turn['question']}")
        for quote in turn["quotes"]:
            lines.append(f"  [P{turn['question_number']}/F{quote['segment_index']}] {quote['text']}")
        lines.append(f"  Fragmentos omitidos: {turn['omitted_segment_indices']}")
        lines.append(f"  Fragmentos conservados por protección: {turn['policy_added_segment_indices']}")
    if not summary["older_turns"]:
        lines.append("No hay turnos antiguos que resumir; no se consultó un modelo.")
    for turn in summary["recent_turns"]:
        lines.extend([f"Pregunta reciente {turn['question_number']} (completa): {turn['question']}",
                      f"  Respuesta completa: {turn['answer']}"])
    lines.extend([
        f"Fragmentos antiguos: {stats['old_segments']}; conservados: {stats['selected_segments']}; omitidos: {stats['omitted_segments']}.",
        f"Caracteres de fragmentos: {stats['source_segment_characters']} → {stats['selected_segment_characters']} (no es un conteo de tokens).",
        "Procedencia y citas verificadas contra la sesión original.",
        "Revisa las omisiones antes de usar la propuesta: una cita literal también puede perder contexto.",
        "La entrevista y su archivo completo permanecen sin cambios; esta vista previa no se aplica al candidato.",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Revisar una propuesta extractiva de turnos antiguos.")
    parser.add_argument("session_path", type=Path)
    parser.add_argument("--keep-recent-pairs", type=int, default=2)
    args = parser.parse_args(argv)
    try:
        session = load_session(args.session_path)
        source = build_summary_source(session, keep_recent_pairs=args.keep_recent_pairs)
        if source["older_turns"]:
            with create_client() as client:
                print(f"Selector: {client.provider}. Modelo: {client.settings.model}. Esperando selección...", flush=True)
                summary, _ = generate_summary(session, client, keep_recent_pairs=args.keep_recent_pairs)
        else:
            summary, _ = generate_summary(session, None, keep_recent_pairs=args.keep_recent_pairs)
    except (SessionLogError, ValueError, LLMError) as error:
        print(f"No se pudo preparar el resumen: {error}")
        return 1
    except KeyboardInterrupt:
        print("\nSelección interrumpida; el archivo de sesión se conserva.")
        return 1
    print(format_summary_preview(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
