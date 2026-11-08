# Historial, sesiones y gestión del contexto

[Índice general](../README.md#documentación)

Las secciones fechadas y los registros de etapas describen el estado y las pruebas de su momento.

## Contenido

- [Cierre funcional de la Etapa 7: historial y contexto](#cierre-etapa-7)
- [Etapa 7.1: turnos de conversación en memoria](#historial-en-memoria)
- [Etapa 7.2: identidad de sesión y registro de intentos](#sesiones-en-memoria)
- [Etapa 7.3: guardar y leer sesiones en JSON local](#persistencia-sesiones)
- [Etapa 7.4a: diagnóstico del contexto registrado](#diagnostico-contexto)
- [Etapa 7.4b: rechazo explícito antes de perder contexto](#proteccion-contexto)
- [Etapa 7.4c: propuesta de resumen extractivo verificable](#resumen-extractivo)
- [Etapa 7.4d: composición del contexto y consulta aislada](#contexto-con-resumen)
- [Etapa 7.4e: resumen activable en el controlador](#resumen-en-entrevista)

<a name="cierre-etapa-7"></a>

## Cierre funcional de la Etapa 7: historial y contexto

La Etapa 7 queda implementada y comprobada en el alcance descrito aquí. La confirmación final del usuario fue **690 passed in 38.14s**, una entrevista nueva de cuatro preguntas y lectura validada del archivo 1.1.0. Este cierre no declara terminadas las pruebas ampliadas de consistencia de la Etapa 8 ni la validación final de la Etapa 9.

### Funcionalidad y evidencia

| Capacidad | Estado comprobado |
| --- | --- |
| Conservar conversación y referencias | Historial completo por sesión y pares recientes completos al preparar extractos; repregunta del usuario conservó Inventario Aula. |
| Identidad y aislamiento | UUID por ejecución, configuración copiada y sesiones independientes; pruebas automatizadas y comprobaciones manuales anteriores. |
| Límite y cierre | Máximo configurable hasta veinte envíos, incluidos fallos del candidato; límites y cierres comprobados con simulaciones. La ejecución final del usuario tuvo cuatro envíos. |
| Guardado y lectura | JSON local UTF-8, creación sin sobrescribir y validación de forma/relaciones. Formatos 1.0.0 y 1.1.0 legibles. |
| Proteger antecedentes | Perfil comprobado antes/después de llamadas y al finalizar; sus bytes y el hash de instrucciones coinciden con la procedencia del archivo final. |
| Medir contexto | Métricas informadas y reservas explícitas; se distingue información pasada de una predicción del siguiente envío. |
| Rechazar exceso | Controles de Ollama y error `context_limit`; el usuario confirmó rechazo, conservación del historial y repregunta posterior. |
| Preparar resumen | Selección de índices, citas literales verificables, anclas conservadas por Python y dos pares recientes completos por defecto. |
| Usar resumen en el controlador | Opción `--extractive-context`, activación por política y eventos separados del contador de preguntas. Una fixture identificada ejercitó el uso real de extractos y conservó referencias. |
| Recuperarse de fallos del selector | Respaldo con historial completo, interrupción antes del envío y protección de integridad; pruebas automatizadas con errores simulados. |

Las comprobaciones unitarias e integraciones usan proveedores simulados. Las llamadas reales y las fixtures están identificadas en sus evidencias; una fixture no se presenta como entrevista natural ni como medición real de sus datos predefinidos.

### Confirmación final del usuario

Archivo: [session-f8d281c9-bca7-4bdd-9b52-d7f9788399e5.json](../outputs/sessions/session-f8d281c9-bca7-4bdd-9b52-d7f9788399e5.json).

- Estado `closed`, motivo `user_exit`, integridad `unchanged` y versión **1.1.0**.
- Cuatro preguntas enviadas y cuatro respuestas `completed`.
- Cero incidencias técnicas.
- Cuatro preparaciones; tres selectores `not_requested` y el cuarto `completed`.
- Una selección de memoria y cero resúmenes aplicados, porque las citas antiguas se conservaron completas.
- Preparación final `full_history` por `no_omissions`, con **27 951 → 27 951 bytes** de mensajes generales.
- Latencias comunicadas: **67,15; 7,51; 7,37 y 3,45 s** para el candidato; **4,58 s** adicionales de preparación en la cuarta pregunta.

El candidato conservó Inventario Aula, sus tecnologías y el total de 21 meses calendario incluyendo práctica. La cuarta respuesta conservó la referencia correcta, aunque su expresión «mi primera pregunta» puede afinarse a «mi primera respuesta». Se registra como observación de redacción para la revisión posterior, sin convertirla en un fallo técnico o afirmar que se alteró el antecedente.

La lectura local reprodujo los estados y la auditoría comunicados, sin modificar el archivo. La confirmación estructurada está en [live-context-user-confirmation-209e77b7567a4699827786bb493d3e7c.json](../outputs/results/live-context-user-confirmation-209e77b7567a4699827786bb493d3e7c.json). Distingue el resultado del usuario de la lectura local y conserva los hashes.

### Uso normal

Con las variables locales y el modelo ya seleccionados, desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview --extractive-context
```

El umbral normal del cliente actual es **7424 tokens de entrada informada**. El valor **1** de la prueba final fue un ajuste deliberado para ejercitar la selección en una conversación breve; no modifica el valor normal. Sin `--extractive-context` se mantiene la ruta anterior.

La opción sigue siendo explícita. Ollama es el proveedor principal; la API externa permanece como alternativa de activación explícita y no se utilizó en estas pruebas reales. Perfil, puesto, configuración aprobada, referencia **2026-10-20**, máximo **20** e instrucciones **1.0.11** se conservan.

### Límites que pasan a la validación posterior

Los estados `completed` y los hashes no certifican la verdad de todas las respuestas. La selección de citas puede omitir contexto importante pese a las anclas; su estado `not_reviewed` no se convierte en una revisión humana. El ahorro de bytes no equivale automáticamente al de tokens y el umbral se basa en llamadas pasadas.

No se garantiza que veinte preguntas arbitrariamente extensas quepan en la capacidad disponible. No se han validado exhaustivamente entrevistas naturales de veinte turnos ni todas las variaciones de modelo. La primera llamada y la preparación pueden tardar; las observaciones aisladas no prueban una latencia garantizada o una mejora de rendimiento.

La clasificación de preguntas, la rúbrica, puntuaciones, niveles y retroalimentación educativa continúan fuera de esta fase. Este cierre no incorpora esos componentes.

### Propuesta de transición a la Etapa 8

La instrucción inicial del usuario indica: «No avances automáticamente entre etapas». Tras este cierre, el usuario autorizó explícitamente la transición con «Pasemos a la etapa 8 también muéstrame que etapas completamos y cuantas faltan». Se inició la [unidad 8.1](validacion-del-candidato.md#referencias-consistencia). El [estado de las nueve etapas](estado-del-proyecto.md#estado-etapas) registra siete completadas y dos por terminar.

La primera unidad propuesta sería un conjunto pequeño de cuatro casos de referencia con criterios de revisión humana:

| Caso propuesto | Entrada | Hechos esperados |
| --- | --- | --- |
| Formación | ¿Dónde estudiaste y qué título obtuviste? | Instituto Profesional Horizonte Digital; Ingeniería en Informática. |
| Duración | ¿Cuántos meses trabajaste en total, incluyendo la práctica? | 21 meses calendario distintos; 3 de práctica y 18 posteriores, sin afirmar equivalencia a jornada completa. |
| Continuidad | Menciona tu proyecto académico. → ¿Cómo se llamaba el proyecto de tu primera respuesta? | Inventario Aula, proyecto académico; la repregunta conserva la referencia. |
| Límite de experiencia | ¿Has utilizado Kubernetes en un proyecto profesional? | Reconocer ausencia de experiencia práctica, sin inventar un proyecto. |

Los casos propuestos ya se prepararon como conjunto de referencia de la unidad 8.1; siguen pendientes la ejecución y revisión de respuestas reales. La revisión debe comprobar compatibilidad de hechos y referencias, no exigir una frase literal completa ni asignar una puntuación educativa. Después podrían ampliarse cronología, ambigüedad, contradicciones y protección de instrucciones, en unidades separadas.

---

<a name="historial-en-memoria"></a>

## Etapa 7.1: turnos de conversación en memoria

Esta unidad conserva preguntas y respuestas completas durante una ejecución. El candidato recibe los turnos previos para interpretar referencias como «ese proyecto» o «mi primera pregunta». El perfil original y la configuración siguen presentes en cada solicitud y no se sustituyen por lo que dijo el modelo.

### Archivos, funciones y dependencias

| Archivo | Cambio |
| --- | --- |
| `harness/runtime.py` | Cada `InterviewRuntime` tiene su propia lista de mensajes. `ask()` añade un par pregunta/respuesta después de una generación completa y de comprobar el perfil. `history_messages()` devuelve una copia. |
| `harness/prompt_builder.py` | `build_messages(..., history=...)` inserta pares anteriores entre el sistema y la pregunta actual. Valida el orden y copia los mensajes. |
| `harness/application/cli.py` | Anuncia que conserva la conversación durante la entrevista y que se pierde al cerrar el programa. |
| `tests/unit/test_conversation_memory.py` | Continuidad, copias, aislamiento, errores, interrupciones e integridad. |
| `tests/integration/test_history_flow.py` | Escenario, controlador, fábrica y adaptador reales con HTTP simulado para Gemma 4. |

Se actualizaron también las pruebas anteriores de consola y su integración, que comprobaban solicitudes sin historial. No hay dependencias nuevas. Se reutilizan `InterviewSetup`, `ChatMessage`, `LLMClient` y las comprobaciones de integridad.

### Flujo de un turno

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

### Errores y aislamiento

Una pregunta enviada sigue contando aunque haya un error o salida cortada. Ese intento no añade un par al contexto: una repregunta posterior recibe únicamente los turnos completos aceptados antes del fallo. No se inventa una respuesta para rellenar el hueco. Desde la unidad 7.2 el registro completo de intentos y errores se conserva en memoria, separado del historial que recibe el modelo; véase [sesiones en memoria](#sesiones-en-memoria). El guardado posterior se documenta en [persistencia de sesiones](#persistencia-sesiones).

Cada controlador crea su propia memoria, aunque comparta escenario o cliente. Pedir `history_messages()` devuelve diccionarios nuevos; modificar esa copia o una solicitud del cliente no altera los turnos almacenados. Los comandos, entradas vacías y repeticiones de `/iniciar` no reinician ni añaden turnos.

`close()` impide más preguntas y conserva la memoria del objeto mientras este exista. Desde la unidad 7.3 se archiva el registro completo al terminar el programa. Volver a ejecutar la consola crea otra entrevista sin conversaciones anteriores.

### Verificación en PowerShell

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

### Alcance pendiente

La memoria contiene afirmaciones del LLM, que pueden ser erróneas. Las instrucciones establecen que el perfil tiene prioridad y que el candidato debe corregir una respuesta previa incompatible; esta unidad no extrae ni certifica hechos automáticamente.

El contexto crece con cada turno. El cliente local solicita 8192 tokens y esta unidad no estima, resume ni recorta conversaciones. Se verifica una conversación breve; el manejo del tamaño se desarrollará en otra unidad antes de validar entrevistas extensas. El límite de veinte preguntas es un control de envíos, no una garantía de que cualquier texto de veinte turnos quepa en ese contexto.

La unidad 7.2 incorpora identificadores de sesión, fechas por intento y registro técnico completo en memoria. El guardado/lectura JSON se añadió en la unidad 7.3. Los resúmenes siguen pendientes. Se espera el resultado del usuario antes de continuar.

### Evidencia obtenida en esta unidad

La suite terminó con **432 passed in 17.73s**: 421 casos unitarios y once integraciones. Se añadieron veinte unitarias y una integración, y se actualizaron las comprobaciones de consola que antes exigían preguntas independientes. La primera recolección encontró un conflicto entre archivos nuevos con el mismo nombre; se resolvió renombrando la integración a `test_history_flow.py`, sin cambiar dependencias ni borrar cachés.

Se ejecutó la consola real con las cuatro preguntas anteriores, `gemma4:e4b` y API externa desactivada. El candidato mantuvo **Inventario Aula** como referencia, enumeró Python, Flask, PostgreSQL, HTML, CSS y JavaScript básico, confirmó que no hubo clientes comerciales ni producción y recordó el nombre al final. Las respuestas tardaron **62,99 s**, **8,62 s**, **6,96 s** y **7,63 s**. El proceso completo duró **87,35 s**, terminó con código 0 y conservó perfil, puesto, configuración e instrucciones. No se midieron las fases del servidor en esta ejecución ni se atribuye la duración inicial a una causa concreta.

Evidencia: [console-memory-18b74d5c14914bf7bf803149eac72746.json](../outputs/results/console-memory-18b74d5c14914bf7bf803149eac72746.json). Fue creada por una verificación externa que capturó entradas y salida del programa; no representa guardado automático de sesiones. La huella del sistema de la primera pregunta sigue siendo `A2596C462EEBACB0B25188C351FA7064C4496565A3AFB359F5097297CF2E8C1B`, igual a la revisión anterior sin historial. Las instrucciones continúan en 1.0.5. La comprobación humana del usuario queda pendiente y esta muestra no certifica consistencia de todas las conversaciones.

### Incidencia posterior del usuario: orden de proyectos

El usuario confirmó 432 pruebas en 16,65 s y la continuidad de las repreguntas. Al añadir MesaFaro y preguntar por el orden de realización, el modelo invirtió la cronología, pese a conservar el perfil. Se registró y corrigió en una unidad acotada, añadiendo fechas ordenadas por inicio y término y meses de coincidencia al contexto. La suite actual es de 440 pruebas y las instrucciones están en 1.0.8. Las evidencias anteriores de esta guía corresponden al sistema 1.0.5 y se conservan como mediciones históricas. Véase la [corrección cronológica](validacion-del-candidato.md#correccion-cronologia) para los intentos fallidos, la revisión final y cómo repetirla.

### Preguntas posteriores: duración y estudios

El usuario confirmó 440 pruebas en 45,40 s y el orden correcto de proyectos. Al ampliar la conversación, el modelo confundió la duración total con la posterior a la práctica y omitió MesaFaro al comparar con los estudios. Se incorporó un módulo puro de hechos temporales: total de empleo de 21 meses calendario, desglose por rol y jornada, y términos conjuntos de proyectos y estudios. La versión actual de instrucciones es 1.0.11 y la suite tiene 451 pruebas. La pregunta sobre tiempo fuera del trabajo se trata como ambigua si no indica periodo. Véase el [registro de esta corrección](validacion-del-candidato.md#correccion-duracion-y-estudios), incluidos intentos insuficientes y el matiz de reconocimiento verbal de un error anterior.

### Continuación: registro de sesiones en memoria

Tras la comprobación del usuario de las cifras y los términos, la unidad 7.2 añadió `SessionState`, identificadores UUID, fechas UTC y registro de todos los intentos. `history_messages()` sigue mostrando únicamente pares completos, ahora derivados de ese registro; los fallos y texto parcial permanecen fuera del contexto válido. `/sesion` presenta un resumen. La suite de la 7.2 tuvo 477 pruebas. Desde la 7.3 hay 530 y guardado/lectura JSON; la gestión del tamaño sigue pendiente. Véase [sesiones en memoria](#sesiones-en-memoria).

### Medición del contexto registrado

La unidad 7.4a añade un diagnóstico sin red de los tokens que ya aparecen en un archivo de sesión. Usa un presupuesto de comparación explícito y reservas, sin cambiar los mensajes o el controlador. La suite actual tiene 559 pruebas. La reducción automática y los resúmenes siguen pendientes; véase [diagnóstico del contexto](#diagnostico-contexto).

La unidad 7.4b solicita a Ollama rechazar el exceso de contexto sin recortar mensajes. El intento rechazado permanece en el archivo y cuenta una vez, mientras el historial válido conserva los pares completos anteriores para una pregunta menor. La suite actual tiene 577 pruebas. Los resúmenes siguen pendientes; véase [protección del contexto](#proteccion-contexto).

La unidad 7.4c prepara propuestas extractivas con citas literales, fuentes verificables y pares recientes completos. Python conserva anclas de cifras, negaciones, nombres y extremos de respuestas; el resultado queda pendiente de revisión porque puede omitir contexto relevante. La conversación activa sigue enviando sus pares completos y la integración del resumen continúa pendiente. La suite actual tiene 632 pruebas; véase [resumen extractivo](#resumen-extractivo).

La unidad 7.4d compone mensajes con citas y pares recientes, vinculados a las fuentes actuales. Conserva la versión completa cuando el resumen no reduce el JSON total. Una consulta aislada permite revisar el contexto sin alterar la entrevista archivada. La suite actual tiene 654 pruebas. La activación en el controlador y su presupuesto siguen pendientes; véase [contexto con resumen](#contexto-con-resumen).

La unidad 7.4e incorpora la política al controlador como opción `--extractive-context`. Conserva el historial íntegro para registro y deriva cada propuesta de sus fuentes originales, con dos pares recientes completos. Las selecciones tienen eventos independientes y no consumen preguntas. Si fallan, se intenta la pregunta con el historial completo; no se repite una generación del candidato. La suite actual tiene 690 pruebas. Véase [resumen en entrevista](#resumen-en-entrevista) para el formato 1.1.0 y sus límites.

El usuario confirmó la unidad final con 690 pruebas aprobadas, cuatro respuestas y lectura del registro 1.1.0. Se documentó el [cierre funcional de la Etapa 7](#cierre-etapa-7), separando pruebas y límites. La transición a la Etapa 8 espera su indicación.

---

<a name="sesiones-en-memoria"></a>

## Etapa 7.2: identidad de sesión y registro de intentos

Esta unidad conserva en memoria la identidad de una entrevista, su configuración y todos los intentos enviados al proveedor. Incluye respuestas completas, errores, interrupciones y respuestas cortadas. Se puede consultar un resumen con `/sesion`. Esta guía documenta la unidad 7.2 original; el guardado y la lectura se añadieron después en la [unidad 7.3](#persistencia-sesiones).

### Archivos y dependencias

| Archivo | Responsabilidad |
| --- | --- |
| `harness/session_state.py` | `SessionState`: identificador UUID, fechas UTC, estado, configuración y registro técnico; copias para consulta. Se completó el archivo previsto en la arquitectura. |
| `harness/runtime.py` | Coordinar cada intento y las comprobaciones de integridad. Contador e historial se obtienen del registro para evitar estados duplicados. |
| `harness/application/cli.py` | Mostrar el identificador, atender `/sesion` y presentar el resumen al cerrar. |
| `scripts/run_interview.py` | Pasar proveedor/modelo solicitados y registrar también la comprobación final de integridad. |
| `tests/unit/test_session_state.py` | Registro, aislamiento, límites, errores simultáneos, interrupciones, copias y protección de detalles internos. |
| `tests/integration/test_session_records_flow.py` | Consola, cliente y datos reales con HTTP simulado: una llamada fallida y otra completa. |

No hay dependencias nuevas. Se usan la biblioteca estándar, los contratos del cliente, el escenario validado y los controles existentes. En la 7.2, `harness/session_log.py` no participaba en el flujo. Su implementación posterior se documenta en la unidad 7.3. No se implementan clasificación, puntuación o retroalimentación.

### Qué conserva cada registro

`runtime.session_id` identifica una entrevista concreta. No reutiliza `config_id`, `candidate_id` o el nombre del archivo. Dos controladores crean identificadores distintos, aunque compartan escenario y cliente. Repetir `/iniciar` no crea otra sesión ni reinicia el contador.

`runtime.session_dict()` devuelve una copia independiente, compuesta por valores serializables a JSON. Todavía no escribe un archivo. Su formato inicial lleva `session_version: 1.0.0` e incluye:

- Identificador de sesión, candidato y puesto; copia de la configuración.
- Hash del candidato y del texto de instrucciones, sin guardar el perfil interno, rutas o texto del sistema.
- Proveedor y modelo solicitados, si el llamador los proporciona. La consola los pasa explícitamente; no se inspecciona el cliente para obtener credenciales o ajustes privados.
- `created_at`, `closed_at`, estado abierto/cerrado y motivo del primer cierre.
- Último resultado de integridad: `not_checked`, `unchanged` o `failed`. Una detección de fallo se conserva aunque después se restauren los bytes.
- Intentos ordenados y posibles incidencias de sesión, como una alteración del perfil detectada antes de enviar una pregunta.

Las fechas de sesión e intentos utilizan la hora real en UTC con zona explícita. No son la fecha de referencia del escenario, que sigue en **2026-10-20**. Estos metadatos no se envían al LLM ni actualizan la trayectoria ficticia.

### Registro de un intento

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

### Historial para el modelo y cierre

`history_messages()` se deriva únicamente de intentos `completed`. Errores, texto parcial e interrupciones permanecen en el registro técnico, pero no aparecen como conversación válida en la siguiente solicitud. La configuración y el perfil no se sustituyen por esas respuestas. Modificar una copia del registro no modifica la memoria o la configuración activa.

El cierre se registra por salida del usuario, máximo de preguntas, fin de entrada, interrupción o fallo de integridad. No admite más preguntas después del cierre. La consola cierra ante `Ctrl+C`; un llamador programático que capture una interrupción puede continuar si aún queda espacio y no hubo un fallo de integridad. Se mantiene ese comportamiento del controlador anterior.

El programa muestra solamente un resumen: identificador, fecha de creación, estado, preguntas enviadas, respuestas completas e incidencias técnicas. No muestra desde `/sesion` respuestas parciales ni información interna de errores. El registro no evalúa la coherencia semántica de las respuestas.

### Comprobación en PowerShell

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

### Límites

En la versión original 7.2, los datos se conservaban mientras existía el controlador y se perdían al terminar el proceso. Desde la 7.3 se guardan y se pueden leer como datos, sin reanudar entrevistas. La extracción automática de hechos y la evaluación educativa siguen pendientes. El manejo del presupuesto del contexto y sus resúmenes continúa pendiente antes de validar entrevistas extensas.

Esta unidad registra la configuración y lo ocurrido; no verifica que cada afirmación del LLM sea correcta. Se espera el resultado del usuario antes de continuar con la siguiente unidad.

### Evidencia de esta unidad

La suite final terminó con **477 passed in 19.10s**: 464 unitarias y trece integraciones. Se añadieron 25 casos unitarios y una integración. Una comprobación previa de 476 casos pasó en 26,97 s; después se añadió el caso de integridad final tras el cierre. No hubo fallos de prueba ni solicitudes reales en pytest.

Se comprobó también la consola real con gemma4:e4b, consultas de `/sesion` antes y después de dos preguntas, y salida anticipada. El mismo identificador se conservó durante la ejecución; los contadores fueron 0, 1 y 2; el cierre dejó dos respuestas completas, cero incidencias y `source_integrity: unchanged`. Las respuestas conservaron 21 meses calendario y el reparto de nueve meses parciales y nueve completos. Tardaron **62,16 s** y **14,98 s**; no se midieron las fases de esas llamadas ni se atribuye la duración a una causa concreta.

Una sesión independiente pidió un nombre de modelo inexistente generado solo para esta comprobación. Ollama devolvió modelo no encontrado: quedó un intento `error`, sin respuesta inventada y con código `model_not_found`. No se descargaron pesos ni se modificó la selección normal del usuario. Los identificadores de ambas sesiones fueron distintos. El proceso de verificación completo duró **78,10 s** y conservó los bytes de perfil, puesto, configuración e instrucciones.

Evidencia externa: [session-records-c2c4375fb58340bf832dce71df8c5554.json](../outputs/results/session-records-c2c4375fb58340bf832dce71df8c5554.json). Incluye la salida y copias completas de los registros al finalizar. El archivo fue escrito por la verificación externa, no por una función de guardado de la aplicación. El registro mantiene pendiente la comprobación del usuario.

La comprobación posterior del usuario confirmó las 477 pruebas en 19,83 s y 19,45 s, los contadores y cierres de una sesión de dos preguntas y otra vacía con distinto UUID. Ambos originales quedaron intactos. La transcripción y el siguiente paso se registran en [persistencia de sesiones](#persistencia-sesiones).

---

<a name="persistencia-sesiones"></a>

## Etapa 7.3: guardar y leer sesiones en JSON local

Al terminar la consola, el programa guarda el registro completo de la sesión en `outputs/sessions/session-<UUID>.json`. Después se puede leer y validar mediante `load_session(path)`. La lectura devuelve datos para revisión; no reanuda la entrevista ni utiliza su contenido como instrucciones.

La unidad depende del registro de la 7.2, del lector JSON estricto y del validador existentes. No añade dependencias. Perfil, puesto, configuración, instrucciones 1.0.11 y elección del proveedor conservan su contenido.

### Archivos y funciones

| Archivo | Responsabilidad |
| --- | --- |
| `schemas/session.schema.json` | Contrato 1.0.0 del registro cerrado, intentos, respuestas, métricas e incidencias. Rechaza campos adicionales. |
| `harness/session_log.py` | `validate_session_data` comprueba estructura y relaciones; `save_session` crea un archivo nuevo; `load_session` lee y valida un archivo existente. |
| `scripts/run_interview.py` | Comprueba la integridad final, cierra el registro, intenta guardarlo y muestra la ruta solo cuando terminó la escritura. |
| `harness/application/cli.py` | Anuncia el guardado local al iniciar. Conserva los comandos y el resumen de sesión. |
| `tests/unit/test_session_log.py` | 45 casos sobre contratos, texto exacto, métricas, errores de lectura/escritura y conservación de archivos. |
| `tests/integration/test_session_persistence_flow.py` | Ocho casos del punto de entrada y sus archivos, con HTTP simulado. |
| `tests/conftest.py` | Dirige el guardado de pytest a carpetas temporales. Las pruebas no llenan la carpeta de sesiones del proyecto. |

### Contrato y guardado

Se conserva la copia de configuración, identidad y procedencia por hashes; proveedor y modelo solicitados; fechas UTC; estado y motivo de cierre; preguntas originales, respuestas y métricas; incidencias de intentos y de sesión. Se guardan también los intentos fallidos y las respuestas cortadas que ya conserva el registro técnico, sin convertirlos en turnos aceptados para el modelo. Las descripciones de errores generadas por la aplicación proceden del catálogo seguro y no copian cuerpos HTTP, claves o mensajes arbitrarios de excepciones.

No se copia el perfil interno completo ni el mensaje de sistema. El archivo conserva lo ocurrido, incluidas afirmaciones que podrían ser incorrectas: un intento `completed` significa que el cliente devolvió una respuesta completa, no que se haya certificado su verdad.

Antes de crear la carpeta, se valida el registro y su configuración con los dos esquemas. Se comprueban UUID canónico de versión 4, coincidencia de candidato/puesto, numeración consecutiva, límite configurado, estados y respuestas compatibles, fechas UTC reales y valores serializables en UTF-8 sin números no finitos. Solo se admiten sesiones cerradas y sin intentos pendientes.

Las fechas de sesión utilizan el reloj real. La referencia ficticia sigue en **2026-10-20**. No se exige monotonía del reloj: una comprobación final de integridad puede registrarse después del primer cierre y un ajuste del reloj no cambia el orden de los intentos.

El archivo se crea con acceso exclusivo; si ya existe, se comunica un error y se conservan sus bytes. La escritura comprueba el número de bytes, vacía el búfer y solicita sincronización al sistema. Si ocurre un fallo detectado, intenta retirar únicamente el archivo que acaba de crear. Si tampoco puede retirarlo, el mensaje identifica el archivo posiblemente incompleto para revisarlo. Este mecanismo no implementa recuperación frente a un corte de energía o terminación forzada del proceso.

### Cierre y errores

Se intenta guardar después de `/salir`, máximo de preguntas, fin de entrada o `Ctrl+C`, incluso si no se enviaron preguntas. Si se detectó una alteración del perfil, se conserva un archivo de diagnóstico con `source_integrity: failed` y el programa devuelve código 1. No restaura ni modifica el perfil. Si la preparación falla antes de crear el controlador, no inventa una sesión.

Un fallo de guardado devuelve código 1 y no muestra «Registro de sesión guardado». Revisar la carpeta, sus permisos y el espacio disponible. No se sobrescribe un archivo existente ni se activa una API alternativa. Una interrupción durante el guardado comunica que no se confirmó el archivo.

`load_session` utiliza el lector existente para rechazar JSON truncado, claves duplicadas y números no finitos; después aplica las mismas validaciones del guardado. No modifica el archivo leído. Las vistas devueltas son datos nuevos: cambiar un diccionario cargado no modifica los bytes del archivo.

### Comprobación en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

Resultado esperado: **530 passed**, 509 unitarias y 21 integraciones, sin llamadas reales en pytest. Dentro del programa, escribir de una en una:

```text
/iniciar
¿Cuántos meses trabajaste en total, incluyendo la práctica?
¿Cuántos fueron a jornada parcial y cuántos a completa?
/salir
```

Debe aparecer un resumen cerrado con dos intentos y la ruta absoluta del archivo guardado. Con dos respuestas completas, los dos estados serán `completed`. El identificador del nombre del archivo debe coincidir con el mostrado al iniciar. Después, de vuelta en PowerShell:

```powershell
$archivoSesion = Get-ChildItem -LiteralPath '.\outputs\sessions' -Filter 'session-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
.\.venv\Scripts\python.exe -X utf8 -c "import sys; from harness.session_log import load_session; sesion = load_session(sys.argv[1]); print('Sesión:', sesion['session_id']); print('Estado:', sesion['status']); print('Integridad:', sesion['source_integrity']); print('Intentos:', len(sesion['attempts'])); print('Estados:', [intento['status'] for intento in sesion['attempts']])" $archivoSesion.FullName
```

Esperado: el mismo UUID de esa ejecución, `closed`, `unchanged`, dos intentos y dos estados `completed`. Si no hay archivo nuevo, conservar el mensaje de guardado: no interpretar un archivo anterior como resultado de esta ejecución. Abrir otra vez y salir sin preguntas debe generar otro UUID y otro archivo con cero intentos, conservando el primero.

### Evidencia y alcance

El usuario confirmó la unidad 7.2 con **477 passed in 19.83s** y **477 passed in 19.45s**. Su primera sesión registró dos respuestas y cero incidencias; la segunda tuvo otro UUID y cero intentos. Ambas terminaron con el original intacto. Los archivos de esas sesiones no existían: aquella versión conservaba registros en memoria y no se crean retrospectivamente.

La suite de esta unidad terminó con **530 passed in 26.20s**. Se añadieron 45 casos unitarios y ocho integraciones; se amplió además el caso existente de integridad final para comprobar su archivo de diagnóstico. La primera recolección detectó una construcción incorrecta de `ProfileIntegrityError` en el código de prueba; se corrigió usando sus tres argumentos. Después pasaron los 51 casos nuevos iniciales; se añadieron dos límites de formato UTC antes de la suite final. No se hicieron solicitudes reales en pytest.

La comprobación real local ejecutó dos preguntas con `gemma4:e4b` y API externa desactivada. La aplicación guardó [session-67fbee76-9926-438d-8d19-5b0da7f20036.json](../outputs/sessions/session-67fbee76-9926-438d-8d19-5b0da7f20036.json), cerrado por `user_exit`, con dos intentos completos, cero incidencias y fuente intacta. Las respuestas conservaron 21 meses y el desglose de nueve parciales y nueve completos; tardaron **64,76 s** y **15,23 s**. No se atribuyen estos tiempos a una causa sin métricas por fase.

Otra ejecución sin preguntas guardó [session-b51cad38-89df-4fcc-b2ef-d7ab450ff366.json](../outputs/sessions/session-b51cad38-89df-4fcc-b2ef-d7ab450ff366.json), con otro identificador y cero intentos, conservando el primer archivo. En ambos casos, la lectura validada coincidió exactamente con la instantánea final del controlador. Perfil, puesto, configuración e instrucciones mantuvieron sus hashes aprobados.

La salida completa y las comparaciones se conservan en [session-persistence-ca7f555825ac4bf29124f9cbb29666b9.json](../outputs/results/session-persistence-ca7f555825ac4bf29124f9cbb29666b9.json). La confirmación anterior del usuario se copió sin alteraciones a [session-user-confirmation-93abca64583446d89fca2a0f5722dc28.txt](../outputs/results/session-user-confirmation-93abca64583446d89fca2a0f5722dc28.txt). Los archivos en `outputs/sessions` los creó la aplicación; el de `outputs/results` es evidencia adicional del verificador.

Se espera el resultado del usuario antes de otra unidad. El tamaño del contexto, los resúmenes y la extracción de hechos relevantes siguen pendientes. Esta unidad no añade clasificación, puntuación ni retroalimentación educativa.

Confirmación posterior: el usuario obtuvo **530 passed in 26.55s** y guardó/leyó la sesión `d8964573-f78f-4fe6-802a-391e2e6913d7` con `closed`, `unchanged` y dos intentos `completed`. La revisión local confirmó el archivo. La siguiente unidad de medición se documenta en [diagnóstico de contexto](#diagnostico-contexto); las cifras de pruebas anteriores se conservan como evidencia histórica de la 7.3.

La unidad 7.4e amplía el contrato: las entrevistas con `--extractive-context` guardan formato 1.1.0, política y eventos de preparación separados de las preguntas. El lector continúa aceptando los archivos 1.0.0 sin migrarlos. Los detalles actuales están en [resumen en entrevista](#resumen-en-entrevista).

---

<a name="diagnostico-contexto"></a>

## Etapa 7.4a: diagnóstico del contexto registrado

Esta unidad permite revisar los tokens de entrada que el proveedor informó en una sesión ya guardada. Es la base de medición antes de integrar una política de reducción o resumen. El comando funciona sin consultar a Ollama o a una API y no escribe archivos. No cambia el controlador, la conversación enviada, el perfil, las instrucciones o el formato de sesión 1.0.0.

### Componentes y dependencias

| Archivo | Función |
| --- | --- |
| `harness/context_budget.py` | `ContextBudget` valida reservas y calcula el límite de entrada; `assess` compara una métrica; `build_context_report` reúne un informe sin copiar textos de la entrevista. |
| `scripts/inspect_context.py` | Lee una sesión mediante `load_session` y muestra su diagnóstico. Acepta capacidad, reserva de salida y margen explícitos. |
| `tests/unit/test_context_budget.py` | 25 casos de límites, valores desconocidos, entradas inválidas, reserva configurable, copias y protección de textos. |
| `tests/integration/test_context_inspection_flow.py` | Cuatro casos del recorrido archivo → validación → informe, sin red ni cambios de archivos. |

No se añaden dependencias. El módulo de cálculo usa la biblioteca estándar. El comando reutiliza el lector y validador de sesiones; obtiene sus valores predeterminados de capacidad y salida de `OllamaSettings`, sin crear un cliente, leer credenciales o cambiar ajustes del proveedor.

### Cálculo y significado

La política de comparación elegida para este proyecto es:

```text
Capacidad de comparación:       8192 tokens
Reserva máxima de salida:       512 tokens
Margen adicional de la política: 256 tokens
Límite de entrada: 8192 - 512 - 256 = 7424 tokens
Margen disponible = 7424 - entrada informada
```

Los 256 tokens son una reserva inicial configurable del proyecto, no un requisito del modelo ni una garantía estadística. Los parámetros se proporcionan al diagnóstico: el archivo 1.0.0 no conserva la capacidad o el máximo de salida solicitado. Por eso el informe no los presenta como metadatos históricos del archivo y no infiere la capacidad a partir del nombre del modelo. Cambiar `--context-size` cambia solo la comparación; no reconfigura Ollama.

La entrada registrada procede de `LLMResponse.input_tokens`. En el adaptador Ollama se obtiene de `prompt_eval_count`, documentado como el número de tokens del prompt. `prompt_eval_cached_count` indica tokens leídos de la caché: se conserva como métrica independiente y no se resta para calcular espacio libre. Fuentes primarias consultadas el 31 de octubre de 2026: [Chat API](https://docs.ollama.com/api/chat) y [Usage](https://docs.ollama.com/api/usage).

El resultado por intento es `within_budget` si queda margen positivo, `at_limit` si queda cero y `over_budget` si es negativo. Si no hubo respuesta o falta `input_tokens`, es `unknown` y el margen queda desconocido. Un cero informado se distingue de una métrica ausente. Se incluyen métricas de respuestas parciales o intentos fallidos que conserven una respuesta; no se inventan conteos para los demás.

Estos son estados de uso técnico; no clasifican preguntas ni evalúan su calidad. El informe conserva el estado original del intento, muestra su número y métricas, y excluye preguntas, respuestas, perfil interno e incidencias detalladas.

### Comprobar en PowerShell

Desde la raíz del proyecto, usando el archivo que el usuario acaba de verificar:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.inspect_context '.\outputs\sessions\session-d8964573-f78f-4fe6-802a-391e2e6913d7.json' --context-size 8192 --max-output-tokens 512 --safety-margin 256
```

Esperado: **559 passed**, 534 unitarias y 25 integraciones. El diagnóstico debe conservar el UUID `d8964573-f78f-4fe6-802a-391e2e6913d7`, mostrar límite de entrada 7424 y:

| Intento | Entrada informada | Margen con las reservas elegidas | Resultado |
| --- | --- | --- | --- |
| 1 | 6023 | 1401 | Dentro del presupuesto |
| 2 | 6097 | 1327 | Dentro del presupuesto |

Mayor entrada informada: 6097. Intentos sin métrica: cero. La ejecución del diagnóstico debe ser breve y no necesita Ollama abierto. No es necesario iniciar otra entrevista para esta unidad.

Si aparece «No se pudo revisar el contexto», comprobar la ruta del JSON y que las reservas dejen entrada positiva. Un archivo inválido se rechaza mediante el lector de sesiones. El programa devuelve código 1 sin modificarlo. No se debe editar la evidencia para que encaje en el presupuesto.

### Evidencia y límites

El usuario confirmó previamente la unidad 7.3: **530 passed in 26.55s**, sesión cerrada con dos respuestas completas, cero incidencias, fuente intacta y el mismo UUID al guardar y leer. Las respuestas dieron 21 meses calendario y nueve meses por cada jornada; latencias 63,13 y 13,22 s. La lectura local del archivo confirmó esos estados y sus métricas. Registro estructurado de la confirmación: [session-persistence-user-confirmation-93b7cab3eadb498d808facee10093926.json](../outputs/results/session-persistence-user-confirmation-93b7cab3eadb498d808facee10093926.json).

La suite de esta unidad pasó con **559 passed in 27.36s**, sin fallos ni solicitudes reales. Se añadieron 25 casos unitarios y cuatro integraciones. Las integraciones impiden llamadas HTTP y comparan los bytes de los archivos antes y después del diagnóstico.

El comando real leyó el archivo anterior y obtuvo los márgenes 1401 y 1327, con código 0. Los hashes de todos los archivos de sesiones y de perfil, puesto, configuración e instrucciones se conservaron. Evidencia: [context-budget-7bbc164655844b038dfe497a064d4101.json](../outputs/results/context-budget-7bbc164655844b038dfe497a064d4101.json). Esta evidencia adicional la escribe el verificador; el comando de diagnóstico solo lee e imprime.

El diagnóstico analiza llamadas pasadas. No cuenta exactamente los tokens de una pregunta futura, no demuestra que el servidor conservara todos los mensajes recibidos y no detecta por sí solo un recorte anterior. No usa equivalencias entre caracteres y tokens ni extrapola cuántas preguntas faltan. Veinte preguntas es el límite de envíos, no una garantía de capacidad del contexto.

La conservación automática de referencias y hechos durante un resumen, la elección del punto de reducción y su integración antes de enviar una pregunta siguen pendientes. Un resumen generado por otro LLM puede omitir o inventar hechos; habrá que conservar las fuentes originales y los registros completos por separado y validar su contenido antes de usarlo. Esta unidad deja comprobada la medición disponible y espera el resultado del usuario antes de continuar.

Confirmación posterior: el usuario obtuvo **559 passed in 25.70s** y los valores esperados del diagnóstico. Antes de resumir, la unidad 7.4b incorpora una [protección frente al recorte de contexto](#proteccion-contexto), verificada con Ollama 0.34.2. Las mediciones y cifras de la 7.4a se conservan como evidencia histórica.

---

<a name="proteccion-contexto"></a>

## Etapa 7.4b: rechazo explícito antes de perder contexto

La unidad anterior midió llamadas pasadas. Antes de integrar una reducción del historial, se añadió una protección que solicita a Ollama rechazar una entrada que no quepa, sin recortar mensajes para continuar. El registro completo se conserva, el intento rechazado cuenta y el usuario puede acortar la pregunta o finalizar para guardar.

Esta unidad usa los controles `truncate: false` y `shift: false` de la solicitud `/api/chat`, fuera del objeto `options`. No aumenta la capacidad configurada ni resume la conversación. Se verificó el servicio local **Ollama 0.34.2** y el modelo instalado **gemma4:e4b**.

### Archivos y dependencias

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

### Decisión y fuentes

Ollama 0.34.2 incluye ambos controles en `ChatRequest`. `truncate` gobierna el recorte de mensajes del prompt y `shift` el desplazamiento al llegar al límite durante la generación. Fuentes primarias consultadas el 31 de octubre de 2026: [tipos de la API 0.34.2](https://github.com/ollama/ollama/blob/v0.34.2/api/types.go), [preparación de mensajes](https://github.com/ollama/ollama/blob/v0.34.2/server/prompt.go) y [rutas de chat](https://github.com/ollama/ollama/blob/v0.34.2/server/routes.go).

Una prueba directa del servidor instalado envió texto sintético, con capacidad 8192 y ambos controles desactivados. Respondió HTTP 400: el motor informó una solicitud de **16 009 tokens** superior a la capacidad. El error venía como JSON codificado dentro del campo `error`, con tipo `exceed_context_size_error`. La prueba tardó **28,03 s**, sin métricas por fase que permitan atribuir una causa.

El adaptador reconoce ese tipo, su forma de objeto directo y mensajes exactos conocidos de longitud excedida. Procesa como máximo una envoltura JSON del campo `error`. Otros rechazos conservan su error genérico; no considera que cualquier HTTP 400 sea un exceso de contexto. El error público y el registro utilizan texto fijo, sin copiar mensajes arbitrarios, credenciales o cuerpos HTTP.

No se reenvía automáticamente una solicitud rechazada, no se recorta el historial local ni se cambia `num_ctx`. La falta de espacio durante una generación también puede producir una respuesta cortada o un error: continúan aplicándose los controles existentes que impiden aceptar texto incompleto como respuesta válida.

### Comprobar en PowerShell

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

### Evidencia

El usuario confirmó la 7.4a con **559 passed in 25.70s** y el diagnóstico de su sesión: entradas 6023/6097, límite 7424, márgenes 1401/1327 y cero métricas ausentes. Se conservó un registro estructurado en [context-diagnostic-user-confirmation-e12379075fb240f7bbbc28ee0aa30ce6.json](../outputs/results/context-diagnostic-user-confirmation-e12379075fb240f7bbbc28ee0aa30ce6.json), que distingue su resultado comunicado de la lectura local del archivo.

La suite final pasó con **577 passed in 26.48s**, sin fallos. Se añadieron 17 casos unitarios y una integración. La integración comprueba que el siguiente envío conserva el primer par completo y excluye la pregunta rechazada, que el sistema se mantiene idéntico y que el registro completo con `context_limit` se guarda y vuelve a cargar correctamente.

La comprobación real usó el punto de entrada de la aplicación: pregunta sobre el aporte a Inventario Aula, entrada sintética extensa y repregunta por el nombre del proyecto. Hubo tres llamadas HTTP, con 2, 4 y 4 mensajes respectivamente. Todas enviaron `truncate: false`, `shift: false`, capacidad 8192 y salida máxima 512. El mensaje de sistema conservó el mismo hash. La repregunta respondió «Inventario Aula»; las dos respuestas completas tardaron **40,80 s** y **5,25 s**. No hubo respuesta inventada ni conteos de tokens para el intento rechazado.

La aplicación creó [session-5705ca05-8c5c-4251-9c34-d9883224391a.json](../outputs/sessions/session-5705ca05-8c5c-4251-9c34-d9883224391a.json), con estados `completed`, `error`, `completed`, fuente sin cambios y cierre por salida del usuario. `load_session` recuperó exactamente el registro del controlador. La evidencia adicional del verificador está en [context-guard-9283a64ac59d4d41bad389f904d650a4.json](../outputs/results/context-guard-9283a64ac59d4d41bad389f904d650a4.json). Los archivos anteriores de sesiones y los cuatro originales del escenario se conservaron.

### Alcance pendiente

Esta protección se verificó con el servicio y modelo indicados; no garantiza el comportamiento de otras versiones o motores. Los controles solicitan el rechazo al servidor y no sustituyen un conteo previo exacto. Las métricas de la 7.4a siguen siendo retrospectivas y el margen adicional 256 continúa siendo una política de comparación.

El resumen controlado y su integración siguen pendientes. Primero se comprueba que el exceso queda registrado sin perder datos; después se podrá probar cómo recuperar espacio manteniendo hechos y referencias. Se espera el resultado del usuario antes de continuar con otra unidad. No se han añadido clasificación de preguntas, puntuación, base de datos o nuevas dependencias.

Confirmación posterior: el usuario obtuvo **577 passed in 28.46s** y la sesión `f7be73ff-ab02-42d4-8f63-17d78db4aeb0` con los estados y el código esperados. La repregunta recordó Inventario Aula. El siguiente componente, todavía separado del controlador, se documenta en [propuesta extractiva verificable](#resumen-extractivo).

---

<a name="resumen-extractivo"></a>

## Etapa 7.4c: propuesta de resumen extractivo verificable

Esta unidad construye y muestra una propuesta para revisar turnos antiguos de una sesión guardada. Conserva preguntas completas, citas literales y los últimos pares completos de conversación. El perfil, la configuración y el registro original permanecen separados. Todavía no se sustituye el historial enviado al candidato.

### Componentes y dependencias

| Archivo | Responsabilidad |
| --- | --- |
| `harness/history_summary.py` | Preparar fuentes, solicitar índices al selector, copiar citas, conservar anclas y verificar la propuesta reconstruyéndola desde el original. |
| `scripts/preview_summary.py` | Leer una sesión validada, mostrar proveedor/modelo y generar una vista previa para revisión. No escribe archivos ni reanuda entrevistas. |
| `tests/unit/test_history_summary.py` | 51 casos de selección, citas, metadatos, cambios, tipos, ventanas recientes, integridad, errores y conservación de anclas. |
| `tests/integration/test_summary_preview_flow.py` | Cuatro casos de lectura → adaptador → selección → vista previa, con HTTP simulado y archivos temporales. |

No se añaden dependencias ni se cambia el contrato `LLMClient.generate`. Se reutilizan el lector de sesiones y el cliente seleccionado por la fábrica. La alternativa externa conserva su activación explícita; las comprobaciones reales de esta unidad utilizaron Ollama y `gemma4:e4b`, con API externa desactivada.

### Cómo se prepara la propuesta

1. Se recibe una sesión validada por `load_session`, con integridad registrada `unchanged`. Se obtienen únicamente intentos `completed`, conservando sus números originales. Los intentos fallidos permanecen en el archivo, pero no se envían al selector como conversación válida.
2. `keep_recent_pairs` determina cuántos pares completos recientes se mantienen. El valor predeterminado es dos; admite de uno a veinte. Si no hay turnos antiguos, no se crea un cliente ni se consulta un modelo.
3. Las respuestas antiguas se separan en fragmentos por puntuación seguida de espacio o saltos de línea. Es segmentación textual, no análisis lingüístico completo. Cada pregunta antigua se conserva íntegra.
4. El selector recibe solamente preguntas antiguas y fragmentos numerados, como datos en un mensaje `user`, con reglas separadas en `system`. No recibe el perfil interno, el puesto, credenciales, instrucciones del candidato, intentos fallidos o los turnos recientes.
5. El modelo debe devolver un JSON con números de pregunta y listas crecientes de índices. Python rechaza texto libre, campos adicionales, claves repetidas, turnos ausentes, cambios de orden, índices inexistentes o repetidos y selecciones cortadas. No reintenta una selección fallida por su cuenta.
6. Python añade anclas conservadoras aunque el selector las omita: primero y último fragmento; fragmentos con cifras, ciertas negaciones o límites; y palabras con mayúscula después de la primera palabra, como indicio de nombres. Estas reglas pueden conservar contenido adicional y no identifican toda la relevancia semántica.
7. Se copian las citas originales por sus índices. La propuesta indica fragmentos omitidos y fragmentos añadidos por la protección. Conserva configuración, candidato/puesto, hashes de perfil e instrucciones, huella del historial aceptado y huella de cada respuesta antigua.
8. `validate_summary` reconstruye la propuesta desde la sesión y compara su representación canónica. Detecta cambios de citas, preguntas, números, configuración, turnos recientes, estadísticas y campos adicionales. Una modificación posterior de la conversación fuente invalida la propuesta anterior.

El resultado lleva `summary_version: 1.0.0` y `review_status: not_reviewed`. No es un archivo de sesión nuevo ni una actualización de los antecedentes. El comando solo imprime; las propuestas incluidas en la evidencia técnica fueron guardadas por el verificador externo.

### Por qué usar citas y revisar omisiones

La generación libre de resúmenes puede introducir contenido no respaldado por la fuente; este riesgo está documentado en [Maynez et al., ACL 2020](https://aclanthology.org/2020.acl-main.173/). Esta implementación limita la salida del modelo a índices y copia las palabras desde el registro original.

La verificación demuestra procedencia, no verdad. Una respuesta anterior del candidato puede contener un error. Además, una selección literal puede cambiar el sentido al omitir contexto, y las reglas léxicas no garantizan que conserven todos los hechos importantes. Por eso se muestra como propuesta para revisión y todavía no se aplica al controlador. El perfil seguirá teniendo prioridad cuando se integre.

Las estadísticas cuentan caracteres de fragmentos, sin sus separadores. No miden tokens ni el ahorro total del futuro mensaje, que también necesitará preguntas, referencias y marcadores. Es válido conservar todos los fragmentos cuando la respuesta es breve o contiene hechos necesarios. No se fuerza una reducción porcentual.

### Comprobación en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.preview_summary '.\outputs\sessions\session-f7be73ff-ab02-42d4-8f63-17d78db4aeb0.json' --keep-recent-pairs 1
```

Esperado: **632 passed**, 602 unitarias y treinta integraciones. La vista previa debe mostrar:

- Sesión de origen `f7be73ff-ab02-42d4-8f63-17d78db4aeb0` y propuesta pendiente de revisión.
- Pregunta antigua **1**, con las dos citas sobre Inventario Aula y sus tecnologías. Ambas quedan protegidas por ser los extremos de esa respuesta.
- Pregunta reciente **3**, con su pregunta y respuesta completas.
- Dos fragmentos antiguos conservados, cero omitidos y **233 → 233** caracteres de fragmentos. No hace falta omitir contenido en esta respuesta breve.
- Confirmación de procedencia y citas verificadas contra la fuente.

No debe aparecer la larga entrada sintética del intento 2. Sus datos siguen en el archivo original. Tampoco se espera un nuevo archivo de sesión después de ejecutar la vista previa.

Con el valor predeterminado de dos pares recientes, esta sesión no tendría turnos antiguos: se mostrarían ambos completos sin consultar al modelo. El argumento uno permite ejercitar el selector en una entrevista corta sin inventar turnos nuevos.

Si falla la conexión, comprobar Ollama y el modelo. Si aparece un error de selección inválida o cortada, conservar la salida: no se acepta una propuesta parcial ni se modifica la fuente. La selección extensa también puede superar el contexto del modelo y ser rechazada por la protección de la 7.4b; aún no hay procesamiento por lotes o resumen jerárquico. Las instrucciones de la entrevista no necesitan cambios para esta prueba.

### Evidencia de desarrollo

El usuario confirmó la 7.4b con **577 passed in 28.46s**, dos respuestas completas y un rechazo por contexto, con estados `completed`, `error`, `completed` y código `context_limit`. La repregunta recordó Inventario Aula; las respuestas tardaron 64,76 y 3,47 s. La lectura local confirmó la sesión, la integridad y el archivo. Se registró en [context-guard-user-confirmation-1d88e6bfc79c41609280cc0042c7c521.json](../outputs/results/context-guard-user-confirmation-1d88e6bfc79c41609280cc0042c7c521.json).

Pasaron primero 48 casos nuevos. Tras añadir una comprobación de tipos en la revalidación, la suite de 626 casos pasó en 50,41 s. La comprobación real posterior detectó un problema: el selector omite anclas aunque el prompt pida conservarlas. La primera verificación se detuvo por incumplir el contrato del primer fragmento; una repetición capturó la respuesta en [summary-selector-preliminary-bebf1172639f49398fecefc0e529c018.json](../outputs/results/summary-selector-preliminary-bebf1172639f49398fecefc0e529c018.json). En esa fixture seleccionó `[1,4]` y `[2]`, omitiendo contexto sobre ausencia de clientes y administración de producción. No se aplicó la propuesta a una entrevista.

La corrección pasó la conservación de anclas a Python, mantuvo el rechazo de índices inexistentes y añadió regresiones. El selector puede proponer índices válidos sin todos los obligatorios: la aplicación repone las citas protegidas y lo indica. La respuesta preliminar guardada se reprodujo bajo la política final y se validó contra sus fuentes. No se depende solo de otra promesa en el prompt.

Los 55 casos nuevos finales pasaron en 6,04 s. La suite conjunta final terminó con **632 passed in 49.16s**, 602 unitarias y treinta integraciones. Son 51 casos unitarios y cuatro integraciones nuevos. Pytest utiliza proveedores simulados; las consultas reales se hicieron en una verificación externa separada.

La revisión final real realizó dos llamadas locales al selector:

- **Sesión real del usuario:** mantuvo sus dos fragmentos antiguos, con 233 → 233 caracteres y cero omisiones; conservó completa la pregunta 3. Selección en **6,37 s**.
- **Fixture explícita de cuatro turnos:** respuestas predefinidas con frases de relleno, no una entrevista natural nueva. Seleccionó `[1,2,4]` en cada una de las dos respuestas antiguas: ocho fragmentos pasaron a seis, 354 → 240 caracteres. Se omitieron únicamente las dos frases de relleno de esa muestra y se conservaron proyectos, tecnologías, ausencia de clientes y límite de producción; los dos turnos recientes quedaron completos. Selección en **11,50 s**. Esta muestra no demuestra que toda omisión futura sea irrelevante.

Evidencia final: [extractive-summary-15bb185e26174f998e069279cc7c8713.json](../outputs/results/extractive-summary-15bb185e26174f998e069279cc7c8713.json). Incluye solicitudes resumidas, salidas del selector, propuestas, vistas previas, reproducción de la selección preliminar y comparación de hashes. Todos los archivos de sesiones anteriores y los cuatro originales del escenario conservaron sus bytes. API externa desactivada, instrucciones 1.0.11 y referencia 2026-10-20 conservadas.

La integración del resumen en una entrevista activa, su presupuesto completo, marcadores de datos y política de activación siguen pendientes. Se espera la comprobación del usuario de esta unidad antes de continuar.

Confirmación posterior: el usuario obtuvo **632 passed in 30.47s** y la vista previa esperada, con citas 1/2 y pregunta reciente 3 completas, sin omisiones. La unidad 7.4d prepara el [contexto con resumen y una consulta aislada](#contexto-con-resumen); la activación en una entrevista sigue siendo otro paso.

---

<a name="contexto-con-resumen"></a>

## Etapa 7.4d: composición del contexto y consulta aislada

Esta unidad reúne el escenario autorizado, las citas antiguas verificadas, los turnos recientes completos y una pregunta de comprobación. Elige la versión con extractos solo si reduce el JSON completo de mensajes. La comparación incluye las marcas y las reglas adicionales, no solo los caracteres de las citas.

La consulta es una prueba aislada sobre una sesión archivada. No reabre esa entrevista, no añade intentos a su registro y no cambia sus contadores. La consola principal continúa usando su controlador actual; la política de activación durante una entrevista sigue pendiente.

### Archivos y funciones

| Archivo | Responsabilidad |
| --- | --- |
| `harness/summary_context.py` | `prepare_summary_context`: revalidar citas, vincular fuentes al escenario, preparar las dos versiones y elegir mensajes junto con un diagnóstico. |
| `scripts/probe_summary_context.py` | Cargar el archivo y el escenario, preparar una propuesta, consultar al candidato y comprobar la integridad del perfil. Solo imprime el resultado. |
| `tests/unit/test_summary_context.py` | 16 casos de composición, vínculos, roles, copias, preguntas inválidas, conservación del sistema y elección según bytes. |
| `tests/integration/test_summary_context_probe_flow.py` | Seis casos con archivo y componentes reales, HTTP simulado y protección de la fuente ante errores o interrupción. |

Se reutilizan `build_messages`, `validate_summary`, `load_session` y la fábrica de clientes. No se añaden dependencias ni se cambian perfil, configuración, puesto, instrucciones del candidato, adaptadores, controlador o esquema de sesión.

### Qué comprueba la preparación

La propuesta se reconstruye desde la sesión antes de cada preparación. Después se comprueban identificador y hash del candidato, referencia del puesto, configuración completa y hash del texto de instrucciones frente a `InterviewSetup` y las instrucciones actuales. Si no coinciden, se rechaza la composición. El archivo 1.0.0 registra la referencia del puesto, no una huella histórica de su descripción; no se afirma verificar un dato que no contiene.

El contexto base se obtiene del constructor existente. El perfil, puesto, configuración y referencias derivadas siguen dentro del mismo mensaje de sistema. Los textos de la conversación no se copian al sistema como reglas nuevas.

Cada pregunta antigua conserva su mensaje `user` exacto. Si su respuesta tiene omisiones, conserva su papel `assistant` y lleva una marca de extracto con el número original. Las citas mantienen su orden y se señala `[…]` entre fragmentos no consecutivos. Si no hay omisiones en esa respuesta, se recupera el texto original completo, incluidos sus espacios. Los pares recientes y la pregunta actual quedan intactos.

Ambas alternativas añaden una guía estática para distinguir orden de mención en la conversación y cronología de los proyectos. La alternativa con extractos añade además otra guía para sus marcas, el carácter histórico de las citas y la prioridad del perfil. Estas guías no incluyen valores procedentes del entrevistador o del selector. Los intentos fallidos siguen excluidos de la conversación enviada y permanecen en el registro completo.

Se comparan los bytes UTF-8 de ambas listas de mensajes serializadas de la misma forma. Si hay omisiones y la alternativa es estrictamente menor, se elige `extractive_summary`. De lo contrario, se elige `full_history`, con motivo `no_omissions` o `no_byte_savings`. La decisión no modifica la propuesta, el registro o el escenario.

La medición corresponde a mensajes generales antes de adaptar el modelo. No equivale a tokens, no incluye el cuerpo completo del transporte y no garantiza que la solicitud quepa. Los controles `truncate: false` y `shift: false` del adaptador local continúan solicitando rechazo ante exceso. No se implementan reenvíos automáticos tras un rechazo.

### Comprobar en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.probe_summary_context '.\outputs\sessions\session-f7be73ff-ab02-42d4-8f63-17d78db4aeb0.json' --keep-recent-pairs 1 --question '¿Cómo se llamaba el proyecto académico que mencionaste antes?'
```

Esperado: **654 passed**, 618 unitarias y 36 integraciones. En esta sesión corta, los dos fragmentos antiguos están conservados; por eso debe elegir **historial completo**, con motivo `no_omissions` y el mismo número de bytes antes y después. La respuesta de comprobación debe identificar **Inventario Aula**, sin exigir una frase idéntica entre ejecuciones.

El comando puede realizar una selección y una consulta al candidato. Si todos los pares se conservan como recientes, solo consulta al candidato. La alternativa externa conserva su activación explícita, pero las variables anteriores seleccionan únicamente Ollama local.

La salida debe terminar indicando que la sesión fuente y sus contadores permanecen sin cambios. No debe generar un archivo nuevo de sesión. Esta prueba no necesita abrir la consola interactiva ni introducir `/iniciar`.

Si aparece un error de coincidencia de fuentes, conservar el mensaje: la sesión y el escenario actual no deben mezclarse modificando sus hashes. Si aparece una selección inválida, una respuesta cortada o un error del proveedor, no se presenta una respuesta de comprobación válida. Se mantienen intactos los archivos y se cierran los recursos del cliente. Ante un error de conexión, comprobar Ollama y el modelo indicado.

### Evidencia y límites

El usuario confirmó la 7.4c con **632 passed in 30.47s**. La propuesta conservó pregunta 1, sus dos citas y la pregunta reciente 3 completa: 233 → 233 caracteres, cero omisiones y procedencia verificada. Se registró en [extractive-summary-user-confirmation-052ae0d7f51c44a1a21a26697ab3d166.json](../outputs/results/extractive-summary-user-confirmation-052ae0d7f51c44a1a21a26697ab3d166.json), distinguiendo el resultado comunicado de la lectura local de la fuente.

Los 22 casos nuevos pasaron en **2,97 s**. La primera suite conjunta terminó con **654 passed in 33.72s**; después de la guía de referencias, la suite final terminó con **654 passed in 34.08s**, 618 unitarias y 36 integraciones, sin fallos. Pytest utiliza proveedores simulados. Las pruebas verifican composición reducida y conservación del historial completo, rechazo de fuentes incompatibles, papeles de conversación, copia independiente, manejo de fallos y archivos sin cambios.

El resumen mantiene su estado `not_reviewed`. Esta unidad comprueba su composición y una consulta de prueba; no certifica que todas las omisiones sean irrelevantes. Las reglas de anclas son conservadoras y las citas pueden contener errores previos del modelo. La integración en una entrevista activa deberá conservar el registro completo y documentar su política de activación y presupuesto.

Durante una prueba real previa, la variante de historial completo respondió por fechas de inicio a una pregunta sobre el primer proyecto mencionado. No se llegó a consultar la alternativa con extractos en esa ejecución. Se registró la discrepancia, sin inventar métricas perdidas, en [summary-context-mention-incident-cb4c3ab00b03407597009c09e7a3e76d.json](../outputs/results/summary-context-mention-incident-cb4c3ab00b03407597009c09e7a3e76d.json). Se añadió la guía de referencias a ambas variantes del constructor de esta unidad. El archivo de instrucciones y los archivos anteriores permanecieron intactos. La consola principal todavía no incorpora este constructor.

La comprobación final real con Ollama y `gemma4:e4b` pasó:

| Caso | Resultado observado |
| --- | --- |
| Archivo real del usuario | Historial completo por `no_omissions`, 27 496 → 27 496 bytes de mensajes; identificó Inventario Aula. Respuesta en 5,39 s. |
| Fixture con historial completo | Identificó Inventario Aula como primer proyecto mencionado y pytest como herramienta de la última respuesta; entrada 6620 tokens, respuesta en 6,69 s. |
| La misma fixture con extractos | Mantuvo esas dos referencias; entrada 6364 tokens, respuesta en 7,94 s. |
| Regresión de fechas con extractos | Indicó MesaFaro como primer proyecto por inicio, en abril de 2025; entrada 6360 tokens, respuesta en 5,08 s. |

La fixture contiene respuestas y selección predefinidas, con frases de relleno introducidas para ejercitar el ahorro. No es una entrevista natural nueva y no se archivó como sesión de la aplicación. En ella, los mensajes pasaron de **30 167 a 28 133 bytes**, ahorro de 2034 bytes. La reducción observada de 256 tokens corresponde solo a las dos consultas comparables de esta muestra; los tiempos no demuestran una mejora de latencia.

La evidencia está en [summary-context-b67d45e6960a4b9dbcb53f51df027355.json](../outputs/results/summary-context-b67d45e6960a4b9dbcb53f51df027355.json). Distingue la consulta sobre el archivo real de las pruebas con fixture y conserva las respuestas completas, métricas, decisiones y hashes. No copia el perfil interno del mensaje de sistema. Todos los archivos de sesiones previos y los cuatro originales del escenario conservaron sus bytes. La API externa permaneció desactivada.

Las referencias y fechas observadas pasaron para estos casos. No se considera resuelta universalmente la interpretación del historial ni se valida automáticamente la calidad semántica de todas las respuestas. La guía nueva afecta a este constructor de prueba; su integración en el controlador principal y la activación durante entrevistas siguen pendientes. Se espera la comprobación del usuario antes de otra unidad.

Confirmación posterior: el usuario obtuvo **654 passed in 35.88s** y la consulta esperada, con Inventario Aula, historial completo y archivo intacto. La unidad 7.4e incorpora la [opción de resumen en el controlador](#resumen-en-entrevista), conservando la modalidad anterior sin la opción.

---

<a name="resumen-en-entrevista"></a>

## Etapa 7.4e: resumen activable en el controlador

La consola permite activar la política con `--extractive-context`. El controlador prepara el contexto de cada pregunta y registra las operaciones de resumen por separado. El historial completo y los antecedentes originales se conservan. Sin esa opción, se mantiene el comportamiento anterior y el formato de sesión 1.0.0.

### Archivos y responsabilidades

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

### Política de activación

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

### Contadores y errores

Una selección de memoria no consume una pregunta. La pregunta del entrevistador empieza a contar cuando se registra su intento de envío al candidato, después de preparar el contexto. Se conserva el máximo configurado de veinte preguntas enviadas y el cierre anticipado.

Si la selección devuelve JSON inválido, índices incorrectos, texto cortado o un error conocido del proveedor, se registra una incidencia y se intenta una sola generación del candidato con el historial completo. El error del selector no se añade como respuesta al historial. Si el contexto completo también es rechazado, el intento del candidato queda fallido y cuenta una vez. No se repite automáticamente esa generación.

`Ctrl+C` durante la selección interrumpe la preparación: no se inventa un intento del candidato. La consola cierra y guarda el registro disponible. Un cambio del perfil durante la selección cierra por integridad y evita enviar la pregunta. Cuando coinciden error del selector y alteración del perfil, se conservan ambas incidencias sin copiar sus mensajes arbitrarios.

El tiempo de generación del candidato y el tiempo adicional de preparación de memoria se muestran por separado cuando hubo selección. Los errores también conservan el tiempo de preparación medido, aunque no haya métricas del proveedor. Una métrica ausente permanece desconocida; no se inventan tokens para llamadas fallidas.

### Archivo de sesión 1.1.0

Con la opción activa se añaden `context_policy` y `context_events`. La política queda fija desde el inicio. Cada evento tiene número, fecha UTC, pregunta que se iba a enviar y `candidate_sent`. Registra motivo de activación, resultado del selector, tiempo de preparación, índices aceptados cuando existen, métricas disponibles, decisión de contexto, bytes y hashes. No copia el perfil interno del sistema ni la respuesta libre de un selector inválido.

Los índices y las citas se pueden reconstruir desde el prefijo del historial completo que existía en ese momento. El lector comprueba orden de eventos, cobertura de preguntas enviadas, política, índices, huella del historial y coherencia aritmética de las medidas. Las fechas siguen usando UTC real; la referencia ficticia permanece en 2026-10-20. El reloj no tiene que ser monótono para validar el orden: lo determinan los números de eventos y preguntas.

`messages_sha256` identifica el JSON general de los mensajes antes de adaptar el modelo. No es una firma de autenticidad del archivo ni un conteo de tokens. La versión 1.0.0 continúa siendo legible y no admite los campos nuevos. Los archivos de sesiones anteriores no se migran o sobrescriben.

### Comprobar en PowerShell

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

### Verificación y límites

El usuario confirmó la unidad 7.4d con **654 passed in 35.88s**, contexto completo por `no_omissions`, 27496 → 27496 bytes y respuesta correcta sobre Inventario Aula en 33,44 s. Se registró en [summary-context-user-confirmation-97b2934e7b5f431e8ed11e68f7b3aa8e.json](../outputs/results/summary-context-user-confirmation-97b2934e7b5f431e8ed11e68f7b3aa8e.json), distinguiendo el resultado comunicado de la lectura local.

La suite previa de compatibilidad pasó con **654 passed in 106.64s**. Los 35 casos nuevos iniciales pasaron en 14,24 s; después se añadió la comprobación del tiempo de preparación. Los 36 casos finales pasaron en **14,86 s**. La suite conjunta terminó con **690 passed in 104.14s**, 650 unitarias y cuarenta integraciones, sin fallos ni llamadas reales dentro de pytest. No se atribuye la variación de duración a una causa sin medirla.

El resumen automático conserva `not_reviewed`: se comprueba procedencia y estructura, no la relevancia de todas las omisiones ni la verdad de las afirmaciones históricas. La opción queda explícita para esta unidad. La protección, los registros originales y la revisión humana de preguntas de referencia continúan siendo necesarios. No se garantiza que cualquier entrevista de veinte turnos quepa en la capacidad indicada.

La entrevista real de cuatro preguntas con Ollama y `gemma4:e4b` terminó con cuatro respuestas completas, cero incidencias y una selección antes de la cuarta pregunta. Conservó Inventario Aula, sus tecnologías y el total de 21 meses. Las respuestas tardaron **117,53; 11,85; 13,28 y 4,98 s**. La preparación final conservó el historial completo por ausencia de omisiones; no se fuerza una reducción en respuestas breves.

La aplicación guardó [session-a5ad4e7c-aeb1-4906-8f41-7d113be13001.json](../outputs/sessions/session-a5ad4e7c-aeb1-4906-8f41-7d113be13001.json), formato **1.1.0**, con cuatro eventos y el patrón de selectores esperado. La lectura validada coincidió exactamente con la instantánea final del controlador. Para Gemma 4 se contrastaron también las huellas de las listas de mensajes realmente enviadas con las registradas en la auditoría.

Un segundo caso preparó tres respuestas y conteos de entrada simulados para ejercitar el ahorro de forma controlada; la selección y la cuarta respuesta sí fueron llamadas reales a Ollama. No se presenta como una entrevista natural. El controlador eligió `extractive_summary`, ahorró **999 bytes de mensajes** y la respuesta mantuvo Inventario Aula y pytest. Su lectura/escritura se comprobó en un directorio temporal, no en la carpeta de entrevistas naturales. No se compara el conteo simulado con los tokens reales para afirmar un ahorro de tokens.

La evidencia adicional está en [live-context-ea4988d6741a40f9be580eb8c7ba4fd2.json](../outputs/results/live-context-ea4988d6741a40f9be580eb8c7ba4fd2.json). Distingue ambos casos, conserva los registros completos y los hashes de las solicitudes, y compara los cuatro originales y todas las sesiones anteriores antes y después. No se atribuye la latencia a una causa sin una comprobación específica ni se promete una mejora de velocidad. La API externa permaneció desactivada.

La funcionalidad queda implementada y comprobada para estos casos. Se espera la ejecución del usuario de esta unidad antes de continuar con nuevas pruebas o cambios de política.

Confirmación posterior: el usuario obtuvo **690 passed in 38.14s**, cuatro respuestas completas, una selección de memoria, cero resúmenes usados y archivo 1.1.0 con cuatro eventos. La lectura local confirmó la sesión `f8d281c9-bca7-4bdd-9b52-d7f9788399e5`. El [cierre funcional de la Etapa 7](#cierre-etapa-7) resume el alcance, los límites y la propuesta de transición; no se ha iniciado automáticamente la Etapa 8.
