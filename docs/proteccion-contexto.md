# Etapa 7.4b: rechazo explícito antes de perder contexto

La unidad anterior midió llamadas pasadas. Antes de integrar una reducción del historial, se añadió una protección que solicita a Ollama rechazar una entrada que no quepa, sin recortar mensajes para continuar. El registro completo se conserva, el intento rechazado cuenta y el usuario puede acortar la pregunta o finalizar para guardar.

Esta unidad usa los controles `truncate: false` y `shift: false` de la solicitud `/api/chat`, fuera del objeto `options`. No aumenta la capacidad configurada ni resume la conversación. Se verificó el servicio local **Ollama 0.34.2** y el modelo instalado **gemma4:e4b**.

## Archivos y dependencias

| Archivo | Cambio |
| --- | --- |
| `harness/llm/ollama_client.py` | Envía los dos controles en cada llamada local y reconoce formas conocidas del error de contexto. |
| `harness/llm/client.py` | Añade `LLMContextLimitError`, dentro del contrato de errores existente. |
| `harness/session_state.py` | Catálogo seguro con código `context_limit`; no copia cuerpos del servidor. |
| `schemas/session.schema.json` | Admite ese código dentro de los incidentes del formato 1.0.0 existente; conserva los anteriores. |
| `harness/application/cli.py` | Explica que el intento cuenta y que se puede acortar la pregunta o finalizar para guardar. |
| `tests/unit/test_ollama_context_guard.py` | 17 casos de controles, reconocimiento seguro, ausencia de reintentos y catálogo. |
| `tests/integration/test_context_rejection_flow.py` | Respuesta → rechazo → repregunta → guardado y lectura, con HTTP simulado. |

Se actualizó además la expectativa del JSON enviado en la prueba existente del adaptador. No hay dependencias nuevas. El controlador conserva su funcionamiento: solo los intentos completos forman el historial válido para el siguiente envío. No se modifican perfil, puesto, configuración, instrucciones ni adaptador externo.

## Decisión y fuentes

Ollama 0.34.2 incluye ambos controles en `ChatRequest`. `truncate` gobierna el recorte de mensajes del prompt y `shift` el desplazamiento al llegar al límite durante la generación. Fuentes primarias consultadas el 31 de octubre de 2026: [tipos de la API 0.34.2](https://github.com/ollama/ollama/blob/v0.34.2/api/types.go), [preparación de mensajes](https://github.com/ollama/ollama/blob/v0.34.2/server/prompt.go) y [rutas de chat](https://github.com/ollama/ollama/blob/v0.34.2/server/routes.go).

Una prueba directa del servidor instalado envió texto sintético, con capacidad 8192 y ambos controles desactivados. Respondió HTTP 400: el motor informó una solicitud de **16 009 tokens** superior a la capacidad. El error venía como JSON codificado dentro del campo `error`, con tipo `exceed_context_size_error`. La prueba tardó **28,03 s**, sin métricas por fase que permitan atribuir una causa.

El adaptador reconoce ese tipo, su forma de objeto directo y mensajes exactos conocidos de longitud excedida. Procesa como máximo una envoltura JSON del campo `error`. Otros rechazos conservan su error genérico; no considera que cualquier HTTP 400 sea un exceso de contexto. El error público y el registro utilizan texto fijo, sin copiar mensajes arbitrarios, credenciales o cuerpos HTTP.

No se reenvía automáticamente una solicitud rechazada, no se recorta el historial local ni se cambia `num_ctx`. La falta de espacio durante una generación también puede producir una respuesta cortada o un error: continúan aplicándose los controles existentes que impiden aceptar texto incompleto como respuesta válida.

## Comprobar en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
```

Esperado: **577 passed**, 551 unitarias y 26 integraciones, sin llamadas reales durante pytest. Para probar el rechazo y la continuidad, este bloque envía automáticamente las entradas al programa; no requiere escribir dentro de la consola:

```powershell
$entradasPrueba = @(
    '/iniciar'
    'Menciona tu proyecto academico.'
    ('dato ' * 16000)
    'Como se llamaba ese proyecto?'
    '/salir'
)
$entradasPrueba | .\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

Las entradas del bloque usan caracteres ASCII para que la tubería funcione también con la codificación predeterminada de Windows PowerShell. La segunda pregunta repite texto únicamente para superar el contexto; no pretende representar una entrevista natural. El texto completo se conserva en el archivo de sesión, aunque la tubería no lo muestre como entrada escrita en pantalla.

Esperado: dos respuestas completas que mantengan Inventario Aula, un rechazo por falta de espacio de contexto, tres preguntas enviadas, una incidencia y confirmación de guardado. Al terminar, de vuelta en PowerShell:

```powershell
$archivoSesion = Get-ChildItem -LiteralPath '.\outputs\sessions' -Filter 'session-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
.\.venv\Scripts\python.exe -X utf8 -c "import sys; from harness.session_log import load_session; s = load_session(sys.argv[1]); print('Sesion:', s['session_id']); print('Estado:', s['status']); print('Integridad:', s['source_integrity']); print('Estados:', [a['status'] for a in s['attempts']]); print('Incidencia:', s['attempts'][1]['issues'][0]['code'])" $archivoSesion.FullName
```

Esperado: mismo UUID de esa ejecución, `closed`, `unchanged`, `['completed', 'error', 'completed']` y `context_limit`. Comprobar antes que el programa confirmó un nuevo guardado; no atribuir un archivo anterior a una ejecución fallida.

Si aparece un error de conexión o modelo no encontrado, comprobar Ollama y el modelo elegido; no es el rechazo esperado de esta prueba. Si la entrada extensa obtiene una respuesta normal en lugar de rechazo, conservar la salida y la versión del servicio para revisarlo antes de continuar. No aumentar el contexto para ocultar el caso de prueba.

## Evidencia

El usuario confirmó la 7.4a con **559 passed in 25.70s** y el diagnóstico de su sesión: entradas 6023/6097, límite 7424, márgenes 1401/1327 y cero métricas ausentes. Se conservó un registro estructurado en [context-diagnostic-user-confirmation-e12379075fb240f7bbbc28ee0aa30ce6.json](../outputs/results/context-diagnostic-user-confirmation-e12379075fb240f7bbbc28ee0aa30ce6.json), que distingue su resultado comunicado de la lectura local del archivo.

La suite final pasó con **577 passed in 26.48s**, sin fallos. Se añadieron 17 casos unitarios y una integración. La integración comprueba que el siguiente envío conserva el primer par completo y excluye la pregunta rechazada, que el sistema se mantiene idéntico y que el registro completo con `context_limit` se guarda y vuelve a cargar correctamente.

La comprobación real usó el punto de entrada de la aplicación: pregunta sobre el aporte a Inventario Aula, entrada sintética extensa y repregunta por el nombre del proyecto. Hubo tres llamadas HTTP, con 2, 4 y 4 mensajes respectivamente. Todas enviaron `truncate: false`, `shift: false`, capacidad 8192 y salida máxima 512. El mensaje de sistema conservó el mismo hash. La repregunta respondió «Inventario Aula»; las dos respuestas completas tardaron **40,80 s** y **5,25 s**. No hubo respuesta inventada ni conteos de tokens para el intento rechazado.

La aplicación creó [session-5705ca05-8c5c-4251-9c34-d9883224391a.json](../outputs/sessions/session-5705ca05-8c5c-4251-9c34-d9883224391a.json), con estados `completed`, `error`, `completed`, fuente sin cambios y cierre por salida del usuario. `load_session` recuperó exactamente el registro del controlador. La evidencia adicional del verificador está en [context-guard-9283a64ac59d4d41bad389f904d650a4.json](../outputs/results/context-guard-9283a64ac59d4d41bad389f904d650a4.json). Los archivos anteriores de sesiones y los cuatro originales del escenario se conservaron.

## Alcance pendiente

Esta protección se verificó con el servicio y modelo indicados; no garantiza el comportamiento de otras versiones o motores. Los controles solicitan el rechazo al servidor y no sustituyen un conteo previo exacto. Las métricas de la 7.4a siguen siendo retrospectivas y el margen adicional 256 continúa siendo una política de comparación.

El resumen controlado y su integración siguen pendientes. Primero se comprueba que el exceso queda registrado sin perder datos; después se podrá probar cómo recuperar espacio manteniendo hechos y referencias. Se espera el resultado del usuario antes de continuar con otra unidad. No se han añadido clasificación de preguntas, puntuación, base de datos o nuevas dependencias.

Confirmación posterior: el usuario obtuvo **577 passed in 28.46s** y la sesión `f7be73ff-ab02-42d4-8f63-17d78db4aeb0` con los estados y el código esperados. La repregunta recordó Inventario Aula. El siguiente componente, todavía separado del controlador, se documenta en [propuesta extractiva verificable](resumen-extractivo.md).
