# Etapa 7.1: turnos de conversación en memoria

Esta unidad conserva preguntas y respuestas completas durante una ejecución. El candidato recibe los turnos previos para interpretar referencias como «ese proyecto» o «mi primera pregunta». El perfil original y la configuración siguen presentes en cada solicitud y no se sustituyen por lo que dijo el modelo.

## Archivos, funciones y dependencias

| Archivo | Cambio |
| --- | --- |
| `harness/runtime.py` | Cada `InterviewRuntime` tiene su propia lista de mensajes. `ask()` añade un par pregunta/respuesta después de una generación completa y de comprobar el perfil. `history_messages()` devuelve una copia. |
| `harness/prompt_builder.py` | `build_messages(..., history=...)` inserta pares anteriores entre el sistema y la pregunta actual. Valida el orden y copia los mensajes. |
| `harness/application/cli.py` | Anuncia que conserva la conversación durante la entrevista y que se pierde al cerrar el programa. |
| `tests/unit/test_conversation_memory.py` | Continuidad, copias, aislamiento, errores, interrupciones e integridad. |
| `tests/integration/test_history_flow.py` | Escenario, controlador, fábrica y adaptador reales con HTTP simulado para Gemma 4. |

Se actualizaron también las pruebas anteriores de consola y su integración, que comprobaban solicitudes sin historial. No hay dependencias nuevas. Se reutilizan `InterviewSetup`, `ChatMessage`, `LLMClient` y las comprobaciones de integridad.

## Flujo de un turno

1. Validar que la entrevista siga abierta y que la pregunta sea texto no vacío.
2. Construir mensajes con el mismo sistema, pares completos previos y pregunta actual.
3. Comprobar el perfil y contar la pregunta enviada.
4. Consultar al cliente y volver a comprobar el archivo, incluso si falla la generación.
5. Rechazar texto cortado. Si la respuesta es completa, añadir pregunta y respuesta a la memoria y devolverla.

Por ejemplo, la segunda solicitud general contiene:

```text
system     → instrucciones y escenario protegido
user       → primera pregunta
assistant  → primera respuesta completa
user       → repregunta actual
```

El contenido original de cada pregunta y respuesta se conserva. El historial no puede añadir mensajes `system`, pares incompletos ni roles desordenados mediante el argumento `history`. Una cadena que imite instrucciones sigue siendo texto de conversación. Esto verifica la estructura, no garantiza obediencia del LLM.

Gemma 4 conserva esos roles nativos. La adaptación existente de Gemma 3n reúne sistema y primera pregunta en el primer turno `user`, y conserva después los turnos `assistant/user`. La alternativa externa sigue utilizando el mismo contrato del candidato; no se activó la API para esta unidad.

## Errores y aislamiento

Una pregunta enviada sigue contando aunque haya un error o salida cortada. Ese intento no añade un par al contexto: una repregunta posterior recibe únicamente los turnos completos aceptados antes del fallo. No se inventa una respuesta para rellenar el hueco. Desde la unidad 7.2 el registro completo de intentos y errores se conserva en memoria, separado del historial que recibe el modelo; véase [sesiones en memoria](sesiones-en-memoria.md). El guardado posterior se documenta en [persistencia de sesiones](persistencia-sesiones.md).

Cada controlador crea su propia memoria, aunque comparta escenario o cliente. Pedir `history_messages()` devuelve diccionarios nuevos; modificar esa copia o una solicitud del cliente no altera los turnos almacenados. Los comandos, entradas vacías y repeticiones de `/iniciar` no reinician ni añaden turnos.

`close()` impide más preguntas y conserva la memoria del objeto mientras este exista. Desde la unidad 7.3 se archiva el registro completo al terminar el programa. Volver a ejecutar la consola crea otra entrevista sin conversaciones anteriores.

## Verificación en PowerShell

Con Ollama abierto, en la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

Resultado técnico esperado actual: **690 passed** (650 unitarias y cuarenta integraciones), sin llamadas reales en pytest. En la consola, debe aparecer que las preguntas y respuestas se conservan durante la entrevista.

Escribir estas entradas dentro del programa, de una en una y esperando cada respuesta:

```text
/iniciar
Cuéntame brevemente tu aporte al proyecto Inventario Aula.
¿Qué tecnologías utilizaste en ese proyecto?
¿Se usó con clientes comerciales o en producción?
¿Cómo se llamaba el proyecto de mi primera pregunta?
/salir
```

Se espera continuidad sobre **Inventario Aula**, su naturaleza académica, las tecnologías respaldadas por el perfil y ausencia de clientes comerciales o producción. La última respuesta debe identificar ese proyecto, sin cambiar a MesaFaro. No se exige una frase idéntica entre ejecuciones. Debe terminar con el original intacto.

Errores habituales:

- **Modelo no encontrado o sin conexión:** comprobar que Ollama esté abierto y que `ollama list` incluya `gemma4:e4b`. El intento fallido cuenta y no aporta un turno completo; cerrar y reiniciar la comprobación si hace falta.
- **Módulo no encontrado:** ejecutar desde la raíz indicada con el Python de `.venv` y `-m scripts.run_interview`.
- **Respuesta incoherente o cambio de proyecto:** conservar preguntas y respuestas completas para revisarlas; no modificar el perfil para hacerlas coincidir.

## Alcance pendiente

La memoria contiene afirmaciones del LLM, que pueden ser erróneas. Las instrucciones establecen que el perfil tiene prioridad y que el candidato debe corregir una respuesta previa incompatible; esta unidad no extrae ni certifica hechos automáticamente.

El contexto crece con cada turno. El cliente local solicita 8192 tokens y esta unidad no estima, resume ni recorta conversaciones. Se verifica una conversación breve; el manejo del tamaño se desarrollará en otra unidad antes de validar entrevistas extensas. El límite de veinte preguntas es un control de envíos, no una garantía de que cualquier texto de veinte turnos quepa en ese contexto.

La unidad 7.2 incorpora identificadores de sesión, fechas por intento y registro técnico completo en memoria. El guardado/lectura JSON se añadió en la unidad 7.3. Los resúmenes siguen pendientes. Se espera el resultado del usuario antes de continuar.

## Evidencia obtenida en esta unidad

La suite terminó con **432 passed in 17.73s**: 421 casos unitarios y once integraciones. Se añadieron veinte unitarias y una integración, y se actualizaron las comprobaciones de consola que antes exigían preguntas independientes. La primera recolección encontró un conflicto entre archivos nuevos con el mismo nombre; se resolvió renombrando la integración a `test_history_flow.py`, sin cambiar dependencias ni borrar cachés.

Se ejecutó la consola real con las cuatro preguntas anteriores, `gemma4:e4b` y API externa desactivada. El candidato mantuvo **Inventario Aula** como referencia, enumeró Python, Flask, PostgreSQL, HTML, CSS y JavaScript básico, confirmó que no hubo clientes comerciales ni producción y recordó el nombre al final. Las respuestas tardaron **62,99 s**, **8,62 s**, **6,96 s** y **7,63 s**. El proceso completo duró **87,35 s**, terminó con código 0 y conservó perfil, puesto, configuración e instrucciones. No se midieron las fases del servidor en esta ejecución ni se atribuye la duración inicial a una causa concreta.

Evidencia: [console-memory-18b74d5c14914bf7bf803149eac72746.json](../outputs/results/console-memory-18b74d5c14914bf7bf803149eac72746.json). Fue creada por una verificación externa que capturó entradas y salida del programa; no representa guardado automático de sesiones. La huella del sistema de la primera pregunta sigue siendo `A2596C462EEBACB0B25188C351FA7064C4496565A3AFB359F5097297CF2E8C1B`, igual a la revisión anterior sin historial. Las instrucciones continúan en 1.0.5. La comprobación humana del usuario queda pendiente y esta muestra no certifica consistencia de todas las conversaciones.

## Incidencia posterior del usuario: orden de proyectos

El usuario confirmó 432 pruebas en 16,65 s y la continuidad de las repreguntas. Al añadir MesaFaro y preguntar por el orden de realización, el modelo invirtió la cronología, pese a conservar el perfil. Se registró y corrigió en una unidad acotada, añadiendo fechas ordenadas por inicio y término y meses de coincidencia al contexto. La suite actual es de 440 pruebas y las instrucciones están en 1.0.8. Las evidencias anteriores de esta guía corresponden al sistema 1.0.5 y se conservan como mediciones históricas. Véase la [corrección cronológica](pruebas/correccion-cronologia.md) para los intentos fallidos, la revisión final y cómo repetirla.

## Preguntas posteriores: duración y estudios

El usuario confirmó 440 pruebas en 45,40 s y el orden correcto de proyectos. Al ampliar la conversación, el modelo confundió la duración total con la posterior a la práctica y omitió MesaFaro al comparar con los estudios. Se incorporó un módulo puro de hechos temporales: total de empleo de 21 meses calendario, desglose por rol y jornada, y términos conjuntos de proyectos y estudios. La versión actual de instrucciones es 1.0.11 y la suite tiene 451 pruebas. La pregunta sobre tiempo fuera del trabajo se trata como ambigua si no indica periodo. Véase el [registro de esta corrección](pruebas/correccion-duracion-y-estudios.md), incluidos intentos insuficientes y el matiz de reconocimiento verbal de un error anterior.

## Continuación: registro de sesiones en memoria

Tras la comprobación del usuario de las cifras y los términos, la unidad 7.2 añadió `SessionState`, identificadores UUID, fechas UTC y registro de todos los intentos. `history_messages()` sigue mostrando únicamente pares completos, ahora derivados de ese registro; los fallos y texto parcial permanecen fuera del contexto válido. `/sesion` presenta un resumen. La suite de la 7.2 tuvo 477 pruebas. Desde la 7.3 hay 530 y guardado/lectura JSON; la gestión del tamaño sigue pendiente. Véase [sesiones en memoria](sesiones-en-memoria.md).

## Medición del contexto registrado

La unidad 7.4a añade un diagnóstico sin red de los tokens que ya aparecen en un archivo de sesión. Usa un presupuesto de comparación explícito y reservas, sin cambiar los mensajes o el controlador. La suite actual tiene 559 pruebas. La reducción automática y los resúmenes siguen pendientes; véase [diagnóstico del contexto](diagnostico-contexto.md).

La unidad 7.4b solicita a Ollama rechazar el exceso de contexto sin recortar mensajes. El intento rechazado permanece en el archivo y cuenta una vez, mientras el historial válido conserva los pares completos anteriores para una pregunta menor. La suite actual tiene 577 pruebas. Los resúmenes siguen pendientes; véase [protección del contexto](proteccion-contexto.md).

La unidad 7.4c prepara propuestas extractivas con citas literales, fuentes verificables y pares recientes completos. Python conserva anclas de cifras, negaciones, nombres y extremos de respuestas; el resultado queda pendiente de revisión porque puede omitir contexto relevante. La conversación activa sigue enviando sus pares completos y la integración del resumen continúa pendiente. La suite actual tiene 632 pruebas; véase [resumen extractivo](resumen-extractivo.md).

La unidad 7.4d compone mensajes con citas y pares recientes, vinculados a las fuentes actuales. Conserva la versión completa cuando el resumen no reduce el JSON total. Una consulta aislada permite revisar el contexto sin alterar la entrevista archivada. La suite actual tiene 654 pruebas. La activación en el controlador y su presupuesto siguen pendientes; véase [contexto con resumen](contexto-con-resumen.md).

La unidad 7.4e incorpora la política al controlador como opción `--extractive-context`. Conserva el historial íntegro para registro y deriva cada propuesta de sus fuentes originales, con dos pares recientes completos. Las selecciones tienen eventos independientes y no consumen preguntas. Si fallan, se intenta la pregunta con el historial completo; no se repite una generación del candidato. La suite actual tiene 690 pruebas. Véase [resumen en entrevista](resumen-en-entrevista.md) para el formato 1.1.0 y sus límites.

El usuario confirmó la unidad final con 690 pruebas aprobadas, cuatro respuestas y lectura del registro 1.1.0. Se documentó el [cierre funcional de la Etapa 7](cierre-etapa-7.md), separando pruebas y límites. La transición a la Etapa 8 espera su indicación.
