# Conversación en consola

Etapa 6 y unidades 7.1–7.4e: consultar CV y puesto, iniciar la entrevista, escribir preguntas, recibir respuestas y conservar turnos completos en memoria. El contador y cierre están implementados. Cada ejecución tiene identificador, fechas UTC y registro de intentos. El guardado JSON y su lectura están implementados; los resúmenes de contexto siguen pendientes.

## Archivos y responsabilidades

| Archivo | Función |
| --- | --- |
| `harness/runtime.py` | `InterviewRuntime`: escenario fijo, preguntas enviadas, límite y comprobaciones del perfil; independiente de la consola. |
| `harness/application/cli.py` | CV público, información del puesto, comandos, entrada de preguntas y presentación de resultados. |
| `scripts/run_interview.py` | Cargar escenario e instrucciones una vez, crear el cliente seleccionado, cerrar recursos y guardar la sesión. |
| `harness/session_log.py` | Validar, guardar y leer los registros cerrados en JSON local. |

El controlador recibe `InterviewSetup`, instrucciones y un cliente con `generate(messages)`. Cada pregunta construye mensajes nuevos desde el mismo escenario e incluye los pares completos de preguntas y respuestas anteriores de esta entrevista. El historial no añade hechos al perfil. No se solicita evaluación. Cambiar la interfaz no requiere incorporar entradas o impresiones al controlador del candidato.

## Ejecutar desde PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

La suite debe mostrar **690 passed**: 650 pruebas unitarias y cuarenta integraciones. No consulta modelos reales. Al ejecutar el programa aparece `SIMULADOR DE ENTREVISTA - PERFIL FICTICIO`, Nicolás Vera Soto, el puesto, el proveedor local y `Menú>`.

Dentro del programa, escribir estas entradas de una en una, pulsando Enter y esperando la respuesta:

```text
/cv
/puesto
/iniciar
¿Dónde estudiaste y qué título obtuviste?
¿Has trabajado con Kubernetes?
/salir
```

Los comandos anteriores se escriben en el programa, después de iniciarlo; no son comandos independientes de PowerShell. Las preguntas ocupan una línea por entrada. Antes de `/iniciar`, escribir texto normal no consulta el modelo.

El CV debe conservar los antecedentes aprobados. El puesto debe incluir Aplicaciones Nexo y las seis competencias. La primera pregunta debe conservar literalmente Instituto Profesional Horizonte Digital e Ingeniería en Informática. La segunda debe reconocer la ausencia de experiencia práctica con Kubernetes, sin atribuir proyectos que no figuren en el perfil. La prueba real de esta unidad solo comprobó la primera; el usuario revisará las demás respuestas. No se exige una frase completa idéntica entre ejecuciones.

La consola muestra `Pregunta 1/20>` y el tiempo de cada respuesta. `/salir` termina antes del máximo y debe aparecer `Archivo original del candidato intacto.` si se conservan sus bytes. La primera respuesta puede tardar por carga y procesamiento; véase [la guía de rendimiento](rendimiento-local.md).

El modelo se elige explícitamente con `OLLAMA_MODEL`; si se omite, usa `gemma3n:e2b`. No cambia tras un error. La prueba posterior del usuario con veinte preguntas detectó fallos semánticos: véase el [registro y la repetición controlada](pruebas/correccion-conducta.md). El contador y la integridad del archivo no prueban que las respuestas sean fieles al perfil.

## Comandos y conteo

| Entrada | Resultado |
| --- | --- |
| `/cv` | Muestra la vista pública del candidato. |
| `/puesto` | Muestra puesto, organización, responsabilidades, requisitos, competencias y nivel esperado. |
| `/sesion` | Muestra identificador, creación, estado y contadores del registro. |
| `/iniciar` | Habilita preguntas. Repetirlo no reinicia el contador. |
| `/ayuda` | Muestra los comandos disponibles. |
| `/salir` | Cierra la ejecución. |
| Entrada vacía o comando desconocido | Mensaje de ayuda, sin consultar al modelo. |

El límite procede de `max_questions`, validado entre 1 y 20. Una entrada de pregunta válida que se envía cuenta una vez, aunque falle la comunicación o la respuesta quede cortada. Una repregunta enviada ocupa otro lugar. Las entradas vacías, comandos y mensajes del programa no cuentan. Las preguntas compuestas no se dividen automáticamente: esta versión cuenta entradas enviadas.

Se detiene al alcanzar el límite y no solicita una pregunta adicional. El controlador también rechaza llamadas programáticas posteriores al límite o al cierre. Volver a ejecutar el programa crea una sesión con otro identificador y un registro independiente. Al cerrar se muestra el resumen final.

## Errores, interrupción y protección de datos

Un error conocido del LLM se presenta en español y permite otra pregunta si quedan lugares. La aplicación no reenvía automáticamente la generación ni cambia de proveedor. Se mantienen los reintentos limitados de conexión del adaptador. Una salida cortada por límite de tokens no se imprime como respuesta válida del candidato.

`Ctrl+C` o fin de entrada cierran la consola y los recursos del cliente. En Windows, el fin de entrada se puede indicar con `Ctrl+Z` y Enter. Si hay un cambio del perfil, se cierra la ejecución y se comunica un error de integridad; no se muestra una respuesta obtenida mientras se detectó esa alteración ni se afirma que el archivo siga intacto.

El perfil se comprueba antes y después de cada generación y al finalizar el programa. Las vistas y preguntas utilizan la instantánea protegida; la interfaz no escribe el archivo del candidato. Esto detecta discrepancias de bytes en los puntos de control, sin bloquear ediciones externas ni restaurar archivos. Configuración y puesto se conservan como instantáneas de la carga inicial.

Errores habituales:

- **No se puede conectar:** comprobar que Ollama esté abierto y que `ollama list` incluya el modelo elegido en `OLLAMA_MODEL`. La pregunta fallida ya cuenta; se puede cerrar con `/salir` y repetir la prueba cuando el servicio esté listo.
- **No se encuentra el módulo:** comprobar `Get-Location` y usar `-m scripts.run_interview` desde la raíz, con el Python de `.venv`.
- **Configuración inválida o API externa desactivada:** utilizar las variables locales del bloque anterior. La opción externa sigue requiriendo activación explícita.
- **Falta de espacio de contexto:** el cliente local solicita rechazar el exceso sin recortar mensajes; el intento cuenta y se registra como `context_limit`. Se puede acortar la pregunta o finalizar con `/salir` para guardar. Véase la [prueba específica](proteccion-contexto.md).
- **Fallo de guardado:** revisar el mensaje, los permisos de la carpeta y el espacio disponible. No se muestra confirmación de guardado ni se sobrescriben archivos anteriores; el programa devuelve código 1.
- **Error de integridad:** conservar el mensaje y revisar los cambios del perfil antes de otra ejecución. El programa no reescribe los antecedentes para ocultar la diferencia.

## Alcance de la memoria y de la evidencia

El candidato recibe el mismo perfil y los turnos completos anteriores, en orden. Una repregunta como «ese proyecto» utiliza lo conversado durante esta ejecución. Los intentos fallidos cuentan, pero no añaden pares incompletos al contexto. La residencia del modelo y su caché son mecanismos de rendimiento distintos de esta memoria explícita. Véase la [guía del historial en memoria](historial-en-memoria.md) para comprobar continuidad, aislamiento y límites del contexto.

Desde la unidad 7.3, al cerrar se guarda automáticamente un JSON por sesión y se muestra su ruta si la escritura terminó correctamente. La lectura para revisión y los errores se explican en [persistencia de sesiones](persistencia-sesiones.md). La evidencia `outputs/results/console-smoke-aad61a8860c740d983b1dc4b002c0c8e.json` fue creada por una verificación técnica controlada del ejecutable, con entradas conocidas, salida capturada y comprobación del original. Es una evidencia histórica de la Etapa 6; se distingue del guardado de sesiones implementado posteriormente.

La prueba real inicial de la Etapa 6 mostró CV y puesto, inició la entrevista, obtuvo la respuesta correcta sobre formación en **34,60 s** y terminó con `/salir`, retorno 0 y perfil intacto. Es una observación de esa pregunta; no certifica consistencia global o latencia de veinte consultas. Las pruebas de límites, interrupciones y errores se realizaron con proveedores simulados.

## Memoria con resumen activable

`python -X utf8 -m scripts.run_interview --extractive-context` activa la política del controlador. Espera tres pares completos, conserva dos recientes y usa como señal la entrada informada de la última respuesta; en el cliente local actual, el umbral normal es 7424. Una selección no cuenta como pregunta. La sesión se guarda en formato 1.1.0 con auditoría; los archivos 1.0.0 siguen siendo legibles y la consola sin la opción conserva su comportamiento. El tiempo adicional de preparación se muestra separado del tiempo de respuesta del candidato. La [guía de la unidad 7.4e](resumen-en-entrevista.md) explica valores, errores y la prueba con umbral forzado.
