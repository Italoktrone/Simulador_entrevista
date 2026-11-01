# Pruebas de integración

## Validación final de la Etapa 9

La suite conjunta terminó con **738 passed in 45.54s**: 687 pruebas unitarias y 51 integraciones. HTTP está simulado o bloqueado en pytest. La entrevista real de veinte preguntas y sus archivos se verificaron por separado; véase la [validación final](../../docs/validacion-final.md).

## Etapa 8.3: conjunto ampliado

[test_extended_reference_cases.py](test_extended_reference_cases.py) comprueba las referencias de los seis casos nuevos y su ejecución con HTTP simulado: diez preguntas exactas, aislamiento, continuidad, guardado/lectura y procedencia. **2 passed in 1.88s**. Hay 738 pruebas disponibles, 687 unitarias y 51 integraciones. La última suite completa fue de 736 pruebas en 123,96 s; no se afirma una nueva ejecución completa de 738. La [ejecución real y sus límites](../../docs/pruebas/consistencia-ampliada.md) se mantienen separados.

## Etapa 8.2: ejecución local por lotes

[test_reference_execution_flow.py](test_reference_execution_flow.py) añade seis comprobaciones de aislamiento, continuidad, persistencia y detención ante errores, salida cortada, interrupción, fallo de guardado o conjunto inválido. Obliga a seleccionar Ollama incluso si el entorno selecciona API. HTTP está simulado y los archivos se guardan en temporales. Casos nuevos: **6 passed in 2.95s**. Suite completa: **736 passed in 123.96s**, 687 unitarias y 49 integraciones. La [ejecución real](../../docs/pruebas/ejecucion-referencias.md) se documenta por separado, pendiente de revisión humana.

## Etapa 8.1: listado de referencias

[test_reference_suite_flow.py](test_reference_suite_flow.py) añade tres casos: carga y presentación de fuentes reales desde otra carpeta, error de archivo ausente y vistas independientes entre cargas. Bloquea HTTP y comprueba que el listado no escribe archivos ni cambia fuentes o sesiones existentes. Suite completa **730 passed in 45.44s**, 687 unitarias y 43 integraciones. No hay respuestas del candidato evaluadas; véase la [guía 8.1](../../docs/pruebas/referencias-consistencia.md).

[test_json_loading.py](test_json_loading.py) contiene las dos primeras pruebas de integración: lectura y validación del candidato aprobado y del puesto aprobado. Combinan [json_loader.py](../../harness/json_loader.py) y [schema_validator.py](../../harness/schema_validator.py).

[test_profile_validation.py](test_profile_validation.py) añade la tercera prueba: el perfil aprobado se lee y pasa tanto el esquema como las reglas de coherencia de [profile.py](../../harness/profile.py). Se comprueba que sus bytes y su hash original no cambien y que tampoco se modifique el archivo del esquema.

El mismo archivo añade una cuarta prueba para `load_profile`: se obtiene una instantánea protegida del candidato real aprobado, se modifica únicamente una copia exportada y se comprueba que la instantánea, el archivo y su huella original permanezcan intactos.

La quinta prueba deriva y presenta el currículum mediante `format_resume`. Comprueba la presencia de antecedentes profesionales del candidato y la ausencia de fragmentos de relatos y limitaciones internas, conservando los bytes y la huella del perfil aprobado.

[test_interview_setup.py](test_interview_setup.py) añade la sexta prueba: prepara los documentos mediante el cargador real, verifica las tres referencias y las competencias del puesto y conserva los archivos y la huella del candidato aprobado.

[test_prompt_context.py](test_prompt_context.py) añade la séptima: carga el escenario y las instrucciones reales, prepara los mensajes iniciales y conserva los cuatro archivos de origen, comprobando además la huella del candidato.

[test_ollama_turn.py](test_ollama_turn.py) añade la octava: prepara esos documentos y envía los mensajes por el adaptador local a un transporte HTTP simulado. Comprueba el destino del turno, recupera una respuesta simulada y conserva los cuatro archivos de origen. No consulta un modelo ni evalúa el significado de su texto.

[test_external_turn.py](test_external_turn.py) añade la novena: usa la fábrica con selección externa y permiso explícitos, clave ficticia y transporte simulado. Comprueba los mensajes reales preparados para el escenario, la ausencia de la clave en el contenido, `store: false`, la respuesta compartida y la conservación de las cuatro fuentes. No consulta la API real ni demuestra calidad de un modelo externo.

[test_console_flow.py](test_console_flow.py) añade la décima: ejecuta `scripts.run_interview.main` con cargadores, controlador y adaptador local reales, entradas de consola controladas y transporte HTTP simulado. Recorre CV, puesto, inicio, dos preguntas y salida. Comprueba los dos mensajes por solicitud, el escenario fijo, las respuestas presentadas, el cierre del cliente y la conservación de las cuatro fuentes. No consulta el modelo ni demuestra continuidad conversacional.

Cada caso lee el JSON y su esquema desde sus rutas reales, valida la estructura y comprueba que los bytes de ambos archivos no cambien. Los archivos de datos también se comparan con los hashes documentados desde su creación. Si se modifican intencionalmente antecedentes aprobados, el cambio y la nueva evidencia deberán revisarse antes de actualizar esa referencia.

## Ejecución y resultado

En PowerShell, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
```

Al cerrar la unidad del lector el 30 de octubre de 2026, el conjunto terminó con **54 passed in 0.90s**: 52 casos unitarios y dos de integración. El usuario repitió ese conjunto en su PowerShell y confirmó **54 passed in 0.95s**, junto con la lectura del nombre y la fecha del candidato.

Después de incorporar la coherencia interna del perfil, el conjunto completo terminó con **95 passed in 6.87s**: 92 casos unitarios y tres de integración. Se usaron Python 3.14.3, `pytest` 9.2.0 y `jsonschema` 4.26.0. No se realizaron consultas a un LLM ni se instalaron nuevas dependencias en esas unidades.

El usuario confirmó esa unidad con **95 passed in 4.29s** y la salida `Perfil validado: cand-001`. Tras incorporar la carga protegida, el conjunto completo terminó con **116 passed in 10.97s**: 112 pruebas unitarias y cuatro de integración. El lector conserva su API anterior y añade la lectura conjunta de datos y bytes para que la validación y el hash correspondan al mismo contenido. No se añadieron dependencias.

El usuario confirmó la carga protegida con **116 passed in 6.06s**, la identidad y fecha del escenario y `Archivo original intacto`. Después de incorporar el currículum derivado y su presentación, el conjunto terminó con **136 passed in 15.11s**: 131 casos unitarios y cinco de integración. El archivo original del candidato conserva su contenido y no se ha creado un JSON paralelo de currículum.

El usuario confirmó posteriormente la salida completa del currículum y **136 passed in 7.76s** desde su PowerShell. La siguiente unidad solo definió `agent/agent.md`; su revisión textual no añade pruebas de integración ni demuestra todavía el comportamiento de un modelo. Véase la [bitácora de desarrollo](../../docs/bitacora/bitacora-desarrollo.md).

Después de definir el archivo básico de configuración y su esquema, el conjunto completo terminó con **176 passed in 14.08s**: 171 casos unitarios y cinco de integración. Los 40 casos nuevos correspondían al contrato estructural; en esa unidad el cargador de referencias todavía no existía.

El usuario confirmó **176 passed in 8.27s**. Tras incorporar `load_interview_setup`, el conjunto terminó con **198 passed in 8.34s**: 192 casos unitarios y seis de integración. La preparación valida las referencias en ejecución, sin iniciar una entrevista ni consultar un modelo.

El usuario confirmó la carga y **198 passed in 8.13s**. Después de incorporar el constructor de contexto y el contrato de mensajes, el conjunto terminó con **226 passed in 9.55s**: 219 pruebas unitarias y siete de integración. El mensaje de sistema contiene instrucciones y datos autorizados; la pregunta ocupa otro mensaje con rol `user`. La integración no realiza solicitudes al LLM.

## Incidencias y correcciones

El usuario confirmó la unidad de contexto con **226 passed in 15.46s**. Después de incorporar el cliente local, el conjunto completo terminó con **279 passed in 10.27s**: 271 casos unitarios y ocho de integración. Las 53 pruebas nuevas simulan HTTP; las mediciones de Ollama se registran por separado en la [bitácora](../../docs/bitacora/bitacora-desarrollo.md) y `outputs/results/`.

Tras observar un tiempo de espera en la primera consulta real, se amplió la espera de lectura de 180 a 300 segundos y se añadieron dos casos unitarios del archivo de evidencia. La ejecución final terminó con **281 passed in 15.48s**: 273 pruebas unitarias y ocho integraciones, sin consultas reales en la suite.

Las regresiones siguientes cubrieron salida cortada, marcas de razonamiento y conservación de mensajes con otros modelos. Tras retirar los ajustes experimentales de plantilla y elegir explícitamente `gemma3n:e2b`, el conjunto terminó con **286 passed in 9.37s**: 278 unitarias y ocho integraciones. Después del ajuste textual de nombres literales en las instrucciones 1.0.1, las 27 pruebas del constructor y estas dos integraciones terminaron con **29 passed in 1.91s**. La consulta real permanece separada de estas mediciones.

El 31 de octubre el usuario confirmó **286 passed in 10.14s**, con la discrepancia del nombre de la institución todavía presente en la respuesta real. Se añadió un índice derivado de denominaciones exactas al contexto y se amplió la séptima integración para comprobar su correspondencia con el perfil aprobado. Con dos casos unitarios nuevos, el conjunto terminó con **288 passed in 9.99s**: 280 unitarias y ocho integraciones. Los originales se conservan; este resultado no certifica la obediencia del modelo.

El usuario confirmó después **288 passed in 12.86s** y una llamada local de 41,42 s con los nombres correctos. Se añadió el adaptador opcional OpenAI y el selector que mantiene Ollama por defecto. La suite terminó con **352 passed in 29.54s**: 343 unitarias y nueve integraciones. Las 64 pruebas nuevas usan simulaciones; no se realizó ninguna llamada real a la API externa.

Tras confirmar el usuario **352 passed in 13.34s** y una llamada de 275,82 s, se añadieron métricas opcionales por fase y permanencia local de 15 minutos. Los 21 casos nuevos fueron unitarios; las nueve integraciones previas siguieron pasando. El conjunto completo terminó con **373 passed in 53.29s**. Las mediciones reales de carga y reutilización se registran por separado, sin atribuir el tiempo de la suite al rendimiento del modelo.

El usuario confirmó **373 passed in 10.12s** y dos respuestas correctas con reutilización del contexto. La unidad de consola añadió 30 casos unitarios y una integración. La suite completa terminó con **404 passed in 14.67s**: 394 unitarias y diez integraciones. La ejecución real del programa con una pregunta fue independiente de esa suite.

La ejecución inicial desde la herramienta restringida no pudo crear directorios temporales para `tmp_path`: terminaron 24 casos aprobados y 30 errores de preparación. Se repitió con el acceso correspondiente a la carpeta temporal de Windows. Este problema no se corrigió modificando los datos ni el lector.

La siguiente ejecución terminó con 53 casos aprobados y uno fallido: una prueba suponía que anidar listas hasta `sys.getrecursionlimit() + 50` siempre provocaría un error del decodificador. Esa suposición no se cumplió con el intérprete utilizado. Se corrigió la prueba para simular directamente un `RecursionError` y comprobar su traducción a `JsonLoadError`, sin fijar un límite arbitrario de profundidad. La ejecución posterior produjo los 54 casos aprobados indicados arriba.

## Límites

La carga y coherencia de datos, la vista pública, el contexto inicial, los adaptadores y la consola con contador están implementados. La separación de roles comprueba la estructura construida por el programa, no la obediencia del modelo. Desde la unidad 7.1, la consola envía los pares anteriores completos y conserva la memoria por ejecución; desde la 7.3 guarda y permite leer registros JSON locales. Estas pruebas no demuestran consistencia completa del texto libre o de una entrevista con historial. Las consultas reales se revisan aparte.

## Formato nativo de Gemma 3n y contexto derivado

Las integraciones de contexto, adaptador y consola comprueban el JSON delimitado y las instrucciones cargadas. El contrato general conserva system/user; el transporte de Gemma 3n reúne el par inicial en un único user con la pregunta original al final. Las dos preguntas independientes de consola comparten los mismos antecedentes y no incluyen respuestas previas. Se mantienen diez integraciones, sin solicitudes reales. Las incidencias semánticas y sus evidencias están [documentadas aparte](../../docs/pruebas/correccion-conducta.md).

## Etapa 7.1: continuidad de la conversación

[test_history_flow.py](test_history_flow.py) añade la undécima integración. Utiliza escenario, instrucciones, controlador, fábrica y adaptador reales con HTTP simulado para gemma4:e4b. Comprueba que la repregunta llega después de la pregunta y respuesta previas con sus roles originales; una segunda entrevista con el mismo cliente comienza sin esos turnos. Conserva el perfil y cierra el cliente.

La integración previa de consola se actualizó para comprobar la secuencia adaptada de Gemma 3n: primer user con sistema y pregunta, assistant anterior y user actual. La ausencia de historial que se describe en las entradas históricas de esta guía corresponde a la Etapa 6 original. La suite actual terminó con **432 passed in 17.73s** (421 unitarias y once integraciones), sin solicitudes reales en pytest. La comprobación real de cuatro preguntas se documenta en [historial en memoria](../../docs/historial-en-memoria.md).

## Contexto con cronología

La integración de preparación de contexto comprueba los proyectos reales ordenados por inicio y su coincidencia de agosto a noviembre de 2025. Distingue las instrucciones de la referencia cronológica derivada final y conserva los archivos fuente. Las demás integraciones mantienen los contratos de conversación y transporte. La suite final terminó con **440 passed in 16.94s**: 429 unitarias y once integraciones. La calidad del texto libre se revisa aparte en las [pruebas cronológicas reales](../../docs/pruebas/correccion-cronologia.md).

## Contexto con duración laboral y términos conjuntos

[test_temporal_context.py](test_temporal_context.py) añade la duodécima integración. Carga las fuentes reales, incorpora un historial con el total anterior incorrecto y comprueba que el sistema conserva 21 meses y todos los hitos correctos sin elevar la respuesta previa a antecedente autorizado. También conserva el archivo original. No comprueba por sí sola que el modelo obedezca esa prioridad. La suite final terminó con **451 passed in 18.36s**, 439 unitarias y doce integraciones. Las consultas reales se revisan [aparte](../../docs/pruebas/correccion-duracion-y-estudios.md).

## Etapa 7.2: registro desde la consola

[test_session_records_flow.py](test_session_records_flow.py) añade la decimotercera integración. Recorre el punto de entrada real con escenario, controlador, fábrica, adaptador y consola; HTTP simulado devuelve primero 500 con un cuerpo reservado y después una respuesta completa. Comprueba que se registran dos intentos y una incidencia, que el fallo no entra en el contexto, que no se copia el cuerpo reservado, que la sesión cierra por salida del usuario y que fuentes y recursos se conservan correctamente. La suite final terminó con **477 passed in 19.10s**: 464 unitarias y trece integraciones. La prueba real local se documenta [aparte](../../docs/sesiones-en-memoria.md).

## Etapa 7.3: guardado del punto de entrada

[test_session_persistence_flow.py](test_session_persistence_flow.py) añade ocho casos: salida sin preguntas, fin de entrada, interrupción, respuesta completa, error HTTP seguido de recuperación, dos fallos de guardado y fallo anterior a crear el controlador. Valida el archivo realmente escrito, su UUID, estados y fuente; protege cuerpos HTTP y los cuatro archivos de escenario. HTTP siempre está simulado y los archivos se aíslan en temporales. La suite final terminó con **530 passed in 26.20s**, 509 unitarias y 21 integraciones. La prueba real se registra [aparte](../../docs/persistencia-sesiones.md).

## Etapa 7.4a: inspección de archivos de sesión

[test_context_inspection_flow.py](test_context_inspection_flow.py) añade cuatro casos con guardado/carga reales en temporales y proveedor simulado: sesión con métricas, sesión vacía, archivo ausente y presupuesto inválido. Bloquea HTTP durante la inspección, comprueba cálculo y textos del diagnóstico, excluye preguntas/respuestas y verifica que no se creen o modifiquen archivos. La suite conjunta terminó con **559 passed in 27.36s**, 534 unitarias y 25 integraciones. Véase la [lectura del archivo real del usuario](../../docs/diagnostico-contexto.md).

## Etapa 7.4b: continuidad después de un rechazo

[test_context_rejection_flow.py](test_context_rejection_flow.py) añade una integración con escenario, adaptador, consola y archivos reales y HTTP simulado. Respuesta completa → HTTP 400 de contexto → repregunta: conserva el primer par, excluye la pregunta fallida del siguiente envío y no cambia el sistema. Comprueba tres llamadas, contador, estados, código seguro `context_limit`, guardado/carga exacta y cierre de recursos. La suite terminó con **577 passed in 26.48s**, 551 unitarias y 26 integraciones. La [prueba real](../../docs/proteccion-contexto.md) se mantiene separada.

## Etapa 7.4c: vista previa del resumen

[test_summary_preview_flow.py](test_summary_preview_flow.py) añade cuatro casos con archivo real temporal y HTTP simulado: selección de citas y protección, omisión del proveedor cuando no hay turnos antiguos, salida inválida e interrupción con cierre de recursos. Comprueba que el selector no recibe intentos fallidos o perfil interno, que los pares recientes quedan completos y que la vista previa no modifica archivos. Suite final **632 passed in 49.16s**, 602 unitarias y treinta integraciones. Las llamadas locales y fixtures se distinguen en [la evidencia](../../docs/resumen-extractivo.md).

## Etapa 7.4d: consulta aislada con contexto compuesto

[test_summary_context_probe_flow.py](test_summary_context_probe_flow.py) añade seis casos. Recorre escenario, archivo, selector, composición y candidato con HTTP simulado: historial reducido, historial completo, respuesta cortada, error HTTP, interrupción y cambio de instrucciones detectado antes de crear cliente. Verifica los controles locales, papeles, pares recientes y conservación exacta del archivo. Suite final **654 passed in 34.08s**, 618 unitarias y 36 integraciones. Las verificaciones locales se registran [aparte](../../docs/contexto-con-resumen.md).

## Etapa 7.4e: consola con resumen activado

[test_live_context_console_flow.py](test_live_context_console_flow.py) añade cuatro casos: selección válida, selección inválida con respaldo completo, interrupción sin nueva pregunta enviada y política inválida anterior a la sesión. Recorre fábrica, adaptador, consola, controlador, guardado y lectura 1.1.0 con HTTP simulado, comprobando contadores y protección de detalles reservados. Suite final **690 passed in 104.14s**, 650 unitarias y cuarenta integraciones. La entrevista local y la fixture sembrada se documentan [aparte](../../docs/resumen-en-entrevista.md).
