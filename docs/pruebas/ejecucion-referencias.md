# Etapa 8.2: ejecución local por lotes

El usuario confirmó la unidad 8.1: **730 passed in 150.75s**, cuatro casos y cinco preguntas con los hechos esperados. Solicitó avanzar más rápido y consumir menos tokens de ChatGPT. Se agrupan ejecución, conservación de evidencias y revisión en bloques; las actualizaciones serán breves y no se pedirá repetir la suite completa después de cada comprobación manual.

## Ejecución

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_reference_cases --model gemma4:e4b
```

El comando usa exclusivamente Ollama local, incluso si el entorno selecciona la API externa. Sin `--model` toma `OLLAMA_MODEL` o el modelo predeterminado existente. No descarga modelos ni cambia los parámetros del cliente. No instala dependencias.

El nuevo archivo [run_reference_cases.py](../../scripts/run_reference_cases.py) reutiliza el cargador de referencias, escenario, instrucciones, fábrica, controlador y guardado existentes. Envía las cinco preguntas una vez; no añade los criterios de revisión al contexto del candidato. Cada caso tiene UUID e historial independientes. Los dos pasos de continuidad comparten su sesión.

La primera llamada puede tardar. Ante error, respuesta cortada, interrupción o fallo al guardar se detiene el lote y conserva la evidencia disponible. No repite la generación ni continúa una repregunta después de un fallo. Cada sesión se guarda con el formato existente; el informe conserva también su instantánea, preguntas originales, respuestas y métricas. Esto permite conservar los datos aunque falle el archivo individual de una sesión.

El resultado está en `outputs/results/reference-run-<UUID>.json`, con la definición del conjunto, hechos resueltos, huellas, parámetros, rutas de sesiones, estados y casos no ejecutados. Se crea sin sobrescribir. El informe tiene `technical_status` y `semantic_review: pending_human_review`: finalizar llamadas no acredita consistencia factual. No incluye el mensaje de sistema ni credenciales.

## Revisión y comprobaciones

Revisar las respuestas originales con las notas del [conjunto](../../data/reference_questions/consistencia_basica.json). Se acepta variación de redacción compatible con los hechos. Una omisión de detalle, una contradicción y un fallo técnico deben registrarse por separado. Las observaciones de ChatGPT se identifican como inspección del asistente y no sustituyen la revisión humana del usuario.

[test_reference_execution_flow.py](../../tests/integration/test_reference_execution_flow.py) comprueba HTTP simulado, aislamiento, continuidad, cierre y lectura de sesiones, elección exclusivamente local, detención ante error/interrupción/salida cortada, fallo de guardado y rechazo del conjunto antes de crear el cliente. Las seis pruebas iniciales pasaron en 2,95 s. Son pruebas técnicas, separadas de la ejecución real con Ollama.

La Etapa 8 continúa en curso. La ampliación de casos y su revisión se agruparán antes del cierre; la Etapa 9 requiere la transición explícita prevista en el plan original.

La suite completa posterior al ejecutor terminó con **736 passed in 123.96s (0:02:03)**: 687 unitarias y 49 integraciones. No se atribuye la variación de tiempo a una causa sin medirla. No se requiere repetir este conjunto por cada ejecución manual del lote.

## Ejecución real registrada

El [lote fd00eb31-7961-4390-9807-c78695f3a247](../../outputs/results/reference-run-fd00eb31-7961-4390-9807-c78695f3a247.json) terminó técnicamente completo con **gemma4:e4b**, cuatro sesiones independientes y cinco respuestas. La [verificación separada](../../outputs/results/reference-execution-verification-fd00eb31-7961-4390-9807-c78695f3a247.json) confirma lectura idéntica de las sesiones guardadas y conservación de los cuatro originales y siete sesiones anteriores. La API externa no se utilizó.

| Caso | Observación al inspeccionar las respuestas | Tiempo de llamada |
| --- | --- | --- |
| Formación | Instituto Profesional Horizonte Digital e Ingeniería en Informática. | 89,73 s |
| Duración | 21 meses calendario distintos; 3 de práctica y 18 como junior, sin afirmar equivalencia a jornada completa. | 11,07 s |
| Continuidad, paso 1 | Mencionó Inventario Aula como proyecto académico y sus tecnologías compatibles con el perfil. | 14,71 s |
| Continuidad, paso 2 | Conservó Inventario Aula y se refirió a su primera respuesta. | 11,47 s |
| Límite técnico | Reconoció ausencia de experiencia práctica con Kubernetes. | 13,01 s |

Estas observaciones son una inspección del asistente de las respuestas originales. La revisión humana del usuario permanece pendiente y no se cambia `semantic_review` del informe. No se encontraron incompatibilidades con los hechos de estos cuatro casos en esta ejecución; esto no sustituye la ampliación de casos ni garantiza consistencia global. Las latencias describen estas llamadas, sin asegurar tiempos futuros.
