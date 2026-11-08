"""Comprobar el recorrido de la interfaz Godot contra la API local real."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess  # nosec B404
import sys
from threading import Thread
from time import monotonic, sleep

import uvicorn
from fastapi.responses import JSONResponse

from app.main import create_app
from harness.candidate_catalog import CANDIDATES, load_candidate_setup
from harness.document_search import GroundedClient
from harness.llm.client import LLMResponse
from harness.session_log import load_session


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "app/godot"


def simulated_factory(options, *, scenario="smoke", offline_url=None):
    from harness.prompt_builder import load_instructions
    from harness.question_evaluator import QuestionEvaluator
    from harness.runtime import InterviewRuntime
    from harness.hybrid_question_classifier import HybridQuestionClassifier
    from harness.llm_question_classifier import LLMQuestionClassifier
    from tests.evaluation_fixtures import EvaluationClient
    from tests.integration.test_pre_response_classification import SemanticClient
    from harness.llm.client import LLMConnectionError
    from harness.llm.config import OllamaSettings
    from harness.llm.ollama_client import OllamaClient

    class Candidate:
        calls = 0

        def generate(self, messages):
            self.calls += 1
            if self.calls == 1 and scenario == "unsupported_claim":
                return LLMResponse("El desarrollador y yo cambiamos la consulta y añadimos una prueba de regresión.",
                                   "simulado", "ollama", 0.01)
            if self.calls == 1 and scenario == "ollama_unavailable":
                # Conexión TCP real a un puerto reservado sin servidor escuchando.
                with OllamaClient(OllamaSettings(base_url=offline_url, connection_retries=0,
                                                connect_timeout_seconds=1.0)) as unavailable:
                    return unavailable.generate(messages)
            if self.calls == 1 and scenario == "timeout":
                sleep(2.0)
            name = load_candidate_setup(options.candidate_id).candidate.to_dict()["name"]
            content = messages[0]["content"]
            source = ""
            if "DOCUMENTOS_PUBLICOS_RECUPERADOS_JSON:\n" in content:
                documents = json.loads(content.split("DOCUMENTOS_PUBLICOS_RECUPERADOS_JSON:\n", 1)[1].split("\nFIN_DOCUMENTOS_PUBLICOS_RECUPERADOS_JSON", 1)[0])
                source = f" [{documents[0]['document_id']}] [document_id: {documents[0]['document_id']}]" if documents else ""
            return LLMResponse(f"Soy {name}. He utilizado Git durante el desarrollo del proyecto. [b]Texto literal[/b]{source}",
                               "simulado", "ollama", 0.01)

    class Evaluation(EvaluationClient):
        calls = 0

        def generate(self, messages):
            self.calls += 1
            if ((scenario == "evaluation_unavailable" and self.calls == 1)
                    or (scenario == "limit" and self.calls == 20)):
                raise LLMConnectionError("Fallo de evaluación provocado para la verificación.")
            return super().generate(messages)

    @contextmanager
    def resources():
        grounded = GroundedClient(Candidate())
        settings = {}
        if options.classify or options.evaluate:
            settings["classifier"] = HybridQuestionClassifier(LLMQuestionClassifier(SemanticClient()))
        if options.evaluate:
            settings["evaluator"] = QuestionEvaluator(Evaluation())
        yield InterviewRuntime(load_candidate_setup(options.candidate_id), load_instructions(), grounded, **settings), grounded

    return resources()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, help="Ruta del ejecutable de Godot 4.7.2")
    parser.add_argument("--live", action="store_true", help="Usar el modelo local de Ollama en vez de modelos simulados")
    parser.add_argument("--model", default="gemma4:e4b")
    parser.add_argument("--candidate", choices=tuple(CANDIDATES), default="cand-001")
    parser.add_argument("--question", default="¿Has utilizado Git?", help="Pregunta del recorrido normal; útil para comprobar regresiones desde la interfaz")
    parser.add_argument("--no-evaluation", action="store_true", help="En modo real, comprobar solo la conversación")
    parser.add_argument("--screenshot", action="store_true", help="Renderizar y capturar la interfaz (requiere escritorio)")
    parser.add_argument("--scenario", choices=("smoke", "ollama_unavailable", "timeout", "evaluation_unavailable", "unsupported_claim", "limit"),
                        default="smoke", help="Provocar fallos o comprobar veinte turnos con modelos simulados")
    args = parser.parse_args(argv)
    if not args.question.strip() or len(args.question) > 4000:
        parser.error("La pregunta debe contener entre 1 y 4000 caracteres.")
    if args.live and args.scenario != "smoke":
        parser.error("Los escenarios provocados son aislados y utilizan modelos simulados.")
    if args.no_evaluation and not args.live:
        parser.error("--no-evaluation se utiliza junto con --live.")
    executable = args.godot or os.environ.get("GODOT_BIN") or shutil.which("godot") or shutil.which("godot4")
    if not executable or not Path(executable).is_file():
        parser.error("Indica --godot con la ruta del ejecutable instalado.")
    executable = str(Path(executable).resolve())
    reports = ROOT / "reports/godot" / ("live" if args.live else "simulated") / args.candidate
    if args.scenario != "smoke":
        reports = ROOT / "reports/godot/verification" / args.scenario / args.candidate
    reports.mkdir(parents=True, exist_ok=True)
    report_path = reports / "interface.json"
    if report_path.exists():
        report_path.unlink()

    # Los dos modos usan una API aislada y guardan sus sesiones en reports/.
    api_token = secrets.token_urlsafe(32)
    # Reservar un puerto sin listen evita tocar el Ollama que usa el usuario.
    offline_socket = socket.socket()
    offline_socket.bind(("127.0.0.1", 0))
    offline_url = f"http://127.0.0.1:{offline_socket.getsockname()[1]}"
    if args.live:
        os.environ.update(LLM_PROVIDER="ollama", LLM_ALLOW_EXTERNAL_API="false", OLLAMA_MODEL=args.model)
        application = create_app(directory=reports / "api", token=api_token)
    else:
        application = create_app(directory=reports / "api", token=api_token,
                                 factory=lambda options: simulated_factory(options, scenario=args.scenario, offline_url=offline_url))
    requests = {}
    if not args.live:
        @application.middleware("http")
        async def lose_first_response(request, call_next):
            # La API completa la operación; se pierde su respuesta para probar la idempotencia.
            route = request.url.path
            payload = await request.json() if request.method == "POST" else {}
            requests.setdefault(route, []).append(payload)
            response = await call_next(request)
            inject = args.scenario == "smoke" and (route in ("/health", "/sessions", "/run") or route.endswith("/close"))
            if inject and len(requests[route]) == 1 and response.status_code < 400:
                if route == "/run":
                    return JSONResponse({"incompatible": True})
                return JSONResponse({"error": {"code": "internal_error"}}, status_code=503)
            return response
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = listener.getsockname()[1]
        config = uvicorn.Config(application, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        worker = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        worker.start()
        deadline = monotonic() + 15
        while not server.started:
            if not worker.is_alive() or monotonic() > deadline:
                raise RuntimeError("La API de comprobación no pudo iniciar.")
            sleep(0.05)
        environment = dict(os.environ, INTERVIEW_API_URL=f"http://127.0.0.1:{port}",
                           INTERVIEW_API_TOKEN=api_token, PYTHONDONTWRITEBYTECODE="1")
        environment["GODOT_SMOKE_NO_EVALUATION"] = "1" if args.no_evaluation else "0"
        display = ["--rendering-method", "gl_compatibility", "--windowed", "--resolution", "1280x820"] if args.screenshot else ["--headless"]
        script = "res://tests/Smoke.gd" if args.scenario == "smoke" else "res://tests/Verification.gd"
        command = [executable, *display, "--path", str(PROJECT), "--script", script,
                   "--", f"--report={report_path.as_posix()}", f"--candidate={args.candidate}", f"--scenario={args.scenario}", f"--question={args.question}"]
        if args.live:
            command.append("--live")
        if args.screenshot:
            command.append(f"--screenshot={(reports / 'interface.png').as_posix()}")
        startup = None
        if os.name == "nt":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
        started = monotonic()
        try:
            result = subprocess.run(command, env=environment, cwd=ROOT, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", startupinfo=startup,
                                    timeout=720 if args.live else 90)  # nosec B603
            (reports / "godot.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        finally:
            server.should_exit = True
            worker.join(timeout=30)
            offline_socket.close()
        if result.returncode or not report_path.is_file():
            print(result.stdout + result.stderr)
            return result.returncode or 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report["ok"]:
        return 1
    saved = reports / "api/sessions" / f"session-{report['session_id']}.json"
    session = load_session(saved)
    expected_attempts = {"smoke": 1, "timeout": 1, "ollama_unavailable": 2, "evaluation_unavailable": 2, "unsupported_claim": 2, "limit": 20}[args.scenario]
    if (session["status"] != "closed" or session["candidate_id"] != args.candidate
            or len(session["attempts"]) != expected_attempts or session["attempts"][-1]["status"] != "completed"):
        raise RuntimeError("El recorrido no conservó la sesión esperada.")
    if not args.live and args.scenario == "smoke":
        mutations = [bodies for route, bodies in requests.items() if route in ("/sessions", "/run") or route.endswith("/close")]
        if len(application.state.service.sessions) != 1 or not all(len(bodies) == 2 and bodies[0] == bodies[1] for bodies in mutations):
            raise RuntimeError("Los reintentos duplicaron una operación o cambiaron su contenido.")
        report["retry_verified"] = True
    if args.scenario == "timeout":
        bodies = requests["/run"]
        if len(bodies) != 2 or bodies[0] != bodies[1]:
            raise RuntimeError("El reintento tras timeout cambió o duplicó la pregunta.")
        report["retry_verified"] = True
    if args.scenario == "ollama_unavailable":
        if session["attempts"][0]["status"] != "error" or not any(i["code"] in {"connection_error", "timeout"} for i in session["attempts"][0]["issues"]):
            raise RuntimeError("No se registró el proveedor local inaccesible.")
    if args.scenario == "unsupported_claim":
        first = session["attempts"][0]
        rejected = any(event.get("error_code") == "unsupported_candidate_claim"
                       for event in application.state.service.logs(report["session_id"]))
        if first["status"] != "error" or not first["response"] or first["issues"][0]["code"] != "invalid_response" or not rejected:
            raise RuntimeError("No se conservó la respuesta rechazada por su atribución de acciones.")
    if args.scenario in ("evaluation_unavailable", "limit"):
        index = 0 if args.scenario == "evaluation_unavailable" else -1
        if session["evaluations"][index]["status"] != "no_disponible" or not session["attempts"][index]["response"]:
            raise RuntimeError("El fallo del evaluador perdió la respuesta.")
    if args.scenario == "limit" and (len(requests["/run"]) != 21 or session["close_reason"] != "question_limit"):
        raise RuntimeError("No se comprobó el rechazo del envío 21.")
    if not args.live:
        report["http_requests"] = requests
    report.update(session_saved=True, model=args.model if args.live else "simulated",
                  godot=executable, scenario=args.scenario, question=args.question if args.scenario == "smoke" else None,
                  session_file=str(saved), elapsed_seconds=round(monotonic() - started, 2))
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Godot: recorrido completo, sesión guardada. Evidencia: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
