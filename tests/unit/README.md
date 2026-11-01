# Pruebas unitarias

## Validación final de la Etapa 9

La suite conjunta terminó con **738 passed in 45.54s**: 687 pruebas unitarias y 51 integraciones. HTTP está simulado o bloqueado en pytest. La entrevista real de veinte preguntas y sus archivos se verificaron por separado; véase la [validación final](../../docs/validacion-final.md).

## Etapa 8.1: referencias y fuentes

[test_reference_cases.py](test_reference_cases.py) añade 37 casos: resolución de hechos reales, valores nulos, copias, huella de los bytes, esquema, vínculos con candidato/puesto/fecha, identificadores, pasos, límite por caso, rutas explícitas, JSON inválido y archivos ausentes. No modifica los originales ni consulta a un modelo. Con las tres integraciones nuevas, **40 passed in 3.69s**; suite completa **730 passed in 45.44s**, 687 unitarias y 43 integraciones. La [guía](../../docs/pruebas/referencias-consistencia.md) distingue preparar casos de revisar respuestas.

La primera unidad implementada es [test_schema_validator.py](test_schema_validator.py), para el módulo común [schema_validator.py](../../harness/schema_validator.py). Usa `pytest`, `jsonschema` y los archivos aprobados del candidato y el puesto. Todas las comprobaciones se ejecutan localmente, sin consultas a un LLM.

La segunda unidad es [test_json_loader.py](test_json_loader.py), con 32 pruebas del lector compartido. [test_profile.py](test_profile.py) contiene 40 de coherencia; [test_profile_snapshot.py](test_profile_snapshot.py), 18 de protección; [test_public_resume.py](test_public_resume.py), 19 del CV; [test_interview_config_schema.py](test_interview_config_schema.py), 40 del contrato; [test_interview_config.py](test_interview_config.py), 21 del escenario, y [test_prompt_builder.py](test_prompt_builder.py), 27 del contexto. Junto con los 22 casos iniciales del validador, el conjunto tiene **219 pruebas unitarias**. Las siete de integración están en [tests/integration](../integration/README.md).

## Contrato del módulo

`validate_data(data, schema)` recibe datos y un esquema ya cargados en memoria. Devuelve `None` si la estructura es válida; ante el primer error de datos lanza `DataValidationError`, con las propiedades `path` y `rule`. Si el esquema contiene una regla inválida, lanza `InvalidSchemaError`.

Los mensajes están en español e indican la raíz o una ruta JSON Pointer, por ejemplo `/education/0/start_month`. El texto de la excepción no incluye el valor rechazado ni un volcado completo del perfil. El módulo no lee ni escribe archivos, no agrega valores predeterminados y no modifica sus entradas.

## Ejecución

En PowerShell, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
.\.venv\Scripts\python.exe -m pytest tests\unit\test_schema_validator.py -q
```

Se requieren las versiones instaladas desde `requirements.txt`. La ejecución del 30 de octubre de 2026 terminó con **22 passed in 0.99s**, usando el entorno de Python 3.14.3, `jsonschema` 4.26.0 y `pytest` 9.2.0. El tiempo puede variar al repetirla.

## Cobertura de esta unidad

- Aceptación del candidato y el puesto aprobados, sin modificar datos ni esquemas en memoria.
- Rechazo de datos sin identificador obligatorio, conservando también las entradas inválidas.
- Conservación de los archivos de origen durante la validación.
- Distinción entre reglas de esquema inválidas y datos inválidos.
- Tipos de raíz incorrectos, campos anidados ausentes, formatos de mes incorrectos y duplicados exactos en listas.
- Proyectos que no cumplen la alternativa estructural correspondiente.
- Rutas con índices de listas y caracteres especiales.
- Mensajes sin valores rechazados ni contenidos completos de proyectos o perfiles.
- Ausencia de incorporación automática de valores por defecto.
- Dos casos que confirman límites: una referencia inexistente y un día imposible conservan una estructura admitida por el esquema.

Estos dos últimos ejemplos no se consideran datos de candidato semánticamente válidos. El módulo de estructura mantiene esa responsabilidad limitada; `validate_profile_data` de [profile.py](../../harness/profile.py) añade las comprobaciones de calendario, cronología, referencias y unicidad de identificadores entre registros. La lectura genérica está implementada en `json_loader.py`, y `load_profile` crea una instantánea protegida del candidato. `to_public_resume` genera su currículum público. No hay pruebas de una entrevista ni del modelo todavía.

Si PowerShell no encuentra el ejecutable o el archivo de pruebas, comprobar primero la carpeta actual. Si aparece `No module named pytest` o `No module named jsonschema`, usar el Python de `.venv` y revisar la [guía del entorno](../../docs/entorno-python.md). Ante un fallo de prueba, conservar la salida completa para corregir la causa antes de cambiar dependencias o antecedentes.

## Lector JSON compartido

`load_json(path)` recibe una ruta de texto o `Path` y devuelve el valor de Python contenido en el archivo. Utiliza UTF-8 estricto, admitiendo también la marca BOM de UTF-8. No convierte archivos de otras codificaciones ni modifica sus bytes. Admite las raíces válidas de JSON; es el esquema el que determina si un documento concreto debe ser un objeto.

Cada lectura devuelve datos independientes. Se rechazan claves repetidas, incluso en objetos anidados, para evitar sobrescrituras silenciosas. También se rechazan constantes numéricas no admitidas por JSON (`NaN`, `Infinity` y `-Infinity`) y decimales que desborden a infinito en Python.

Ante problemas de lectura o interpretación se genera `JsonLoadError`, con la propiedad `path` y un mensaje en español. Los errores de sintaxis incluyen línea y columna. Los permisos y errores de dispositivo se simulan en las pruebas unitarias, sin cambiar permisos reales. El caso de recursión simula un `RecursionError` del decodificador; no establece un límite fijo de profundidad para el archivo.

Las 30 pruebas iniciales cubren codificación, tipos de raíz, rutas, archivos ausentes, directorios, errores de lectura, sintaxis, claves repetidas, números no admitidos, recursión del decodificador, independencia entre lecturas y conservación del archivo. Al incorporar la carga protegida se añadieron dos casos de `load_json_with_bytes(path)`: conservación exacta de BOM y saltos de línea Windows, y procedencia de los datos y bytes de una misma lectura. El lector tiene ahora 32 pruebas y sigue usando únicamente la biblioteca estándar de Python; sus pruebas requieren `pytest`.

`load_json` conserva su contrato. Internamente delega en `load_json_with_bytes`, que devuelve `(datos, bytes_originales)`. Para ello se cambió la lectura interna de texto a bytes y luego se decodifica el mismo contenido como UTF-8. Se actualizaron los puntos simulados de errores de lectura de `Path.read_text` a `Path.read_bytes`; las comprobaciones de comportamiento anteriores se conservaron.

Para ejecutar el conjunto completo comprobado, desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
```

Al terminar la unidad del lector el 30 de octubre de 2026, la ejecución terminó con **54 passed in 0.90s**, incluidos los 22 casos anteriores y las dos pruebas de integración. El usuario había confirmado previamente los 22 casos del validador en su PowerShell con resultado `22 passed in 0.69s`. Después confirmó los 54 casos con `54 passed in 0.95s` y la lectura directa del nombre y la fecha del candidato.

## Coherencia del perfil

`validate_profile_data(profile, schema)` de [profile.py](../../harness/profile.py) aplica primero el esquema y después las relaciones estructuradas del candidato. Devuelve `None` si se cumplen las reglas, o lanza `ProfileConsistencyError` con `path`, `rule` y un mensaje en español. Los errores de estructura siguen siendo `DataValidationError` del módulo común.

Las 40 pruebas de [test_profile.py](test_profile.py) cubren:

- El perfil aprobado, preservando datos y esquema en memoria.
- Fechas reales de calendario, incluido un 29 de febrero válido y otro inválido.
- Años o meses inexistentes, periodos invertidos y antecedentes posteriores al mes de referencia.
- Titulación anterior al fin de los estudios o posterior a la referencia.
- Identificadores repetidos entre registros diferentes, incluidos cargos anidados.
- Referencias inexistentes en formación, proyectos, logros, situaciones, competencias, fortalezas y mejoras.
- Correspondencia entre cargo y experiencia, entre proyecto de título y formación, y entre el proyecto y el periodo que lo respalda.
- Vínculos recíprocos de proyectos cuando el cargo declara `project_ids`.
- Incompatibilidad entre las referencias explícitas de un logro y su situación.
- Cobertura, huecos y solapamientos de los periodos de jornada.
- Conservación de entradas inválidas y aceptación de periodos de jornada desordenados sin reordenar el perfil original.

Los meses inicial y final son inclusivos. Las fechas mensuales se comparan por mes: no se inventan días para determinar si un periodo del mismo mes acabó antes o después del día de referencia. No se usa la fecha actual del ordenador. El perfil aprobado mantiene estudios y trabajo simultáneos, lo que no se considera automáticamente una incompatibilidad.

La ejecución completa posterior a esta unidad terminó el 30 de octubre de 2026 con **95 passed in 6.87s**: 92 pruebas unitarias y tres de integración. No se añadieron dependencias ni se consultó un LLM. Los tiempos pueden variar.

Las reglas no verifican automáticamente el significado de los relatos, el respaldo técnico descrito en texto libre ni la correspondencia con un archivo externo del puesto. La carga protegida y el currículum público se documentan a continuación; la entrevista sigue pendiente.

## Carga protegida e integridad

`load_profile(path, schema_path=...)` de [profile.py](../../harness/profile.py) lee el documento, aplica su esquema y las reglas de coherencia, y devuelve `CandidateProfile`. El esquema predeterminado se localiza respecto del módulo y no depende de la carpeta actual del proceso.

El objeto conserva una cadena JSON interna inmutable y una ruta absoluta con la huella SHA-256 de los bytes originales. Sus campos no se pueden reasignar mediante el uso normal de la clase. `candidate_id` y `scenario_reference_date` permiten consultar esos datos; `to_dict()` devuelve una copia independiente, incluidos los objetos y listas anidados. `repr` no vuelca el contenido interno.

`assert_source_unchanged()` devuelve `None` si el archivo conserva su huella, o lanza `ProfileIntegrityError` con ruta y regla: `source_changed`, `source_missing` o `source_unreadable`. Se ejecuta al terminar la carga para detectar cambios durante la validación y queda disponible para la futura finalización de una entrevista. No restaura ni sobrescribe archivos.

Las 18 pruebas de [test_profile_snapshot.py](test_profile_snapshot.py) cubren la carga y huella, campos inmutables, copias independientes, representación sin datos internos, archivos intactos, cambios de hechos o formato, eliminación, permisos, rutas relativas ante cambios de carpeta, datos o esquemas inválidos, esquema explícito y modificación del archivo durante la validación. Las pruebas que modifican o eliminan documentos usan copias temporales.

El 30 de octubre de 2026 el conjunto completo terminó con **116 passed in 10.97s**: 112 casos unitarios y cuatro de integración. Incluye los 95 casos anteriores, que el usuario había confirmado con **95 passed in 4.29s**, además de la validación directa con salida `Perfil validado: cand-001`. No se añadieron dependencias ni se consultó un LLM.

Esta protección conserva la instantánea y detecta diferencias en el archivo; no impide que otra aplicación edite el original. Un cambio de formato también cambia la huella y no implica por sí mismo una contradicción factual. El hash no garantiza que las futuras respuestas del modelo sean semánticamente correctas.

## Currículum público desde la fuente única

`CandidateProfile.to_public_resume()` devuelve una copia nueva con una selección explícita de campos profesionales: identidad, resumen, formación, cargos y periodos, responsabilidades, áreas técnicas, herramientas y proyectos con sus aportes. La selección también es explícita en los objetos anidados. No se mantiene un segundo JSON con antecedentes copiados manualmente.

Se excluyen situaciones conductuales, logros internos y sus evidencias, competencias internas, fortalezas, áreas de mejora, motivación, personalidad, límites de experiencia, notas del equipo y de autoridad, motivos de término de contrato, alcance detallado de conocimientos y límites internos de las contribuciones. Los identificadores de relaciones, huellas y rutas de archivos tampoco se muestran en el texto de consola. La selección se realiza por campos: no es un clasificador semántico de los textos autorizados, que siguen requiriendo revisión humana.

`format_resume(profile)` en [harness/application/cli.py](../../harness/application/cli.py) obtiene esa vista pública y devuelve texto legible con meses en español. No lee archivos ni imprime directamente. El módulo de perfil selecciona datos; el módulo de consola decide su presentación. La conversación, el menú y la configuración del puesto no se implementaron en esta unidad.

Las 19 pruebas de [test_public_resume.py](test_public_resume.py) comprueban la derivación, los campos autorizados en todos los niveles, la ausencia de marcadores colocados en 12 tipos de campos internos, las copias independientes, la actualización al cargar otra fuente, la combinación de responsabilidades sin duplicados, las fechas y secciones legibles y la generación desde la instantánea sin acceso al disco.

El usuario confirmó la unidad anterior con **116 passed in 6.06s**, los valores `cand-001` y `2026-10-20`, y la comprobación `Archivo original intacto`. El conjunto completo posterior al CV terminó el 30 de octubre de 2026 con **136 passed in 15.11s**: 131 casos unitarios y cinco de integración. No se añadieron dependencias ni se consultó un LLM.

Para mostrar el currículum, desde la raíz del proyecto en PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from harness.profile import load_profile; from harness.application.cli import format_resume; perfil = load_profile('data/candidates/candidato_junior.json'); print(format_resume(perfil)); perfil.assert_source_unchanged()"
```

La salida comienza con `CURRÍCULUM RESUMIDO - PERFIL FICTICIO` y el nombre de Nicolás Vera Soto, seguida de resumen, formación, experiencia, conocimientos, herramientas y proyectos. `-X utf8` configura UTF-8 únicamente para esa ejecución. La última operación verifica la huella del archivo original sin imprimir mensajes adicionales si se conserva.

## Configuración básica: contrato estructural

[test_interview_config_schema.py](test_interview_config_schema.py) aplica el validador existente a [basica.json](../../config/interviews/basica.json) y a su esquema. Los 40 casos cubren el archivo inicial, las tres modalidades y enfoques, estilos individuales y combinados, límites 1 y 20, cada campo obligatorio, valores incorrectos, límites fuera de rango, tipos incompatibles y un campo de evaluación no declarado. Se comprobó también el mensaje con ruta `/max_questions` y regla `maximum` para un valor de 21.

El esquema no comprueba archivos externos: un caso demuestra que `cand-999` tiene formato válido aunque no identifique al candidato cargado. Esa relación se comprueba ahora en el cargador de configuración, manteniendo separadas ambas responsabilidades. Las preferencias no clasifican ni puntúan preguntas, y todavía no existe un contador de entrevista.

El conjunto completo del 30 de octubre de 2026 terminó con **176 passed in 14.08s**, incluyendo los 136 casos anteriores. No se añadieron dependencias ni llamadas a un LLM.

## Preparación del escenario y referencias

`load_interview_setup()` de [interview_config.py](../../harness/interview_config.py) carga configuración, candidato y puesto con sus validaciones y comprueba sus tres relaciones por identificador. Devuelve un `InterviewSetup` inmutable: `candidate` es el perfil protegido; `config_dict()` y `job_dict()` devuelven copias independientes. Las rutas iniciales se ubican respecto del módulo y se pueden sustituir por otras rutas; no se buscan documentos por identificador.

Las 21 pruebas de [test_interview_config.py](test_interview_config.py) cubren escenario válido, cinco discrepancias, otros identificadores coherentes, validación de configuración antes de cargar los demás archivos, documentos ausentes o inválidos, copias independientes, objeto inmutable, nuevas cargas, cambios externos, otra carpeta actual, cambios del candidato durante la preparación y representación sin volcar documentos completos.

El usuario confirmó **176 passed in 8.27s**. La ejecución posterior terminó el 30 de octubre de 2026 con **198 passed in 8.34s**, incluidos los casos anteriores y una nueva integración. No se añadieron dependencias ni se consultó un LLM. No hay sesión ni contador activo todavía.

## Constructor del contexto autorizado

`load_instructions(path=...)` de [prompt_builder.py](../../harness/prompt_builder.py) lee texto UTF-8 con o sin BOM y comunica archivos ausentes, errores de lectura o codificación y contenido vacío mediante `PromptBuildError`. La futura sesión debe cargar instrucciones confiables una vez y conservar ese texto; el constructor no las obtiene de la pregunta.

`build_messages(setup, question, instructions=...)` recibe un escenario preparado, una pregunta no vacía y las instrucciones mediante argumento explícito. Produce exactamente dos mensajes nuevos: `system` con instrucciones y un objeto JSON de perfil interno, puesto y configuración, y `user` con la pregunta original. La serialización compacta conserva los hechos sin añadir un CV duplicado, rutas de origen, huellas ni variables de entorno.

El contrato `ChatMessage` de [harness/llm/messages.py](../../harness/llm/messages.py) documenta las claves `role` y `content` mediante `TypedDict`. Es una anotación de tipos, no una barrera de seguridad en ejecución. Los roles del mensaje se asignan explícitamente en el constructor; no se interpretan etiquetas ni objetos JSON escritos dentro de la pregunta.

Las 27 pruebas nuevas comprueban estructura serializable, datos completos y fieles al escenario, omisión de rutas/huellas/credenciales de prueba, cuatro preguntas con texto que simula órdenes o roles, entradas vacías o de tipo incorrecto, lectura de instrucciones, errores de archivo, ausencia de acceso a disco durante la construcción e independencia entre llamadas y copias. No se buscan frases particulares de las reglas para presentarlas como pruebas de comportamiento.

El usuario confirmó las 198 pruebas anteriores con **198 passed in 8.13s**. El conjunto completo del 30 de octubre de 2026 terminó con **226 passed in 9.55s**: 219 pruebas unitarias y siete de integración. No se instalaron paquetes ni se consultó un modelo.

Estos resultados verifican el mensaje que construye el programa. No demuestran que Qwen rechace los intentos de manipulación o mantenga todos los hechos al responder. No hay historial ni mecanismo de resumen todavía. El mensaje `system` contiene antecedentes internos autorizados para el modelo; su contenido no es una vista pública del candidato.

## Cliente local de Ollama

El usuario confirmó el constructor con **226 passed in 15.46s** y los roles `system` y `user`. Se añadieron 52 casos en `test_ollama_client.py`, con `httpx.MockTransport`, sin solicitudes reales. Comprueban contrato HTTP, parámetros, texto final separado del razonamiento, métricas disponibles o desconocidas, errores HTTP sin volcar el cuerpo, JSON inválido, respuesta incompleta, modelo ausente, reintentos limitados de conexión, recuperación, ausencia de repetición tras una generación iniciada y rechazo de redirecciones.

También comprueban la validación de mensajes antes de acceder a la red, direcciones remotas o con credenciales rechazadas, parámetros incompatibles y ausencia de selección de modelo o credenciales desde variables de entorno. El adaptador real desactiva el uso de proxies del entorno con `trust_env=False`; el transporte simulado no demuestra el comportamiento de una red real.

El conjunto completo terminó el 30 de octubre de 2026 con **279 passed in 10.27s**: 271 unitarias y ocho integraciones. Se instaló HTTPX 0.28.1 en `.venv`. La prueba real con Ollama se ejecuta por separado mediante `python -X utf8 -m scripts.smoke_test`; su resultado no forma parte de estos 279 casos ni certifica consistencia conversacional.

La primera llamada real agotó la espera de lectura de 180 segundos. Se amplió a 300 y se añadieron dos pruebas de `scripts/smoke_test.py`: guardado de evidencia con respuesta simulada y con fallo de conexión. Ambos casos conservan el original y dejan pendiente la revisión semántica. El conjunto final terminó con **281 passed in 15.48s**: 273 unitarias y ocho integraciones. Las métricas de los transportes simulados son datos de prueba, no mediciones de rendimiento.

Las incidencias reales motivaron otras cinco regresiones: salida cortada rechazada por el script, conservación de mensajes con otras dos selecciones explícitas de modelo y rechazo de dos formas de marcas de razonamiento en `content`. Se retiraron los prefijos y las plantillas experimentales; el modelo predeterminado quedó en `gemma3n:e2b`, ya instalado, después de identificar que los pesos Qwen3-4B-Thinking-2507 solo admiten razonamiento.

La suite completa con esa configuración terminó con **286 passed in 9.37s**: 278 unitarias y ocho integraciones. Tras reforzar los nombres literales en las instrucciones 1.0.1, las 27 comprobaciones del constructor y las dos integraciones de contexto/transporte terminaron con **29 passed in 1.91s**. No se añadieron pruebas de coincidencia de frases para simular obediencia; las respuestas reales requieren revisión aparte.

## Índice derivado de nombres exactos: 31 de octubre de 2026

El usuario confirmó **286 passed in 10.14s** y una llamada de 36,20 s que repitió la discrepancia de la institución. Se añadió `literal_name_references` al final del objeto JSON del contexto: una proyección de nombres y denominaciones desde el candidato y la oferta. Sus claves indican el campo de origen y sus valores se copian literalmente; no depende de la pregunta ni reemplaza datos de la respuesta.

Dos pruebas nuevas del constructor verifican cobertura y correspondencia de cada referencia con su campo original, además de otro perfil y puesto en archivos temporales, con acentos, comillas y barra invertida. La integración de contexto comprueba el índice sobre el escenario aprobado y conserva los cuatro archivos originales. Las verificaciones previas siguen cubriendo independencia entre llamadas y preguntas que simulan roles.

El conjunto terminó con **288 passed in 9.99s**: 280 unitarias y ocho integraciones. Estas pruebas verifican la derivación y serialización del contexto, no que el LLM copie correctamente cada nombre. Las llamadas reales y su revisión se registran aparte.

## Alternativa externa desactivada: 31 de octubre de 2026

El usuario confirmó **288 passed in 12.86s** y una respuesta local de 41,42 s que conservó la institución y el título exactos. Se implementó `OpenAIClient`, con parámetros sin claves en `OpenAISettings`, y `create_client` para seleccionar el proveedor con Ollama predeterminado. OpenAI requiere selección y permiso externo explícitos, además de modelo y clave; tener una clave no cambia de proveedor.

Los 48 casos de `test_openai_client.py` usan HTTPX MockTransport y una clave ficticia. Cubren destino oficial y autorización, mensajes sin cambios, separación del texto y razonamiento, estados incompletos, ausencia de texto válido, rechazo, herramientas no solicitadas, JSON inválido, métricas desconocidas, errores HTTP, redirección rechazada, reintentos limitados de conexión y ausencia de repetición después de fallos de lectura. Verifican además que cuerpos y excepciones simulados con la clave no la expongan en el error presentado, y que configuración y credenciales inválidas fallen antes de generar.

Los 13 casos de `test_llm_factory.py` comprueban valores predeterminados locales, creación sin solicitudes, ausencia de consulta de claves externas desde la ruta local, autorización exacta requerida, proveedores desconocidos, modelo y clave obligatorios y ausencia de cambio automático a la API cuando falla Ollama. Dos casos nuevos del script verifican el bloqueo externo y la evidencia de una respuesta externa simulada, sin guardar la clave.

Con una integración adicional, el conjunto terminó con **352 passed in 29.54s**: 343 unitarias y nueve integraciones. Son 63 casos unitarios nuevos y una integración. No se instalaron dependencias ni se invocó un modelo externo. Autenticación real, disponibilidad del modelo, cuota, facturación y calidad de respuestas externas siguen pendientes hasta que se decida activar la opción.

## Tiempos por fase y permanencia del modelo: 31 de octubre de 2026

El usuario confirmó **352 passed in 13.34s**, con una respuesta correcta de 275,82 s. El registro del servicio permitió identificar 232,60 s de procesamiento del contexto y 14,31 s de generación en esa llamada. Se añadieron métricas opcionales a `LLMResponse` y su conversión desde las duraciones de Ollama, además de `keep_alive: 15m` en la configuración y solicitud locales.

Los 21 casos nuevos de `test_ollama_client.py` cubren conversión de nanosegundos, valores ausentes, cero válido, datos de duración incompatibles o desbordados, conteo de caché imposible, envío de permanencia configurada y rechazo de duraciones no admitidas. Los campos ausentes quedan desconocidos y no invalidan una respuesta de texto que sí sea válida. Los contratos de los proveedores y las llamadas posicionales anteriores a `LLMResponse` se conservaron en la suite.

El conjunto terminó con **373 passed in 53.29s**: 364 unitarias y nueve integraciones. No hubo nuevas dependencias. Estas pruebas no miden rendimiento; las dos consultas locales reales y sus límites están en la [guía de rendimiento](../../docs/rendimiento-local.md) y la bitácora.

## Primera consola y controlador de preguntas: 31 de octubre de 2026

El usuario confirmó **373 passed in 10.12s** y dos consultas correctas de 1,84 y 1,81 s, ambas con 5072 tokens reutilizados. Se implementó `InterviewRuntime` y la consola de `scripts.run_interview`. Los 30 casos nuevos de `test_console_interview.py` usan clientes simulados y copias temporales cuando se modifica el perfil.

Cubren preguntas válidas o vacías, instrucciones inválidas, contador independiente y de solo lectura, límite configurado y de veinte preguntas, cierre idempotente, error de proveedor contado una vez, ausencia de reenvío automático, salida cortada rechazada y cambios del archivo antes o durante la generación, incluido un fallo simultáneo del proveedor. Las pruebas de interfaz cubren CV público y puesto, comandos sin consumo, inicio obligatorio, `/iniciar` repetido sin reinicio, cierre manual, límite, fin de entrada, interrupción al leer y al esperar respuesta, errores de preparación y cierre de recursos desde el punto de ejecución.

La primera ejecución de esos casos terminó con **1 failed, 28 passed**: la comprobación de privacidad utilizaba la clave inexistente `situation` en vez de `context`. Se corrigió la referencia en la prueba, manteniendo el perfil intacto. Se añadió además la interrupción durante la generación y una integración del flujo completo. El conjunto final terminó con **404 passed in 14.67s**: 394 unitarias y diez integraciones.

Los mocks verifican control e interfaces, no conversación semántica. El historial todavía no se incorpora a los mensajes y la consola no guarda entrevistas. La prueba real del ejecutable y su evidencia técnica están en la [guía de consola](../../docs/consola.md).

## Corrección tras la prueba ampliada de consola

Se actualizaron los controles del contexto para delimitar el JSON y conservar al final las instrucciones confiables. Un caso nuevo comprueba que el índice por proyecto solo contiene situaciones con relación explícita y conserva sus hechos. Dos casos nuevos del adaptador verifican la fusión del par inicial de Gemma 3n sin modificar preguntas o turnos posteriores y la conservación de mensajes sin system. Cuatro casos nuevos de la fábrica comprueban selección explícita de Gemma 4 local y rechazo de selecciones vacías o de nube antes de enviar solicitudes.

Son siete pruebas unitarias nuevas: 401 en total. Las diez integraciones siguen separadas. No se considera que la presencia de instrucciones en el texto pruebe obediencia del modelo; esa revisión se documenta en [las incidencias y pruebas reales](../../docs/pruebas/correccion-conducta.md).

## Etapa 7.1: historial en memoria

[test_conversation_memory.py](test_conversation_memory.py) añade veinte casos: orden de repreguntas, conservación del sistema, copias frente a modificaciones externas o del cliente, aislamiento incluso con cliente compartido, cierre, entrada inválida, error técnico, interrupción, salida cortada e integridad durante una repregunta. También rechaza historiales incompletos, desordenados o con nuevos roles system. Los textos de conversaciones anteriores se conservan en su rol y no se incorporan a los hechos autorizados del JSON. Se actualizaron las comprobaciones de consola para incluir turnos completos anteriores.

La suite conjunta terminó con **432 passed in 17.73s**: 421 unitarias y once integraciones. Antes de ello hubo un error de recolección por el mismo nombre de archivo en las dos carpetas de pruebas; se renombró la integración, sin alterar las comprobaciones. La revisión del texto real del LLM permanece separada de estos controles. Véase la [guía de historial](../../docs/historial-en-memoria.md).

## Corrección de cronología tras la prueba de memoria

[test_project_chronology.py](test_project_chronology.py) añade ocho casos sobre orden por inicio y término, solapamientos mensuales, contención, límites compartidos, cambio de año y fechas de inicio coincidentes. Comprueba también el índice del perfil aprobado, su vista legible y la independencia del orden de entrada o de una afirmación incorrecta en el historial. Se actualizaron las pruebas de formato del sistema porque la referencia cronológica se presenta después de las instrucciones bajo su propio marcador.

La suite final terminó con **440 passed in 16.94s**: 429 unitarias y once integraciones. Estas comprobaciones garantizan el cálculo y la estructura de esta unidad, no la interpretación del modelo. Las regresiones reales, incluidos dos intentos insuficientes y la revisión final 1.0.8, están en la [corrección de cronología](../../docs/pruebas/correccion-cronologia.md).

## Duración laboral y términos de estudios/proyectos

[test_temporal_facts.py](test_temporal_facts.py) añade diez casos: 21 meses del perfil y desglose por jornadas, cómputo mensual inclusivo y entre años, unión de empleos concurrentes, exclusión de un proyecto académico del empleo, distinción entre término de estudios y titulación, presentación de todos los hitos y ausencia de mutaciones. El cálculo utiliza el perfil validado y no un LLM. Las pruebas del contexto se actualizaron al orden final de las referencias.

La suite final terminó con **451 passed in 18.36s**: 439 unitarias y doce integraciones. Los resultados reales, omisiones anteriores y el matiz de autocorrección verbal se conservan en el [registro de duración y estudios](../../docs/pruebas/correccion-duracion-y-estudios.md).

## Etapa 7.2: sesión y registro técnico

[test_session_state.py](test_session_state.py) añade 25 casos. Comprueba identidad y aislamiento, fechas UTC y datos serializables, copias, estados pendientes/finales, retención de fallos y texto parcial sin incorporarlos al contexto, contador y límite, cierre idempotente, interrupciones, errores simultáneos de proveedor e integridad, catálogo sin detalles arbitrarios o credenciales y resumen de consola. Un caso adicional detecta una alteración después del cierre en la comprobación final, sin borrar la incidencia cuando se restauran los bytes. Las modificaciones del perfil se hacen solo sobre copias temporales.

La suite final terminó con **477 passed in 19.10s**, 464 unitarias y trece integraciones. Una ejecución previa de 476 casos pasó en 26,97 s antes de añadir el último caso de integridad. La prueba real permanece separada y está en [sesiones en memoria](../../docs/sesiones-en-memoria.md).

## Etapa 7.3: archivo de sesión

[test_session_log.py](test_session_log.py) añade 45 casos: fidelidad UTF-8 y de métricas, lectura independiente sin cambios del archivo, sesiones vacías, no sobrescritura, contratos y relaciones inválidas, fechas UTC reales, límites, conservación de errores y texto parcial, JSON inválido y fallos de escritura con limpieza del archivo propio. El caso existente de integridad final comprueba ahora que el diagnóstico se guarda incluso después del cierre. `tests/conftest.py` dirige todo guardado de la aplicación a carpetas temporales. La suite final terminó con **530 passed in 26.20s**, 509 unitarias y 21 integraciones. La primera recolección de esta unidad detectó una excepción simulada construida con argumentos incompletos; se corrigió el código de prueba. Véase [persistencia](../../docs/persistencia-sesiones.md).

## Etapa 7.4a: presupuesto de comparación

[test_context_budget.py](test_context_budget.py) añade 25 casos de cálculo puro: reservas, límite exacto, exceso, cero frente a métrica ausente, tipos inválidos, valores negativos/no finitos, configuración inmutable y reportes independientes sin copiar textos o descontar caché. La suite conjunta terminó con **559 passed in 27.36s**, 534 unitarias y 25 integraciones. No se tokeniza texto ni se predicen llamadas futuras. Véase [diagnóstico](../../docs/diagnostico-contexto.md).

## Etapa 7.4b: controles del adaptador y error de contexto

[test_ollama_context_guard.py](test_ollama_context_guard.py) añade 17 casos: controles en el nivel correcto para Gemma 3n/4, conservación de mensajes y ajustes, ocho formas/status de rechazo, seis cuerpos ajenos o malformados que conservan error genérico y catálogo sin datos arbitrarios. Se actualizó la expectativa de la solicitud en la prueba existente del adaptador. La suite terminó con **577 passed in 26.48s**, 551 unitarias y 26 integraciones. No hubo llamadas reales en pytest. La verificación local se documenta en [protección del contexto](../../docs/proteccion-contexto.md).

## Etapa 7.4c: fuentes y citas de resumen

[test_history_summary.py](test_history_summary.py) añade 51 casos: exclusión de fallos, numeración original, ventana reciente, copias, tipos, JSON sin duplicados o texto libre, índices, procedencia, cambios en citas/configuración/fuentes y errores o salidas cortadas sin reintento propio. Se incluyen regresiones de anclas omitidas por el selector: Python las repone de forma determinista. Los 55 casos nuevos conjuntos pasaron en 6,04 s; suite final **632 passed in 49.16s**, 602 unitarias y treinta integraciones. Las propuestas no certifican relevancia ni verdad. La incidencia real y su corrección se registran en [resumen extractivo](../../docs/resumen-extractivo.md).

## Etapa 7.4d: composición del contexto

[test_summary_context.py](test_summary_context.py) añade 16 casos de papeles, citas, referencias, guías estáticas de referencias y extractos, conservación de la pregunta y pares recientes, bytes de toda la lista de mensajes, ausencia de ahorro, vínculos con escenario/instrucciones y copias independientes. Comprueba que una orden contenida en la conversación siga como dato assistant y no se copie al sistema; no implica resistencia semántica universal. Los 22 casos nuevos conjuntos pasaron en 2,97 s. Suite final **654 passed in 34.08s**, 618 unitarias y 36 integraciones. Véase [contexto con resumen](../../docs/contexto-con-resumen.md).

## Etapa 7.4e: controlador y auditoría de memoria

[test_live_context.py](test_live_context.py) añade 32 casos: umbrales y datos desconocidos, política inválida, conservación de originales, selección separada del contador, activación persistente, rechazo previo sin reenvío, respaldo ante selección inválida o timeout, interrupción antes de enviar, integridad incluso con fallos simultáneos, máximo de preguntas y auditoría inválida. Verifica lectura de 1.0.0 y 1.1.0. Los 36 casos nuevos conjuntos pasaron en 14,86 s; suite final **690 passed in 104.14s**, 650 unitarias y cuarenta integraciones. La [guía](../../docs/resumen-en-entrevista.md) distingue pruebas simuladas y reales.
