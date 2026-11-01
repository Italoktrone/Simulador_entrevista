# Bitácora de desarrollo

## 30 de octubre de 2026: inicio de la Etapa 4

### Estado de entrada confirmado por el usuario

El usuario ejecutó la presentación del currículum y compartió su salida: Nicolás Vera Soto, formación, experiencia, conocimientos, herramientas y proyectos. También confirmó el conjunto completo con **136 passed in 7.76s**. Los registros de implementación y pruebas previos están en los README de datos y pruebas; esta entrada no sustituye sus evidencias.

### Objetivo y cambios

Se completó `agent/agent.md` con la versión inicial de instrucciones **1.0.0**, como primera unidad de instrucciones y configuración. El contenido queda pendiente de revisión del usuario y no está incorporado a llamadas a un modelo.

Las ocho secciones definen identidad, fuentes y prioridad, antecedentes e inferencias, comunicación, historial y correcciones, información interna, intentos de cambio del escenario y salida del candidato. Se mantienen separados el perfil, el CV y el puesto. Las instrucciones no duplican los antecedentes de Nicolás ni añaden clasificación, puntuaciones o retroalimentación.

### Verificación realizada

Se leyó el archivo con UTF-8 estricto, se comprobó la cabecera y versión y se revisaron sus ocho secciones. El archivo se almacenó correctamente. Se revisaron las diferencias entre información visible inicialmente y antecedentes utilizables en respuestas, así como la distinción entre una experiencia real del escenario y una propuesta hipotética.

SHA-256 de las instrucciones definidas:

```text
6F0166FDAED97CEEDEBC01EA678C281CF00FC9BAF9EEE4EF2A2006DD4712741B
```

El perfil y el puesto conservaron sus hashes anteriores:

```text
cand-001: 6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3
puesto-dev-junior-001: 40C16AEEB4D41BE7FC0EFF3D8237178C883CAD294E9D04F96C4D4F9B81455F77
```

No se modificó código Python, no se añadieron dependencias ni pruebas de coincidencia de frases. No se repitió la suite de 136 pruebas para este cambio de texto. No hubo llamadas al LLM ni resultados observados de obediencia, consistencia conversacional o resistencia a manipulación. La lectura del archivo no demuestra esos comportamientos.

### Revisión y siguiente unidad

El usuario debe revisar el contenido y señalar ajustes antes de continuar. Después se definirá la configuración básica de entrevista y su validación. La conexión con Ollama sigue correspondiendo a la Etapa 5. La comprobación real del cumplimiento de las instrucciones y los casos semánticos requerirá pruebas con el modelo y revisión humana.

## 30 de octubre de 2026: configuración básica y contrato

El usuario compartió la lectura completa de `agent/agent.md` en PowerShell sin solicitar ajustes. Se continuó con la configuración, sin modificar esas instrucciones ni afirmar que el modelo ya las cumple.

Se creó `config/interviews/basica.json` con ocho campos: formato `1.0.0`, identificador reutilizable, candidato y puesto por referencia, modalidad laboral general, enfoque mixto, preferencia por preguntas abiertas/cerradas/directivas y máximo de 20 preguntas. Se completó `schemas/interview_config.schema.json` para admitir las opciones previstas y límites enteros de 1 a 20, rechazando campos adicionales. No se incluyeron rúbricas ni parámetros de evaluación o del proveedor.

La combinación general y mixta se eligió como punto de partida para la primera entrevista. Los estilos son preferencias, sin valoración automática de calidad. `config_id` no se utilizará como identificador único de sesión. Las competencias y la fecha de referencia permanecen en sus fuentes originales.

Se añadió un único mensaje de error al validador existente para la regla `maximum`, de modo que un límite superior a 20 tenga una explicación en español. Las 40 pruebas del contrato y los 136 casos anteriores terminaron con **176 passed in 14.08s**. No se añadieron dependencias ni se consultó un LLM. Una prueba documenta que el esquema por sí solo acepta un identificador bien formado pero inexistente; la resolución de archivos no se ha implementado todavía.

Una comprobación puntual confirmó que `candidate_id`, `job_id` y el puesto objetivo del perfil coinciden con los documentos aprobados. SHA-256 de los archivos comprobados:

```text
basica.json: A9E1A5B95802F1B0E404BA3B4344919F4FC2CB97E54528A6DC76B8D1F95109BD
interview_config.schema.json: 622741D6C1C955F319FE2D3205FED65B99422C87E48C497B2E45E58D439C715A
```

La siguiente unidad será el cargador de configuración y la comprobación de sus vínculos con el candidato y puesto. El contador y la finalización de entrevista siguen siendo responsabilidades futuras del controlador.

## 30 de octubre de 2026: carga integrada del escenario

El usuario confirmó `basica.json` y **176 passed in 8.27s**. Se implementó `harness/interview_config.py` con `load_interview_setup`, `InterviewSetup` e `InterviewConfigError`.

El cargador valida la configuración, carga el candidato con sus reglas e integridad, valida el puesto y comprueba las tres referencias. Los archivos iniciales son valores predeterminados, se permiten otras rutas y no se buscan archivos a partir de identificadores. Devuelve instantáneas con copias de acceso y vuelve a comprobar la huella del perfil antes de devolver el escenario.

Se añadieron 21 pruebas unitarias y una integración. El conjunto terminó con **198 passed in 8.34s**: 192 casos unitarios y seis de integración. Se verificaron discrepancias, otros identificadores válidos, errores de archivos, cargas independientes, cambios externos y del candidato durante la preparación. La integración conserva los tres archivos aprobados.

La comprobación directa de `load_interview_setup()` produjo:

```text
entrevista-basica-001
cand-001
Desarrollador de Software Junior
20
```

No se añadieron dependencias, no se consultó un LLM ni se creó una sesión. La correspondencia de identificadores no demuestra cumplimiento de todos los requisitos de la oferta. La siguiente unidad será preparar el contexto autorizado manteniendo las preguntas separadas de las instrucciones.

## 30 de octubre de 2026: contexto autorizado inicial

El usuario confirmó **198 passed in 8.13s** y las cuatro líneas de la carga integrada. Se implementaron `load_instructions`, `build_messages` y `PromptBuildError` en `harness/prompt_builder.py`, y el contrato `ChatMessage` en `harness/llm/messages.py`.

Las instrucciones se leen en UTF-8 y se pasan explícitamente al constructor para poder conservarlas durante una sesión. El mensaje `system` contiene reglas y un objeto JSON compacto con perfil interno, puesto y configuración. La pregunta se conserva sin modificaciones en un mensaje `user` separado. El constructor no lee archivos, credenciales ni variables de entorno, y cada llamada devuelve objetos nuevos. No se incorporó historial ni resumen.

Se añadieron 27 pruebas unitarias y una de integración. El conjunto terminó con **226 passed in 9.55s**: 219 casos unitarios y siete de integración. Las preguntas con texto que simula roles no modificaron el mensaje de sistema ni su estructura. La integración conservó los cuatro archivos de origen y la huella del candidato. No se añadieron dependencias ni se consultó un LLM.

La verificación directa produjo:

```text
['system', 'user']
¿Dónde estudiaste?
Contexto preparado
Caracteres del mensaje system: 17460
```

El recuento de caracteres es una observación de esta versión del contexto, no una medición de tokens ni una garantía de que quepa en una ventana concreta del modelo. Los tokens, la latencia y las respuestas se medirán al conectar Ollama. No se ha observado todavía obediencia real, resistencia a manipulación o consistencia conversacional del modelo.

Queda pendiente la confirmación de esta unidad por el usuario antes de comenzar la Etapa 5, conexión con el LLM. El cliente local y la alternativa externa aún no están implementados.

## 30 de octubre de 2026: inicio de la Etapa 5, cliente local

El usuario confirmó **226 passed in 15.46s** y la salida de roles, pregunta y `Contexto preparado`. Se verificó el servicio Ollama **0.34.2**, con `qwen3:4b`, `gemma3n:e2b` y `qwen3:8b` instalados. `qwen3:4b` informa capacidades de completado, herramientas y razonamiento. Se mantuvo el modelo aprobado, sin descargas ni cambios en los datos.

Se instaló **HTTPX 0.28.1** y sus dependencias únicamente en `.venv`; `pip check` no encontró incompatibilidades. Se definieron `OllamaSettings`, la interfaz `LLMClient.generate`, `LLMResponse`, errores compartidos y el adaptador `OllamaClient`. El adaptador valida mensajes, envía JSON a `/api/chat` y recupera solo la respuesta final. No carga credenciales o `.env`, usa únicamente una dirección local y no tiene cambio automático a API externa. El adaptador externo sigue pendiente como otra unidad.

La configuración inicial solicita contexto de 8192, salida máxima de 512 tokens, temperatura 0,2 y desactivación del razonamiento. La espera de conexión es de 5 segundos con un reintento limitado. Las esperas de lectura y los errores HTTP no provocan otra generación automática. No se creó entrevista interactiva, historial, contador o evaluación.

Se añadieron 52 pruebas unitarias del contrato HTTP y una integración, con transporte simulado: **279 passed in 10.27s**. Tras el primer intento real se amplió la espera y se añadieron dos pruebas del guardado de evidencia, con respuesta y error: **281 passed in 15.48s**, 273 unitarias y ocho integraciones. Ninguna de estas pruebas consulta un modelo ni demuestra coherencia de respuestas.

### Primera llamada real y diagnóstico

`python -X utf8 -m scripts.smoke_test` preguntó «¿Dónde estudiaste y qué título obtuviste?». La primera llamada agotó los **180 segundos** de espera de lectura y terminó con `LLMTimeoutError`, sin devolver texto. El perfil conservó su huella original. La evidencia se guardó en `outputs/results/ollama-smoke-9cde55f5de494d35ad3836f6911b7862.json`; su fecha UTC es 31 de octubre, correspondiente al 30 de octubre en Santiago.

El registro del servicio mostró carga del modelo, contexto de **4311 tokens**, avance de procesamiento y cancelación al terminar la espera del cliente. `ollama ps` informó 4,1 GB de carga, 65 % CPU / 35 % GPU y contexto de 8192. Estos valores describen esa ejecución; no se deducen del tamaño en disco ni se generalizan a otras cargas. No se atribuyó una causa definitiva al tiempo total a partir de esos mensajes.

Se amplió la espera de lectura a **300 segundos** para repetir la observación. El script también registra desde entonces `test_elapsed_seconds`, duración total hasta terminar la comprobación de integridad, distinta del tiempo de la llamada HTTP informado en la respuesta. La evidencia inicial se conservó intacta. Las restricciones de la herramienta impidieron el primer acceso a localhost; se ejecutaron las consultas con el acceso correspondiente. No fue un error de instalación del modelo.

### Intentos de respuesta directa y corrección del diagnóstico

El segundo intento, con los mismos pesos, terminó en **177,54 s**, entrada **4311**, salida **512**, motivo `length`. El texto no fue una intervención válida del candidato. La evidencia `ollama-smoke-e924fab38ad84258bff28d889e2db8d1.json` conserva el estado `completed` de la primera versión del script; ese estado era solo técnico y no se acepta como éxito semántico. Se corrigió el script para devolver `incomplete` y código 1 cuando se alcanza el límite de salida, sin mostrar el texto parcial como respuesta del candidato.

Un prefijo vacío enviado como mensaje tampoco resolvió el comportamiento: **135,96 s**, entrada **4313**, salida **410**, motivo `stop`, con texto de preparación y respuesta mezclados. Evidencia: `ollama-smoke-89dc371382004e19a5b1deee14459b1e.json`. Ese resultado también es semánticamente inválido pese al antiguo estado técnico `completed`.

Se creó temporalmente `qwen3:4b-candidato`, reutilizando las capas del modelo instalado, para comprobar una hipótesis de plantilla. La primera plantilla simplificada no fue seleccionada por Ollama, que prefirió la integrada en el GGUF: **142,65 s**, entrada **4309**, salida **393**, motivo `stop`, también con salida mezclada. Evidencia: `ollama-smoke-797b34c140a6447c995732686d027980.json`. Se confirmó la selección de una segunda plantilla completa y su final con un bloque vacío cerrado mediante diagnóstico de renderizado; aun así no resolvió el comportamiento. La llamada terminó con `LLMInvalidResponseError` después de añadir el rechazo de marcas `<think>` y `</think>` en el contenido. Evidencia: `ollama-smoke-c5f5c4cfb1764fd9ae938d840fe417ff.json`. No se registró como texto de candidato ni se afirmó éxito semántico.

La inspección posterior de `/api/show` identificó la causa que faltaba comprobar al recomendar el modelo: `general.finetune: Thinking`, `general.version: 2507` y referencia a **Qwen3-4B-Thinking-2507**. La [ficha oficial de esos pesos](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507) indica que solo admiten razonamiento. El método de prefijo vacío para variantes híbridas no justificaba esperar ese comportamiento de esta variante. Se corrigió la recomendación; la hipótesis de solucionar todo mediante plantilla quedó descartada.

Se retiró únicamente la variante experimental creada durante esta unidad y su Modelfile del proyecto. Se retiró también la modificación de mensajes en el adaptador. Los tres modelos originales conservaron sus etiquetas e identificadores. No se descargaron pesos ni se activó un proveedor externo.

### Selección explícita de Gemma y revisión factual

Se eligió `gemma3n:e2b`, ya instalado, como predeterminado en `OllamaSettings`. Fue una decisión explícita de configuración después del diagnóstico, no un cambio automático al fallar una solicitud. Se conservó la interfaz `generate(messages)` y los dos mensajes originales.

La primera consulta con Gemma terminó en **43,15 s**, entrada **4744**, salida **37**, motivo `stop`, con respuesta directa en español. Coincidieron la carrera y la titulación de diciembre de 2025, pero el nombre de la institución apareció como **Instituto Profesional Horizontes Digital**, mientras que el perfil aprobado dice **Instituto Profesional Horizonte Digital**. Esa discrepancia se registró, sin modificar el perfil ni corregir silenciosamente la salida. Evidencia: `ollama-smoke-bf8c3cc943f1460da07af66652a4cce8.json`.

Se reforzó de manera general la copia literal de nombres propios y denominaciones en `agent/agent.md`, versión **1.0.1**, sin introducir nombres del candidato en las instrucciones. SHA-256 del archivo revisado:

```text
31F9CC393E8FEA854342C5C3A755D2F214BC03819BFA779A87C44D2656914CF6
```

La repetición, con el modelo ya cargado, terminó en **15,89 s**, entrada **4811**, salida **33**, motivo `stop`, pero mantuvo el mismo plural incorrecto. Evidencia: `ollama-smoke-257950f0aaa246638c6dc1d6c4c97fdc.json`. El ajuste textual no demostró corregir ese error. El estado técnico `completed` no implica consistencia factual; la revisión humana sigue pendiente. No se implementó un sustituidor de palabras, clasificador o evaluador para ocultar el fallo.

La conexión básica local está implementada y comprobada, pero **la discrepancia del nombre de la institución queda abierta**. Estos resultados no permiten certificar consistencia global, seguridad ante manipulación o latencia de una entrevista de 20 preguntas. La opción externa sigue pendiente de implementación y desactivada; la consola e historial también están pendientes. Se espera la comprobación del usuario antes de otra unidad.

### Comprobaciones finales de esta unidad

Se añadieron en total **59 pruebas unitarias y una integración**, con transporte simulado. La suite completa final con Gemma configurado terminó con **286 passed in 9.37s**: 278 unitarias y ocho integraciones. Después del ajuste de instrucciones, los 27 casos del constructor y las dos integraciones de contexto y transporte terminaron con **29 passed in 1.91s**. Estos son resultados de programa, separados de las siete llamadas al modelo y de la consulta mínima de diagnóstico. `pip check` confirmó de nuevo dependencias compatibles.

El candidato conservó `6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3` y el puesto `40C16AEEB4D41BE7FC0EFF3D8237178C883CAD294E9D04F96C4D4F9B81455F77`. La fecha del escenario continúa en **2026-10-20**. Cada llamada real comprobó la integridad del original. Las marcas horarias de los JSON se guardan en UTC; esta entrada usa la fecha local de Santiago.

## 31 de octubre de 2026: índice derivado de denominaciones exactas

El usuario confirmó **286 passed in 10.14s** y una llamada real con Gemma de **36,20 s**, entrada **4811**, salida **37**, motivo `stop`, con el perfil intacto. La respuesta volvió a escribir **Horizontes** en lugar de **Horizonte**. Evidencia del usuario: `outputs/results/ollama-smoke-9c9bf4f798ac426191563daade6c6c59.json`. Las instrucciones literales 1.0.1 no habían corregido el caso.

Se amplió `build_messages` con `literal_name_references`, último campo del objeto JSON del contexto. Es un índice derivado en memoria de campos del candidato y el puesto: nombre, instituciones y títulos académicos, organizaciones y cargos laborales, proyectos, título y organización de la oferta. Cada valor conserva su ruta de origen, para distinguir los datos del candidato de las denominaciones del puesto. No se duplica un CV, no se mantiene otro archivo de antecedentes y no hay un nombre de institución incorporado en el código.

La instrucción de uso del índice se coloca antes de los datos. Se conservan el perfil interno completo, las instrucciones aprobadas, los roles `system` y `user` y la pregunta sin cambios. La construcción no consulta archivos, entorno o modelo. No se añadió un clasificador ni un sustituidor de palabras en la respuesta.

El script de prueba registra desde esta revisión `instructions_text_sha256` y `system_message_sha256`: huellas del texto interpretado y del contexto preparado en UTF-8, sin guardar el contexto completo. No se confunden con la huella de bytes del archivo del candidato. Los registros anteriores se conservan con los campos que tenían al generarse.

Dos pruebas nuevas comprueban cobertura y correspondencia exacta de las referencias con los campos originales, y un perfil y puesto alternativos en archivos temporales, con acentos, comillas y barra invertida. Se amplió la integración del contexto sobre las fuentes aprobadas. La suite completa terminó con **288 passed in 9.99s**: 280 unitarias y ocho integraciones, sin red en las pruebas automatizadas. Esas comprobaciones validan el contexto generado, no la obediencia del modelo.

### Consultas reales y revisión del caso

Se hicieron tres consultas consecutivas de «¿Dónde estudiaste y qué título obtuviste?» con `gemma3n:e2b`, temperatura 0,2, contexto solicitado 8192 y salida máxima 512, conservando cada respuesta sin sustituciones de texto:

| Evidencia en outputs/results | Tiempo | Entrada | Salida | Finalización |
| --- | --- | --- | --- | --- |
| `ollama-smoke-d390c8177b8641fa97f4389e51bd12af.json` | 20,08 s | 5073 | 24 | stop |
| `ollama-smoke-c430631a48b94940b457a21e20510d08.json` | 2,33 s | 5073 | 24 | stop |
| `ollama-smoke-8f71c174056747c2b9a129708752780f.json` | 1,95 s | 5073 | 24 | stop |

Las tres respuestas conservaron exactamente **Instituto Profesional Horizonte Digital** e **Ingeniería en Informática**, con frases naturales ligeramente distintas alrededor de esos nombres. Ninguna añadió una institución o título distinto. La pregunta no exigía el mes de titulación y estas respuestas no lo incluyeron. El agente comparó ese contenido con el perfil; los JSON mantienen la revisión humana pendiente para el usuario. No se presentan como tres sesiones completas ni como garantía estadística de consistencia.

Los tres registros informaron el mismo mensaje de sistema:

```text
instructions_text_sha256: 31F9CC393E8FEA854342C5C3A755D2F214BC03819BFA779A87C44D2656914CF6
system_message_sha256: E28C856A14A39663CB389DEAA0098EC6537D9A13EFCEB11BF867AD86A7CE0B93
```

El modelo y el contexto se reutilizaron en las repeticiones. Los tiempos breves de la segunda y tercera consulta no se usan para predecir la latencia de preguntas nuevas ni de una carga inicial. No se incorporaron mediciones ficticias o metas como si fueran resultados.

El candidato y puesto conservan los hashes documentados, la fecha **2026-10-20** y el máximo configurado de **20**. Las instrucciones siguen en 1.0.1, sin cambios. No hubo instalaciones, descargas, cambio de modelo ni activación externa en esta unidad.

La discrepancia observada no reapareció en estas tres consultas. Queda pendiente la comprobación del usuario antes de otra unidad; la consistencia de otras preguntas y nombres, el historial, la consola y el adaptador externo siguen en sus etapas correspondientes.

## 31 de octubre de 2026: alternativa externa con activación explícita

El usuario confirmó **288 passed in 12.86s** y una respuesta real con `gemma3n:e2b` que conservó exactamente la institución y el título. La llamada tardó **41,42 s**, entrada **5073**, salida **24**, motivo `stop`, con el original intacto. Evidencia del usuario: `outputs/results/ollama-smoke-7042a2809d634998a709f5bde360d3f3.json`.

Se implementó la alternativa solicitada de API externa como adaptador OpenAI Responses, conservando Ollama predeterminado. Se consultó OpenAI Docs y la documentación oficial del contrato de entrada/salida y errores. La referencia HTML de creación excedía el tamaño admitido por el navegador y su versión Markdown no era compatible con ese lector; se leyeron los campos concretos de la versión Markdown oficial mediante una solicitud de documentación, sin credenciales ni inferencia. No se obtuvo ni configuró una clave real.

Los archivos nuevos son `harness/llm/openai_client.py` y `harness/llm/factory.py`. `OpenAISettings` contiene modelo explícito y límites, sin claves; `LLMAuthenticationError` distingue acceso rechazado. La fábrica utiliza variables de la sesión y no carga `.env`. Exige `LLM_PROVIDER=openai`, `LLM_ALLOW_EXTERNAL_API=true`, modelo y clave para la ruta externa. La ruta Ollama no consulta las credenciales externas. No hay cambio automático de proveedor ante errores.

El adaptador usa HTTPX ya instalado y el endpoint oficial fijo con HTTPS, sin redirecciones ni proxies del entorno. Envía los mismos mensajes en `input`, solicita `store: false` y `stream: false` y recupera solo texto de mensajes completados. Omite elementos de razonamiento y rechaza salida incompleta, vacía, de rechazo o de herramientas no solicitadas. Los errores no imprimen cuerpos HTTP o excepciones de transporte que puedan incluir credenciales. La clave solo se incorpora a la cabecera de autorización y queda fuera de la configuración serializable.

La configuración externa inicial requiere un modelo elegido al activar la opción, salida máxima 512 tokens, conexión de 5 s, lectura de 90 s y un reintento de conexión. La referencia oficial indica un mínimo de salida de 16 tokens y que el límite incluye razonamiento; la validación refleja ese mínimo. No se enviaron parámetros particulares de una familia de modelos, como temperatura. No se eligió ni recomendó un modelo de API sin verificar disponibilidad y costos para el momento de activación.

El script de prueba usa ahora la fábrica y conserva proveedor, parámetros sin claves y los controles de integridad existentes. La salida local mantiene su presentación. Se documentaron las variables en `.env.example`, sin activar ni cargar ese archivo, y el procedimiento futuro en `docs/conexion-api-opcional.md`. El script puede usar la opción externa cuando se habilite expresamente; no es un adaptador desconectado del punto de ejecución.

### Pruebas y límites de la verificación externa

Se añadieron 48 casos unitarios del adaptador, 13 de la fábrica, dos del script y una integración: **64 pruebas nuevas**. Se utilizaron una clave y un modelo ficticios con transporte simulado. Se comprobaron contrato HTTP, rechazo de estados incompletos, tipos de error, reintentos limitados, ausencia de cambio de proveedor, controles de activación y ausencia de clave en mensajes, evidencia y errores de prueba, incluso cuando el cuerpo HTTP o el error simulado la incluían.

El conjunto completo terminó con **352 passed in 29.54s**: 343 unitarias y nueve integraciones. `pip check` devolvió `No broken requirements found.`. No se añadieron paquetes ni se realizaron solicitudes reales a la API de modelos externa. Esta verificación no acredita autenticación real, acceso al modelo, cuota, facturación, conectividad al servicio o calidad de respuestas externas. Esas comprobaciones se harán cuando el usuario decida utilizar la opción.

Una comprobación de valores predeterminados sin solicitudes imprimió:

```text
Proveedor: ollama
Modelo: gemma3n:e2b
```

### Comprobación real de la ruta local compartida

Se ejecutó el script actualizado en un proceso con `LLM_PROVIDER=ollama` y `LLM_ALLOW_EXTERNAL_API=false`. La llamada a Ollama terminó en **43,71 s**, entrada **5073**, salida **24**, motivo `stop`, con «Instituto Profesional Horizonte Digital» e «Ingeniería en Informática» exactos. El original quedó intacto. Evidencia: `outputs/results/ollama-smoke-8eed79894c7443c2a5fbfbf2028963c1.json`.

La llamada confirma la integración local del selector; no es una medición externa. No se cambia la interpretación de los tiempos anteriores ni se certifica consistencia global a partir de esta pregunta. La fecha del escenario, máximo de preguntas, perfil, puesto e instrucciones no se modificaron. Se espera la comprobación del usuario antes de pasar a otra unidad o a la consola.

## 31 de octubre de 2026: diagnóstico de la llamada de 275,82 segundos

El usuario confirmó **352 passed in 13.34s** y otra respuesta correcta de Gemma, con entrada **5073**, salida **24**, motivo `stop` y el original intacto, pero la llamada tardó **275,82 s**. Evidencia: `outputs/results/ollama-smoke-5f2399bfb48b4c6e9e09d93a4122bc94.json`. Se revisó esta demora antes de añadir la consola, por su efecto en una demostración.

### Observaciones y límites del diagnóstico

El registro técnico del servicio terminó esa solicitud a las **03:06:35, hora de Santiago**, coincidiendo con inicio UTC y duración del JSON. Informó:

```text
prompt eval time = 232601.99 ms / 5073 tokens
eval time = 14312.32 ms / 24 tokens
total time = 246914.31 ms / 5097 tokens
HTTP 200, POST /api/chat, 4m35s
```

Se identificó el procesamiento del contexto como la mayor parte de esa llamada. El resto de los 275,82 s no se atribuyó automáticamente a carga: la respuesta guardada no tenía todavía el desglose. No se modificó la evidencia antigua ni se reconstruyeron sus campos como si hubieran sido recibidos en ese JSON.

Las comprobaciones actuales mostraron `gemma3n:e2b` cargado con tamaño informado de 6,2 GB, reparto 76 % CPU / 24 % GPU y contexto de 8192. La lectura de memoria disponible rondó 4,4 GB. Son observaciones del momento de diagnóstico, no una medición continua durante la llamada anterior. No permiten establecer por sí solas una causa térmica, de energía, controladores o competencia entre procesos. No se cambió ninguna configuración del equipo para probar esas hipótesis.

### Ajuste acotado y observabilidad

`LLMResponse` añade campos opcionales de total del servidor, carga, procesamiento de contexto, generación y tokens reutilizados. El adaptador Ollama convierte las duraciones enteras de nanosegundos a segundos; tipos incompatibles, negativos o desbordados quedan desconocidos. Cero sigue siendo válido. Un conteo de caché superior a la entrada informada tampoco se presenta como medición válida. OpenAI conserva los campos en `None`, sin inventar información.

El script muestra y conserva ese desglose. `OllamaSettings.keep_alive` solicita ahora **15 minutos** de permanencia después de responder y se envía en cada solicitud local. Esto ayuda a evitar otra preparación por descarga automática entre pausas, manteniendo memoria ocupada durante ese periodo. No se aumentó el tiempo de lectura de 300 s, no se redujo contexto ni se alteraron los antecedentes.

Se añadieron **21 pruebas unitarias** para conversión, ausencia de métricas, cero, valores inválidos, caché inconsistente y permanencia configurable. El conjunto terminó con **373 passed in 53.29s**: 364 unitarias y nueve integraciones. Las solicitudes de la suite fueron simuladas. No se instalaron bibliotecas o modelos.

### Dos consultas reales con el mismo contexto

La prueba se ejecutó con Ollama y uso externo desactivado. La segunda consulta solo se inició después del éxito de la primera; no se repitió ninguna generación tras un tiempo de espera.

| Campo | Primera consulta | Repetición inmediata |
| --- | --- | --- |
| Tiempo de llamada | 55,54 s | 2,18 s |
| Total del servidor | 55,49 s | 2,17 s |
| Carga informada | 34,88 s | 0,02 s |
| Procesamiento del contexto | 18,58 s | 0,10 s |
| Generación | 1,94 s | 1,96 s |
| Entrada | 5073 | 5073 |
| Tokens reutilizados | 0 | 5072 |
| Salida | 24 | 24 |
| Finalización | stop | stop |

Evidencias: `outputs/results/ollama-smoke-4704e1947b3e498db5a82648ea37450b.json` y `outputs/results/ollama-smoke-817805040fce484da953c8f208c62767.json`. Ambas conservaron la institución y el título literales y comprobaron el original intacto. La huella de sistema siguió siendo `E28C856A14A39663CB389DEAA0098EC6537D9A13EFCEB11BF867AD86A7CE0B93`, igual que en la llamada de 275,82 s. El proveedor, modelo, instrucciones y antecedentes no cambiaron.

Una comprobación posterior con `ollama ps` mostró el mismo reparto de CPU/GPU y **12 minutos restantes** de permanencia. Confirma la aceptación de la solicitud de 15 minutos; no implica que se haya medido una pausa completa de 15 minutos.

La repetición confirma reutilización efectiva del contexto. La caída de 275,82 a 55,54 s en las primeras consultas no se atribuye a `keep_alive`, que controla residencia y no velocidad de cálculo. La variabilidad inicial sigue sin explicarse completamente. Tampoco se promete 2,18 s para nuevas preguntas, otro estado del equipo o una entrevista completa.

Se documentó cómo preparar el candidato antes de la demostración, comprobar dos consultas seguidas y conservar los resultados. La prueba aislada no inicia entrevista ni cuenta preguntas. La consola sigue pendiente de la siguiente unidad, después de la comprobación del usuario. Los hashes del perfil, puesto e instrucciones siguen intactos; la fecha de referencia continúa en **2026-10-20** y el máximo configurado en **20**. La API externa permaneció desactivada.

## 31 de octubre de 2026: Etapa 6, primera conversación en consola

El usuario confirmó **373 passed in 10.12s** y dos respuestas locales correctas de **1,84 s** y **1,81 s**, con 5072 de los 5073 tokens de entrada reutilizados, salida 24 y motivo `stop`. Las dos conservaron el original. Evidencias del usuario: `ollama-smoke-6b81c5beaa554c0b9ffe21c2629ea3e7.json` y `ollama-smoke-6ceeb90947634da7a8fdd9534134d0a0.json`. Son mediciones con contexto reutilizado, no una garantía de carga inicial.

Se implementaron `InterviewRuntime` en `harness/runtime.py`, `format_job` y `run_console` en `harness/application/cli.py`, y el punto ejecutable `scripts/run_interview.py`. El cargador y las instrucciones se utilizan una vez al abrir el programa. La fábrica conserva la selección local por defecto y la alternativa externa explícita. No hubo nuevas dependencias ni cambios del perfil, puesto, configuración o instrucciones.

La consola presenta candidato, puesto y proveedor, permite consultar `/cv` y `/puesto`, comenzar con `/iniciar`, mostrar `/ayuda` y terminar con `/salir`. Cada entrada de pregunta tiene una línea. El CV utiliza la vista pública existente; el puesto muestra responsabilidades, requisitos, competencias y nivel esperado, sin volcar instrucciones o relatos internos del perfil.

El controlador es independiente de entrada y salida de terminal: recibe escenario, instrucciones y el contrato del cliente. Cuenta una pregunta válida enviada aunque falle la respuesta; comandos, entradas vacías y mensajes del programa no cuentan. Repetir `/iniciar` no reinicia el contador. Aplica el límite de la configuración, probado también en veinte preguntas, e impide otra llamada después de terminar. Cada ejecución crea un contador independiente.

Se muestra un error conocido del proveedor y se permite otra pregunta si quedan lugares; no se vuelve a enviar automáticamente la generación. Una salida cortada no se presenta como respuesta válida del candidato. Fin de entrada y `Ctrl+C` cierran de forma controlada. El cliente se cierra desde su contexto de recursos. El perfil se comprueba antes y después de generar y al terminar el programa; un cambio detectado cierra la ejecución y no produce un mensaje de archivo intacto.

### Pruebas y corrección de una referencia de prueba

La primera ejecución de las pruebas nuevas terminó con **1 failed, 28 passed**. La comprobación de que el menú no expusiera un relato privado buscaba la clave `situation`, que no existe en ese registro. Se revisó el perfil y se corrigió únicamente la referencia de prueba a `context`, sin modificar antecedentes. Se añadió la interrupción durante la espera del modelo y una integración de extremo a extremo con HTTP simulado.

La suite completa terminó con **404 passed in 14.67s**: 394 unitarias y diez integraciones. Son 30 casos unitarios y una integración nuevos. Cubren límites, contadores, independencia de ejecuciones, roles sin historial, errores y ausencia de reenvío, salida cortada, comandos, privacidad de vistas, interrupciones, errores de preparación, cierre del cliente y cambios del perfil antes o durante una generación, incluso si esta falla. Las modificaciones de datos se hicieron sobre copias temporales. No hubo solicitudes reales en pytest.

### Ejecución real del programa

Se ejecutó un proceso real de `python -X utf8 -m scripts.run_interview`, con entrada UTF-8 controlada, `LLM_PROVIDER=ollama` y `LLM_ALLOW_EXTERNAL_API=false`. Las entradas fueron `/cv`, `/puesto`, `/iniciar`, «¿Dónde estudiaste y qué título obtuviste?» y `/salir`.

El programa mostró las dos vistas, inició el contador en 1/20, obtuvo «Instituto Profesional Horizonte Digital» e «Ingeniería en Informática» exactos y terminó antes de agotar el máximo. La respuesta tardó **34,60 s**. El proceso devolvió 0 y comprobó el original intacto. Se revisó visualmente la salida capturada.

Evidencia técnica: `outputs/results/console-smoke-aad61a8860c740d983b1dc4b002c0c8e.json`. El registro fue creado por la verificación controlada, con las entradas, salida del ejecutable y huella del perfil; no es un guardado automático de entrevista. No se midieron en esta ejecución las fases del proveedor ni se atribuyó la duración a una causa específica.

### Límites de esta unidad y siguiente paso

Cada pregunta se responde desde el mismo perfil y configuración, sin incluir preguntas o respuestas previas. La interfaz lo anuncia para que el usuario formule preguntas independientes. El programa todavía no guarda conversaciones, crea identificadores de sesión o resume contexto. Esas funciones permanecen en la Etapa 7. No se implementaron clasificación, evaluación, puntuaciones o retroalimentación educativa.

El control de veinte preguntas se verificó con respuestas simuladas; la prueba real revisó solo la pregunta de formación. No se certifica consistencia global ni latencia de una entrevista completa. El máximo sigue en **20** y la fecha del escenario en **2026-10-20**. Se espera la comprobación del usuario antes de iniciar la siguiente unidad.

## 31 de octubre de 2026: incidencias de la prueba ampliada y corrección previa al historial

El usuario confirmó **404 passed in 14.84s** y aportó una transcripción de veinte preguntas. Se conservó íntegra como `outputs/results/console-user-2026-10-31.txt`. Hubo un HTTP 500, siete salidas rechazadas por longitud y doce respuestas completas. El contador y la integridad funcionaron, pero se observaron invenciones SQL, cambios de autoría, abandono del rol, explicación de funcionamiento interno y caracteres U+2581. Las tres solicitudes de instrucciones, scraping y trayectoria nueva que terminaron por longitud no se calificaron como rechazos semánticos correctos, porque el texto no estaba disponible. El pequeño programa Python de la pregunta 16 no demuestra por sí solo un cambio de rol.

Se trabajó en esta corrección antes de incorporar historial. Las instrucciones llegaron a **1.0.5**, tras conservar varios intentos insuficientes. El contexto delimita el JSON, conserva al final las instrucciones y añade un índice de relaciones explícitas por proyecto. Este índice se deriva de la instantánea validada y no añade relatos a proyectos sin vínculo. El candidato, puesto y configuración aprobados conservan sus hashes originales, la fecha 2026-10-20 y el máximo de veinte preguntas.

Se inspeccionó la plantilla local de Gemma 3n: transforma system y user en turnos user separados. El adaptador reúne únicamente ese par inicial para esta familia, preservando la pregunta y los turnos posteriores. El contrato general del constructor sigue siendo system/user. La documentación de Google describe ese formato sin system nativo; Gemma 4 admite system y conserva los mensajes generales. La adaptación aislada de Gemma 3n no resolvió las incidencias semánticas.

El inventario actual mostró gemma3n:e2b (719372f8c7de), gemma4:e2b (b37049369adf) y gemma4:e4b (dc35e8d9c606), con Ollama 0.34.2. El intento de usar qwen3:8b, basado en el listado histórico, recibió errores de modelo ausente; no se descargaron pesos para sustituirlo. Se añadió OLLAMA_MODEL como selección local explícita de la fábrica, sin cambiar el predeterminado gemma3n:e2b ni habilitar fallback. Durante las pruebas se descargó de memoria el modelo e2b ya probado mediante ollama stop, sin eliminar sus archivos.

Las consultas diagnósticas nuevas a /api/show de Gemma 3n devolvieron una respuesta sin JSON utilizable; el registro técnico indicó `json: unsupported value: -Inf` para esas consultas. Esto no identifica la causa del HTTP 500 de la transcripción del usuario. No se cambió Ollama, sus opciones globales, controladores o ajustes de energía.

Se incorporó scripts/check_candidate_behavior.py: repetición exclusivamente local de trece preguntas independientes, guardado de cada respuesta original, errores y texto parcial, métricas, huellas y comprobación de integridad. No clasifica preguntas, puntúa al entrevistador ni sustituye respuestas. El retorno 0 solo representa finalización técnica. La revisión semántica del usuario queda pendiente. No es persistencia automática de una entrevista.

Se añadieron siete pruebas unitarias significativas para relaciones por proyecto, formato de transporte y selección local explícita. Las integraciones se adaptaron al formato nativo de Gemma 3n y verifican la conservación del contrato general y de las fuentes. La suite final terminó con **411 passed in 24.09s**: 401 unitarias y diez integraciones, sin solicitudes reales en pytest. Las pruebas reales se registran aparte. La documentación de incidencias conserva todos los intentos, incluido el fracaso de una reformulación del intercambio de roles en la versión 1.0.4, pese a trece llamadas completas.

El alcance continúa siendo la corrección del candidato en consola: sin historial, resúmenes, sesiones persistentes, clasificación, evaluación educativa o cambios de los antecedentes. La API externa permaneció desactivada.

La repetición final con **instrucciones 1.0.5 y gemma4:e4b** terminó con trece respuestas completas, sin cortes, HTTP 500 o U+2581, y con el original intacto. Evidencia: `outputs/results/candidate-behavior-dead1e1a42224d539303014d0a4e538d.json`. Las llamadas sumaron 135,92 s, con máximo de 25,47 s y salida máxima de 101 tokens. La reformulación que había cambiado el rol en 1.0.4 ahora recibió un rechazo breve; la petición legítima de Python mantuvo código y explicación. Se revisaron institución, límites, proyectos, autoría de identificación del error y ausencia de divulgación en los casos probados. El relato describe el cambio posterior como conjunto, un matiz más amplio que la fuente que queda señalado para revisión del usuario. No se declara aprobación semántica universal.

El resultado se obtuvo con el modelo e4b y el contexto revisado conjuntamente; no se atribuye la mejora solo al tamaño del modelo. El modelo predeterminado del proyecto no cambió. Se documentó cómo elegir e4b explícitamente, ejecutar las 411 pruebas y repetir los trece casos. Se espera la comprobación del usuario antes del historial.

## 31 de octubre de 2026: comprobación del usuario de la corrección en consola

El usuario aportó **411 passed in 14.84s** y la repetición de los trece casos con `gemma4:e4b`, proveedor local y API externa desactivada. La transcripción se conservó íntegra como `outputs/results/console-user-correction-2026-10-31.txt`. Se revisó también el archivo real `candidate-behavior-5cfb16b620624f6fb9beb5a6bf774ad8.json`: trece respuestas completas con stop, sin errores, cortes o U+2581 y con el perfil intacto. Las llamadas sumaron 100,52 s, el máximo fue de 19,53 s y la salida más larga de 84 tokens. Las huellas de sistema e instrucciones son las de 1.0.5. No se hicieron nuevas llamadas al modelo ni se atribuyeron las mediciones a esta revisión.

La revisión comprobó institución y título, límites técnicos, ausencia de consultas exactas inventadas y conservación del rol ante ambas formas de pedir el intercambio. El ejemplo legítimo de Python siguió disponible. S1 mantiene que Nicolás identifica el error y consulta su propuesta, aunque añade «tras su guía», una ampliación del apoyo no detallada por la fuente. Se registró como matiz bajo observación, sin cambiar los datos ni afirmar fidelidad universal. Los hashes de candidato, puesto y configuración permanecen iguales a los aprobados.

Se cierra la corrección acotada de la Etapa 6 con evidencia del usuario y se mantiene ese matiz para la revisión posterior. Se propone como siguiente unidad de la Etapa 7 conservar turnos completos en memoria y comprobar repreguntas y aislamiento. No se implementa esa etapa en esta revisión: el prompt maestro exige «No avances automáticamente entre etapas». No se cambian código, dependencias, proveedor o modelo predeterminado.

## 31 de octubre de 2026: Etapa 7.1, historial de turnos completos en memoria

El usuario indicó «Continuemos» tras revisar la corrección de consola y la propuesta de comenzar el historial en memoria. Se explicó el alcance antes de implementar: conservar turnos durante la ejecución, comprender repreguntas y comprobar aislamiento; las demás unidades de sesiones y contexto se mantienen posteriores.

Se amplió `build_messages` con el argumento opcional history. Acepta pares completos user/assistant, rechaza nuevas reglas system o estructuras incompletas, conserva los textos y devuelve copias nuevas. El sistema, perfil y configuración no se obtienen del historial. Sin historial, el mensaje de sistema inicial conserva la huella anterior. No se modificaron instrucciones, perfil, puesto, configuración, adaptadores, selección de proveedor o dependencias.

`InterviewRuntime` conserva una lista propia por objeto y expone `history_messages()` mediante copias. Cada generación recibe el sistema, los turnos completos previos y la pregunta actual. Solo se incorpora el nuevo par después de una respuesta completa y de las comprobaciones de integridad. Errores, interrupciones y salidas cortadas siguen contando como preguntas enviadas, pero no aportan pares incompletos al contexto. Los comandos y la repetición de iniciar no borran ni añaden turnos. Cerrar impide continuar y conserva la lista mientras exista el objeto; el programa todavía no la guarda en disco.

La consola informa de que conserva la conversación durante esta entrevista y de que se pierde al cerrar el programa. Se creó la guía `docs/historial-en-memoria.md` y se actualizaron las guías actuales, arquitectura y pruebas dependientes.

La primera ejecución de pytest encontró **1 error de recolección en 0,75 s**: los dos archivos nuevos tenían el nombre test_conversation_memory.py y se importaban sin paquetes separados. Se renombró solo el de integración a test_history_flow.py, conservando sus comprobaciones; no se borraron cachés ni se cambió pytest. Después, la suite completa terminó con **432 passed in 17.73s**: 421 unitarias y once integraciones. Son veinte casos unitarios y una integración nuevos. Las comprobaciones anteriores del contador y la consola se actualizaron al nuevo contexto de turnos completos.

Se comprobó además el ejecutable real con cuatro preguntas enlazadas sobre Inventario Aula y gemma4:e4b, manteniendo la API externa desactivada. El candidato describió su aporte, las tecnologías, la ausencia de clientes comerciales o producción y recordó el proyecto de la primera pregunta. Las llamadas tardaron 62,99; 8,62; 6,96 y 7,63 segundos. El proceso duró 87,35 s y terminó con 0. No se midieron las fases del servidor ni se atribuyó la latencia inicial a carga, caché u otra causa sin evidencia.

Evidencia externa: `outputs/results/console-memory-18b74d5c14914bf7bf803149eac72746.json`. Guarda entradas, salida original y hashes antes/después; todos los archivos del escenario e instrucciones quedaron intactos. El sistema inicial sigue en A2596C462EEBACB0B25188C351FA7064C4496565A3AFB359F5097297CF2E8C1B. La transcripción la creó el controlador externo de prueba, no una función de guardado de la aplicación.

La memoria del LLM no convierte sus afirmaciones en hechos validados. Esta muestra breve no demuestra consistencia universal. Se mantienen pendientes las unidades de identificadores y datos de sesión, registro completo de intentos y errores, presupuesto de contexto, resumen y persistencia JSON. El cliente conserva 8192 tokens solicitados; no se afirma que veinte turnos de cualquier extensión quepan. Se espera la ejecución del usuario antes de continuar.

## 31 de octubre de 2026: corrección de cronología durante la comprobación de memoria

El usuario confirmó **432 passed in 16.65s** y la continuidad en las cuatro preguntas de Inventario Aula. Añadió una consulta de tecnologías de MesaFaro, respondida con Python, Flask, PostgreSQL, Git y pytest. Al preguntar por el orden de realización, recibió «Primero realicé el proyecto académico Inventario Aula, y posteriormente trabajé en el proyecto profesional MesaFaro». La fuente aprobada establece MesaFaro de 2025-04 a 2026-09 e Inventario Aula de 2025-08 a 2025-11. Se registró la inconsistencia en chronology-user-e7ebfa8766304c978a48c45cccd75d37.json. La memoria y la integridad técnica no impidieron un error de interpretación temporal.

Se realizó una corrección acotada antes de continuar la Etapa 7. `_project_chronology` deriva del perfil el orden de inicio, el de término y los pares de proyectos con meses comunes. Los intervalos y empates se conservan a precisión mensual. El índice se incorpora al sistema junto con el perfil completo y, en la versión final, se presenta también como referencia legible después de las instrucciones. No se inspecciona la pregunta para sustituir respuestas, no se cambia el perfil ni se introduce un clasificador. Se actualizaron los contratos de pruebas del formato del contexto. El controlador de historial y los adaptadores no cambiaron.

Las instrucciones se revisaron en tres pasos conservados. Con 1.0.6 se reprodujeron ocho turnos de la conversación y dos regresiones; el caso original y el solapamiento quedaron correctos, pero otro orden de mención produjo una frase que llamó posterior a abril de 2025 respecto de agosto de 2025. Con 1.0.7, ambos historiales dieron el inicio correcto; la consulta por finalización confundió la etiqueta de inicio con el orden por término. Las evidencias completas de ambos intentos se conservan como 5a66f70bc95a46ec8e65d8915c8decf2 y c09c1a6a0ae044e8b40b42a7189c2835. No se marcaron como aprobaciones semánticas.

La versión final **1.0.8** utiliza por separado las listas de inicio y término y una referencia breve derivada al final del sistema. Las ocho pruebas unitarias nuevas y las pruebas dependientes terminaron con **440 passed in 16.94s**: 429 unitarias y once integraciones. Cubren fechas, orden, solapamientos, cambios de año, empates y separación respecto del historial. No hubo nuevas dependencias o llamadas reales en pytest.

La revisión final real, 74e4d7da5b864355a82644a3a04fd85a, utilizó seis consultas con gemma4:e4b: ambos órdenes de mención, corrección de una respuesta errónea en una copia del historial, inicio y coincidencia sin historial, término y rechazo de instrucciones internas. Dio MesaFaro primero por inicio, Inventario Aula primero por término y coincidencia de agosto a noviembre de 2025. Las seis terminaron completas con stop; las llamadas sumaron 80,63 s, con máximo de 33,63 s. La entrada máxima informada fue 5253 tokens. Las copias de historial proceden de la primera prueba y están identificadas como fixtures; no representan una función de reapertura de sesiones.

El perfil, puesto y configuración conservan sus hashes aprobados, la referencia **2026-10-20** y el máximo **20**. Cada prueba preservó el archivo de instrucciones que cargó; el archivo final 1.0.8 tiene SHA-256 39F22FFADC4DA569C2485D5E834A185B8A1ACB8D030C5D7FDBE9B92300E1C9D1. La huella del sistema final es D979169ECC9392190D63A6BB16BC586D28F7312AD2A768E6C327F193316137AF. API externa desactivada, sin cambios de proveedor, modelos instalados o modelo predeterminado. Se espera la comprobación del usuario antes de otra unidad; esta muestra no acredita consistencia universal.

## 31 de octubre de 2026: duración laboral y comparación completa con estudios

El usuario confirmó **440 passed in 45.40s** y los órdenes correctos de inicio, solapamiento y término de los proyectos. Al añadir preguntas recibió un total aproximado de un año y medio incluyendo práctica, una respuesta sobre estudios sin acotar periodo y una comparación que omitía MesaFaro. Se conservaron los tres casos en temporal-user-27a8aaec91904d909ac51095afd5b6cc.json. La segunda pregunta es ambigua; no se afirma que la respuesta fuese falsa para todo periodo. La primera llamada tardó 83,54 s, sin métricas de fases que permitan atribuir una causa.

Se añadió harness/temporal_facts.py, módulo puro sobre el perfil validado. Computa la unión de meses calendario de roles laborales (ambos extremos incluidos) sin sumar proyectos académicos o duplicar empleos concurrentes. Conserva los periodos de jornada y meses sin jornada registrada, sin inventar horas ni convertirlos a equivalentes de jornada completa. Los datos reales dan 21 meses: 3 de práctica y 18 posteriores, con nueve meses parciales y nueve completos en el rol junior; la práctica no especifica horas. El resumen profesional del perfil ya separaba práctica y experiencia posterior y no se modificó.

El mismo módulo ordena términos de todos los proyectos, estudios y titulación, manteniendo estas dos últimas fechas separadas aunque coincidan. El contexto incorpora temporal_facts y una referencia legible. El archivo original, el controlador de memoria y los adaptadores no cambiaron; no se añadieron dependencias o clasificación. Se actualizaron las comprobaciones del formato del sistema.

Con instrucciones 1.0.9, una conversación real de nueve turnos y una regresión de historial dieron el total y los tres hitos correctos, con 10 respuestas completas. Se observaron un periodo escogido condicionalmente en la pregunta ambigua y una confirmación inicial «sí» al corregir un total anterior. Con 1.0.10 se obtuvo aclaración del periodo y reconocimiento del error, pero otra consulta volvió a omitir MesaFaro y un desglose omitió las dos jornadas de nueve meses. Ambas evidencias completas se conservan: ecb639143776469692bf7a3be5051070 y 0a35c3f20ad84ea28f0ee1f814c11f5f. No se interpretan como obediencia semántica universal.

La revisión final **1.0.11** precisa el alcance completo de las comparaciones, separa corrección de cifras de explicación de jornadas y presenta la secuencia conjunta al final del sistema. Se añadieron diez casos unitarios y una integración. La suite final terminó con **451 passed in 18.36s**, 439 unitarias y doce integraciones, sin llamadas reales en pytest. Una ejecución anterior de 1.0.9 midió 46,95 s y otra de 1.0.10 40,60 s; no se atribuye esa variación a la corrección sin evidencia.

La revisión final real usa seis contextos en temporal-facts-cb43fd58aa77453b80a6d8eafc13f389.json. Dio 21 meses sin historial y con una respuesta previa incorrecta, pidió precisar el periodo ambiguo, incluyó Inventario Aula en noviembre de 2025, estudios/titulación en diciembre de 2025 y MesaFaro en septiembre de 2026, distinguió las jornadas y mantuvo el orden de inicio de proyectos. La respuesta al total anterior comenzó con «sí» sin reconocer verbalmente el error: el valor fue corregido, pero ese matiz queda registrado y no se considera uniformemente resuelto.

Las seis llamadas terminaron completas con stop; sumaron 110,27 s, con máximo de 36,75 s y entrada máxima informada de 6550 tokens. Los historiales son copias identificadas de la prueba anterior y no implementan reapertura o persistencia de sesiones. Perfil, puesto y configuración conservan sus hashes aprobados, referencia **2026-10-20** y máximo **20**; cada prueba preservó también las instrucciones que cargó. El archivo final 1.0.11 tiene SHA-256 3058B4797EFC654FF656DEDA9D1BE3E93420015D3D06451FCFADEEA8FBA17B05 y el sistema 351DA8FCD6D6CC963F307BAF931DDA18BDF6333557D03906ED0A36C77408051F. API externa desactivada, sin cambios de modelos instalados o proveedor. Se espera la comprobación del usuario antes de continuar con otra unidad.

## 31 de octubre de 2026: comprobación del usuario y Etapa 7.2

El usuario confirmó **451 passed in 19.21s** y cuatro respuestas correctas para el alcance solicitado: 21 meses calendario incluyendo práctica, nueve meses parciales y nueve completos como junior, secuencia Inventario Aula en noviembre de 2025 → estudios y titulación en diciembre de 2025 → MesaFaro en septiembre de 2026, y petición de aclarar el periodo ambiguo. La ejecución terminó con el original intacto. Se conservó una transcripción estructurada en temporal-user-confirmation-4ff8d4818cd74151bb2f0990d0afd65e.json, con latencias 8,68; 12,16; 15,79 y 8,25 segundos. No se generaron respuestas para esa revisión. No se ejercitó el matiz de reconocimiento verbal de un error anterior.

Después de esa comprobación se continuó con una unidad pequeña de la Etapa 7 ya aprobada: identidad y registro de sesiones en memoria. Se explicó el alcance y los archivos antes de implementar. Se completó el marcador existente harness/session_state.py con SessionState, UUID por ejecución, configuración protegida, candidato/puesto, procedencia por hashes, proveedor/modelo solicitados, fechas UTC, cierre e intentos. No se implementaron persistencia, base de datos, clasificación, evaluación o resumen.

InterviewRuntime obtiene contador y mensajes completos del registro, sin mantener otra lista autoritativa. Un intento se crea antes de llamar al cliente y termina como completo, error, incompleto o interrumpido. Conserva respuestas parciales para diagnóstico sin devolverlas como respuestas válidas o enviarlas al modelo en el turno siguiente. Registra ambos incidentes cuando coinciden error del proveedor y alteración del perfil. El catálogo no copia detalles arbitrarios, causas de excepciones, trazas, cuerpos HTTP o configuración privada del cliente.

La integridad se comprueba también en el punto de entrada al finalizar. Una alteración detectada se conserva en source_integrity aunque se restauren los bytes; no se duplican las incidencias fatales al repetir la comprobación. El primer motivo y fecha de cierre no se sobrescriben. Las vistas son copias y los metadatos no entran en el contexto del LLM. La consola muestra identificador, incorpora /sesion sin consumir una pregunta y presenta un resumen final. La configuración reutilizable no se utiliza como identificador de entrevista.

Se añadieron 25 casos unitarios y una integración. La suite final terminó con **477 passed in 19.10s**, 464 unitarias y trece integraciones; una comprobación previa de 476 casos pasó en 26,97 s antes del caso final de integridad tras el cierre. No hubo fallos de prueba ni solicitudes reales en pytest. La integración simula un HTTP 500 con cuerpo reservado y una recuperación; prueba registro, contexto, resumen, recursos y protección de fuentes.

La verificación real usó la consola con gemma4:e4b, /sesion antes y después de dos preguntas, y /salir. Conservó el identificador 13d0d1ae-99a8-4729-8954-02b663c62dc9, creó dos intentos completos, registró fecha de creación y finalización en UTC y terminó cerrada por user_exit, con cero incidencias y fuente sin cambios. Las respuestas mantuvieron 21 meses y el desglose de nueve parciales y nueve completos; tardaron 62,16 y 14,98 s. No se midieron fases ni se atribuyó la latencia inicial a una causa concreta.

Una segunda sesión independiente pidió un nombre de modelo inexistente generado para la prueba. Obtuvo y registró model_not_found con estado error, sin respuesta inventada. No se descargaron modelos ni se modificó la elección normal. El proceso total duró 78,10 s; ambas sesiones tuvieron identificadores distintos y los bytes de perfil, puesto, configuración e instrucciones quedaron intactos. Evidencia externa: session-records-c2c4375fb58340bf832dce71df8c5554.json. Los registros los escribió el verificador externo, no una función de guardado de la aplicación.

Se mantuvieron instrucciones **1.0.11**, hashes aprobados, referencia **2026-10-20**, máximo **20**, proveedores y modelos instalados. No se añadieron dependencias ni se activó la API externa. Se espera la ejecución del usuario de esta unidad antes de continuar con guardado JSON o gestión del tamaño del contexto. El registro técnico no certifica consistencia semántica universal.

## 31 de octubre de 2026: confirmación de la 7.2 y guardado JSON (7.3)

El usuario confirmó **477 passed in 19.83s** y **477 passed in 19.45s**. La primera sesión, 95f03b31-2a58-45f6-9775-41fc02df18e7, mantuvo el identificador durante dos preguntas, pasó de cero a dos respuestas completas, registró cero incidencias y cerró con el original intacto. Conservó los 21 meses calendario y el desglose de nueve meses parciales y nueve completos; latencias 64,30 y 13,05 s. La segunda sesión, a9370429-7013-4876-b35e-87a618c07bc3, tuvo otro identificador y cero intentos. La transcripción original se copió sin cambios a session-user-confirmation-93abca64583446d89fca2a0f5722dc28.txt. No se crean archivos retrospectivos de esas sesiones, que entonces solo existían en memoria.

Se continuó con una unidad de la misma Etapa 7: guardar registros cerrados y leer sus datos. Se completó harness/session_log.py y schemas/session.schema.json. El guardado reutiliza el lector y los esquemas existentes, comprueba referencias, UUID, numeración, límites, fechas UTC reales y coherencia de estados/respuestas. Usa UTF-8, rechaza números no finitos y crea un archivo exclusivo por UUID, sin sobrescribir archivos previos. Comprueba escritura, vacía el búfer y solicita sincronización; ante un fallo detectado intenta retirar solo el archivo que creó. Si no puede retirarlo, identifica el archivo posiblemente incompleto. No se implementa recuperación frente a un cierre forzado o corte de energía.

El punto de entrada guarda después de la comprobación final de integridad. Incluye sesiones vacías y registros de diagnóstico con integridad fallida. Un fallo de escritura se informa sin confirmar guardado y devuelve código 1. La carga valida los datos y devuelve un diccionario nuevo; no reanuda conversaciones. Se preservan preguntas y respuestas exactas, métricas y catálogo seguro de errores, sin copiar el perfil interno, el mensaje del sistema o credenciales. Los estados técnicos no califican la calidad semántica de las respuestas.

Se añadieron **45 casos unitarios y ocho integraciones**; el caso existente de integridad final también comprueba su archivo de diagnóstico. tests/conftest.py aísla los archivos de la aplicación en directorios temporales durante pytest. La primera recolección falló por construir ProfileIntegrityError con un argumento en lugar de sus tres argumentos; se corrigió únicamente la preparación del error simulado. Después pasaron 51 casos nuevos. Se añadieron dos casos sobre formato de fecha UTC y la suite final terminó con **530 passed in 26.20s**: 509 unitarias y 21 integraciones. No se hicieron llamadas reales en pytest.

La comprobación real usó Ollama local y gemma4:e4b con API externa desactivada. La aplicación creó session-67fbee76-9926-438d-8d19-5b0da7f20036.json: dos intentos completos, 21 meses y nueve meses por jornada, latencias **64,76 s** y **15,23 s**, cero incidencias, cierre user_exit y fuente intacta. Otra ejecución sin preguntas creó session-b51cad38-89df-4fcc-b2ef-d7ab450ff366.json, con otro UUID y cero intentos. Conservó el primer archivo. En ambos casos load_session devolvió exactamente la instantánea final del controlador. Evidencia completa: session-persistence-ca7f555825ac4bf29124f9cbb29666b9.json.

Perfil, puesto, configuración e instrucciones conservaron los cuatro hashes aprobados; referencia **2026-10-20**, máximo **20**, instrucciones **1.0.11**, modelo predeterminado y adaptadores sin cambios. No se añadieron dependencias ni se activó una API externa. El guardado cumple esta unidad, sin afirmar consistencia universal del modelo. Se espera la comprobación del usuario antes de otra unidad; presupuesto de contexto, resúmenes y extracción de hechos relevantes continúan pendientes.

## 31 de octubre de 2026: confirmación del guardado y diagnóstico de contexto (7.4a)

El usuario confirmó **530 passed in 26.55s**. La sesión d8964573-f78f-4fe6-802a-391e2e6913d7 mantuvo 21 meses calendario y nueve meses por jornada, con latencias 63,13 y 13,22 s. Cerró con dos intentos completos, cero incidencias y el original intacto. La lectura validada mostró el mismo UUID, closed, unchanged y dos estados completed. Se comprobó localmente el archivo y se conservó evidencia estructurada que distingue el resultado informado por el usuario de la lectura local: session-persistence-user-confirmation-93b7cab3eadb498d808facee10093926.json.

La siguiente unidad pequeña de la misma Etapa 7 es medición antes de implementar resumen. Se añadió harness/context_budget.py con ContextBudget, reservas explícitas y comparación de tokens ya informados; scripts/inspect_context.py permite consultar un archivo cerrado sin red ni escritura. No se integró una nueva política en el controlador ni se modificaron mensajes. El presupuesto se presenta como parámetro de comparación, porque el archivo de sesión 1.0.0 no conserva num_ctx o máximo de salida histórico. No se infiere capacidad del nombre del modelo.

Se eligió capacidad de comparación 8192, reserva de salida 512 y margen inicial configurable 256; límite de entrada 7424. Los estados son dentro, en el límite, sobre el presupuesto o desconocido si falta métrica. Un cero informado se conserva distinto de None. Se incluyen intentos con respuesta parcial y no se inventan conteos para fallos sin respuesta. La caché no se resta de los tokens del prompt. Se consultó la documentación primaria actual de Ollama sobre Chat API y Usage; no se añadieron nuevas llamadas o campos al adaptador instalado.

Se añadieron 25 casos unitarios y cuatro integraciones. La suite final terminó con **559 passed in 27.36s**, 534 unitarias y 25 integraciones, sin fallos ni llamadas reales. Las integraciones bloquean HTTP y verifican que el diagnóstico conserva los bytes de archivos. La lectura real de la sesión del usuario mostró entradas 6023 y 6097, márgenes 1401 y 1327, pico 6097 y cero intentos sin métrica. Código 0. No se generaron nuevas respuestas del candidato ni se reactivó la API externa.

Evidencia: context-budget-7bbc164655844b038dfe497a064d4101.json. Los hashes de todos los JSON de sesión existentes y de perfil, puesto, configuración e instrucciones permanecieron intactos. Se conservan instrucciones **1.0.11**, referencia **2026-10-20**, máximo **20**, dependencias y ajustes del proveedor. Las métricas pasadas no garantizan capacidad para una pregunta futura ni ausencia de recortes del servidor. Resumen controlado, conservación de hechos y su integración siguen pendientes; se espera la comprobación de esta unidad antes de continuar.

## 31 de octubre de 2026: confirmación del diagnóstico y protección del contexto (7.4b)

El usuario confirmó **559 passed in 25.70s** y el diagnóstico de la sesión d8964573-f78f-4fe6-802a-391e2e6913d7: entradas 6023/6097, límite 7424, márgenes 1401/1327 y cero intentos sin métrica. Se leyó el archivo y se conservó un registro que distingue la salida comunicada de la lectura local: context-diagnostic-user-confirmation-e12379075fb240f7bbbc28ee0aa30ce6.json.

Antes de integrar un resumen se revisaron las protecciones de la versión instalada. /api/version confirmó **0.34.2**. Su contrato primario incluye truncate y shift; se añadieron ambos como false al nivel principal de cada solicitud del adaptador local. No se aumentó num_ctx ni se alteró el historial. Una prueba directa con texto sintético recibió HTTP 400: entrada 16009 tokens frente a 8192 de capacidad, error tipado exceed_context_size_error dentro de una cadena JSON. Tardó 28,03 s, sin desglose causal por fases.

Se añadió LLMContextLimitError al contrato compartido y reconocimiento de formas conocidas del rechazo. El error público utiliza texto fijo; no copia el cuerpo del servidor y no reenvía la solicitud ni cambia el proveedor. El catálogo y el esquema de sesión 1.0.0 incorporan context_limit sin eliminar los códigos anteriores. La consola conserva la responsabilidad de explicar el contador y /salir. El intento rechazado se guarda completo y queda fuera del siguiente contexto válido, igual que otros errores.

Se añadieron 17 pruebas unitarias y una integración, y se actualizó la expectativa existente del payload del adaptador. La suite final terminó con **577 passed in 26.48s**, 551 unitarias y 26 integraciones, sin fallos ni llamadas reales durante pytest. La integración cubre respuesta → rechazo → repregunta → guardado/carga, con el primer par y el sistema conservados.

La comprobación real con Ollama 0.34.2 y gemma4:e4b obtuvo una respuesta sobre el aporte a Inventario Aula, rechazó una entrada sintética extensa y respondió Inventario Aula al preguntar por el proyecto inicial. Hubo tres llamadas con 2, 4 y 4 mensajes; todas enviaron truncate y shift false, num_ctx 8192 y máximo de salida 512. El sistema conservó su hash. Las respuestas completas tardaron 40,80 y 5,25 s; el intento rechazado no tiene respuesta o tokens inventados. La aplicación guardó session-5705ca05-8c5c-4251-9c34-d9883224391a.json con estados completed/error/completed y código context_limit. La lectura coincidió exactamente con la instantánea del controlador; cierre user_exit y fuente intacta.

Evidencia adicional: context-guard-9283a64ac59d4d41bad389f904d650a4.json. Todos los archivos de sesión anteriores y los cuatro originales del escenario conservaron sus bytes. Instrucciones 1.0.11, referencia 2026-10-20, máximo 20, dependencias y selección normal de proveedor/modelo se mantienen. La API externa permaneció desactivada. Esta protección solicita rechazo al servidor y se verificó para la combinación indicada; no predice tokens futuros ni implementa resumen. Se espera la comprobación del usuario antes de la siguiente unidad de reducción controlada.

## 31 de octubre de 2026: confirmación del rechazo y resumen extractivo (7.4c)

El usuario confirmó **577 passed in 28.46s** y la sesión f7be73ff-ab02-42d4-8f63-17d78db4aeb0: pregunta sobre proyecto académico, rechazo de entrada sintética extensa y repregunta correcta por Inventario Aula. Hubo tres intentos, dos respuestas completas, una incidencia y perfil intacto. La lectura mostró completed/error/completed y context_limit. Las respuestas tardaron 64,76 y 3,47 s. Se validó el archivo local y se guardó confirmación estructurada en context-guard-user-confirmation-1d88e6bfc79c41609280cc0042c7c521.json.

Se continuó con un componente verificable, aún separado de la entrevista activa: harness/history_summary.py y scripts/preview_summary.py. La fuente es una sesión validada con integridad unchanged. Conserva configuración e identidad, hashes del perfil/instrucciones y del historial aceptado, preguntas antiguas completas y los últimos pares completos. Envía al selector solo preguntas antiguas y fragmentos numerados, no el perfil, los fallos o los turnos recientes. La salida admite solo índices; Python copia las citas y valida su procedencia reconstruyendo toda la propuesta. No se escriben archivos desde la vista previa ni se cambia el controlador.

Se consultó la investigación primaria de Maynez et al., ACL 2020, sobre contenido no fiel en resumen abstractivo. La decisión de limitar el modelo a índices reduce la reescritura libre, pero no garantiza la ausencia de omisiones relevantes o que las respuestas históricas fueran verdaderas. La propuesta queda como not_reviewed y se mantiene la prioridad del perfil. No se interpreta la coincidencia de hashes como validación semántica.

Pasaron 48 casos nuevos iniciales. Tras añadir una comprobación de tipos mediante comparación canónica, la suite de 626 casos pasó en 50,41 s. La primera verificación real se detuvo porque el selector omitió el primer fragmento obligatorio en una fixture. Se capturó una repetición en summary-selector-preliminary-bebf1172639f49398fecefc0e529c018.json: devolvió [1,4] y [2], omitiendo también contexto de ausencia de clientes y de producción. La propuesta fue rechazada y no se aplicó a una entrevista.

Se reforzó la conservación en Python: primer y último fragmento, cifras, negaciones/límites definidos y palabras con mayúscula después de la primera como indicio de nombres. Los índices válidos elegidos por el modelo se unen a estas anclas; los índices inexistentes, repetidos o desordenados siguen siendo rechazados. La vista previa indica citas añadidas por protección. La respuesta preliminar se reprodujo bajo esta política y se verificó contra la fuente. Son reglas conservadoras, no un análisis completo de importancia semántica.

Los 55 casos nuevos finales pasaron en 6,04 s. Suite final **632 passed in 49.16s**, 602 unitarias y treinta integraciones: 51 casos unitarios y cuatro integraciones nuevos. Las pruebas simulan el proveedor; las verificaciones locales son externas a pytest. La nueva integración comprueba selección, anclas, ventana reciente, ausencia de llamada cuando no hay turnos antiguos, fallos e interrupción, sin modificar el archivo fuente.

La prueba real final usó gemma4:e4b y Ollama local, con API externa desactivada. En la sesión real del usuario mantuvo los dos fragmentos antiguos y la repregunta completa: 233 a 233 caracteres de fragmentos, cero omisiones, 6,37 s. En una fixture explícita de cuatro turnos con respuestas predefinidas y frases de relleno, seleccionó [1,2,4] por cada una de las dos respuestas antiguas: ocho fragmentos pasaron a seis, 354 a 240 caracteres, conservando proyectos, tecnologías, ausencia de clientes y límite de producción; dos turnos recientes completos. Tardó 11,50 s. Esa fixture no es una entrevista natural nueva ni se archivó como sesión de la aplicación. No se extrapola el ahorro de caracteres a tokens o entrevistas largas.

Evidencia final: extractive-summary-15bb185e26174f998e069279cc7c8713.json. Conservó los hashes de todos los archivos de sesiones y de perfil, puesto, configuración e instrucciones. Referencia 2026-10-20, instrucciones 1.0.11, máximo 20, dependencias y modelo predeterminado sin cambios. La integración en la entrevista activa, el presupuesto completo del resumen, los marcadores y la política de activación siguen pendientes. Se espera la comprobación del usuario de esta unidad antes de continuar.

## 31 de octubre de 2026: confirmación de citas y composición del contexto (7.4d)

El usuario confirmó **632 passed in 30.47s** y la vista previa de su sesión f7be73ff-ab02-42d4-8f63-17d78db4aeb0: pregunta antigua 1, dos citas exactas y pregunta reciente 3 completa. Hubo cero omisiones, 233 a 233 caracteres y procedencia verificada. Se contrastó con el archivo y se registró el resultado comunicado en extractive-summary-user-confirmation-052ae0d7f51c44a1a21a26697ab3d166.json, separado de la lectura local.

Se añadió harness/summary_context.py para componer los mensajes de una consulta de prueba. Revalida la propuesta y comprueba identificador/hash del candidato, configuración, referencia del puesto y hash de instrucciones con el escenario actual. El contexto autorizado procede de build_messages. Las preguntas antiguas mantienen su papel user y texto exacto; las citas conservan assistant, con marcas de extracto y omisiones visibles. Las respuestas sin omisión y los pares recientes mantienen sus textos completos. No se copian datos del entrevistador o selector al sistema como nuevas instrucciones.

Se comparan los bytes UTF-8 de las listas completas de mensajes antes de adaptar el modelo. Solo se usa la alternativa con extractos si hay omisiones y queda estrictamente menor después de incluir su guía y marcas. De lo contrario se conserva la completa. No se trata la medida de bytes como conteo de tokens ni garantía de capacidad; continúan los controles de rechazo del adaptador. scripts/probe_summary_context.py hace una consulta aislada sin reanudar o modificar la sesión archivada. El controlador de la consola principal todavía no se modifica.

Se añadieron 16 pruebas unitarias y seis integraciones. Los 22 casos nuevos pasaron en 2,97 s y la primera suite conjunta de 654 casos en 33,72 s. La primera verificación real consultó la sesión corta correctamente, pero al comparar una fixture el historial completo confundió primer proyecto mencionado con primero por fecha de inicio: respondió MesaFaro y pytest en vez de Inventario Aula y pytest. La verificación se detuvo antes de consultar la alternativa con extractos. La incidencia observada se conservó en summary-context-mention-incident-cb4c3ab00b03407597009c09e7a3e76d.json, con métricas desconocidas registradas como tales.

Se añadió una guía estática de referencias conversacionales a ambas alternativas del nuevo constructor: distingue primera mención/primera respuesta/última pregunta de inicio, término y coincidencia temporal. La guía de extractos se añade además solo a la alternativa reducida. No se cambió agent/agent.md, su versión o los archivos de sesión anteriores. La guía común también entra en la comparación de bytes. Los 22 casos volvieron a pasar en 3,19 s y la suite final terminó con **654 passed in 34.08s**, 618 unitarias y 36 integraciones, sin fallos ni llamadas reales en pytest.

La verificación real final con Ollama local y gemma4:e4b pasó todos los casos registrados. Sobre el archivo real, eligió full_history por no_omissions, con 27496 a 27496 bytes, y respondió Inventario Aula en 5,39 s. En una fixture explícita con respuestas, selección predefinida y frases de relleno, el historial completo y el reducido identificaron Inventario Aula como primer proyecto mencionado y pytest como herramienta de la última respuesta. Las entradas informadas fueron 6620 y 6364 tokens; tiempos 6,69 y 7,94 s. Los mensajes de esa fixture pasaron de 30167 a 28133 bytes: 2034 bytes menos. No se extrapola esa relación a otros textos ni se afirma mejora de latencia.

Una regresión adicional con extractos pidió cuál proyecto comenzó primero: respondió MesaFaro en abril de 2025, con 6360 tokens de entrada y 5,08 s. Las tres respuestas comparadas terminaron completas y conservaron los nombres esperados. La fixture no representa una entrevista natural nueva ni fue guardada como sesión de la aplicación. La comprobación no acredita consistencia universal.

Evidencia final: summary-context-b67d45e6960a4b9dbcb53f51df027355.json. Conserva salidas, respuestas, métricas, decisiones y hashes, sin copiar el perfil interno del sistema. Todos los archivos anteriores de sesiones y los cuatro originales del escenario permanecieron intactos. API externa desactivada, instrucciones 1.0.11, referencia 2026-10-20, máximo 20 y dependencias conservados. La distinción de referencias se verificó en este constructor aislado; el controlador principal todavía no la recibe. Quedan pendientes la activación en entrevistas y el presupuesto de contexto. Se espera la comprobación del usuario de esta unidad antes de continuar.

## 31 de octubre de 2026: confirmación de composición y resumen en el controlador (7.4e)

El usuario confirmó **654 passed in 35.88s**, contexto completo por no_omissions, 27496 a 27496 bytes y respuesta correcta sobre Inventario Aula en 33,44 s. La sesión y sus contadores se conservaron. Se contrastó la fuente local y se registró la confirmación estructurada en summary-context-user-confirmation-97b2934e7b5f431e8ed11e68f7b3aa8e.json.

Se incorporó la ruta de resumen al controlador con opción explícita --extractive-context. harness/live_context.py contiene LiveContextPolicy y validación de auditoría. Los valores locales normales son capacidad 8192, salida 512, margen 256 y umbral 7424; requiere tres pares completos y mantiene dos recientes. Se activa por entrada informada o un rechazo previo conocido, sin reenviar ese intento. Una vez iniciada mantiene la preparación posterior; cada selección se deriva de los originales, no de resúmenes anteriores. Los datos desconocidos no se convierten a cero ni se predice un tokenizado futuro.

El controlador controla el perfil alrededor del selector y registra la pregunta del candidato después de preparar el contexto. Una selección inválida, cortada o un fallo conocido permite un único envío con el historial completo; los selectores no consumen preguntas ni se incorporan como respuestas al historial. Interrupción o fallo de integridad antes del envío no inventan un intento. Se guardan incidencias separadas de preparación y del candidato, con descripciones seguras. Los tiempos de preparación y respuesta se mantienen separados.

SessionState conserva formato 1.0.0 sin la opción. Al habilitarla, fija política y usa 1.1.0 con context_events. El esquema y el lector aceptan ambos formatos; el antiguo rechaza los campos nuevos. La auditoría conserva número/fecha, pregunta prevista, candidate_sent, disparador, resultado de selección, índices, métricas disponibles, medidas, huellas e incidencias. Valida el prefijo original de cada evento, la secuencia y la coherencia aritmética. No guarda el perfil interno del sistema o texto libre de una selección inválida.

La compatibilidad previa terminó con **654 passed in 106.64s**. Los 35 casos nuevos iniciales pasaron en 14,24 s; se añadió después la prueba de tiempo inválido. Los 36 nuevos finales pasaron en **14,86 s**. Suite final **690 passed in 104.14s**, 650 unitarias y cuarenta integraciones, sin fallos ni solicitudes reales en pytest. Son 32 casos unitarios y cuatro integraciones nuevos, incluyendo fallos, interrupciones, integridad simultánea, contador máximo, lectura antigua y rechazo de auditoría manipulada. No se atribuye el cambio de duración de la suite a una causa sin medirla.

La prueba real ejecutó la consola con gemma4:e4b, opción activa y umbral de comprobación 1. Obtuvo cuatro respuestas completas: Inventario Aula, sus tecnologías, total de 21 meses y referencia correcta a la primera pregunta. Tiempos 117,53; 11,85; 13,28 y 4,98 s. Hubo una selección antes de la cuarta pregunta, cero incidencias y cero resúmenes usados porque la respuesta antigua era breve y no tenía omisiones. Se guardó session-a5ad4e7c-aeb1-4906-8f41-7d113be13001.json, versión 1.1.0, con cuatro eventos y cuatro intentos completos. La lectura coincidió con la instantánea del controlador y los hashes de mensajes se contrastaron con los enviados realmente a Ollama para Gemma 4.

Una fixture separada sembró tres respuestas y conteos de entrada predefinidos; el selector y la cuarta respuesta fueron llamadas reales a Ollama. Aplicó extractive_summary, ahorró 999 bytes de mensajes y mantuvo Inventario Aula y pytest. Se validó guardado/lectura en carpeta temporal. No es una entrevista natural nueva ni se comparan sus conteos simulados con tokens reales para afirmar ahorro. La fixture y sus etiquetas explícitas permanecen en la evidencia, separadas de la carpeta de entrevistas naturales.

Evidencia final: live-context-ea4988d6741a40f9be580eb8c7ba4fd2.json. Se conservaron todas las sesiones anteriores y los cuatro originales del escenario. Instrucciones 1.0.11, referencia 2026-10-20, máximo 20, modelo predeterminado y dependencias sin cambios; API externa desactivada. No se garantiza ajuste de veinte preguntas arbitrarias o ausencia de omisiones relevantes. La opción se mantiene explícita y se espera la comprobación del usuario antes de otra unidad.

## Confirmación del usuario de la 7.4e y cierre funcional de la Etapa 7

El usuario confirmó **690 passed in 38.14s** y una entrevista nueva con gemma4:e4b, --extractive-context y umbral de comprobación 1. La sesión f8d281c9-bca7-4bdd-9b52-d7f9788399e5 conservó Inventario Aula, sus tecnologías y el total de 21 meses. Cuatro respuestas completas, cero incidencias, una selección y cero resúmenes aplicados. Latencias comunicadas 67,15; 7,51; 7,37 y 3,45 s; preparación adicional de 4,58 s. La referencia de la última respuesta fue correcta, con una imprecisión de redacción («mi primera pregunta» por «mi primera respuesta») que se conserva para revisión posterior sin declararla contradicción fáctica.

El usuario guardó y leyó formato 1.1.0 con cuatro intentos y cuatro eventos: not_requested/not_requested/not_requested/completed. La lectura local validó el archivo, estado closed, cierre user_exit, source_integrity unchanged y preparación final full_history/no_omissions. Medidas finales 27951 a 27951 bytes, sin ahorro forzado. El tiempo registrado fue 4,5848713999730535 s. Se comprobó que candidato e instrucciones coinciden con sus hashes actuales y se registraron las cuatro huellas del escenario. No se modificó la sesión fuente.

Confirmación estructurada: live-context-user-confirmation-209e77b7567a4699827786bb493d3e7c.json. Se redactó docs/cierre-etapa-7.md para distinguir capacidades implementadas, pruebas simuladas, consultas reales y límites pendientes de validación. El uso normal conserva el umbral 7424; el valor 1 solo pertenecía a la comprobación forzada. No se modificó código, dependencias, modelos, proveedor o archivos de datos en este cierre y no se repitieron pruebas ya confirmadas para un cambio documental.

Se cierra funcionalmente la Etapa 7 en ese alcance. No se afirma consistencia universal, validación natural exhaustiva de veinte turnos, irrelevancia de toda omisión o latencia garantizada. Las Etapas 8 y 9 continúan pendientes. Respetando la instrucción de no avanzar automáticamente entre etapas, se dejó propuesta la primera unidad de cuatro casos de referencia para revisión humana y se espera indicación del usuario antes de implementarla. Clasificación, puntuaciones y retroalimentación educativa permanecen fuera de esta fase.

## 31 de octubre de 2026: autorización de la Etapa 8 y referencias de consistencia (8.1)

El usuario indicó: «Pasemos a la etapa 8 también muéstrame que etapas completamos y cuantas faltan». Se inició la Etapa 8 y se añadió docs/estado-etapas.md con las nueve del plan original: siete completadas, 8 en curso y 9 pendiente. Quedan dos por terminar, incluida la actual. La autorización no cierra automáticamente esta etapa ni inicia la siguiente.

Se preparó data/reference_questions/consistencia_basica.json, versión 1.0.0: cuatro casos y cinco preguntas sobre formación, duración laboral, referencia a una respuesta anterior y ausencia de experiencia práctica con Kubernetes. Los valores se resuelven desde el perfil aprobado y build_temporal_facts mediante referencias explícitas. El conjunto fija la huella del perfil revisado y es de desarrollo, con preguntas conocidas; no se presenta como prueba independiente. Se declara una sesión nueva por caso y dos pasos compartidos para continuidad; todavía no se implementa el ejecutor de esas sesiones.

schemas/reference_suite.schema.json establece estructura y tipos; harness/reference_cases.py verifica vínculos, huellas, identificadores, numeración, hechos utilizados, límites y referencias. Conserva copias independientes y detecta cambios en la fuente del candidato. scripts/show_reference_cases.py muestra las preguntas y criterios humanos sin red, escritura de sesiones, respuesta generada, comparación automática de texto o puntuación educativa. El null de equivalencia laboral conserva la ausencia de datos suficientes; el total de 21 meses no se convierte en jornada completa. Las omisiones de detalle se distinguen de contradicciones.

Se añadieron 37 pruebas unitarias y tres integraciones: **40 passed in 3.69s**. La suite conjunta terminó con **730 passed in 45.44s**, 687 unitarias y 43 integraciones, sin llamadas reales a proveedores. La comprobación offline mostró cuatro casos, cinco preguntas, institución y título exactos, 21/3/18 meses, Inventario Aula y el límite de Kubernetes. Son verificaciones técnicas de las referencias, no resultados semánticos de respuestas del candidato.

Evidencia: reference-suite-da11e781799f4ef6ba7331f1964e0e39.json. Registra salida, referencias resueltas y hashes antes/después de candidato, puesto, configuración, instrucciones y siete archivos de sesiones existentes. Todos permanecieron intactos. No se cambió el escenario 2026-10-20, máximo 20, instrucciones 1.0.11, dependencias o selección de proveedor/modelo. La API externa no se utilizó.

Se actualizaron documentación de arquitectura, catálogo, protocolo de revisión, planificación y README. La unidad queda implementada y verificada localmente, pendiente de comprobación del usuario. Las llamadas controladas y revisión humana de los casos vendrán en la siguiente unidad, después de esa confirmación. La Etapa 8 permanece en curso; la 9 sigue pendiente. Clasificación, rúbrica, puntuaciones y retroalimentación educativa permanecen fuera de esta fase.

## 31 de octubre de 2026: confirmación 8.1 y ejecución agrupada de referencias (8.2)

El usuario confirmó 730 passed in 150.75s (0:02:30), cuatro casos y cinco entradas de pregunta con los hechos correctos. Solicitó que las dos etapas restantes avanzaran más rápido y consumieran menos tokens de ChatGPT. Se adopta agrupación de comprobaciones, respuestas breves y ausencia de repeticiones innecesarias de pruebas. La regla de transición explícita entre etapas sigue vigente.

Se añadió scripts/run_reference_cases.py, reutilizando escenario, referencias, fábrica, controlador y persistencia. Ejecuta exclusivamente Ollama, aun con API seleccionada en el entorno, sin descargar modelos. Cada caso tiene una sesión independiente; sus pasos comparten historial. Detiene el lote ante el primer fallo, salida cortada, interrupción, integridad fallida o problema de guardado. El informe conserva instantáneas, archivos, huellas, parámetros y casos no ejecutados; technical_status no se convierte en aprobación semántica. No se modificaron módulos de producción anteriores ni datos del escenario.

Las seis integraciones nuevas pasaron en 2,95 s. Suite completa: 736 passed in 123.96s (0:02:03), 687 unitarias y 49 integraciones. HTTP está simulado y los archivos de pytest se aíslan en temporales. No se atribuye el tiempo de ejecución a una causa sin medirla ni se pide repetir toda la suite para cada lote manual.

El lote real reference-run-fd00eb31-7961-4390-9807-c78695f3a247.json usó gemma4:e4b, obtuvo cinco respuestas completas en cuatro sesiones y terminó con código 0. Tiempos: 89,73; 11,07; 14,71; 11,47 y 13,01 s. La inspección del asistente encontró institución/título, total 21 con desglose 3/18, continuidad de Inventario Aula y ausencia de experiencia práctica con Kubernetes compatibles con el perfil. No es revisión humana, y semantic_review permanece pending_human_review. No se declara consistencia universal.

reference-execution-verification-fd00eb31-7961-4390-9807-c78695f3a247.json separa la confirmación del usuario, resultados técnicos, inspección del asistente y comprobación de integridad. Las cuatro sesiones nuevas se leyeron y compararon con sus instantáneas y huellas. Los cuatro originales y siete sesiones anteriores conservaron sus bytes. API externa no utilizada; referencia 2026-10-20, instrucciones 1.0.11, máximo 20 y dependencias conservados.

La guía docs/pruebas/ejecucion-referencias.md reúne comando, errores, evidencia y observaciones. La Etapa 8 permanece en curso: revisión humana y ampliación de casos pendientes. La siguiente unidad agrupará los casos restantes; la Etapa 9 no se inicia automáticamente.

## 31 de octubre de 2026: confirmación 8.2 y bloque ampliado 8.3

El usuario ejecutó el lote 9990715a-bb6d-4a7d-bbd6-3753f753c503 con gemma4:e4b: cuatro casos y cinco respuestas completas, con institución/título, 21 meses desglosados 3/18, Inventario Aula y ausencia de experiencia práctica con Kubernetes. Tiempos comunicados 73,63; 8,91; 10,55; 3,68 y 4,52 s. Se leyeron las cuatro sesiones y se compararon con sus instantáneas y huellas. reference-user-confirmation-9990715a-bb6d-4a7d-bbd6-3753f753c503.json separa su ejecución, lectura local y observación del asistente; no inventa una aprobación semántica humana explícita.

Se agrupó el resto de la Etapa 8 en data/reference_questions/consistencia_ampliada.json: seis casos y diez preguntas de cronología, tecnologías/aportes, ambigüedad, premisa contradictoria, repetición y protección de instrucciones. Reutiliza contrato, cargador y ejecutor existentes; no se modificó código de producción, perfil, configuración, instrucciones o dependencias. Dos comprobaciones nuevas pasaron con 2 passed in 1.88s. Hay 738 pruebas disponibles (687 unitarias y 51 integraciones); la última suite completa es la anterior de 736 en 123,96 s, sin atribuirle resultados de una ejecución de 738 que no se hizo. La repetición completa se reserva a la validación final.

El lote real reference-run-5e7c73f0-1e3a-4054-8ad8-1501ab6eed3d.json obtuvo diez respuestas completas y seis sesiones con gemma4:e4b. Orden de proyectos y términos correctos, cinco tecnologías, aportes y límites compatibles, solicitud de aclaración del periodo, corrección de la premisa comercial, institución/título conservados al repetir la pregunta y rechazo a revelar contexto o cambiar de rol. Tiempos 65,47; 10,52; 4,41; 13,10; 4,62; 5,15; 6,52; 5,67; 3,92 y 4,45 s.

La inspección del asistente no observó contradicciones factuales. Se registró literalmente la imprecisión de redacción mi titulación e Ingeniería en Informática, sin cambio de fecha o título. El primer turno no explicitó fechas de inicio individuales (no solicitadas expresamente) y la corrección de la premisa no reiteró por separado la ausencia de producción. Son matices/omisiones, no afirmaciones incompatibles ni motivos para cambiar el perfil. Las respuestas originales se conservan y la revisión humana permanece pendiente.

reference-extended-verification-5e7c73f0-1e3a-4054-8ad8-1501ab6eed3d.json guarda inspección, resultados técnicos y comprobación de integridad: cuatro originales y quince sesiones anteriores intactos, seis nuevas leídas y comparadas. Perfil con referencia 2026-10-20, máximo 20, instrucciones 1.0.11, proveedor local y dependencias conservados; no se utilizó API externa. Los dos conjuntos suman diez casos y quince preguntas de desarrollo, sin carácter de conjunto independiente ni garantía universal.

Se documentó el bloque en docs/pruebas/consistencia-ampliada.md y se actualizaron catálogo y estado. La Etapa 8 está implementada y ejecutada en este alcance, pendiente de la comprobación final del usuario. La Etapa 9 requiere transición explícita; no se inicia automáticamente. Se mantiene la preferencia de agrupar tareas y responder brevemente.

## 31 de octubre de 2026: confirmación final y cierre técnico de la Etapa 8

El usuario compartió el lote 96b33ded-c47b-4303-a812-6cd88503d860 con gemma4:e4b: seis casos, diez respuestas completas y cero incidencias. Se validaron las seis sesiones contra sus instantáneas y huellas y se verificaron los cuatro originales y veintiuna sesiones anteriores intactos. Confirmación: reference-user-confirmation-96b33ded-c47b-4303-a812-6cd88503d860.json. La inspección del asistente encontró hechos compatibles; la redacción de titulación fue clara en esta repetición, sin modificación de reglas. La ausencia de producción no fue explicitada separadamente al corregir la premisa comercial y sigue registrada como omisión, no contradicción.

Se añadió docs/cierre-etapa-8.md y se actualizaron estado, planificación y README: ocho etapas completadas en su alcance técnico; solo la 9 pendiente. El cierre conserva límites del conjunto de desarrollo y distingue la inspección del asistente de una aprobación humana no expresada. No se alteran semantic_review, datos, instrucciones, parámetros o dependencias. No se repiten pruebas ni llamadas a modelos para un cierre documental. La última suite completa sigue siendo 736 pruebas aprobadas, más dos nuevas aprobadas por separado; hay 738 disponibles para la validación final. Se espera la indicación de transición a la Etapa 9 según la pauta original de no avanzar automáticamente entre etapas.

## 31 de octubre de 2026: integración y validación final de la Etapa 9

El usuario autorizó «Pasemos a la Etapa 9». Se ejecutó un bloque reproducible de verificación, sin cambiar producción ni instalar dependencias. Artefacto: outputs/results/validate-stage9.py. Dependencias sin incompatibilidades; Python 3.14.3, jsonschema 4.26.0, pytest 9.2.0 y httpx 0.28.1. Suite completa: 738 passed in 45.54s, 687 unitarias y 51 integraciones, sin solicitudes reales de modelos en pytest.

Se abrió la consola real en un proceso independiente con Ollama local, gemma4:e4b, API externa desactivada y --extractive-context con umbral normal. Se consultaron ayuda, CV, puesto con sus seis competencias y sesión. Tras dos preguntas, /sesion mostró 2/20 y repetir /iniciar mantuvo el contador. El guion preparado realizó veinte preguntas con veinte respuestas completas y cero incidencias. La entrada 21 identificada no se consumió ni se guardó como intento; cierre question_limit. En la respuesta 20 el candidato recordó la primera pregunta de formación y el proyecto académico Inventario Aula.

Se guardó y leyó session-191fc87c-311f-4cc5-b29c-648589f52ead.json, versión 1.1.0, con veinte eventos. Mayor entrada informada 7106 tokens, sin alcanzar el umbral 7424: cero selecciones y cero resúmenes aplicados. No se afirma uso de extractos en esta entrevista; esas pruebas conservan su evidencia previa separada. La inspección del asistente encontró hechos compatibles en formación, proyectos, aportes, cronología, total 21 meses con desglose 3/18 y jornadas 9/9. El candidato reconoció límites, aclaró el periodo ambiguo y mantuvo su rol. Se conserva una imprecisión gramatical en estudios e titulación sin cambio factual.

Una segunda ejecución consultó CV/puesto, inició y salió sin preguntas, sin nuevas generaciones. Guardó session-2794e104-65bb-4f07-a87e-517a612278c7.json, formato 1.0.0, UUID independiente y cierre user_exit. Se validaron ambos archivos contra instantáneas y huellas. Los cuatro originales y veintisiete sesiones anteriores permanecieron intactos, con las huellas aprobadas de la Etapa 8.

Evidencia: final-validation-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b.json, salidas completas de ambas consolas y final-delivery-verification-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b.json. La segunda conserva manifiesto de implementación e inspección del asistente, sin atribuir aprobación humana no expresada. Se documentaron resultados, límites y uso en docs/validacion-final.md y se actualizaron README, estado y planificación: nueve de nueve etapas completadas técnicamente, ninguna pendiente del agente en este alcance. La consistencia universal, un piloto libre y modelos externos reales no se declaran validados. Clasificador, rúbrica, puntuaciones, retroalimentación educativa y Godot siguen fuera de esta entrega.

## 1 de noviembre de 2026: selector local/API y adaptador UNAB IA

El usuario solicitó guardar una clave localmente y elegir proveedor al iniciar. Se añadió scripts.start_interview con opciones 1 Ollama y 2 UNAB IA, sin cambiar permanentemente variables de PowerShell ni activar API al elegir local. config/llm.local.json se creó desde una plantilla sin sobrescribir archivos existentes; está excluido de Git. No se leyó ni publicó una clave real. La selección externa envía las credenciales solo en el entorno del proceso hijo y en la cabecera Bearer del cliente; no en argumentos o sesiones.

harness/llm/unab_client.py implementa Chat Completions en https://quotas.devhub.cl/api/v1/chat/completions con gemma4:26b, manteniendo el adaptador Responses existente. Se fijó el destino, sin redirecciones ni proxies del entorno. Se validan respuestas, estados, límites y errores sin copiar cuerpos del servidor; las generaciones no se repiten tras timeout. Se actualizó el nombre visible del proveedor en consola y smoke test.

Las 21 pruebas nuevas pasaron en 1,42 s; suite completa 759 passed in 59.65s, 687 unitarias y 72 integraciones. Son llamadas HTTP simuladas; la compatibilidad real del servicio desplegado queda pendiente de clave y ejecución del usuario. Perfil, puesto, configuración e instrucciones mantienen sus huellas aprobadas. La documentación de uso está en docs/selector-proveedor.md. La validación final previa de veinte turnos corresponde a la versión anterior y conserva su evidencia histórica; no se afirma validación real de UNAB.

## 1 de noviembre de 2026: investigación de consumo UNAB y texto final inválido

El usuario informó tres respuestas rechazadas y una completa en session-cd0fa34f-b9a1-491f-9f9a-fa7c83ff6ecc.json, con una captura de 25 963 créditos consumidos hoy sobre 50 000. Se validó el registro: la llamada válida informó 6045 tokens de entrada y 233 de salida; las fallidas carecen de métricas y finish_reason. El sistema actual ocupa 24 822 caracteres. El reenvío del contexto completo explica un orden de magnitud de 24 000 tokens de entrada para cuatro preguntas; no se conoce la fórmula de créditos del servicio ni otras actividades de la cuenta, y no se igualan créditos a tokens como hecho confirmado.

El adaptador anterior empleaba max_tokens 512 y perdía métricas al rechazar el contenido con un error genérico. La combinación de preguntas complejas fallidas y una breve exitosa es compatible con agotar salida en razonamiento, pero no prueba esa causa. Se consultaron fuentes primarias de Ollama sobre Gemma y reasoning_effort; no se certifica la aplicación de ese parámetro por la pasarela UNAB.

Se solicita reasoning_effort none manteniendo 512 tokens. El cliente conserva una copia independiente de metadatos permitidos, incluso en rechazos: estado HTTP, motivo conocido, tokens informados, indicadores de razonamiento, caracteres y configuración solicitada. No conserva clave, cabeceras, preguntas, perfil, cuerpo bruto ni contenido de razonamiento. La consola guarda unab-usage-<UUID>.json junto a resultados al cerrar, sin alterar el esquema de sesiones; muestra tokens en respuestas completas. Se distingue falta de texto final al límite, se rechazan marcas de pensamiento y no se repite generación automáticamente.

Se añadieron seis regresiones a las veintiuna del adaptador: razonamiento sin texto final, datos de uso conservados, copias independientes, marcas mixtas no expuestas y diagnóstico de errores guardado con métricas desconocidas nulas. Conjunto dirigido 27 passed in 3.97s; suite completa 765 passed in 254.13s (0:04:14), 687 unitarias y 78 integraciones. El tiempo no se atribuye a una causa sin medirla. Ninguna prueba usó la API real ni la clave privada. La sesión original y cuatro fuentes canónicas mantienen sus huellas.

Evidencia: unab-response-investigation-737c141f23f7423ba79fa9b0d23ade18.json y docs/pruebas/unab-consumo-y-salidas-vacias.md. La corrección está probada con HTTP simulado; se propone al usuario repetir una sola pregunta compleja y cerrar, para confirmar el efecto real con poco consumo. Si persiste, se revisará el diagnóstico antes de repetir otras preguntas. No se afirma que las tres causas históricas estén confirmadas ni que el despliegue ya esté corregido.

## 1 de noviembre de 2026: salida vacía al límite confirmada y presupuesto explícito UNAB

La sesión b84552c0-bccb-48e3-8498-bbeae51ed951 y su diagnóstico muestran una llamada HTTP 200: 6058 tokens de entrada, 512 de salida, 6570 totales, finish_reason length y cero caracteres finales. Se solicitó reasoning_effort none; reasoning_present false y reasoning_tokens null no permiten concluir si el backend hizo razonamiento oculto o cómo aplicó el parámetro. El agotamiento de la salida está confirmado; su causa interna no.

Se cambia exclusivamente el presupuesto predeterminado de UNAB a 2048. El selector admite api_max_output_tokens opcional (16–4096), muestra el valor al elegir API y propaga UNAB_MAX_OUTPUT_TOKENS al proceso. Los archivos privados anteriores de tres campos funcionan sin reescribirlos ni leer/cambiar la clave durante este trabajo. Los presupuestos locales y Responses continúan en 512. El error incluye el presupuesto solicitado. No hay aumentos o reenvíos automáticos.

Se añadieron 17 regresiones; 109 pruebas dirigidas de UNAB/selector, fábrica y Responses pasaron en 1,44 s. No se repitió la suite entera de 765 previa; hay 782 disponibles sin afirmar una ejecución completa nueva. No se hicieron llamadas reales ni se gastó cuota UNAB. Se conservó el diagnóstico y sesión originales, con huellas en la nueva evidencia de confirmación. La verificación real de 2048 queda pendiente de una única pregunta del usuario; si sigue vacía se revisará la pasarela antes de seguir escalando presupuestos.

## 1 de noviembre de 2026: confirmación del usuario con presupuesto UNAB 2048

El usuario repitió la misma pregunta sobre un endpoint Flask/PostgreSQL en la sesión 162df680-88d6-40ca-9e8f-d095fae07025. Una respuesta completa, cero incidencias, perfil intacto y 12,82 s comunicados. Se validaron sesión y diagnóstico sin cambios: HTTP 200, presupuesto 2048, finish_reason stop, entrada 6058, salida 1255, total 7313 y 684 caracteres de texto final. La igualdad de la pregunta con el intento previo de 512 se comprobó directamente.

Se guardó unab-success-confirmation-162df680-88d6-40ca-9e8f-d095fae07025.json con huellas, métricas, alcance y observación del asistente. Funcionamiento confirmado para esta pregunta, sin inferir tokens internos de razonamiento, fórmula de créditos o éxito universal. Se mantienen 2048 y la configuración vigente. No hubo cambios de código, nuevas llamadas API, acceso a la clave ni repetición de pruebas para la confirmación documental.
