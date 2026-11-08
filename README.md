# Simulador de entrevistas con candidato virtual

Agente educativo en Python con candidato ficticio, clasificación descriptiva, evaluación provisional e historial por entrevista. La API conecta una futura interfaz de Godot 4 con el arnés existente. Incluye un cliente de transporte GDScript para incorporarlo a las escenas.

## Inicio rápido

Requiere Git, Python **3.14** y, para generar respuestas locales, Ollama con el modelo elegido. Ejecutar desde la raíz de una copia del repositorio.

En PowerShell:

```powershell
git clone https://github.com/Italoktrone/Simulador_entrevista.git
cd Simulador_entrevista
py -3.14 -m venv .venv
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -m pip install --no-compile -r requirements-dev.txt
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma3n:e2b'
ollama pull gemma3n:e2b
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

En Linux, crear el entorno con `python3.14 -m venv .venv`, usar `.venv/bin/python` y definir las mismas variables con `export`. Ollama debe estar iniciado antes de enviar preguntas. `/health` comprueba el servicio Python y declara que la disponibilidad del modelo todavía no se ha sondeado.

Abrir [la documentación interactiva de la API](http://127.0.0.1:8000/docs). Desde otra terminal de PowerShell se puede iniciar una entrevista y enviar un turno:

```powershell
$base = 'http://127.0.0.1:8000'
$inicio = @{ request_id = [guid]::NewGuid().ToString(); classify = $true; evaluate = $true } | ConvertTo-Json
$sesion = Invoke-RestMethod ($base + '/sessions') -Method Post -ContentType 'application/json' -Body $inicio
$turno = @{ session_id = $sesion.session_id; request_id = [guid]::NewGuid().ToString(); question = '¿Qué hiciste en MesaFaro?'; use_rag = $true } | ConvertTo-Json
$resultado = Invoke-RestMethod ($base + '/run') -Method Post -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($turno))
$resultado
Invoke-RestMethod ($base + '/sessions/' + $sesion.session_id + '/close') -Method Post
```

Clasificación y evaluación pueden realizar llamadas adicionales al modelo. Para comprobar únicamente la conversación, iniciar con `classify = $false` y `evaluate = $false`. Conservar `request_id` al repetir una solicitud cuya respuesta se perdió.

Los proveedores UNAB IA y OpenAI se seleccionan en el proceso Python con sus variables y activación externa explícita. Las claves pertenecen al servidor. La [guía de operación](docs/operacion.md#api-y-godot) describe su configuración y la integración con Godot.

## API y contratos

| Operación | Uso |
| --- | --- |
| `GET /health` | Estado del servicio Python. |
| `GET /metadata` | Manifiesto, capacidades, límites y herramienta declarada. |
| `POST /sessions` | Crear entrevista con un `request_id` UUID. |
| `GET /sessions/{session_id}` | CV público, puesto, estado y turnos. |
| `POST /run` | Enviar una pregunta con sesión e identificador de solicitud. |
| `POST /sessions/{session_id}/close` | Cerrar y guardar la entrevista. |
| `GET /logs?session_id=...` | Consultar eventos JSONL estructurados. |
| `POST /tools/search_documents` | Recuperar pasajes documentales con fuentes. |

El [manifiesto](agent/manifest.yaml), los schemas de [entrada](agent/input.schema.json) y [salida](agent/output.schema.json), los [ejemplos válidos e inválidos](agent/examples.json) y [tools.yaml](agent/tools.yaml) definen la interfaz.

La [herramienta documental](harness/document_search.py) selecciona pasajes del CV público y del puesto mediante búsqueda léxica. Con `use_rag` activo llegan al modelo del candidato como datos delimitados. `sources` muestra los documentos recuperados. La exactitud de las afirmaciones del modelo requiere revisión adicional.

Las sesiones activas y los resultados idempotentes viven en un único proceso. Un reinicio requiere crear otra entrevista. Los registros y las sesiones cerradas quedan en `outputs/api/`, excluido de Git. Se admiten hasta cien entrevistas por proceso. `INTERVIEW_API_TOKEN` permite exigir `Authorization: Bearer ...`.

## Verificación reproducible

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_project
```

Ejecuta pytest, Ruff y Bandit, comprueba los schemas y evalúa los casos de recuperación documental. Las pruebas usan modelos simulados y bloquean HTTP real. Los resultados técnicos quedan en `reports/`. GitHub Actions ejecuta el mismo comando y conserva los informes como artefactos.

Para validar una instalación independiente del estado local:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_clean_install
```

Exporta los archivos vigentes registrados y nuevos, instala dependencias en otro entorno y repite las comprobaciones. Excluye claves, `.venv`, logs y artefactos locales. Incluye cambios pendientes de commit. La validación de un clon remoto corresponde al workflow después de publicar esos cambios.

## Mapa del proyecto

| Ruta | Propósito |
| --- | --- |
| `agent/` | Instrucciones, manifiesto, contratos, ejemplos y herramienta. |
| `app/` | API HTTP y cliente GDScript para Godot. |
| `harness/` | Entrevista, modelos, contexto, clasificación, evaluación y documentos. |
| `schemas/` | Contratos internos del dominio. |
| `config/` | Escenarios, rúbricas y demostraciones. |
| `data/` | Perfil, puesto y casos de evaluación. |
| `tests/` | Pruebas unitarias y de integración. |
| `scripts/` | Consola, evaluación y verificación. |
| `reports/` | Resultados técnicos generados localmente y en CI. |
| `docs/` | Documentación agrupada por tema. |
| `outputs/` | Sesiones y evidencias locales. |

La consola está disponible con `python -m scripts.start_interview` y admite `--evaluate`. El selector de consola usa `config/llm.local.json`; la API lee variables del proceso Python.

## Documentación

| Tema | Contenido |
| --- | --- |
| [Estado, decisiones e historial](docs/estado-del-proyecto.md) | Continuidad, planificación, bitácora y cambios. |
| [Arquitectura](docs/arquitectura.md) | Componentes y funcionamiento del arnés. |
| [Operación y Godot](docs/operacion.md#api-y-godot) | API, cliente GDScript y configuración. |
| [Historial, sesiones y contexto](docs/contexto-y-sesiones.md) | Persistencia y resumen extractivo. |
| [Clasificador](docs/clasificador.md) | Contratos, referencias y regresiones. |
| [Evaluador](docs/evaluador.md) | Rúbrica, calibraciones y límites. |
| [Validación del candidato](docs/validacion-del-candidato.md) | Protocolo, casos y resultados históricos. |

Las evaluaciones educativas son provisionales. Los registros fechados describen las versiones y pruebas de su momento.
