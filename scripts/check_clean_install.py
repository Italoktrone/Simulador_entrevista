"""Verificar una copia limpia del estado local sin copiar claves ni artefactos."""

import argparse
import json
import os
from pathlib import Path
import shutil
# Comandos locales constantes de Python, pip y Git, sin shell.
import subprocess  # nosec B404
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheels", type=Path, help="Carpeta opcional de paquetes para instalar sin red")
    args = parser.parse_args(argv)
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Se necesita Git para exportar los archivos del proyecto.")
    # Git se resuelve a una ruta absoluta y los argumentos de lectura son constantes.
    inventory = subprocess.run(  # nosec B603
        [git, "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT, check=True, capture_output=True
    ).stdout.decode("utf-8").split("\0")
    allowed = {"agent", "app", "config", "data", "docs", "harness", "scripts", "schemas", "tests", ".github"}
    allowed_files = {"README.md", "requirements.txt", "requirements-dev.txt", "pyproject.toml", ".gitignore", ".env.example"}
    with TemporaryDirectory(prefix="clean-install-", dir=reports) as temporary:
        snapshot = Path(temporary) / "project"
        snapshot.mkdir()
        copied = 0
        for relative in sorted(set(inventory)):
            path = Path(relative)
            if not path.parts or (path.parts[0] not in allowed and relative not in allowed_files):
                continue
            source = ROOT / path
            if not source.is_file() or source.is_symlink():
                continue
            if not source.resolve().is_relative_to(ROOT):
                raise ValueError("Ruta de origen fuera del proyecto.")
            destination = snapshot / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied += 1
        environment = Path(temporary) / "venv"
        commands = [[sys.executable, "-B", "-m", "venv", str(environment)]]
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        install = [str(python), "-B", "-m", "pip", "install", "--no-compile", "-r", "requirements-dev.txt"]
        if args.wheels:
            install.extend(["--no-index", "--find-links", str(args.wheels.resolve())])
        commands.extend([install, [str(python), "-B", "-m", "scripts.check_project"]])
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("LLM_", "OLLAMA_", "UNAB_", "OPENAI_", "INTERVIEW_", "PYTHONPATH"))}
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", LLM_ALLOW_EXTERNAL_API="false")
        logs = []
        exit_code = 0
        for command in commands:
            result = subprocess.run(command, cwd=snapshot, env=env, capture_output=True, text=True, encoding="utf-8")  # nosec B603
            logs.append(result.stdout + result.stderr)
            if result.returncode:
                exit_code = result.returncode
                break
        (reports / "clean-install.txt").write_text("\n".join(logs), encoding="utf-8")
        if (snapshot / "reports").is_dir():
            shutil.copytree(snapshot / "reports", reports / "clean-checks", dirs_exist_ok=True)
        (reports / "clean-install.json").write_text(json.dumps({
            "method": "working_tree_export", "includes_uncommitted_files": True,
            "files_copied": copied, "exit_code": exit_code,
        }, indent=2), encoding="utf-8")
        print(f"Instalación limpia: {exit_code}; {copied} archivos de proyecto.")
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
