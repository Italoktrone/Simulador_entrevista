# Etapa 7.3: guardar y leer sesiones en JSON local

Al terminar la consola, el programa guarda el registro completo de la sesión en `outputs/sessions/session-<UUID>.json`. Después se puede leer y validar mediante `load_session(path)`. La lectura devuelve datos para revisión; no reanuda la entrevista ni utiliza su contenido como instrucciones.

La unidad depende del registro de la 7.2, del lector JSON estricto y del validador existentes. No añade dependencias. Perfil, puesto, configuración, instrucciones 1.0.11 y elección del proveedor conservan su contenido.

## Archivos y funciones

| Archivo | Responsabilidad |
| --- | --- |
| `schemas/session.schema.json` | Contrato 1.0.0 del registro cerrado, intentos, respuestas, métricas e incidencias. Rechaza campos adicionales. |
| `harness/session_log.py` | `validate_session_data` comprueba estructura y relaciones; `save_session` crea un archivo nuevo; `load_session` lee y valida un archivo existente. |
| `scripts/run_interview.py` | Comprueba la integridad final, cierra el registro, intenta guardarlo y muestra la ruta solo cuando terminó la escritura. |
| `harness/application/cli.py` | Anuncia el guardado local al iniciar. Conserva los comandos y el resumen de sesión. |
| `tests/unit/test_session_log.py` | 45 casos sobre contratos, texto exacto, métricas, errores de lectura/escritura y conservación de archivos. |
| `tests/integration/test_session_persistence_flow.py` | Ocho casos del punto de entrada y sus archivos, con HTTP simulado. |
| `tests/conftest.py` | Dirige el guardado de pytest a carpetas temporales. Las pruebas no llenan la carpeta de sesiones del proyecto. |

## Contrato y guardado

Se conserva la copia de configuración, identidad y procedencia por hashes; proveedor y modelo solicitados; fechas UTC; estado y motivo de cierre; preguntas originales, respuestas y métricas; incidencias de intentos y de sesión. Se guardan también los intentos fallidos y las respuestas cortadas que ya conserva el registro técnico, sin convertirlos en turnos aceptados para el modelo. Las descripciones de errores generadas por la aplicación proceden del catálogo seguro y no copian cuerpos HTTP, claves o mensajes arbitrarios de excepciones.

No se copia el perfil interno completo ni el mensaje de sistema. El archivo conserva lo ocurrido, incluidas afirmaciones que podrían ser incorrectas: un intento `completed` significa que el cliente devolvió una respuesta completa, no que se haya certificado su verdad.

Antes de crear la carpeta, se valida el registro y su configuración con los dos esquemas. Se comprueban UUID canónico de versión 4, coincidencia de candidato/puesto, numeración consecutiva, límite configurado, estados y respuestas compatibles, fechas UTC reales y valores serializables en UTF-8 sin números no finitos. Solo se admiten sesiones cerradas y sin intentos pendientes.

Las fechas de sesión utilizan el reloj real. La referencia ficticia sigue en **2026-10-20**. No se exige monotonía del reloj: una comprobación final de integridad puede registrarse después del primer cierre y un ajuste del reloj no cambia el orden de los intentos.

El archivo se crea con acceso exclusivo; si ya existe, se comunica un error y se conservan sus bytes. La escritura comprueba el número de bytes, vacía el búfer y solicita sincronización al sistema. Si ocurre un fallo detectado, intenta retirar únicamente el archivo que acaba de crear. Si tampoco puede retirarlo, el mensaje identifica el archivo posiblemente incompleto para revisarlo. Este mecanismo no implementa recuperación frente a un corte de energía o terminación forzada del proceso.

## Cierre y errores

Se intenta guardar después de `/salir`, máximo de preguntas, fin de entrada o `Ctrl+C`, incluso si no se enviaron preguntas. Si se detectó una alteración del perfil, se conserva un archivo de diagnóstico con `source_integrity: failed` y el programa devuelve código 1. No restaura ni modifica el perfil. Si la preparación falla antes de crear el controlador, no inventa una sesión.

Un fallo de guardado devuelve código 1 y no muestra «Registro de sesión guardado». Revisar la carpeta, sus permisos y el espacio disponible. No se sobrescribe un archivo existente ni se activa una API alternativa. Una interrupción durante el guardado comunica que no se confirmó el archivo.

`load_session` utiliza el lector existente para rechazar JSON truncado, claves duplicadas y números no finitos; después aplica las mismas validaciones del guardado. No modifica el archivo leído. Las vistas devueltas son datos nuevos: cambiar un diccionario cargado no modifica los bytes del archivo.

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

## Evidencia y alcance

El usuario confirmó la unidad 7.2 con **477 passed in 19.83s** y **477 passed in 19.45s**. Su primera sesión registró dos respuestas y cero incidencias; la segunda tuvo otro UUID y cero intentos. Ambas terminaron con el original intacto. Los archivos de esas sesiones no existían: aquella versión conservaba registros en memoria y no se crean retrospectivamente.

La suite de esta unidad terminó con **530 passed in 26.20s**. Se añadieron 45 casos unitarios y ocho integraciones; se amplió además el caso existente de integridad final para comprobar su archivo de diagnóstico. La primera recolección detectó una construcción incorrecta de `ProfileIntegrityError` en el código de prueba; se corrigió usando sus tres argumentos. Después pasaron los 51 casos nuevos iniciales; se añadieron dos límites de formato UTC antes de la suite final. No se hicieron solicitudes reales en pytest.

La comprobación real local ejecutó dos preguntas con `gemma4:e4b` y API externa desactivada. La aplicación guardó [session-67fbee76-9926-438d-8d19-5b0da7f20036.json](../outputs/sessions/session-67fbee76-9926-438d-8d19-5b0da7f20036.json), cerrado por `user_exit`, con dos intentos completos, cero incidencias y fuente intacta. Las respuestas conservaron 21 meses y el desglose de nueve parciales y nueve completos; tardaron **64,76 s** y **15,23 s**. No se atribuyen estos tiempos a una causa sin métricas por fase.

Otra ejecución sin preguntas guardó [session-b51cad38-89df-4fcc-b2ef-d7ab450ff366.json](../outputs/sessions/session-b51cad38-89df-4fcc-b2ef-d7ab450ff366.json), con otro identificador y cero intentos, conservando el primer archivo. En ambos casos, la lectura validada coincidió exactamente con la instantánea final del controlador. Perfil, puesto, configuración e instrucciones mantuvieron sus hashes aprobados.

La salida completa y las comparaciones se conservan en [session-persistence-ca7f555825ac4bf29124f9cbb29666b9.json](../outputs/results/session-persistence-ca7f555825ac4bf29124f9cbb29666b9.json). La confirmación anterior del usuario se copió sin alteraciones a [session-user-confirmation-93abca64583446d89fca2a0f5722dc28.txt](../outputs/results/session-user-confirmation-93abca64583446d89fca2a0f5722dc28.txt). Los archivos en `outputs/sessions` los creó la aplicación; el de `outputs/results` es evidencia adicional del verificador.

Se espera el resultado del usuario antes de otra unidad. El tamaño del contexto, los resúmenes y la extracción de hechos relevantes siguen pendientes. Esta unidad no añade clasificación, puntuación ni retroalimentación educativa.

Confirmación posterior: el usuario obtuvo **530 passed in 26.55s** y guardó/leyó la sesión `d8964573-f78f-4fe6-802a-391e2e6913d7` con `closed`, `unchanged` y dos intentos `completed`. La revisión local confirmó el archivo. La siguiente unidad de medición se documenta en [diagnóstico de contexto](diagnostico-contexto.md); las cifras de pruebas anteriores se conservan como evidencia histórica de la 7.3.

La unidad 7.4e amplía el contrato: las entrevistas con `--extractive-context` guardan formato 1.1.0, política y eventos de preparación separados de las preguntas. El lector continúa aceptando los archivos 1.0.0 sin migrarlos. Los detalles actuales están en [resumen en entrevista](resumen-en-entrevista.md).
