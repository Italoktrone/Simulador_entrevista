# Simulador de entrevistas con candidato virtual

Agente educativo en Python con tres candidatos ficticios, clasificación descriptiva, evaluación provisional e historial por entrevista. Incluye una interfaz de escritorio en **Godot 4.7.2**, con selección de candidato y conectada al arnés Python mediante la API local.

## Inicio rápido

Requiere Git, Python **3.14**, Godot **4.7.2** y, para generar respuestas locales, Ollama con el modelo elegido. Ejecutar desde la raíz de una copia del repositorio. El desarrollo está en la rama **E2**; `main` conserva la versión inicial.

Si ya trabajas en una copia local que contiene `app/godot/project.godot`, utiliza esa carpeta y omite los dos comandos de clonación. Clonar crea otra copia y solo descarga los cambios publicados; los cambios locales sin commit no aparecen allí.

En PowerShell:

```powershell
git clone --branch E2 https://github.com/Italoktrone/Simulador_entrevista.git
cd Simulador_entrevista
py -3.14 -m venv .venv
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -m pip install --no-compile -r requirements-dev.txt
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
ollama pull gemma4:e4b
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Si ya clonaste y falta `requirements-dev.txt`, comprueba `git branch --show-current` y cambia con `git switch E2` antes de instalar. Si la instalación falla, resuelve ese error antes de iniciar la API: `No module named uvicorn` indica que sus dependencias todavía no están instaladas en ese entorno. El aviso de actualización de pip es informativo.

En Linux, crear el entorno con `python3.14 -m venv .venv`, usar `.venv/bin/python` y definir las mismas variables con `export`. Ollama debe estar iniciado antes de enviar preguntas. Se puede elegir otro modelo instalado mediante `OLLAMA_MODEL`. `/health` comprueba el servicio Python y declara que la disponibilidad del modelo todavía no se ha sondeado.

Dejar esa terminal abierta. En Godot, **Importar** el archivo [app/godot/project.godot](app/godot/project.godot), abrir el proyecto y pulsar **F5**. Con el indicador «Servicio conectado», elegir uno de los tres nombres y consultar las pestañas Currículum/Puesto. Pulsar **Iniciar entrevista** y enviar una pregunta con Enter o Enviar. La respuesta y el análisis se muestran por separado; las fuentes consultadas aparecen debajo de la conversación. **Cerrar y guardar** permite finalizar y elegir otro candidato.

| Identificador | Candidato ficticio | Experiencia principal |
| --- | --- | --- |
| `cand-001` | Nicolás Vera Soto | Desarrollo web junior con Python y Flask. |
| `cand-002` | Camila Rojas Medina | Pruebas de software y automatización de APIs. |
| `cand-003` | Diego Muñoz Leiva | Soporte de datos, consultas SQL y scripts. |

Los tres postulan al mismo cargo junior, con fortalezas y límites diferentes. La selección queda fija durante cada entrevista. El interruptor **Analizar mis preguntas**, configurable antes de iniciar, permite comprobar solo la conversación cuando se desactiva. La ambientación y los personajes animados corresponden a una mejora visual posterior.

Abrir [la documentación interactiva de la API](http://127.0.0.1:8000/docs). Desde otra terminal de PowerShell se puede iniciar una entrevista y enviar un turno:

```powershell
$base = 'http://127.0.0.1:8000'
$inicio = @{ request_id = [guid]::NewGuid().ToString(); candidate_id = 'cand-001'; classify = $true; evaluate = $true } | ConvertTo-Json
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
| `GET /candidates` | Catálogo público de los tres perfiles, sin crear sesiones ni llamar al modelo. |
| `GET /candidates/{candidate_id}` | CV público y puesto del candidato elegido. |
| `POST /sessions` | Crear entrevista con un `request_id` UUID. |
| `GET /sessions/{session_id}` | CV público, puesto, estado y turnos. |
| `POST /run` | Enviar una pregunta con sesión e identificador de solicitud. |
| `POST /sessions/{session_id}/close` | Cerrar y guardar la entrevista. |
| `GET /logs?session_id=...` | Consultar eventos JSONL estructurados. |
| `POST /tools/search_documents` | Recuperar pasajes documentales con fuentes. |

El [manifiesto](agent/manifest.yaml), los schemas de [turno](agent/input.schema.json), [salida](agent/output.schema.json) y [creación de sesión](agent/session.schema.json), los [ejemplos válidos e inválidos](agent/examples.json) y [tools.yaml](agent/tools.yaml) definen la interfaz. `POST /sessions` acepta `candidate_id`; si se omite conserva `cand-001`. Un identificador desconocido devuelve `404 candidate_not_found`; un formato inválido devuelve 422. El catálogo usa rutas permitidas explícitas.

La [herramienta documental](harness/document_search.py) selecciona pasajes del CV público y del puesto mediante búsqueda léxica. Con `use_rag` activo llegan al modelo del candidato como datos delimitados. `sources` muestra los documentos recuperados. La exactitud de las afirmaciones del modelo requiere revisión adicional.

Las sesiones activas y los resultados idempotentes viven en un único proceso. Un reinicio requiere crear otra entrevista. Los registros y las sesiones cerradas quedan en `outputs/api/`, excluido de Git. Se admiten hasta cien entrevistas por proceso. `INTERVIEW_API_TOKEN` permite exigir `Authorization: Bearer ...`.

## Verificación reproducible

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_project
```

Ejecuta pytest, Ruff y Bandit, comprueba los schemas y evalúa los casos de recuperación documental. Las pruebas usan modelos simulados y bloquean HTTP real. Los resultados técnicos quedan en `reports/`. GitHub Actions ejecuta el mismo comando y conserva los informes como artefactos.

Para comprobar la interfaz con el ejecutable de Godot instalado:

```powershell
$godot = 'C:\ruta\Godot_v4.7.2-stable_win64_console.exe'
.\.venv\Scripts\python.exe -B -m scripts.check_godot --godot $godot
.\.venv\Scripts\python.exe -B -m scripts.check_godot --godot $godot --candidate cand-002 --live --model gemma4:e4b
```

El primer comando abre una API temporal y recorre los controles reales de Godot con modelos simulados: catálogo, CV de cada perfil, selección, pregunta, evaluación, cierre y reintentos tras respuestas perdidas o incompatibles. Verifica que se conserve una sola sesión y un solo turno del candidato elegido. `--candidate cand-001`, `cand-002` o `cand-003` elige el perfil del recorrido. `--live` utiliza Ollama local; requiere el modelo instalado y puede tardar varios minutos. Resultados y sesiones: `reports/godot/{simulated|live}/{candidate_id}/`. `--screenshot` añade una captura con renderizado y requiere un escritorio. Estos comandos son independientes de las comprobaciones Python de GitHub Actions.

`--scenario ollama_unavailable`, `timeout` y `evaluation_unavailable` provocan fallos aislados y comprueban los mensajes, la conservación de datos y la recuperación. `--scenario limit` recorre veinte envíos, provoca un fallo de evaluación en el último y comprueba el rechazo del siguiente. Usan modelos simulados; el primer escenario además intenta una conexión TCP real a un puerto sin Ollama. No detienen el servicio del usuario. Sus resultados quedan en `reports/godot/verification/`.

Para repetir las preguntas conocidas de aislamiento con Ollama real:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_npc_isolation --model gemma4:e4b --questions P03 P08 P09 P12 --with-history
```

Conserva la primera salida, las fuentes y las sesiones; no repite generaciones para mejorar un resultado. La revisión de precisión y autoría se hace contra cada perfil. La validación de citas rechaza rutas internas e identificadores que no estén entre los documentos recuperados, conservando el texto original rechazado en la sesión para auditoría. No sustituye el cotejo semántico.

Para validar una instalación independiente del estado local:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_clean_install
```

Exporta los archivos vigentes registrados y nuevos, instala dependencias en otro entorno y repite las comprobaciones. Excluye claves, `.venv`, logs y artefactos locales. Esta exportación incluye cambios pendientes de commit; para comprobar únicamente código publicado se utiliza el modo siguiente.

Para comprobar específicamente la versión publicada de E2 desde un clon remoto y un entorno nuevo, añadir `--published`:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_clean_install --published --branch E2 --godot $godot --with-live-godot --model gemma4:e4b
```

Repite la instalación sin caché de pip, la suite técnica y, por cada candidato, el recorrido normal, los tres fallos, veinte preguntas y una conversación con Ollama real. Conserva el commit clonado y los resultados en `reports/published-install/`, con un resumen en `reports/clean-install.json`. El clon y su entorno temporal se eliminan al terminar. Omitir `--with-live-godot` permite comprobar solo modelos simulados; omitir `--godot` limita la revisión a Python. El workflow de GitHub verifica Python en Windows y Linux; estas comprobaciones locales añaden Godot y Ollama.

## Mapa del proyecto

| Ruta | Propósito |
| --- | --- |
| `agent/` | Instrucciones, manifiesto, contratos, ejemplos y herramienta. |
| `app/` | API HTTP y proyecto de interfaz Godot con escena, controles y cliente HTTP. |
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
| [Operación y Godot](docs/operacion.md#api-y-godot) | Uso de la interfaz, API, reintentos y configuración. |
| [Historial, sesiones y contexto](docs/contexto-y-sesiones.md) | Persistencia y resumen extractivo. |
| [Clasificador](docs/clasificador.md) | Contratos, referencias y regresiones. |
| [Evaluador](docs/evaluador.md) | Rúbrica, calibraciones y límites. |
| [Validación del candidato](docs/validacion-del-candidato.md) | Protocolo, casos y resultados históricos. |

Las evaluaciones educativas son provisionales. Los registros fechados describen las versiones y pruebas de su momento.
