# API externa opcional: OpenAI Responses

Unidad de la Etapa 5. El proveedor principal sigue siendo Ollama con `gemma3n:e2b`. La alternativa OpenAI está implementada y desactivada por defecto. Se verificó con un transporte HTTP simulado y claves ficticias; no se hizo una llamada real a OpenAI, ni se comprobó acceso, cuota, facturación o calidad de un modelo externo.

## Componentes

| Archivo | Responsabilidad |
| --- | --- |
| `harness/llm/config.py` | `OpenAISettings`, parámetros inmutables sin credenciales; el modelo es obligatorio. |
| `harness/llm/openai_client.py` | Adaptador HTTPX para `https://api.openai.com/v1/responses`. |
| `harness/llm/factory.py` | `create_client`, selección explícita y bloqueo del uso externo. |
| `harness/llm/client.py` | Contrato `generate(messages)`, respuesta común y errores, incluido acceso rechazado. |
| `scripts/smoke_test.py` | Una pregunta con el proveedor seleccionado y evidencia sin claves. |

Ambos adaptadores reciben los mismos mensajes. OpenAI los envía en `input`, solicita `store: false` y `stream: false`, y recupera únicamente bloques `output_text` de mensajes de asistente completados. Los elementos de razonamiento no se devuelven como respuesta. Estos campos siguen el [contrato documentado de Responses](https://developers.openai.com/api/docs/guides/migrate-to-responses).

Los estados externos incompletos o fallidos, rechazos sin texto de candidato y salidas de herramientas no solicitadas se comunican como errores; no se aceptan respuestas parciales. El adaptador tampoco acepta marcas de razonamiento en el texto. Esto no valida los hechos o la obediencia del modelo. `LLMResponse.finish_reason` conserva `completed`, el estado nativo de la respuesta externa; Ollama conserva su motivo, por ejemplo `stop`.

## Selección y activación explícita

La fábrica lee variables de la sesión del proceso. No carga archivos `.env`; `.env.example` documenta las variables sin activarlas.

| Variable | Valor predeterminado | Función |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | Selección exacta: `ollama` u `openai`. |
| `LLM_ALLOW_EXTERNAL_API` | `false` | Solo el texto exacto `true` habilita el uso externo al seleccionar OpenAI. |
| `OPENAI_MODEL` | Sin valor | Modelo compatible con Responses, obligatorio al habilitar la API. |
| `OPENAI_API_KEY` | Sin valor | Credencial, obligatoria al habilitar la API. |

La ruta Ollama no consulta el modelo ni la clave externa. Una clave por sí sola no activa OpenAI. Una selección desconocida o incompleta produce un error antes de enviar solicitudes. Si falla Ollama, el programa no cambia a OpenAI; si falla OpenAI, tampoco cambia de proveedor. Crear un cliente no genera una respuesta ni envía una solicitud.

La fábrica es el punto de entrada usado por el script. La clase `OpenAIClient` también permite uso programático explícito, con parámetros y credenciales recibidos por argumento; no descubre ni activa claves por su cuenta.

## Comprobación de esta unidad, manteniendo Ollama

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

## Activación futura cuando se necesite

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

## Parámetros y errores

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
