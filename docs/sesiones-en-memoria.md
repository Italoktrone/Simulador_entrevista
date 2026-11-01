# Etapa 7.2: identidad de sesión y registro de intentos

Esta unidad conserva en memoria la identidad de una entrevista, su configuración y todos los intentos enviados al proveedor. Incluye respuestas completas, errores, interrupciones y respuestas cortadas. Se puede consultar un resumen con `/sesion`. Esta guía documenta la unidad 7.2 original; el guardado y la lectura se añadieron después en la [unidad 7.3](persistencia-sesiones.md).

## Archivos y dependencias

| Archivo | Responsabilidad |
| --- | --- |
| `harness/session_state.py` | `SessionState`: identificador UUID, fechas UTC, estado, configuración y registro técnico; copias para consulta. Se completó el archivo previsto en la arquitectura. |
| `harness/runtime.py` | Coordinar cada intento y las comprobaciones de integridad. Contador e historial se obtienen del registro para evitar estados duplicados. |
| `harness/application/cli.py` | Mostrar el identificador, atender `/sesion` y presentar el resumen al cerrar. |
| `scripts/run_interview.py` | Pasar proveedor/modelo solicitados y registrar también la comprobación final de integridad. |
| `tests/unit/test_session_state.py` | Registro, aislamiento, límites, errores simultáneos, interrupciones, copias y protección de detalles internos. |
| `tests/integration/test_session_records_flow.py` | Consola, cliente y datos reales con HTTP simulado: una llamada fallida y otra completa. |

No hay dependencias nuevas. Se usan la biblioteca estándar, los contratos del cliente, el escenario validado y los controles existentes. En la 7.2, `harness/session_log.py` no participaba en el flujo. Su implementación posterior se documenta en la unidad 7.3. No se implementan clasificación, puntuación o retroalimentación.

## Qué conserva cada registro

`runtime.session_id` identifica una entrevista concreta. No reutiliza `config_id`, `candidate_id` o el nombre del archivo. Dos controladores crean identificadores distintos, aunque compartan escenario y cliente. Repetir `/iniciar` no crea otra sesión ni reinicia el contador.

`runtime.session_dict()` devuelve una copia independiente, compuesta por valores serializables a JSON. Todavía no escribe un archivo. Su formato inicial lleva `session_version: 1.0.0` e incluye:

- Identificador de sesión, candidato y puesto; copia de la configuración.
- Hash del candidato y del texto de instrucciones, sin guardar el perfil interno, rutas o texto del sistema.
- Proveedor y modelo solicitados, si el llamador los proporciona. La consola los pasa explícitamente; no se inspecciona el cliente para obtener credenciales o ajustes privados.
- `created_at`, `closed_at`, estado abierto/cerrado y motivo del primer cierre.
- Último resultado de integridad: `not_checked`, `unchanged` o `failed`. Una detección de fallo se conserva aunque después se restauren los bytes.
- Intentos ordenados y posibles incidencias de sesión, como una alteración del perfil detectada antes de enviar una pregunta.

Las fechas de sesión e intentos utilizan la hora real en UTC con zona explícita. No son la fecha de referencia del escenario, que sigue en **2026-10-20**. Estos metadatos no se envían al LLM ni actualizan la trayectoria ficticia.

## Registro de un intento

Una pregunta válida se registra después de comprobar el perfil y antes de llamar al cliente. En ese momento ya cuenta como enviada y tiene estado `pending`.

| Campo | Contenido |
| --- | --- |
| `question_number` | Orden de envío, incluidos intentos fallidos. |
| `question` | Texto original sin sustituirlo ni recortarlo. |
| `requested_at` / `finished_at` | Fechas UTC de registro del inicio y resultado; la segunda está vacía mientras está pendiente. |
| `status` | `pending`, `completed`, `error`, `incomplete` o `interrupted`. Son estados técnicos, no calificaciones de una pregunta. |
| `response` | Respuesta y métricas informadas por el cliente, cuando este devolvió una respuesta. Puede conservar texto parcial para diagnóstico sin aceptarlo como turno. |
| `issues` | Códigos y descripciones de un catálogo seguro. No copia mensajes arbitrarios de excepciones, causas, trazas o cuerpos HTTP. |

El registro distingue el modelo solicitado del modelo informado en una respuesta. Si una llamada falla, no se inventa una respuesta ni un conteo de tokens. Si coinciden un error del proveedor y un cambio del perfil, se conservan ambos incidentes.

La comprobación final del programa actualiza también la integridad del registro. El primer motivo y fecha de cierre se conservan; una incidencia detectada después del cierre puede añadirse sin reabrir la sesión. La fecha de finalización de un intento es la de registro de su resultado; en un fallo de integridad la sesión puede haberse cerrado antes de terminar de registrar ese incidente.

## Historial para el modelo y cierre

`history_messages()` se deriva únicamente de intentos `completed`. Errores, texto parcial e interrupciones permanecen en el registro técnico, pero no aparecen como conversación válida en la siguiente solicitud. La configuración y el perfil no se sustituyen por esas respuestas. Modificar una copia del registro no modifica la memoria o la configuración activa.

El cierre se registra por salida del usuario, máximo de preguntas, fin de entrada, interrupción o fallo de integridad. No admite más preguntas después del cierre. La consola cierra ante `Ctrl+C`; un llamador programático que capture una interrupción puede continuar si aún queda espacio y no hubo un fallo de integridad. Se mantiene ese comportamiento del controlador anterior.

El programa muestra solamente un resumen: identificador, fecha de creación, estado, preguntas enviadas, respuestas completas e incidencias técnicas. No muestra desde `/sesion` respuestas parciales ni información interna de errores. El registro no evalúa la coherencia semántica de las respuestas.

## Comprobación en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

Resultado esperado: **477 passed**, 464 unitarias y trece integraciones, sin solicitudes reales en pytest. En la consola, escribir de una en una:

```text
/sesion
/iniciar
¿Cuántos meses trabajaste en total, incluyendo la práctica?
/sesion
¿Cuántos fueron a jornada parcial y cuántos a completa?
/sesion
/salir
```

Debe mantenerse el mismo identificador y aumentar de 0 a 1 y a 2 preguntas enviadas. Con dos respuestas completas, debe mostrar dos respuestas y cero incidencias. `/sesion` no consume una pregunta. Al salir, debe aparecer estado **cerrada** y el original intacto. Otra ejecución debe comenzar con otro identificador y sin registros de la anterior.

Si aparece «modelo no encontrado» o falla la conexión, comprobar Ollama y `OLLAMA_MODEL`; el intento se registra como error y cuenta una vez. No se reenvía automáticamente una generación ni se cambia de proveedor. Se mantienen los reintentos limitados de conexión del adaptador dentro del mismo intento del controlador. No es necesario provocar fallos para esta comprobación: las pruebas cubren esas rutas.

## Límites

En la versión original 7.2, los datos se conservaban mientras existía el controlador y se perdían al terminar el proceso. Desde la 7.3 se guardan y se pueden leer como datos, sin reanudar entrevistas. La extracción automática de hechos y la evaluación educativa siguen pendientes. El manejo del presupuesto del contexto y sus resúmenes continúa pendiente antes de validar entrevistas extensas.

Esta unidad registra la configuración y lo ocurrido; no verifica que cada afirmación del LLM sea correcta. Se espera el resultado del usuario antes de continuar con la siguiente unidad.

## Evidencia de esta unidad

La suite final terminó con **477 passed in 19.10s**: 464 unitarias y trece integraciones. Se añadieron 25 casos unitarios y una integración. Una comprobación previa de 476 casos pasó en 26,97 s; después se añadió el caso de integridad final tras el cierre. No hubo fallos de prueba ni solicitudes reales en pytest.

Se comprobó también la consola real con gemma4:e4b, consultas de `/sesion` antes y después de dos preguntas, y salida anticipada. El mismo identificador se conservó durante la ejecución; los contadores fueron 0, 1 y 2; el cierre dejó dos respuestas completas, cero incidencias y `source_integrity: unchanged`. Las respuestas conservaron 21 meses calendario y el reparto de nueve meses parciales y nueve completos. Tardaron **62,16 s** y **14,98 s**; no se midieron las fases de esas llamadas ni se atribuye la duración a una causa concreta.

Una sesión independiente pidió un nombre de modelo inexistente generado solo para esta comprobación. Ollama devolvió modelo no encontrado: quedó un intento `error`, sin respuesta inventada y con código `model_not_found`. No se descargaron pesos ni se modificó la selección normal del usuario. Los identificadores de ambas sesiones fueron distintos. El proceso de verificación completo duró **78,10 s** y conservó los bytes de perfil, puesto, configuración e instrucciones.

Evidencia externa: [session-records-c2c4375fb58340bf832dce71df8c5554.json](../outputs/results/session-records-c2c4375fb58340bf832dce71df8c5554.json). Incluye la salida y copias completas de los registros al finalizar. El archivo fue escrito por la verificación externa, no por una función de guardado de la aplicación. El registro mantiene pendiente la comprobación del usuario.

La comprobación posterior del usuario confirmó las 477 pruebas en 19,83 s y 19,45 s, los contadores y cierres de una sesión de dos preguntas y otra vacía con distinto UUID. Ambos originales quedaron intactos. La transcripción y el siguiente paso se registran en [persistencia de sesiones](persistencia-sesiones.md).
