# Etapa 7.4e: resumen activable en el controlador

La consola permite activar la política con `--extractive-context`. El controlador prepara el contexto de cada pregunta y registra las operaciones de resumen por separado. El historial completo y los antecedentes originales se conservan. Sin esa opción, se mantiene el comportamiento anterior y el formato de sesión 1.0.0.

## Archivos y responsabilidades

| Archivo | Cambio |
| --- | --- |
| `harness/live_context.py` | `LiveContextPolicy`, decisiones de activación, metadatos de preparación y validación de la auditoría. |
| `harness/runtime.py` | Preparación antes de enviar la pregunta, controles del perfil alrededor del selector y respaldo con historial completo. |
| `harness/session_state.py` | Política fija por sesión y eventos de contexto independientes de los intentos del candidato. |
| `schemas/session.schema.json` | Lectura de 1.0.0 y nuevo contrato 1.1.0 con política y eventos obligatorios. |
| `harness/session_log.py` | Comprobar fechas, orden, fuentes, selección y medidas del registro de contexto antes de guardar o cargar. |
| `scripts/run_interview.py` | Opciones explícitas para activar la política y elegir un umbral de comprobación. |
| `harness/application/cli.py` | Resumen de operaciones de memoria y tiempo adicional de preparación. |
| `tests/unit/test_live_context.py` | 32 casos de política, ejecución, errores, integridad y auditoría inválida. |
| `tests/integration/test_live_context_console_flow.py` | Cuatro recorridos de consola, cliente y archivos, con HTTP simulado. |

No se añaden dependencias. Perfil, puesto, configuración básica, instrucciones 1.0.11, selección de modelos y adaptadores conservan sus archivos.

## Política de activación

Valores normales al activar la opción con el cliente local actual:

| Parámetro | Valor |
| --- | ---: |
| Capacidad solicitada a Ollama | 8192 tokens |
| Reserva de salida | 512 tokens |
| Margen adicional | 256 tokens |
| Umbral de entrada informada | 7424 tokens |
| Mínimo de pares completos antes de resumir | 3 |
| Pares recientes conservados completos | 2 |

Después del mínimo de pares, la política intenta resumir si la última respuesta completa informó una entrada igual o superior al umbral. También puede activarse en una pregunta nueva si el intento anterior fue rechazado por contexto. No reenvía ese intento anterior: permanece fallido, registrado y contado.

Una vez iniciada la política de selección en esa entrevista, sigue preparando propuestas en las preguntas posteriores. Cada propuesta se deriva del historial completo original; no resume sucesivamente un resumen anterior. Si falta la métrica de entrada, no la interpreta como cero ni estima un tamaño futuro. El umbral es una señal retrospectiva, no un conteo previo exacto.

El controlador conserva el contexto completo cuando no hay omisiones o los mensajes con extractos no disminuyen sus bytes. La reducción de bytes no garantiza un ahorro idéntico de tokens ni que la solicitud quepa. Ollama continúa recibiendo `truncate: false` y `shift: false`.

`--summary-trigger-tokens` permite un umbral explícito entre uno y el límite con reservas. La opción **1** del ejemplo siguiente fuerza la selección en una entrevista corta para comprobarla; no es el valor normal recomendado para cada ejecución. La capacidad local declarada debe coincidir con la solicitada al cliente. Para otro proveedor sin capacidad declarada, el llamador debe proporcionar `--summary-context-size`; esta unidad no infiere capacidades de nombres de modelos ni realizó llamadas externas.

## Contadores y errores

Una selección de memoria no consume una pregunta. La pregunta del entrevistador empieza a contar cuando se registra su intento de envío al candidato, después de preparar el contexto. Se conserva el máximo configurado de veinte preguntas enviadas y el cierre anticipado.

Si la selección devuelve JSON inválido, índices incorrectos, texto cortado o un error conocido del proveedor, se registra una incidencia y se intenta una sola generación del candidato con el historial completo. El error del selector no se añade como respuesta al historial. Si el contexto completo también es rechazado, el intento del candidato queda fallido y cuenta una vez. No se repite automáticamente esa generación.

`Ctrl+C` durante la selección interrumpe la preparación: no se inventa un intento del candidato. La consola cierra y guarda el registro disponible. Un cambio del perfil durante la selección cierra por integridad y evita enviar la pregunta. Cuando coinciden error del selector y alteración del perfil, se conservan ambas incidencias sin copiar sus mensajes arbitrarios.

El tiempo de generación del candidato y el tiempo adicional de preparación de memoria se muestran por separado cuando hubo selección. Los errores también conservan el tiempo de preparación medido, aunque no haya métricas del proveedor. Una métrica ausente permanece desconocida; no se inventan tokens para llamadas fallidas.

## Archivo de sesión 1.1.0

Con la opción activa se añaden `context_policy` y `context_events`. La política queda fija desde el inicio. Cada evento tiene número, fecha UTC, pregunta que se iba a enviar y `candidate_sent`. Registra motivo de activación, resultado del selector, tiempo de preparación, índices aceptados cuando existen, métricas disponibles, decisión de contexto, bytes y hashes. No copia el perfil interno del sistema ni la respuesta libre de un selector inválido.

Los índices y las citas se pueden reconstruir desde el prefijo del historial completo que existía en ese momento. El lector comprueba orden de eventos, cobertura de preguntas enviadas, política, índices, huella del historial y coherencia aritmética de las medidas. Las fechas siguen usando UTC real; la referencia ficticia permanece en 2026-10-20. El reloj no tiene que ser monótono para validar el orden: lo determinan los números de eventos y preguntas.

`messages_sha256` identifica el JSON general de los mensajes antes de adaptar el modelo. No es una firma de autenticidad del archivo ni un conteo de tokens. La versión 1.0.0 continúa siendo legible y no admite los campos nuevos. Los archivos de sesiones anteriores no se migran o sobrescriben.

## Comprobar en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview --extractive-context --summary-trigger-tokens 1
```

Esperado: **690 passed**, 650 unitarias y cuarenta integraciones. Dentro del programa, introducir una por una:

```text
/iniciar
Menciona tu proyecto académico.
¿Qué tecnologías utilizaste en ese proyecto?
¿Cuántos meses trabajaste en total, incluyendo la práctica?
¿Cómo se llamaba el proyecto de mi primera pregunta?
/salir
```

Se esperan cuatro preguntas enviadas y cuatro respuestas completas. La preparación del resumen se intenta antes de la cuarta, con los dos pares más recientes completos. En respuestas breves puede conservarse el historial completo; eso no es un error. El primer proyecto debe seguir siendo Inventario Aula. El programa debe confirmar el perfil intacto y el guardado.

Después de la confirmación de guardado, de vuelta en PowerShell:

```powershell
$archivoSesion = Get-ChildItem -LiteralPath '.\outputs\sessions' -Filter 'session-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
.\.venv\Scripts\python.exe -X utf8 -c "import sys; from harness.session_log import load_session; s = load_session(sys.argv[1]); print('Versión:', s['session_version']); print('Preguntas:', len(s['attempts'])); print('Estados:', [a['status'] for a in s['attempts']]); print('Preparaciones:', len(s['context_events'])); print('Selectores:', [e['selector_status'] for e in s['context_events']]); print('Modo final:', s['context_events'][-1]['preparation']['mode'])" $archivoSesion.FullName
```

Esperado: **1.1.0**, cuatro preguntas, cuatro estados `completed`, cuatro preparaciones y selectores `not_requested`, `not_requested`, `not_requested`, `completed`. La preparación adicional no debe sumar una quinta pregunta.

Para una entrevista normal con el umbral 7424, usar solo `--extractive-context`. Sin la opción se conserva la consola anterior. Si falla el selector, revisar su incidencia en el archivo: puede haber respuestas completas con una incidencia de preparación. Ante error de conexión comprobar Ollama y el modelo. Un fallo de integridad o guardado debe conservarse para revisión; no se deben editar los hashes para ocultarlo.

## Verificación y límites

El usuario confirmó la unidad 7.4d con **654 passed in 35.88s**, contexto completo por `no_omissions`, 27496 → 27496 bytes y respuesta correcta sobre Inventario Aula en 33,44 s. Se registró en [summary-context-user-confirmation-97b2934e7b5f431e8ed11e68f7b3aa8e.json](../outputs/results/summary-context-user-confirmation-97b2934e7b5f431e8ed11e68f7b3aa8e.json), distinguiendo el resultado comunicado de la lectura local.

La suite previa de compatibilidad pasó con **654 passed in 106.64s**. Los 35 casos nuevos iniciales pasaron en 14,24 s; después se añadió la comprobación del tiempo de preparación. Los 36 casos finales pasaron en **14,86 s**. La suite conjunta terminó con **690 passed in 104.14s**, 650 unitarias y cuarenta integraciones, sin fallos ni llamadas reales dentro de pytest. No se atribuye la variación de duración a una causa sin medirla.

El resumen automático conserva `not_reviewed`: se comprueba procedencia y estructura, no la relevancia de todas las omisiones ni la verdad de las afirmaciones históricas. La opción queda explícita para esta unidad. La protección, los registros originales y la revisión humana de preguntas de referencia continúan siendo necesarios. No se garantiza que cualquier entrevista de veinte turnos quepa en la capacidad indicada.

La entrevista real de cuatro preguntas con Ollama y `gemma4:e4b` terminó con cuatro respuestas completas, cero incidencias y una selección antes de la cuarta pregunta. Conservó Inventario Aula, sus tecnologías y el total de 21 meses. Las respuestas tardaron **117,53; 11,85; 13,28 y 4,98 s**. La preparación final conservó el historial completo por ausencia de omisiones; no se fuerza una reducción en respuestas breves.

La aplicación guardó [session-a5ad4e7c-aeb1-4906-8f41-7d113be13001.json](../outputs/sessions/session-a5ad4e7c-aeb1-4906-8f41-7d113be13001.json), formato **1.1.0**, con cuatro eventos y el patrón de selectores esperado. La lectura validada coincidió exactamente con la instantánea final del controlador. Para Gemma 4 se contrastaron también las huellas de las listas de mensajes realmente enviadas con las registradas en la auditoría.

Un segundo caso preparó tres respuestas y conteos de entrada simulados para ejercitar el ahorro de forma controlada; la selección y la cuarta respuesta sí fueron llamadas reales a Ollama. No se presenta como una entrevista natural. El controlador eligió `extractive_summary`, ahorró **999 bytes de mensajes** y la respuesta mantuvo Inventario Aula y pytest. Su lectura/escritura se comprobó en un directorio temporal, no en la carpeta de entrevistas naturales. No se compara el conteo simulado con los tokens reales para afirmar un ahorro de tokens.

La evidencia adicional está en [live-context-ea4988d6741a40f9be580eb8c7ba4fd2.json](../outputs/results/live-context-ea4988d6741a40f9be580eb8c7ba4fd2.json). Distingue ambos casos, conserva los registros completos y los hashes de las solicitudes, y compara los cuatro originales y todas las sesiones anteriores antes y después. No se atribuye la latencia a una causa sin una comprobación específica ni se promete una mejora de velocidad. La API externa permaneció desactivada.

La funcionalidad queda implementada y comprobada para estos casos. Se espera la ejecución del usuario de esta unidad antes de continuar con nuevas pruebas o cambios de política.

Confirmación posterior: el usuario obtuvo **690 passed in 38.14s**, cuatro respuestas completas, una selección de memoria, cero resúmenes usados y archivo 1.1.0 con cuatro eventos. La lectura local confirmó la sesión `f8d281c9-bca7-4bdd-9b52-d7f9788399e5`. El [cierre funcional de la Etapa 7](cierre-etapa-7.md) resume el alcance, los límites y la propuesta de transición; no se ha iniciado automáticamente la Etapa 8.
