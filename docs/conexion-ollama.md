# Primera conexión local con Ollama

Guía de la conexión de la Etapa 5: una pregunta preparada con el escenario autorizado y una respuesta del modelo. La consola de la Etapa 6 ya utiliza ese adaptador y aplica el contador; véase [su guía de uso](consola.md). Historial y persistencia siguen pendientes.

## Archivos y responsabilidades

| Archivo | Función |
| --- | --- |
| `harness/llm/config.py` | Parámetros explícitos, validados e inmutables de Ollama. |
| `harness/llm/client.py` | Interfaz `generate(messages)`, `LLMResponse` y errores comunes. |
| `harness/llm/messages.py` | Tipos y validación de los mensajes antes del envío. |
| `harness/llm/ollama_client.py` | Solicitud HTTP local y comprobación de la respuesta. |
| `harness/llm/factory.py` | Selección de proveedor; Ollama predeterminado y bloqueo del uso externo. |
| `scripts/smoke_test.py` | Una pregunta real y su evidencia técnica. |

`generate` recibe mensajes y devuelve texto final, proveedor, modelo, duración de la llamada, tokens informados y motivo de finalización. Si faltan métricas válidas, devuelve `None`; no calcula tokens a partir de caracteres. No devuelve el campo `thinking`.

## Parámetros iniciales

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

Se envían `stream: false` y `think: false`, conforme al [contrato de chat de Ollama](https://docs.ollama.com/api/chat) y al [control de razonamiento](https://docs.ollama.com/capabilities/thinking). El constructor conserva los mensajes `system` y `user`. Solo para `gemma3n`, el transporte reúne el par inicial en un turno `user`, con una separación explícita para la pregunta original, porque su plantilla no ofrece un rol `system` nativo. No añade respuestas ficticias ni modifica el texto de la pregunta. Otros modelos conservan sus mensajes; véase el [registro de corrección](pruebas/correccion-conducta.md).

Se corrigió la recomendación inicial después de inspeccionar los metadatos de los pesos: `qwen3:4b`, ID `359d7dd4bcda`, es **Qwen3-4B-Thinking-2507** (`general.finetune: Thinking`, versión `2507`). Su [ficha oficial](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507) indica que solo admite razonamiento. Los intentos con `think: false`, prefijo vacío y una variante de plantilla no produjeron una respuesta directa válida. La variante experimental fue retirada; no forma parte de la instalación final.

Se eligió explícitamente `gemma3n:e2b`, ID `719372f8c7de`, entre los modelos ya instalados. No se descargaron otros pesos ni se cambiaron los tres modelos originales. Este cambio de configuración conserva Ollama y la interfaz del cliente; no es un fallback automático tras un error. La calidad durante una entrevista completa sigue pendiente de evaluación.

La elección de contexto es provisional: el límite anunciado por el modelo no equivale al que conviene usar en la memoria disponible.

Los tiempos de espera son de operaciones de red, no un cronómetro global. Un tiempo de espera de lectura no se reintenta automáticamente, porque el servidor podría seguir generando. Los errores HTTP tampoco se repiten. El cliente rechaza respuestas sin texto o sin confirmación de finalización, y texto que contenga las marcas `<think>` o `</think>`. Conserva `done_reason: length`; el script marca ese resultado como `incomplete`, no imprime el texto como respuesta del candidato y termina con código de error. Estos controles no identifican todo posible razonamiento sin marcas ni garantizan que el contenido sea correcto.

La primera ejecución real agotó una espera inicial de 180 segundos. El registro confirmó la carga del modelo y el procesamiento de un contexto de 4311 tokens; la solicitud terminó cancelada cuando el cliente dejó de esperar. Se amplió la espera de lectura a 300 segundos para poder observar la respuesta completa. Esto no resuelve por sí mismo la latencia para una demostración.

El segundo intento terminó en 177,54 segundos con 512 tokens de salida y motivo `length`. Se observó texto de preparación de respuesta en lugar de una intervención válida del candidato. Las pruebas posteriores tampoco justificaron usar esos pesos para respuestas directas. Las evidencias se conservan en la bitácora; sus antiguos estados de éxito técnico no equivalen a respuestas satisfactorias. Se añadieron el rechazo de salidas cortadas en el script y el rechazo de marcas de razonamiento en el adaptador.

El adaptador Ollama no utiliza credenciales, redirecciones ni proxies del entorno, no descarga modelos ni cambia de proveedor. La fábrica no carga archivos `.env`. La alternativa OpenAI está implementada y desactivada por defecto; comparte la interfaz y se verificó con transporte simulado. Véase [la guía de API opcional](conexion-api-opcional.md).

## Repetir las comprobaciones

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

## Resultados observados

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

El usuario confirmó después el nombre correcto y las 352 pruebas, pero una llamada tardó 275,82 s. Su registro técnico mostró 232,60 s de procesamiento del contexto y 14,31 s de generación. Se añadieron métricas opcionales y una permanencia solicitada de 15 minutos. Dos mediciones posteriores tardaron 55,54 s y 2,18 s, con reutilización de 5072 tokens en la repetición. La lentitud inicial sigue siendo variable y no se considera resuelta por ese cambio; véase [el diagnóstico de rendimiento](rendimiento-local.md).

## Errores habituales

- **No se pudo conectar:** abrir Ollama y comprobar `ollama list` en PowerShell. Repetir el comando de prueba cuando el servicio responda. No es necesario instalar otro modelo.
- **Modelo no encontrado:** comprobar que `ollama list` incluya `gemma3n:e2b`. No se cambia automáticamente a otro modelo.
- **Tiempo de espera:** conservar el error y la evidencia. Comprobar la carga del equipo y `ollama ps` antes de repetir. No ejecutar varias pruebas simultáneas mientras la anterior sigue pendiente.
- **No module named httpx:** usar el Python de `.venv`; si falta la biblioteca, ejecutar `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` desde la raíz.
- **No se encuentra scripts.smoke_test:** comprobar la carpeta actual con `Get-Location` y usar `-m scripts.smoke_test` tal como aparece arriba.

## Fuentes técnicas

- [Errores de Ollama](https://docs.ollama.com/api/errors).
- [Tiempos de espera de HTTPX](https://www.python-httpx.org/advanced/timeouts/).
- [Transportes simulados de HTTPX](https://www.python-httpx.org/advanced/transports/).

Las pruebas simuladas verifican el programa y sus errores. Las mediciones reales y sus límites se registran por separado en la bitácora y en los archivos de evidencia.
