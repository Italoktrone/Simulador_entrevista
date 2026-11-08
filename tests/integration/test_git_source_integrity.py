"""Comprobar las fuentes aprobadas tras la conversión real de Git al extraerlas."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

from harness.classifier_few_shot import load_few_shot
from harness.evaluator_few_shot import load_evaluator_examples
from harness.scoring import load_rubric


ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    "config/classifier_few_shot.json",
    "config/evaluator_few_shot.json",
    "data/reference_questions/clasificacion_basica.json",
    "data/reference_questions/evaluacion_calidad_aprobada.json",
    "data/reference_questions/evaluator_demonstrations.json",
    "data/jobs/desarrollador_junior.json",
)


@pytest.mark.parametrize("autocrlf", ["true", "false", "input"])
def test_git_checkout_keeps_approved_examples_valid(tmp_path, autocrlf):
    git = shutil.which("git")
    if git is None:
        pytest.skip("La regresión de extracción requiere Git.")
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    for relative in SOURCES:
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Simular un editor de Windows antes de añadir las fuentes al índice.
        raw = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        destination.write_bytes(raw.replace(b"\n", b"\r\n"))

    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def run(*args):
        subprocess.run(
            [git, "-c", f"core.autocrlf={autocrlf}", "-c", "core.safecrlf=false",
             "-C", str(repository), *args],
            env=environment, check=True, capture_output=True, text=True,
        )

    run("init", "--quiet", "--template=")
    run("add", "--", ".gitattributes", *SOURCES)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    run("checkout-index", "--all", f"--prefix={checkout.as_posix()}/")

    for relative in SOURCES:
        assert b"\r" not in (checkout / relative).read_bytes()
    _, evaluator, _ = load_evaluator_examples(
        load_rubric(), checkout / SOURCES[1], checkout / SOURCES[3],
        checkout / SOURCES[4], checkout / SOURCES[5],
    )
    _, classifier = load_few_shot(checkout / SOURCES[0], checkout / SOURCES[2])
    assert evaluator["enabled"] and len(evaluator["case_ids"]) == 6
    assert classifier["enabled"] and len(classifier["case_ids"]) == 6
