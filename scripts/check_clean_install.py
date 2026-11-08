"""Verificar una copia limpia del estado local sin copiar claves ni artefactos."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
# Comandos locales constantes de Python, pip y Git, sin shell.
import subprocess  # nosec B404
import sys
from tempfile import TemporaryDirectory
from time import monotonic
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheels", type=Path, help="Carpeta opcional de paquetes para instalar sin red")
    parser.add_argument("--published", action="store_true", help="Clonar la rama publicada de origin en lugar de exportar cambios locales")
    parser.add_argument("--branch", default="E2")
    parser.add_argument("--godot", type=Path, help="Añadir el recorrido de Godot, fallos y límite para los tres perfiles")
    parser.add_argument("--with-live-godot", action="store_true", help="Añadir un recorrido con Ollama por perfil")
    parser.add_argument("--model", default="gemma4:e4b")
    args = parser.parse_args(argv)
    if args.with_live_godot and not args.godot:
        parser.error("--with-live-godot requiere --godot.")
    if args.godot and not args.godot.is_file():
        parser.error("No existe el ejecutable de Godot indicado.")
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    if not reports.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("El directorio temporal debe quedar dentro del proyecto.")
    proof = reports / ("published-install-" if args.published else "clean-install-") / uuid4().hex
    proof.mkdir(parents=True)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Se necesita Git para exportar los archivos del proyecto.")
    inventory = []
    remote = None
    if args.published:
        remote = subprocess.run([git, "remote", "get-url", "origin"], cwd=ROOT, check=True,
                                capture_output=True, text=True).stdout.strip()  # nosec B603
    else:
        # Git se resuelve a una ruta absoluta y los argumentos de lectura son constantes.
        inventory = subprocess.run(  # nosec B603
            [git, "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT, check=True, capture_output=True
        ).stdout.decode("utf-8").split("\0")
    allowed = {"agent", "app", "config", "data", "docs", "harness", "scripts", "schemas", "tests", ".github"}
    allowed_files = {"README.md", "requirements.txt", "requirements-dev.txt", "pyproject.toml", ".gitignore", ".gitattributes", ".env.example"}
    summary = {"method": "remote_clone" if args.published else "working_tree_export",
               "includes_uncommitted_files": not args.published, "commit": None,
               "branch": args.branch if args.published else None,
               "started_at_utc": datetime.now(timezone.utc).isoformat(), "checks": [],
               "evidence_directory": str(proof), "exit_code": None}
    environment_values = {key: value for key, value in os.environ.items()
                          if not key.startswith(("LLM_", "OLLAMA_", "UNAB_", "OPENAI_", "INTERVIEW_", "PYTHONPATH", "PYTHONHOME"))}
    environment_values.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", LLM_ALLOW_EXTERNAL_API="false")
    with TemporaryDirectory(prefix="clean-install-", dir=reports) as temporary:
        snapshot = Path(temporary) / "project"
        if args.published:
            cloned = subprocess.run([git, "clone", "--branch", args.branch, "--single-branch", "--", remote, str(snapshot)],
                                    cwd=ROOT, env=environment_values, capture_output=True, text=True, encoding="utf-8")  # nosec B603
            (proof / "clone.txt").write_text(cloned.stdout + cloned.stderr, encoding="utf-8")
            cloned.check_returncode()
            summary["commit"] = subprocess.run([git, "rev-parse", "HEAD"], cwd=snapshot, check=True,
                                               capture_output=True, text=True).stdout.strip()  # nosec B603
            summary["clean_before_install"] = not subprocess.run(
                [git, "status", "--porcelain"], cwd=snapshot, check=True, capture_output=True, text=True).stdout.strip()  # nosec B603
        else:
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
        commands = [("venv", [sys.executable, "-B", "-m", "venv", str(environment)])]
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        install = [str(python), "-B", "-m", "pip", "install", "--no-compile", "--no-cache-dir", "-r", "requirements-dev.txt"]
        if args.wheels:
            install.extend(["--no-index", "--find-links", str(args.wheels.resolve())])
        commands.extend([("install", install),
                         ("pip-check", [str(python), "-B", "-m", "pip", "check"]),
                         ("quality", [str(python), "-B", "-m", "scripts.check_project"])])
        if args.godot:
            for candidate in ("cand-001", "cand-002", "cand-003"):
                for scenario in ("smoke", "ollama_unavailable", "timeout", "evaluation_unavailable", "limit"):
                    commands.append((f"godot-{candidate}-{scenario}", [str(python), "-B", "-m", "scripts.check_godot",
                                     "--godot", str(args.godot.resolve()), "--candidate", candidate, "--scenario", scenario]))
                if args.with_live_godot:
                    commands.append((f"godot-{candidate}-live", [str(python), "-B", "-m", "scripts.check_godot", "--live",
                                     "--godot", str(args.godot.resolve()), "--candidate", candidate, "--model", args.model]))
        logs = []
        exit_code = 0
        for label, command in commands:
            print(f"Comprobando {label}...", flush=True)
            started = monotonic()
            result = subprocess.run(command, cwd=snapshot, env=environment_values, capture_output=True, text=True, encoding="utf-8")  # nosec B603
            logs.append(result.stdout + result.stderr)
            (proof / f"{label}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
            summary["checks"].append({"name": label, "exit_code": result.returncode,
                                      "elapsed_seconds": round(monotonic() - started, 2)})
            print(f"{label}: {result.returncode}", flush=True)
            if result.returncode:
                exit_code = result.returncode
                break
        (reports / "clean-install.txt").write_text("\n".join(logs), encoding="utf-8")
        if (snapshot / "reports").is_dir():
            shutil.copytree(snapshot / "reports", proof / "checks")
        summary.update(files_copied=copied if not args.published else None, exit_code=exit_code,
                       python=str(python), finished_at_utc=datetime.now(timezone.utc).isoformat(),
                       readme_sha256=hashlib.sha256((snapshot / "README.md").read_bytes()).hexdigest(),
                       venv_config=(environment / "pyvenv.cfg").read_text(encoding="utf-8") if (environment / "pyvenv.cfg").is_file() else None)
        if args.published:
            summary["clean_after_checks"] = not subprocess.run(
                [git, "status", "--porcelain"], cwd=snapshot, check=True, capture_output=True, text=True).stdout.strip()  # nosec B603
            if not summary["clean_before_install"] or not summary["clean_after_checks"]:
                exit_code = 1
        if not summary["venv_config"] or "include-system-site-packages = false" not in summary["venv_config"]:
            exit_code = 1
        summary["exit_code"] = exit_code
        (reports / "clean-install.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (proof / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Instalación limpia: {exit_code}; {copied} archivos de proyecto.")
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
