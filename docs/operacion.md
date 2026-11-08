# Instalación, consola y proveedores

[Índice general](../README.md#documentación)

Las secciones fechadas y los registros de etapas describen el estado y las pruebas de su momento.

## Contenido

- [API HTTP y conexión con Godot](#api-y-godot)
- [Entorno de Python del proyecto](#entorno-python)
- [Entrevista en consola](#consola)
- [Elegir Ollama o UNAB IA desde la terminal](#selector-proveedor)
- [Primera conexión local con Ollama](#conexion-ollama)
- [API externa opcional: OpenAI Responses](#conexion-api-opcional)
- [Tiempos de Ollama y preparación para la demostración](#rendimiento-local)
- [UNAB IA: consumo y respuestas rechazadas](#unab-consumo-y-salidas-vacias)

<a name="api-y-godot"></a>

## API HTTP y conexión con Godot

La API de `app/main.py` utiliza el controlador de `harness/runtime.py`. El [inicio rápido](../README.md#inicio-rápido) prepara el entorno, Ollama y Uvicorn. Usar un único proceso con `--workers 1`, en `127.0.0.1:8000`. Las sesiones activas se mantienen en memoria. El máximo es de cien entrevistas por proceso, incluidas las cerradas conservadas para reintentos.

### Uso de la interfaz

El proyecto [app/godot/project.godot](../app/godot/project.godot) está preparado para Godot **4.7.2** con renderizado Compatibility. Importarlo desde el administrador de proyectos y pulsar **F5**, manteniendo la API y Ollama iniciados como indica el inicio rápido. La pantalla ofrece tres candidatos mediante controles nativos; el CV y el puesto se consultan antes de iniciar. La ambientación y los personajes animados quedan para una mejora visual posterior.

1. Al abrir, comprueba `GET /health` y muestra la conexión. Esto confirma el servicio Python; la disponibilidad del modelo se comprueba al preguntar. **Reconectar** repite esta comprobación.
2. Elegir uno de los tres nombres y revisar su CV y el puesto. Esta vista no crea una sesión ni consulta al modelo. Configurar **Analizar mis preguntas**: activado solicita clasificación y evaluación; desactivado comprueba solo la conversación. **Iniciar entrevista** fija el candidato elegido y crea la sesión. La selección se bloquea hasta cerrar.
3. Escribir una pregunta y pulsar **Enviar** o Enter. Mientras se procesa, aparecen la espera y los controles bloqueados. El candidato, el clasificador y el evaluador pueden tardar varios minutos; la espera del turno admite hasta diez minutos.
4. La conversación muestra la respuesta u orientación. El panel independiente muestra pertinencia, adecuación metodológica, claridad y neutralidad, más la sugerencia disponible. Las evaluaciones parciales o no disponibles conservan ese estado. No se calcula una nota de entrevista. Los textos del modelo se muestran sin interpretar marcas de formato. Las referencias exactas a documentos recuperados se retiran del diálogo visible y sus títulos aparecen en **Fuentes consultadas**; la respuesta original y los identificadores se conservan en la API y el registro.
5. **Cerrar y guardar** espera la confirmación de Python y habilita **Nueva entrevista**. Cerrar la ventana con una sesión abierta, sin solicitudes en curso, también solicita el guardado. Si hay una operación pendiente, se permite volver y reintentar antes de salir.

[Main.tscn](../app/godot/Main.tscn) define la pantalla; [Main.gd](../app/godot/Main.gd) controla la sesión y presenta los resultados. [InterviewApi.gd](../app/godot/InterviewApi.gd) crea su propio `HTTPRequest` y emite `request_started`, `received` y `failed`. Conserva las operaciones `metadata()`, `get_logs()` y `search_documents()` para ampliar la interfaz. La recuperación documental ya se utiliza en cada pregunta con `use_rag=true`; sus fuentes se conservan en el resultado de la API.

El cliente conserva la petición tras un error de transporte, un fallo de servidor o una respuesta incompatible. **Reintentar** llama a `retry_request()` con el mismo UUID y contenido y mantiene bloqueados los envíos nuevos hasta resolverla. El servidor devuelve el resultado ya calculado durante la vida de ese proceso. Un UUID reutilizado con otros datos devuelve `409 request_conflict`. Otra petición simultánea de la misma sesión devuelve `409 session_busy` y permite reintentar cuando termine el turno activo.

`scripts.check_godot` comprueba ese recorrido con una API temporal real y modelos simulados, incluyendo los tres CV, la selección bloqueada durante la sesión, la pérdida de la primera respuesta de inicio/cierre y una respuesta de turno incompatible después de que Python ya lo haya calculado. Comprueba los reintentos con idéntico contenido y la persistencia de una sola sesión y un solo turno del perfil elegido. `--candidate cand-002` o `cand-003` cambia el candidato del ensayo. `--live --model gemma4:e4b` realiza la entrevista con Ollama; `--no-evaluation` permite limitar ese modo a la conversación. `--screenshot` captura el renderizado cuando hay escritorio. Los comandos completos están en [Verificación reproducible](../README.md#verificación-reproducible). Las evidencias son locales en `reports/godot/{simulated|live}/{candidate_id}/`, excluidas de Git.

Godot genera su caché de importación en `app/godot/.godot/`, ignorada por Git. Se puede borrar con Godot cerrado y se reconstruirá al abrir. Los archivos `.gd.uid` sí se conservan para mantener las referencias a scripts.

Al alcanzar veinte preguntas o cerrar voluntariamente, la sesión se valida y se guarda en `outputs/api/sessions/`. Los eventos quedan en `outputs/api/logs/` en JSONL con fecha UTC, `session_id` y `run_id`. Incluyen huella de pregunta, estado y documentos recuperados. Los textos de preguntas y respuestas están en el registro y la consulta de esa sesión. Un reinicio o cierre abrupto pierde el estado activo y requiere iniciar otra entrevista. Los logs escritos siguen disponibles con su UUID. El cierre normal guarda las sesiones abiertas.

### Configuración y acceso

La API lee variables del proceso. Para Ollama usar `LLM_PROVIDER=ollama` y `OLLAMA_MODEL` con un modelo instalado. Para UNAB IA usar `LLM_PROVIDER=unab`, `LLM_ALLOW_EXTERNAL_API=true`, `UNAB_API_KEY`, `UNAB_MODEL` y opcionalmente `UNAB_MAX_OUTPUT_TOKENS`. OpenAI utiliza sus variables descritas en la sección de conexión externa. El archivo privado del selector de consola no se carga automáticamente al iniciar Uvicorn.

`INTERVIEW_API_TOKEN` exige `Authorization: Bearer ...`. Godot lee esa misma variable y, opcionalmente, `INTERVIEW_API_URL` para sustituir `http://127.0.0.1:8000`. Abrir Godot desde la terminal que define esas variables para que las herede. También se puede configurar `base_url` en el nodo Api. Las claves de los proveedores se configuran en Python. Esta versión prepara la integración de escritorio local. Una exportación web requiere además una política explícita de orígenes autorizados y HTTPS cuando se publique.

### Herramienta y recuperación documental

[agent/tools.yaml](../agent/tools.yaml) declara `search_documents`, disponible en `POST /tools/search_documents`. Recibe `query` y `limit` entre uno y cinco. Busca términos normalizados en secciones del puesto y del CV público. Cada pasaje incluye `document_id`, título, origen, texto y SHA-256. Una consulta sin coincidencias devuelve una lista vacía. El llamador no puede elegir rutas de archivo.

`GET /candidates` devuelve el catálogo y `GET /candidates/{candidate_id}` su CV público y puesto. `POST /sessions` acepta `candidate_id` con valor predeterminado `cand-001`; el identificador se conserva en la sesión y no cambia durante el diálogo. El catálogo de `harness/candidate_catalog.py` permite únicamente tres escenarios explícitos, valida sus relaciones y rechaza perfiles desconocidos antes de crear recursos del modelo. `search_documents` también acepta `candidate_id`; durante `/run` se utiliza exclusivamente el escenario de la sesión y la procedencia documental apunta al archivo de ese candidato.

Con `use_rag=true`, la API recupera hasta tres pasajes y los incorpora al contexto del candidato como datos delimitados. El modelo recibe instrucciones de apoyar sus afirmaciones en ellos y reconocer evidencia ausente. Los requisitos del puesto conservan su condición de requisitos. El clasificador y el evaluador conservan clientes independientes. `sources` identifica los pasajes recuperados, sin certificar que cada afirmación del modelo esté respaldada.

La suite `data/reference_questions/rag_basica.json` verifica recuperación y ausencia de resultados para consultas desconocidas. Las pruebas HTTP comprueban que los pasajes llegan al candidato, se conserva el historial, los errores quedan controlados y los reintentos no duplican generaciones. Las llamadas a modelos son simuladas.

### Contratos y evidencia de entrega

Los schemas públicos de `agent/` se generan desde `RunInput`, `RunOutput` y `SessionInput` en `app/contracts.py`. `scripts.check_project` comprueba su igualdad antes de ejecutar pruebas. `agent/examples.json` contiene entradas y salidas válidas e inválidas. Los resultados de pytest, Ruff, Bandit y recuperación quedan en `reports/`, excluidos de Git y conservados por GitHub Actions como artefactos.

Los archivos JSON versionados usan saltos de línea LF, fijados en `.gitattributes`, también al clonar en Windows. Las huellas de las referencias y demostraciones se comprueban sobre los bytes del archivo: editar conservando LF evita diferencias de formato entre equipos. La corrección de CI del 8 de noviembre de 2026 actualiza las dos huellas que se habían calculado con CRLF a las de los mismos JSON con LF; no cambia preguntas, niveles, razones ni ejemplos. Los registros históricos conservan sus huellas originales. GitHub Actions comprueba Windows y Linux y conserva un artefacto separado por sistema. La regresión realiza una extracción real con Git para `core.autocrlf=true`, `false` e `input`, y valida las demostraciones del evaluador y del clasificador.

`scripts.check_clean_install` exporta el estado local vigente, crea otro entorno, instala las dependencias y ejecuta la verificación completa. `--wheels RUTA` permite usar paquetes previamente descargados. El resumen distingue esa exportación de un clon remoto.

<a name="entorno-python"></a>

## Entorno de Python del proyecto

### Estado comprobado

El 30 de octubre de 2026 se creó `.venv` dentro del proyecto con Python **3.14.3**. Se instalaron las dependencias de `requirements.txt` en ese entorno y se verificó que `sys.prefix` es distinto de `sys.base_prefix`. La instalación se realizó en el entorno del proyecto, no en el Python global.

| Componente directo | Versión comprobada | Uso |
| --- | --- | --- |
| Python | 3.14.3 | Intérprete del proyecto |
| jsonschema | 4.26.0 | Validación estructural de los JSON |
| httpx | 0.28.1 | Comunicación HTTP con Ollama |
| pytest | 9.2.0 | Ejecución de las pruebas automatizadas |

`requirements.txt` fija las tres dependencias directas. Los paquetes auxiliares se instalaron automáticamente porque esas bibliotecas los necesitan. HTTPX se incorporó al comenzar la Etapa 5 y `pip check` volvió a confirmar que no hay dependencias incompatibles.

### Uso desde PowerShell

Trabajar desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
```

Se usa directamente `.\.venv\Scripts\python.exe`. No hace falta activar el entorno para ejecutar los comandos documentados ni modificar la configuración de ejecución de scripts de PowerShell.

Para comprobar el entorno ya creado:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; print('jsonschema:', version('jsonschema')); print('httpx:', version('httpx')); print('pytest:', version('pytest'))"
```

Resultado esperado:

```text
Python 3.14.3
No broken requirements found.
jsonschema: 4.26.0
httpx: 0.28.1
pytest: 9.2.0
```

Estos comandos comprueban el intérprete, las dependencias instaladas y sus versiones. No ejecutan todavía una entrevista ni una suite de pruebas.

### Recreación del entorno

Este procedimiento es para una copia del proyecto que todavía no tenga `.venv`; no es necesario repetirlo para la instalación ya comprobada. Requiere Python 3.14 instalado y conexión para descargar paquetes.

En PowerShell, desde la raíz del proyecto:

```powershell
py -3.14 -m venv .venv
Test-Path -LiteralPath '.venv\Scripts\python.exe'
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check --timeout 15 --retries 1 -r requirements.txt
```

La creación puede terminar sin mensajes. `Test-Path` debe mostrar `True`. La instalación debe terminar con un mensaje de paquetes instalados, o indicar que ya estaban satisfechos. Después se deben ejecutar las comprobaciones de la sección anterior.

Las versiones directas están fijadas; las versiones auxiliares podrían cambiar al resolver una instalación futura. El siguiente listado documenta lo realmente instalado en esta comprobación, sin afirmar que `requirements.txt` sea un bloqueo completo de todas las dependencias:

```text
anyio==4.15.1
attrs==26.1.0
certifi==2026.10.23
colorama==0.4.6
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
iniconfig==2.3.1
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
packaging==26.3
pluggy==1.7.0
Pygments==2.21.0
pytest==9.2.0
referencing==0.37.0
rpds-py==2026.9.1
typing_extensions==4.16.0
```

### Evidencia de verificación

- El ejecutable utilizado fue `C:\Users\franc\Downloads\Ejemplo_de_proyecto\.venv\Scripts\python.exe` y confirmó un entorno virtual activo por su ruta, sin activación de la terminal.
- `pip check` devolvió `No broken requirements found.`.
- `python -m pytest --version` devolvió `pytest 9.2.0`. Esto comprueba su disponibilidad; no equivale a haber ejecutado pruebas del proyecto.
- `Draft202012Validator.check_schema` aceptó los esquemas de candidato y puesto.
- `Draft202012Validator.validate` aceptó ambos JSON aprobados.
- Dos copias en memoria, cada una sin su identificador obligatorio, produjeron `ValidationError` por la regla `required`.
- Ambos JSON conservaron los contenidos y hashes documentados previamente. No se consultó un LLM.

Estas comprobaciones puntuales verifican el entorno y la aplicación básica de los esquemas desde Python. No implementan el módulo de carga ni resuelven las comprobaciones semánticas de fechas, identificadores y referencias pendientes.

El usuario confirmó en su PowerShell las versiones de Python, `jsonschema` y `pytest`, junto con la salida satisfactoria de `pip check`. Después se implementó el validador estructural compartido y se ejecutaron sus primeras 22 pruebas con éxito; véase [el registro de pruebas unitarias](validacion-del-candidato.md#unit).

### Incidencias y correcciones

La primera ejecución de `py -3.14 -m venv .venv` no pudo acceder al lanzador de Python desde el entorno restringido de la herramienta. Se repitió con el permiso correspondiente y terminó correctamente.

La primera descarga de dependencias no pudo resolver el servidor de paquetes (`getaddrinfo failed`). Se repitió con el permiso de conexión y la instalación terminó correctamente. No fue un error de los JSON ni una incompatibilidad de las versiones elegidas.

### Errores habituales al repetir los comandos

- Si PowerShell no encuentra `.\.venv\Scripts\python.exe`, comprobar la carpeta con `Get-Location` y la existencia del ejecutable con `Test-Path`. Si falta el entorno, seguir el procedimiento de recreación.
- Si aparece `No module named jsonschema` o `No module named pytest`, utilizar el ejecutable de `.venv` y repetir la instalación desde `requirements.txt` en ese entorno.
- Si falla la descarga, conservar el mensaje completo y comprobar la conexión antes de cambiar versiones o instalar otras herramientas.

### Referencias consultadas

- [Documentación oficial de venv](https://docs.python.org/3/library/venv.html).
- [jsonschema 4.26.0 en PyPI](https://pypi.org/project/jsonschema/4.26.0/).
- [pytest 9.2.0 en PyPI](https://pypi.org/project/pytest/9.2.0/).
- [HTTPX 0.28.1 en PyPI](https://pypi.org/project/httpx/0.28.1/).

---

<a name="consola"></a>

## Entrevista en consola

La consola organiza el menú, el CV, el puesto, el inicio y el estado de sesión mediante títulos, separadores y espacios. Cada intervención presenta por separado la pregunta del entrevistador, la respuesta del candidato y, cuando está activa, la evaluación provisional de la pregunta. El texto se ajusta a 78 columnas, sin recortar las respuestas ni necesitar colores, bibliotecas adicionales o una interfaz gráfica.

### Iniciar desde PowerShell

Desde la raíz del proyecto, con la configuración de proveedor ya preparada:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview --evaluate
```

El selector permite elegir **1: Ollama local** (también al pulsar Enter) o **2: UNAB IA**. La segunda opción envía el escenario y la conversación al servicio externo y requiere la configuración privada existente. La presentación no cambia el proveedor, los presupuestos ni la activación de evaluación. Al omitir `--evaluate` se conserva el modo sin evaluación educativa.

Para iniciar directamente con el modelo local:

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview --evaluate --extractive-context
```

Los comandos siguientes se escriben dentro del programa, después de abrirlo; no son comandos de PowerShell:

```text
/cv
/puesto
/iniciar
¿Dónde estudiaste y qué título obtuviste?
/respuestas
/respuesta 1
/sesion
/salir
```

### Comandos

| Comando | Resultado |
| --- | --- |
| `/cv` | CV público por secciones: resumen, formación, experiencia, conocimientos, herramientas y proyectos. |
| `/puesto` | Oferta por secciones: descripción, responsabilidades, requisitos, competencias y nivel esperado. |
| `/iniciar` | Habilita las preguntas y explica el límite. Repetirlo conserva el contador. |
| `/sesion` | Estado, preguntas disponibles, respuestas completas, incidencias y apartados de memoria, clasificación o evaluación si están activos. |
| `/respuestas` | Índice numerado de las preguntas enviadas, con el estado de su respuesta. |
| `/respuesta N` | Pregunta, respuesta completa y evaluación ya registrada del número solicitado; por ejemplo, `/respuesta 3`. |
| `/menu` o `/ayuda` | Muestra el menú con la descripción de cada comando. |
| `/salir` | Finaliza y guarda el registro local. |

Las consultas no generan respuestas nuevas, no llaman al modelo y no consumen preguntas. Si el número no existe o está mal escrito, se explica cómo consultar el índice. El CV usa únicamente los datos públicos aprobados del perfil.

### Lectura de una intervención

1. **INTERVENCIÓN 01**: contiene la pregunta del entrevistador, separada de los mensajes de espera.
2. **RESPUESTA DEL CANDIDATO | PREGUNTA 01/20**: muestra el texto completo y su tiempo de respuesta. En UNAB se conserva el dato de tokens cuando está informado.
3. **EVALUACIÓN DE LA PREGUNTA 01 | PROVISIONAL**: muestra el resultado, los cuatro niveles por criterio, la retroalimentación, la sugerencia y la reformulación cuando exista. Su tiempo se presenta aparte.

La respuesta del candidato aparece antes de esperar al evaluador. La evaluación valora la pregunta del entrevistador. Los niveles se leen del registro validado, sin volver a calcularlos ni cambiar la rúbrica o la Regla Crítica. Las evaluaciones parciales se identifican sin inventar un nivel global o completar criterios ausentes.

Una intervención atendida por el simulador sin enviarse al candidato lleva un aviso explícito y no consume el límite. Por eso el número de intervención puede diferir del número de pregunta enviada. `/respuesta N` siempre usa el número de pregunta enviada y busca su propia evaluación, aunque haya avisos intercalados.

Un intento fallido conserva su número en el índice. La consulta muestra su estado y no publica una respuesta incompleta como si fuera válida. Si falla únicamente la evaluación, la respuesta completa sigue disponible.

Vista previa con respuestas y evaluaciones de una sesión anterior, sin nuevas inferencias: [presentación de ejemplo](../outputs/previews/console-presentation.txt). Sus tiempos y resultados corresponden al registro original.

### Contador, guardado y errores

Se mantiene el máximo configurado de preguntas enviadas (20 en el escenario actual). Cada envío cuenta aunque falle la respuesta; los comandos y los avisos sin envío no cuentan. La consola finaliza automáticamente al alcanzar el límite, sin pedir otra entrada. Volver a ejecutar el programa crea una sesión independiente.

Al salir, al alcanzar el límite o al interrumpir con `Ctrl+C`, se presenta el resumen y se intenta guardar `outputs/sessions/session-<UUID>.json`. La confirmación incluye la ruta solo si el guardado terminó. El texto original de preguntas, respuestas y evaluaciones permanece en el registro; los saltos de línea añadidos a la presentación no lo modifican. La consulta por comandos se realiza durante la ejecución actual; no reanuda entrevistas cerradas.

Se conservan los mensajes de conexión, contexto, integridad y guardado. Una salida incompleta no se imprime como respuesta válida. La presentación no incorpora reintentos, cambios de modelo ni generaciones adicionales. El archivo del candidato se sigue comprobando antes y después de las llamadas y al cerrar.

### Componentes

| Archivo | Responsabilidad |
| --- | --- |
| `harness/application/console_view.py` | Formatos de texto y consulta de respuestas almacenadas; sin llamadas al modelo ni escritura del registro. |
| `harness/application/cli.py` | Menú, comandos, CV, puesto, sesión y orden de presentación. |
| `scripts/start_interview.py` | Selección del proveedor con las mismas opciones existentes. |
| `scripts/run_interview.py` | Preparación, cierre de recursos y guardado de la sesión. |
| `harness/runtime.py` | Conversación, clasificación, evaluación, contador e integridad; su lógica no cambia por esta presentación. |

El MVP del evaluador continúa cerrado y aceptado. Esta mejora corresponde a la legibilidad de la consola y no reabre su calibración semántica.

### Verificación de esta mejora

Se comprobaron 250 casos dirigidos de consola, CV público, sesión, clasificación previa, evaluación, selector, memoria, errores y guardado. La primera ronda aprobó 249 y detectó una expectativa de texto en una sola línea; se adaptó la comprobación a los saltos de línea de presentación. La repetición final de los 70 casos afectados pasó completa. El resultado más reciente de cada uno de los 250 casos es satisfactorio; no se suman las repeticiones como casos distintos ni se presenta esta selección como una nueva suite completa del proyecto.

Se verificó que la consulta no envíe llamadas al modelo ni consuma preguntas, que cada respuesta conserve su evaluación aunque existan avisos intercalados y que no se publiquen respuestas incompletas. La vista previa mantiene 78 columnas y conserva intacta su sesión fuente. Trece fuentes del evaluador y de la configuración verificables contra la versión de cierre permanecen intactas. No hubo inferencias reales ni lectura de la configuración privada.

Evidencia: `outputs/results/console-presentation-verification.json`; resultados de la revisión final: `outputs/results/console-presentation-final-tests.xml`.

---

<a name="selector-proveedor"></a>

## Elegir Ollama o UNAB IA desde la terminal

Ante consumo con respuestas rechazadas, consultar el [diagnóstico de salidas vacías y uso](#unab-consumo-y-salidas-vacias). El adaptador solicita ahora `reasoning_effort: none`, solicita un máximo configurable de 2048 tokens de salida y guarda métricas permitidas de las llamadas en un archivo separado al cerrar; su aplicación por UNAB requiere verificación real.

La ampliación añade un menú inicial. Reutiliza el candidato, historial y guardado existentes. El proveedor UNAB usa el protocolo Chat Completions; el adaptador Responses anterior conserva su funcionamiento independiente.

### Clave privada

El archivo local `config/llm.local.json` ya está creado con estos campos:

```json
{
  "local_model": "gemma4:e4b",
  "api_model": "gemma4:26b",
  "api_max_output_tokens": 2048,
  "api_key": ""
}
```

Escribir la clave entre las comillas de `api_key` y guardar. No pegarla en el chat. El archivo no se incorpora a Git; `config/llm.local.example.json` es la plantilla sin credenciales. La exclusión de Git no cifra el archivo: al compartir una copia o ZIP del proyecto hay que excluir `config/llm.local.json`.

Para abrirlo desde la raíz del proyecto:

```powershell
notepad .\config\llm.local.json
```

### Inicio

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview
```

El menú ofrece:

1. Modelo local — Ollama. Enter también selecciona esta opción. Funciona con la clave vacía, desactiva la API y activa la política normal de memoria extractiva.
2. API — UNAB IA. Esta selección autoriza el envío del escenario interno y la conversación al servicio externo para esa ejecución. Requiere la clave y usa `gemma4:26b`.

Después se conserva el menú `/cv`, `/puesto`, `/iniciar`, `/sesion`, `/salir`. No hace falta definir variables de entorno manualmente. La selección se aplica al proceso de entrevista, sin cambiar permanentemente el entorno de PowerShell. No se cambia de proveedor automáticamente si hay un error.

La URL está fijada en `https://quotas.devhub.cl/api/v1/`, con solicitud a `chat/completions`. La clave viaja en la cabecera Bearer, no en argumentos de terminal, configuración pública del cliente ni sesiones. Se usan TLS, redirecciones desactivadas y errores sin copiar cuerpos del servidor. No se instalan dependencias nuevas.

La API recibe el historial completo. No se supone una capacidad de contexto del servicio remoto ni se activa automáticamente el resumen con una capacidad inventada. El inicio anterior `scripts.run_interview` sigue disponible con sus opciones existentes.

### Estado de verificación

Las 21 pruebas nuevas usan respuestas HTTP simuladas: formato del endpoint, autenticación, salidas inválidas, límite de salida, errores y timeout sin repetir generación; selector, configuración inválida y guardado sin claves. No se ha utilizado una clave real ni se ha certificado la compatibilidad del servidor desplegado. La configuración facilitada por el usuario indica compatibilidad OpenAI; la consulta pública al endpoint no permitió obtener documentación. Si el servicio devuelve un error de endpoint o modelo, conservar su código y revisar el protocolo sin publicar la clave.

Verificación final: **759 passed in 59.65s**, incluidas las 21 comprobaciones nuevas. Perfil, puesto, configuración de entrevista e instrucciones mantienen sus huellas aprobadas. La llamada real a UNAB IA queda pendiente de que el usuario configure su clave y seleccione la opción 2.

El campo api_max_output_tokens es opcional: el archivo previo funciona con 2048 por defecto, sin modificar la clave. Solo afecta a UNAB; se muestra al elegir la opción 2. Rango admitido 16–4096. El usuario confirmó una pregunta compleja con presupuesto 2048: respuesta completa, 1255 tokens de salida y cero incidencias. Véase el diagnóstico enlazado al inicio; no se extrapola a todas las preguntas.

---

<a name="conexion-ollama"></a>

## Primera conexión local con Ollama

Guía de la conexión de la Etapa 5: una pregunta preparada con el escenario autorizado y una respuesta del modelo. La consola de la Etapa 6 ya utiliza ese adaptador y aplica el contador; véase [su guía de uso](#consola). Historial y persistencia siguen pendientes.

### Archivos y responsabilidades

| Archivo | Función |
| --- | --- |
| `harness/llm/config.py` | Parámetros explícitos, validados e inmutables de Ollama. |
| `harness/llm/client.py` | Interfaz `generate(messages)`, `LLMResponse` y errores comunes. |
| `harness/llm/messages.py` | Tipos y validación de los mensajes antes del envío. |
| `harness/llm/ollama_client.py` | Solicitud HTTP local y comprobación de la respuesta. |
| `harness/llm/factory.py` | Selección de proveedor; Ollama predeterminado y bloqueo del uso externo. |
| `scripts/smoke_test.py` | Una pregunta real y su evidencia técnica. |

`generate` recibe mensajes y devuelve texto final, proveedor, modelo, duración de la llamada, tokens informados y motivo de finalización. Si faltan métricas válidas, devuelve `None`; no calcula tokens a partir de caracteres. No devuelve el campo `thinking`.

### Parámetros iniciales

| Parámetro | Valor | Propósito |
| --- | --- | --- |
| Servicio | `http://127.0.0.1:11434` | Ollama en este equipo. |
| Modelo | `gemma3n:e2b` | Alternativa ya instalada para respuestas directas. |
| Espera de conexión | 5 segundos | Detectar que el servicio no responde al conectar. |
| Espera de lectura | 300 segundos | Permitir carga y generación local. |
| Contexto solicitado | 8192 tokens | Punto de partida a comprobar con métricas reales. |
| Salida máxima | 512 tokens | Limitar la respuesta de esta primera prueba. |
| Temperatura | 0,2 | Parámetro inicial; no garantiza hechos correctos. |
| Reintentos de conexión | 1 | Como máximo dos intentos de establecer conexión. |
| Permanencia solicitada | `15m` | Conservar el modelo en memoria entre consultas. |

Se envían `stream: false` y `think: false`, conforme al [contrato de chat de Ollama](https://docs.ollama.com/api/chat) y al [control de razonamiento](https://docs.ollama.com/capabilities/thinking). El constructor conserva los mensajes `system` y `user`. Solo para `gemma3n`, el transporte reúne el par inicial en un turno `user`, con una separación explícita para la pregunta original, porque su plantilla no ofrece un rol `system` nativo. No añade respuestas ficticias ni modifica el texto de la pregunta. Otros modelos conservan sus mensajes; véase el [registro de corrección](validacion-del-candidato.md#correccion-conducta).

Se corrigió la recomendación inicial después de inspeccionar los metadatos de los pesos: `qwen3:4b`, ID `359d7dd4bcda`, es **Qwen3-4B-Thinking-2507** (`general.finetune: Thinking`, versión `2507`). Su [ficha oficial](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507) indica que solo admite razonamiento. Los intentos con `think: false`, prefijo vacío y una variante de plantilla no produjeron una respuesta directa válida. La variante experimental fue retirada; no forma parte de la instalación final.

Se eligió explícitamente `gemma3n:e2b`, ID `719372f8c7de`, entre los modelos ya instalados. No se descargaron otros pesos ni se cambiaron los tres modelos originales. Este cambio de configuración conserva Ollama y la interfaz del cliente; no es un fallback automático tras un error. La calidad durante una entrevista completa sigue pendiente de evaluación.

La elección de contexto es provisional: el límite anunciado por el modelo no equivale al que conviene usar en la memoria disponible.

Los tiempos de espera son de operaciones de red, no un cronómetro global. Un tiempo de espera de lectura no se reintenta automáticamente, porque el servidor podría seguir generando. Los errores HTTP tampoco se repiten. El cliente rechaza respuestas sin texto o sin confirmación de finalización, y texto que contenga las marcas `<think>` o `</think>`. Conserva `done_reason: length`; el script marca ese resultado como `incomplete`, no imprime el texto como respuesta del candidato y termina con código de error. Estos controles no identifican todo posible razonamiento sin marcas ni garantizan que el contenido sea correcto.

La primera ejecución real agotó una espera inicial de 180 segundos. El registro confirmó la carga del modelo y el procesamiento de un contexto de 4311 tokens; la solicitud terminó cancelada cuando el cliente dejó de esperar. Se amplió la espera de lectura a 300 segundos para poder observar la respuesta completa. Esto no resuelve por sí mismo la latencia para una demostración.

El segundo intento terminó en 177,54 segundos con 512 tokens de salida y motivo `length`. Se observó texto de preparación de respuesta en lugar de una intervención válida del candidato. Las pruebas posteriores tampoco justificaron usar esos pesos para respuestas directas. Las evidencias se conservan en la bitácora; sus antiguos estados de éxito técnico no equivalen a respuestas satisfactorias. Se añadieron el rechazo de salidas cortadas en el script y el rechazo de marcas de razonamiento en el adaptador.

El adaptador Ollama no utiliza credenciales, redirecciones ni proxies del entorno, no descarga modelos ni cambia de proveedor. La fábrica no carga archivos `.env`. La alternativa OpenAI está implementada y desactivada por defecto; comparte la interfaz y se verificó con transporte simulado. Véase [la guía de API opcional](#conexion-api-opcional).

### Repetir las comprobaciones

En PowerShell, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.smoke_test
```

La suite debe mostrar **477 passed** y no consulta Ollama ni una API real. El comando de `smoke_test` sí requiere el servicio abierto y `gemma3n:e2b` instalado. Las variables del bloque seleccionan expresamente la ruta local. Muestra pregunta, respuesta, tiempo, tokens informados, motivo de finalización, comprobación del original y ruta de evidencia. Incluye las duraciones de carga, procesamiento y generación y los tokens reutilizados que informe Ollama. La primera carga puede tardar más que una ejecución con el modelo ya en memoria.

La respuesta esperada debe mencionar Ingeniería en Informática en el Instituto Profesional Horizonte Digital, conservando esos nombres literalmente. Si añade el mes de titulación, debe ser diciembre de 2025; no es obligatorio mencionarlo en esta pregunta. Las frases que rodean esos nombres pueden variar. La revisión debe comparar lo dicho con el perfil aprobado y detectar antecedentes añadidos. Una respuesta correcta no demuestra consistencia durante toda una entrevista.

Cada ejecución escribe un JSON nuevo en `outputs/results/`, incluso ante errores conocidos. No incluye el mensaje de sistema completo. La revisión semántica queda pendiente para el usuario. `completed` solo describe el éxito técnico de la llamada.

Desde la unidad del 31 de octubre se guardan también `instructions_text_sha256` y `system_message_sha256`: huellas SHA-256 del texto de instrucciones cargado y del mensaje de sistema preparado, codificados en UTF-8. Permiten distinguir contextos sin volcar los antecedentes internos al registro. La primera se calcula sobre el texto interpretado por Python, con saltos de línea normalizados por la lectura; no se presenta como huella de los bytes originales del archivo. La huella del candidato mantiene su significado anterior, sobre sus bytes originales.

### Resultados observados

Con Gemma, la primera llamada terminó en 43,15 s, con 4744 tokens de entrada y 37 de salida. La repetición con el modelo ya cargado e instrucciones 1.0.1 terminó en 15,89 s, entrada 4811 y salida 33. Ambas finalizaron con `stop` y conservaron el archivo original. Son dos mediciones de esta pregunta, no un promedio o una garantía de tiempo de respuesta.

Ambas respuestas cambiaron **Horizonte** por **Horizontes** en el nombre de la institución. La carrera y el mes de titulación coincidieron. El refuerzo genérico de nombres literales no corrigió esa discrepancia en la repetición y el usuario la confirmó de nuevo el 31 de octubre, en una llamada de 36,20 s. Esa diferencia quedó abierta al cerrar la primera unidad del cliente.

El 31 de octubre se añadió `literal_name_references` al final del JSON de contexto: un índice de denominaciones exactas derivado de los datos del perfil y puesto, con una ruta de origen por valor. Incluye nombres del candidato, instituciones, títulos, empresas, cargos y proyectos, y distingue los datos de la oferta. No contiene nombres mantenidos manualmente en el código ni selecciona una respuesta según la pregunta. El perfil completo permanece disponible y la respuesta no se modifica después de generarse.

Con ese contexto se ejecutaron tres consultas reales consecutivas de la misma pregunta en Gemma:

| Consulta | Tiempo de llamada | Entrada | Salida | Revisión de institución y título |
| --- | --- | --- | --- | --- |
| Primera | 20,08 s | 5073 | 24 | Ambos exactos |
| Segunda | 2,33 s | 5073 | 24 | Ambos exactos |
| Tercera | 1,95 s | 5073 | 24 | Ambos exactos |

Todas finalizaron con `stop`, conservaron el original y se registraron sin sustituciones de palabras. Las tres huellas del mensaje de sistema coincidieron. Las repeticiones reutilizaron el mismo contexto y el modelo ya cargado; sus tiempos no predicen la latencia de preguntas nuevas o una carga inicial.

La discrepancia no reapareció en estas tres pruebas del caso observado. Falta la comprobación del usuario y no se generaliza el resultado a todos los nombres, otras preguntas o una entrevista completa. Las evidencias anteriores permanecen como resultados históricos fallidos. Los archivos y el detalle de los intentos están en la bitácora.

El usuario confirmó después el nombre correcto y las 352 pruebas, pero una llamada tardó 275,82 s. Su registro técnico mostró 232,60 s de procesamiento del contexto y 14,31 s de generación. Se añadieron métricas opcionales y una permanencia solicitada de 15 minutos. Dos mediciones posteriores tardaron 55,54 s y 2,18 s, con reutilización de 5072 tokens en la repetición. La lentitud inicial sigue siendo variable y no se considera resuelta por ese cambio; véase [el diagnóstico de rendimiento](#rendimiento-local).

### Errores habituales

- **No se pudo conectar:** abrir Ollama y comprobar `ollama list` en PowerShell. Repetir el comando de prueba cuando el servicio responda. No es necesario instalar otro modelo.
- **Modelo no encontrado:** comprobar que `ollama list` incluya `gemma3n:e2b`. No se cambia automáticamente a otro modelo.
- **Tiempo de espera:** conservar el error y la evidencia. Comprobar la carga del equipo y `ollama ps` antes de repetir. No ejecutar varias pruebas simultáneas mientras la anterior sigue pendiente.
- **No module named httpx:** usar el Python de `.venv`; si falta la biblioteca, ejecutar `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` desde la raíz.
- **No se encuentra scripts.smoke_test:** comprobar la carpeta actual con `Get-Location` y usar `-m scripts.smoke_test` tal como aparece arriba.

### Fuentes técnicas

- [Errores de Ollama](https://docs.ollama.com/api/errors).
- [Tiempos de espera de HTTPX](https://www.python-httpx.org/advanced/timeouts/).
- [Transportes simulados de HTTPX](https://www.python-httpx.org/advanced/transports/).

Las pruebas simuladas verifican el programa y sus errores. Las mediciones reales y sus límites se registran por separado en la bitácora y en los archivos de evidencia.

---

<a name="conexion-api-opcional"></a>

## API externa opcional: OpenAI Responses

Unidad de la Etapa 5. El proveedor principal sigue siendo Ollama con `gemma3n:e2b`. La alternativa OpenAI está implementada y desactivada por defecto. Se verificó con un transporte HTTP simulado y claves ficticias; no se hizo una llamada real a OpenAI, ni se comprobó acceso, cuota, facturación o calidad de un modelo externo.

### Componentes

| Archivo | Responsabilidad |
| --- | --- |
| `harness/llm/config.py` | `OpenAISettings`, parámetros inmutables sin credenciales; el modelo es obligatorio. |
| `harness/llm/openai_client.py` | Adaptador HTTPX para `https://api.openai.com/v1/responses`. |
| `harness/llm/factory.py` | `create_client`, selección explícita y bloqueo del uso externo. |
| `harness/llm/client.py` | Contrato `generate(messages)`, respuesta común y errores, incluido acceso rechazado. |
| `scripts/smoke_test.py` | Una pregunta con el proveedor seleccionado y evidencia sin claves. |

Ambos adaptadores reciben los mismos mensajes. OpenAI los envía en `input`, solicita `store: false` y `stream: false`, y recupera únicamente bloques `output_text` de mensajes de asistente completados. Los elementos de razonamiento no se devuelven como respuesta. Estos campos siguen el [contrato documentado de Responses](https://developers.openai.com/api/docs/guides/migrate-to-responses).

Los estados externos incompletos o fallidos, rechazos sin texto de candidato y salidas de herramientas no solicitadas se comunican como errores; no se aceptan respuestas parciales. El adaptador tampoco acepta marcas de razonamiento en el texto. Esto no valida los hechos o la obediencia del modelo. `LLMResponse.finish_reason` conserva `completed`, el estado nativo de la respuesta externa; Ollama conserva su motivo, por ejemplo `stop`.

### Selección y activación explícita

La fábrica lee variables de la sesión del proceso. No carga archivos `.env`; `.env.example` documenta las variables sin activarlas.

| Variable | Valor predeterminado | Función |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | Selección exacta: `ollama` u `openai`. |
| `LLM_ALLOW_EXTERNAL_API` | `false` | Solo el texto exacto `true` habilita el uso externo al seleccionar OpenAI. |
| `OPENAI_MODEL` | Sin valor | Modelo compatible con Responses, obligatorio al habilitar la API. |
| `OPENAI_API_KEY` | Sin valor | Credencial, obligatoria al habilitar la API. |

La ruta Ollama no consulta el modelo ni la clave externa. Una clave por sí sola no activa OpenAI. Una selección desconocida o incompleta produce un error antes de enviar solicitudes. Si falla Ollama, el programa no cambia a OpenAI; si falla OpenAI, tampoco cambia de proveedor. Crear un cliente no genera una respuesta ni envía una solicitud.

La fábrica es el punto de entrada usado por el script. La clase `OpenAIClient` también permite uso programático explícito, con parámetros y credenciales recibidos por argumento; no descubre ni activa claves por su cuenta.

### Comprobación de esta unidad, manteniendo Ollama

En PowerShell, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.smoke_test
```

La suite debe mostrar **477 passed**: 464 casos unitarios y trece de integración. Las pruebas de HTTP son simuladas y no necesitan claves reales. El último comando consulta únicamente Ollama y muestra `Modelo local: gemma3n:e2b`, la respuesta y la comprobación del archivo original. La consola también utiliza la fábrica y conserva estas condiciones de activación externa; no solicita una clave por su cuenta.

Para comprobar la selección predeterminada sin consultar ningún modelo:

```powershell
.\.venv\Scripts\python.exe -c "from harness.llm.factory import create_client; cliente = create_client({}); print(cliente.provider); print(cliente.settings.model); cliente.close()"
```

Debe mostrar `ollama` y `gemma3n:e2b`. El diccionario vacío representa los valores predeterminados, sin leer otras variables de la sesión.

### Activación futura cuando se necesite

Este procedimiento está documentado para el momento en que se decida usar la API. Antes se debe elegir un modelo compatible, comprobar su disponibilidad y precio y disponer de una clave propia. No hay un modelo externo elegido por defecto ni una clave guardada en el proyecto. No es necesario ejecutar este bloque para verificar la unidad actual.

En PowerShell, desde la raíz, la entrada de la clave se oculta:

```powershell
$env:OPENAI_MODEL = Read-Host 'Identificador del modelo compatible con Responses'
$claveApiTemporal = Read-Host 'Clave API de OpenAI' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $claveApiTemporal).Password
Remove-Variable -Name claveApiTemporal
$env:LLM_PROVIDER = 'openai'
$env:LLM_ALLOW_EXTERNAL_API = 'true'
.\.venv\Scripts\python.exe -X utf8 -m scripts.smoke_test
```

Al ejecutar el último comando con esa selección se hace una llamada externa real, sujeta al uso y facturación de la cuenta. Solo se envía el contexto ficticio preparado para la entrevista. Estos comandos no se ejecutaron en esta unidad. La clave no debe pegarse en el chat, el código ni los registros.

Para regresar a la selección local en esa terminal y retirar la clave de su entorno:

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
Remove-Item -LiteralPath 'Env:\OPENAI_API_KEY' -ErrorAction SilentlyContinue
```

### Parámetros y errores

La configuración externa usa espera de conexión de 5 s, lectura de 90 s y un reintento de conexión. Las esperas son de operaciones de red, no un plazo global. No repite errores HTTP ni solicitudes tras un fallo de lectura; una generación podría seguir en el servidor. La salida máxima inicial es de 512 tokens e incluye los tokens de razonamiento que el modelo utilice. El mínimo admitido por la configuración es 16, conforme a la [referencia de creación de Responses](https://developers.openai.com/api/reference/python/resources/responses/methods/create).

El endpoint es fijo, con HTTPS, sin redirecciones y sin proxies del entorno. No se añade temperatura u otro parámetro específico de una familia de modelos. La clave solo se utiliza en la cabecera de autorización; no está en `OpenAISettings`, el contexto enviado al modelo o la evidencia serializada.

- **API desactivada:** falta seleccionar `openai` y habilitar expresamente el uso externo. La comprobación local utiliza los valores del bloque de esta unidad.
- **Modelo o clave ausentes:** se comunica un error de configuración antes de enviar la solicitud. No se imprime el valor recibido.
- **HTTP 401/403:** el proveedor rechazó credenciales o permisos; comprobarlos en la cuenta cuando se use la API.
- **HTTP 404:** comprobar nombre y disponibilidad del modelo para esa cuenta.
- **HTTP 429:** comprobar límites de uso o cuota. No se repite automáticamente.
- **Respuesta incompleta:** la generación no terminó o no devolvió texto de candidato válido. El programa no la presenta como entrevista completada.

Los errores se traducen sin imprimir cuerpos HTTP ni excepciones de transporte que puedan contener credenciales. Las pruebas de no exposición usaron una clave ficticia, incluso en cuerpos y errores simulados. La [guía oficial de errores](https://developers.openai.com/api/docs/guides/error-codes) documenta las categorías del servicio.

La evidencia usa `ollama-smoke-...json`, `openai-smoke-...json` o `llm-smoke-...json` si falló la selección antes de crear un cliente. Incluye proveedor y parámetros sin claves. `completed` describe éxito técnico; la revisión factual sigue siendo necesaria.

---

<a name="rendimiento-local"></a>

## Tiempos de Ollama y preparación para la demostración

Unidad de diagnóstico previa a la consola. El usuario confirmó 352 pruebas y una respuesta correcta que tardó **275,82 s**. La evidencia original permanece en `outputs/results/ollama-smoke-5f2399bfb48b4c6e9e09d93a4122bc94.json` y no se modificó para añadirle métricas posteriores.

### Qué se pudo comprobar de esa llamada

El registro técnico del servicio, con finalización a las 03:06:35 del 31 de octubre de 2026 en Santiago, mostró:

| Medición del registro | Tiempo |
| --- | --- |
| Procesar los 5073 tokens de contexto | 232,60 s |
| Generar los 24 tokens de respuesta | 14,31 s |
| Total de esas dos fases | 246,91 s |
| Llamada completa medida por el cliente | 275,82 s |

La mayor parte del tiempo de esa consulta se consumió al procesar el contexto. La diferencia restante no se atribuye íntegramente a carga: el JSON antiguo no conservó su duración específica. La lectura actual de CPU/GPU no describe necesariamente su estado durante esa consulta. No se determinó la causa exacta de la variación frente a las llamadas anteriores.

### Cambio implementado

`LLMResponse` añade métricas opcionales que el adaptador Ollama obtiene de la respuesta del servicio:

| Campo | Fuente y significado |
| --- | --- |
| `server_total_seconds` | `total_duration`, total informado por el servidor. |
| `load_seconds` | `load_duration`, carga informada por el proveedor. |
| `prompt_eval_seconds` | `prompt_eval_duration`, procesamiento del contexto. |
| `eval_seconds` | `eval_duration`, generación de la respuesta. |
| `cached_input_tokens` | `prompt_eval_cached_count`, tokens de entrada reutilizados de caché. |

Las duraciones se convierten de nanosegundos a segundos según el [contrato de chat de Ollama](https://docs.ollama.com/api/chat). Un campo ausente o inválido queda en `None` y se muestra como `no informado`; cero es una medición válida. No se inventan métricas para OpenAI u otro proveedor. El tiempo de llamada del cliente sigue separado del total del servidor; no se presupone que las fases sumen exactamente ese total.

`OllamaSettings.keep_alive` vale ahora **`15m`** y el adaptador lo envía en cada solicitud local. Pide conservar el modelo en memoria después de responder, reduciendo la posibilidad de volver a cargarlo por una pausa de pocos minutos. Durante ese tiempo ocupa memoria. La opción no acelera por sí misma una preparación inicial sin caché y el servicio puede liberar el modelo si se detiene o necesita los recursos para otra carga.

No se aumentó la espera de lectura de 300 s ni se redujo la ventana de 8192 tokens para truncar antecedentes. Perfil, puesto, instrucciones y contexto autorizado permanecen iguales. La API externa continúa desactivada en estas comprobaciones.

### Mediciones después del cambio

Se ejecutaron dos consultas consecutivas de la misma pregunta, con el mismo mensaje de sistema:

| Medición | Primera | Repetición inmediata |
| --- | --- | --- |
| Llamada del cliente | 55,54 s | 2,18 s |
| Carga informada | 34,88 s | 0,02 s |
| Procesamiento del contexto | 18,58 s | 0,10 s |
| Generación | 1,94 s | 1,96 s |
| Total del servidor | 55,49 s | 2,17 s |
| Tokens de entrada | 5073 | 5073 |
| Tokens reutilizados | 0 | 5072 |
| Tokens de salida | 24 | 24 |

Ambas finalizaron con `stop`, conservaron la institución y el título exactos y comprobaron el original intacto. Evidencias:

- `outputs/results/ollama-smoke-4704e1947b3e498db5a82648ea37450b.json`.
- `outputs/results/ollama-smoke-817805040fce484da953c8f208c62767.json`.

Esto confirma reutilización del contexto en la repetición. No demuestra que cambiar `keep_alive` haya acelerado la primera consulta de 275,82 a 55,54 s: esa opción regula permanencia, no velocidad de procesamiento. Tampoco permite prometer 2,18 s para preguntas nuevas, otra carga del equipo o una entrevista completa. `ollama ps` confirmó que el modelo seguía cargado y que restaban 12 minutos al comprobarlo después de las pruebas.

### Repetir en PowerShell

Desde la raíz del proyecto, con Ollama abierto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.smoke_test
if ($LASTEXITCODE -eq 0) {
    .\.venv\Scripts\python.exe -X utf8 -m scripts.smoke_test
}
ollama ps
```

La suite debe mostrar **404 passed**: 394 casos unitarios y diez integraciones, sin consultas reales. Cada ejecución del script hace una pregunta local y muestra el desglose de tiempos y tokens reutilizados, junto con la respuesta y la comprobación del perfil. La repetición solo se ejecuta si la primera llamada termina correctamente. Si falla o agota la espera, conservar su evidencia y revisar el servicio antes de iniciar otra generación.

Para la demostración conviene preparar el candidato con una consulta de prueba antes de iniciar la entrevista, dejando margen para la carga y el procesamiento inicial. La prueba aislada no crea una sesión ni incrementa un contador de entrevista. Mantener pausas inferiores a la permanencia solicitada ayuda a conservar los recursos preparados; otras solicitudes o cambios de contexto pueden reducir la reutilización.

Si no se reutilizan tokens, conservar ambos JSON y la salida de `ollama ps` para revisarlos. Si aparece un tiempo de espera, no asumir que una solicitud nueva resolverá la lentitud ni activar la API automáticamente. El ajuste es local al proyecto y no cambia el plan de energía, los controladores o la configuración global de Ollama.

---

<a name="unab-consumo-y-salidas-vacias"></a>

## UNAB IA: consumo y respuestas rechazadas

### Evidencia de la sesión del usuario

[Sesión cd0fa34f-b9a1-491f-9f9a-fa7c83ff6ecc](../outputs/sessions/session-cd0fa34f-b9a1-491f-9f9a-fa7c83ff6ecc.json): cuatro preguntas, tres errores `invalid_response` y una respuesta completa. La institución y fecha de titulación fueron correctas; el perfil conserva su huella aprobada.

La llamada completa informó **6045 tokens de entrada y 233 de salida**. Las tres rechazadas no conservaron métricas, motivo de finalización ni forma del contenido: no puede determinarse su causa exacta retrospectivamente. El adaptador emitía el mismo error para varias causas distintas y no registraba uso de respuestas rechazadas; las pruebas iniciales no cubrían una salida vacía al agotar tokens con razonamiento.

El contexto fijo actual contiene **24 822 caracteres**, y se vuelve a enviar en cada pregunta junto al historial completo aceptado. Los intentos fallidos se conservan en el registro, pero no se añaden al contexto posterior. Cuatro entradas del orden de 6000 tokens implican unas 24 000 unidades de entrada, antes de sumar la generación. La captura muestra **25 963 créditos consumidos hoy de 50 000**, con **24 037 disponibles**. Es un consumo compatible en orden de magnitud; no se conoce la equivalencia exacta crédito/token del servicio ni si hubo otras llamadas. No se afirma que toda la cifra proceda de esta sesión.

### Hipótesis y primera corrección (histórica: 512 tokens)

El límite enviado era `max_tokens: 512`. Una respuesta compleja puede gastar su presupuesto en razonamiento y terminar sin texto final. Gemma admite modos de razonamiento según su [ficha oficial en Ollama](https://ollama.com/library/gemma4), y la [documentación de compatibilidad](https://docs.ollama.com/api/openai-compatibility) describe `reasoning_effort: none`. Eso hace plausible la hipótesis; no demuestra cómo la pasarela UNAB resolvió las tres llamadas anteriores.

En la primera corrección se solicitó `reasoning_effort: none`, manteniendo **512 tokens** y sin aumentar presupuesto ni repetir automáticamente generaciones. La pasarela puede aplicar, ignorar o rechazar el parámetro: su efecto real debe comprobarse con un único intento controlado. No se presenta como reparación confirmada en el servicio desplegado.

El cliente conserva metadatos permitidos incluso al rechazar contenido: estado HTTP, finalización conocida, límite solicitado, caracteres de contenido, presencia de razonamiento y métricas de uso disponibles. Los valores desconocidos permanecen `null`; no se estiman ni convierten a cero. Los contadores de razonamiento y caché son desgloses cuando el servidor los informa, no cargos adicionales que deban sumarse otra vez al total.

No se guardan mensajes, cabeceras, claves, cuerpo bruto ni razonamiento. Los marcadores de pensamiento conocidos se rechazan como respuesta final, sin exponer su contenido. Al cerrar la consola se escribe `outputs/results/unab-usage-<UUID>.json`, separado del registro original de la entrevista y sin alterar su esquema. Las respuestas completas muestran sus tokens informados en terminal.

### Comprobación del usuario

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview
```

Elegir **2**, usar `/iniciar`, formular **solo la primera pregunta compleja** y cerrar con `/salir`. Revisar la respuesta y el archivo indicado como **Diagnóstico de uso de API**. Si falla, conservar ese diagnóstico antes de repetir preguntas. El diagnóstico distingue salida vacía al límite de otras salidas inválidas; permite comprobar o descartar la hipótesis sin publicar la clave.

La reparación se prueba con HTTP simulado; no se utilizó la clave privada ni se consumió cuota UNAB durante esta investigación. El historial, perfil e instrucciones originales permanecen sin cambios. Este trabajo mejora observabilidad y solicita menor razonamiento; no reduce por sí solo los aproximadamente 6000 tokens de contexto inicial por petición ni cambia la contabilidad del proveedor.

Verificación: **27 passed in 3.97s** en el adaptador; suite completa **765 passed in 254.13s (0:04:14)**, 687 unitarias y 78 integraciones. Evidencia: [investigación y hechos confirmados](../outputs/results/unab-response-investigation-737c141f23f7423ba79fa9b0d23ade18.json). No hubo llamadas reales a UNAB ni acceso a la clave privada; la sesión original conserva su huella.

### Comprobación posterior: límite confirmado y presupuesto configurable

El usuario probó una sola pregunta sobre lentitud de Flask/PostgreSQL. [Diagnóstico b84552c0-bccb-48e3-8498-bbeae51ed951](../outputs/results/unab-usage-b84552c0-bccb-48e3-8498-bbeae51ed951.json): HTTP 200, entrada 6058, salida 512, total informado 6570, finish_reason length y contenido final de cero caracteres. Se había solicitado reasoning_effort none. No se recibió razonamiento en los campos inspeccionados y su número de tokens no fue informado; no equivale a demostrar que no hubo procesamiento interno ni que la pasarela aplicó o ignoró el parámetro.

Se confirmó el agotamiento de la salida sin respuesta, no su causa interna. La solución controlada siguiente solicita **2048 tokens de salida para UNAB**, mantiene reasoning_effort none y no repite la generación. El límite 512 de Ollama y del adaptador Responses anterior no cambia. El máximo es un techo solicitado, no garantiza que se consuma entero ni define la fórmula de créditos UNAB.

El selector muestra el presupuesto antes de abrir la entrevista. El archivo privado anterior de tres campos funciona sin editarlo ni cambiar la clave. Opcionalmente admite api_max_output_tokens como entero entre 16 y 4096; si falta, usa 2048. Nunca se aumenta el presupuesto de forma automática. La fábrica también admite UNAB_MAX_OUTPUT_TOKENS para uso programático; al iniciar con el selector prevalece el archivo privado o su valor por defecto.

Se verificaron **109 pruebas en 1,44 s** del adaptador/selector, fábrica y Responses, sin cuota API. Incluyen 17 regresiones nuevas para límites, tipos inválidos, compatibilidad local, valor predeterminado y correspondencia del presupuesto enviado con el diagnóstico. No se repitió toda la suite para este cambio aislado; el resultado completo anterior de 765 queda como evidencia histórica. Hay 782 pruebas disponibles, no una nueva ejecución completa de 782.

Repetir únicamente la misma pregunta y cerrar con /salir. El diagnóstico debe indicar requested_max_tokens 2048. Si vuelve a finalizar sin texto, detener la prueba y revisar el diagnóstico y la configuración del servicio antes de seguir aumentando límites o repitiendo llamadas. Esta modificación aún no tiene validación real del usuario.

### Confirmación real con 2048

El usuario repitió exactamente la misma pregunta sobre Flask/PostgreSQL. La [sesión 162df680-88d6-40ca-9e8f-d095fae07025](../outputs/sessions/session-162df680-88d6-40ca-9e8f-d095fae07025.json) terminó con una respuesta completa y cero incidencias; el perfil permaneció intacto. El [diagnóstico](../outputs/results/unab-usage-162df680-88d6-40ca-9e8f-d095fae07025.json) informó HTTP 200, presupuesto 2048, finish_reason stop, entrada 6058, salida 1255 y total 7313. El contenido final tuvo 684 caracteres. Tiempo comunicado: 12,82 s.

La respuesta distinguió cantidad de consultas por petición, duración/plan de ejecución y tiempo total del endpoint, presentándolo como propuesta hipotética. La inspección del asistente no sustituye una aprobación semántica humana. La repetición confirma funcionamiento de este caso con el presupuesto mayor; no demuestra el comportamiento interno del parámetro de razonamiento ni la compatibilidad de todas las preguntas. El proveedor no desglosó tokens de razonamiento o caché, y sigue sin conocerse su fórmula de créditos.

Se mantiene el presupuesto configurado de 2048, sin cambios adicionales ni reintentos. Se validaron los dos archivos sin modificarlos; no se hicieron nuevas llamadas o lecturas de la clave privada ni se repitieron tests para registrar esta confirmación. [Evidencia estructurada](../outputs/results/unab-success-confirmation-162df680-88d6-40ca-9e8f-d095fae07025.json).
