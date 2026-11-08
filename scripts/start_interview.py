"""Selector interactivo local/API; evaluación educativa opcional."""

import os
import argparse
from pathlib import Path
# El proceso hijo es el módulo local elegido por las opciones cerradas del menú.
import subprocess  # nosec B404
import sys

from harness.json_loader import load_json
from harness.application.console_view import format_provider_menu


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/llm.local.json"


def selected_environment(config, selection, environ):
    required = {"local_model", "api_model", "api_key"}
    if not isinstance(config, dict) or not required <= set(config) or set(config) - required - {"api_max_output_tokens"}:
        raise ValueError("La configuración necesita local_model, api_model y api_key; admite api_max_output_tokens opcional.")
    if any(not isinstance(config[key], str) for key in required):
        raise ValueError("Los campos de configuración deben contener texto.")
    env = dict(environ)
    if selection == "1":
        env.update(LLM_PROVIDER="ollama", LLM_ALLOW_EXTERNAL_API="false", OLLAMA_MODEL=config["local_model"])
        env.pop("UNAB_API_KEY", None)
    elif selection == "2":
        if not config["api_key"]:
            raise ValueError("Coloca tu clave en api_key dentro de config/llm.local.json.")
        budget = config.get("api_max_output_tokens", 2048)
        if type(budget) is not int or not 16 <= budget <= 4096:
            raise ValueError("api_max_output_tokens debe ser un entero entre 16 y 4096.")
        env.update(LLM_PROVIDER="unab", LLM_ALLOW_EXTERNAL_API="true", UNAB_MAX_OUTPUT_TOKENS=str(budget),
                   UNAB_MODEL=config["api_model"], UNAB_API_KEY=config["api_key"])
    else:
        raise ValueError("Selecciona 1 o 2.")
    return env


def main(argv=None):
    parser = argparse.ArgumentParser(description="Seleccionar proveedor para la entrevista.")
    parser.add_argument("--evaluate", action="store_true", help="Activar evaluación provisional de preguntas")
    parser.add_argument("--no-classifier-examples", action="store_true", help="Desactivar demostraciones del clasificador")
    parser.add_argument("--no-evaluator-examples", action="store_true", help="Desactivar demostraciones del evaluador")
    args = parser.parse_args([] if argv is None else argv)
    if args.no_evaluator_examples and not args.evaluate:
        parser.error("Desactivar ejemplos del evaluador requiere --evaluate.")
    try:
        try:
            config = load_json(CONFIG_PATH)
        except ValueError:
            raise ValueError("No se pudo leer config/llm.local.json. Revisa el archivo y su formato JSON.") from None
        print(format_provider_menu(), flush=True)
        while True:
            selection = input("Elige 1 o 2 (Enter = local): ").strip() or "1"
            if selection in {"1", "2"}:
                break
            print("Selecciona 1 o 2.")
        env = selected_environment(config, selection, os.environ)
        if selection == "2":
            print(f"UNAB IA: presupuesto máximo de salida {env['UNAB_MAX_OUTPUT_TOKENS']} tokens por pregunta.", flush=True)
        command = [sys.executable, "-X", "utf8", "-m", "scripts.run_interview", "--classify"]
        if args.evaluate:
            command.append("--evaluate")
        if args.no_classifier_examples:
            command.append("--no-classifier-examples")
        if args.no_evaluator_examples:
            command.append("--no-evaluator-examples")
        if selection == "1":
            command.append("--extractive-context")
        return subprocess.run(command, cwd=ROOT, env=env).returncode  # nosec B603
    except ValueError as error:
        print(str(error))
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nInicio cancelado.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
