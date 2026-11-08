# Estado, decisiones e historial del proyecto

[Índice general](../README.md#documentación)

Las secciones fechadas y los registros de etapas describen el estado y las pruebas de su momento.

## Contenido

- [Estado actual — 8 de noviembre de 2026](#estado-actual)
- [Continuidad del proyecto — 2 de noviembre de 2026](#continuidad-agente)
- [Estado de las nueve etapas del agente candidato](#estado-etapas)
- [Alcance y planificación](#planificacion)
- [Registro de decisiones](#decisiones)
- [Registro de cambios](#changelog)
- [Bitácora de desarrollo](#bitacora-desarrollo)

<a name="estado-actual"></a>

## Estado actual — 8 de noviembre de 2026

La interfaz de Godot 4.7.2 incorpora selección de tres perfiles: Nicolás Vera Soto (desarrollo web), Camila Rojas Medina (calidad y pruebas de API) y Diego Muñoz Leiva (soporte de datos y SQL). El CV público y el puesto se consultan antes de crear la sesión; la selección queda bloqueada durante la entrevista. La API incorpora catálogo y vista previa, acepta `candidate_id` al iniciar y mantiene el escenario y los documentos del perfil elegido durante toda la sesión. El catálogo resuelve rutas explícitas y rechaza identificadores desconocidos. Los perfiles nuevos tienen validación técnica; la revisión humana de sus antecedentes y la aceptación del flujo ampliado siguen pendientes.

Las citas documentales conocidas se presentan mediante sus títulos bajo la conversación y se retiran únicamente del diálogo visible; los textos originales siguen en el registro. Se mantienen respuesta y evaluación separadas, contador, espera, reintentos idempotentes y cierre con guardado. La caché `.godot/` queda excluida de Git y los identificadores `.gd.uid` se conservan.

La ampliación añade 21 pruebas de selección y perfiles a la suite Python. Los recorridos simulados de Godot comprobaron los tres CV, selección y ausencia de proyectos ajenos, bloqueo durante la entrevista, pregunta, evaluación, reintentos y guardado del perfil elegido. Los tres candidatos completaron también una entrevista con Ollama `gemma4:e4b`, evaluación disponible y cierre validado. Las duraciones observadas fueron 86,42 s, 136,65 s y 141,18 s para el recorrido completo de cada candidato; las dos últimas incluyen captura renderizada. No son mediciones aisladas de latencia ni una validación semántica exhaustiva. Evidencias por candidato en `reports/godot/`.

La validación anterior de la ampliación terminó con **1905 pruebas aprobadas**, una advertencia de dependencia, Ruff y Bandit sin hallazgos y recuperación documental 6/6. Ese resultado corresponde a las instrucciones 1.0.11.

### Verificación de fallos, aislamiento y reproducción

T12 añade escenarios reproducibles de proveedor inaccesible, timeout y evaluación no disponible. Se comprueban desde los controles de Godot, con API aislada y modelos simulados; el proveedor inaccesible además usa una conexión TCP real a un puerto sin servidor. El timeout conserva UUID y contenido al reintentar, sin añadir otra pregunta. Un error confirmado del modelo consume un intento, conserva el borrador y permite un nuevo envío. La indisponibilidad del análisis conserva la respuesta y permite continuar.

Los tres perfiles superaron también veinte envíos desde Godot, guardado automático por límite y rechazo del envío 21 tanto en pantalla como en la API. El fallo del evaluador en el turno 20 conserva las veinte respuestas. Es aceptación técnica con modelos simulados, no una medición semántica de conversaciones largas con Ollama.

Las instrucciones 1.0.13 hacen explícito que las situaciones sin `project_id` carecen de proyecto y empresa documentados, distinguen ayuda recibida de ayuda prestada y conservan el tipo proyecto/organización. La validación de citas impide publicar rutas internas o IDs no recuperados, preservando la salida original rechazada en el JSON de sesión. Los perfiles, las demostraciones y la rúbrica no se modifican. `scripts.check_npc_isolation` conserva primeras respuestas reales y sesiones independientes o con continuidad para cotejo; completar las llamadas no implica aprobación semántica automática.

T17 dispone de `scripts.check_clean_install --published`: clona origin/E2, crea un entorno nuevo, instala sin caché de pip, comprueba dependencias y repite calidad y Godot. Registra el commit y conserva evidencias fuera del clon; el entorno temporal se elimina al terminar. Los comandos y límites de cada modo se agrupan en el README. El cierre en Notion debe referirse al resultado de ejecución y a su versión publicada.

### Hito T06: interfaz mínima publicada y comprobada

Verificación de interfaz: 21 comprobaciones con la API real y modelos simulados, incluyendo pérdida de respuestas después de completar la operación y respuesta de turno incompatible. Los reintentos conservan UUID y contenido, con una sola sesión y un solo turno guardado. También funcionó una copia del proyecto sin caché del editor. Con Ollama `gemma4:e4b` se completaron 12 comprobaciones, respuesta real, evaluación de cuatro criterios y cierre validado; el recorrido con captura duró 65,42 segundos. Resultados locales en `reports/godot/simulated/interface.json` y `reports/godot/live/interface.json`; sesión real `334055c4-3ad9-4213-bee3-3035ac89670d`. Es una prueba funcional, sin ampliar las métricas de precisión del modelo.

Verificación general posterior: **1884 pruebas aprobadas en 301,54 segundos**, Ruff y Bandit sin hallazgos, seis de seis casos de recuperación documental correctos. Una advertencia de obsolescencia de Starlette/HTTPX no afecta al resultado. Evidencia en `reports/quality-summary.json` y `reports/pytest.txt`.

La interfaz mínima está publicada en E2 mediante el commit `d3c1646`. GitHub Actions n.º 5 aprobó Windows y Linux. Un clon remoto de esa versión con entorno Python nuevo aprobó 1882 pruebas, con dos omisiones por sesiones manuales históricas no distribuidas, Ruff y Bandit sin hallazgos, seis casos documentales y los recorridos de Godot simulado y con Ollama real. Esa validación corresponde a T06 con un candidato. Evidencia: `reports/t06-clone-validation.json`.

Uso y repetición en [operación y Godot](operacion.md#api-y-godot) y [README](../README.md). La ampliación de perfiles y selección se valida por separado; los registros anteriores conservan el alcance de sus respectivas etapas.

<a name="continuidad-agente"></a>

## Continuidad del proyecto — 2 de noviembre de 2026

### Trabajo posterior autorizado: legibilidad de la consola

El usuario solicitó una presentación limpia y profesional del menú, CV, puesto, sesión, inicio y respuestas, sin interfaz gráfica avanzada. Se implementó `harness/application/console_view.py` y se adaptó la consola: bloques numerados para pregunta/respuesta/evaluación, 78 columnas, secciones y espacios. `/respuestas` lista preguntas enviadas; `/respuesta N` muestra la respuesta completa y su evaluación asociada sin generar otra; `/menu` muestra la ayuda. Las consultas no consumen preguntas ni alteran el historial. Los fallos conservan su número y no exponen respuestas incompletas. El orden respuesta → evaluación se conserva.

Guía actualizada: `docs/operacion.md#consola`; vista previa con respuestas de la sesión guardada a6616bd6: `outputs/previews/console-presentation.txt`. No se leyó la configuración privada ni se consultaron modelos. No se modifican prompts, fuentes aprobadas, evaluador, clasificador, puntuación o contratos. El estado 12/12 y el cierre de calibración del MVP siguen vigentes.

Verificación de presentación: 250 casos dirigidos distintos con resultado más reciente satisfactorio. Primera ronda 249/250; la única expectativa fallida se adaptó a los saltos de línea del mensaje de contexto. Repetición final 70/70, incluyendo consola, sesión, consultas y rechazo de contexto tras ajustar el pie del cierre. No sumar repeticiones ni afirmar que se repitió toda la suite de 1810. Evidencia: `outputs/results/console-presentation-verification.json`; sesión de ejemplo intacta, trece fuentes comprobadas contra el cierre sin cambios.

### Estado vigente: MVP del evaluador cerrado y aceptado

El usuario cerró y validó explícitamente el Bloque 11 y aceptó los resultados de Claridad 12/12 y Neutralidad 9/12 como suficientes para el MVP. Indicó que no se invertirán más recursos intentando alcanzar inferencia perfecta en casos límite como E11 y E30 con la configuración local actual. El plan vigente queda **12/12 bloques completados dentro del alcance del MVP**. El Bloque 12 ya estaba implementado y se actualizó con este cierre documental. No reabrir calibración ni ejecutar inferencias adicionales por las discrepancias conocidas sin una nueva solicitud del usuario.

Acta vigente: `docs/evaluador.md#cierre-mvp-evaluador`; lista: `docs/evaluador.md#estado-bloques-evaluador`; aceptación separada de la evidencia experimental: `outputs/results/evaluator-mvp-acceptance-20261102.json`. Las métricas, E11 sin corregir, E30 y otras diferencias permanecen intactas como limitaciones aceptadas de la configuración evaluada. Última suite técnica: 1810 aprobadas. Este cierre solo modifica documentación/estado y no ejecuta modelos o pruebas de nuevo. Godot/interfaz gráfica y evaluación global 1–7 están fuera de este plan y requerirían una fase nueva expresamente solicitada.

### Historial: calibración ampliada de Claridad y Neutralidad

El usuario solicitó añadir literalmente una instrucción que separa comprensibilidad/referentes de tono, inducción o formato cerrado, y evaluar al menos diez casos nuevos fuera de las seis demostraciones. La instrucción ya está en `agent/evaluator.md`; la aclaración adicional impide penalizar automáticamente neutralidad por ser cerrada. Se preservan la rúbrica 1.1.0, Regla Crítica, referencias y seis ejemplos aprobados. El prompt previo está en `outputs/baselines/evaluator-before-clarity-separation-20261102.md`.

Muestra prefijada: doce nuevos E01/E04/E09/E10/E17/E18/E19/E24/E25/E26/E28/E30 y E11 aparte como regresión. Los doce excluyen E05/E07/E08/E11 del piloto anterior y los seis ejemplos; todos son desarrollo aprobado. `scripts/calibrate_evaluator_clarity.py` guarda caso a caso, permite continuar solo pendientes con fuentes idénticas y no reintenta transporte. Pasaron 46 pruebas dirigidas. Lote local completado: `outputs/results/evaluator-clarity-expanded-8818f677-14ed-4c76-bcb3-c703f29bed0a.json`. El ejecutor admite `--resume` para futuras interrupciones, pero este lote ya no tiene casos pendientes. Guía: `docs/evaluador.md#calibracion-ampliada-claridad-neutralidad`. No solicitar nuevamente aprobación de referencias, regla o uso de Ollama autorizado para esta evaluación.

Lote completado: los doce casos nuevos obtuvieron análisis válido al primer intento, Claridad 12/12, Neutralidad 9/12, cuatro criterios/global 5/12. No se ajustaron referencias o ejemplos. E10/E19 obtienen N4 frente a N3; E30 N4 frente a N2 omite una revisión presupuesta no confirmada. E17/E18/E28 conservan C3/C2/C2, respectivamente. E28 presenta razones genéricas/incompletas; el acuerdo numérico no acredita todo el fundamento.

E11 agotó 90,05 s inicialmente. Se anunció y ejecutó una sola comprobación posterior tras completar el lote, sin elevar límites: `outputs/results/question-evaluation-f2dafe39-f60d-4cc7-84c8-d20e272d7514.json`, 58,83 s, resultado 3/2/3/2 frente a 3/2/4/2. Su razón de claridad es «El uso de», incompleta. No dar E11 por resuelto ni afirmar que su causa siga siendo el tono: la explicación no permite determinarlo. Se preservó el fallo inicial. Total 14 solicitudes locales; trece análisis obtenidos, uno ausente por timeout. No repetir el lote para buscar mejores notas.

Suite completa final: **1810 pruebas aprobadas en 333,02 s**, sin fallos, errores u omisiones. Cuarenta y dos fuentes previas intactas; solo se modificó el prompt autorizado y se añadieron ejecutor/pruebas/documentación. Versión de 45 archivos congelada durante evaluación/suite. `outputs/results/evaluator-clarity-expanded-summary.json` y `outputs/results/evaluator-clarity-expanded-verification.json` consolidan resultados y huellas. El bloque 11 sigue abierto para E11, neutralidad en E10/E19/E30 y calidad de razones; los 12 nuevos ya están evaluados y no requieren continuación.

### Estado anterior: Regla Crítica y calibración inicial

El usuario aprobó explícitamente las 40 referencias revisadas 1.1.0, sus contextos, la Regla Crítica de máximo En desarrollo ante cualquier criterio en 1 y las seis demostraciones. El conjunto activo es `data/reference_questions/evaluacion_calidad_aprobada.json`. Se conservan los JSON original y de propuesta con sus bytes previos; la copia aprobada identifica al revisor y registra su procedencia. Solo cambiaron los globales derivados E09/E10/E12 al aplicar la regla autorizada; niveles y contextos aprobados se preservaron.

Rúbrica activa 1.1.0, protocolo/análisis 1.2.0, registros nuevos 1.3.0 y sesiones 1.3.0. La nueva regla conserva promedio/porcentaje, no eleva Inicial y no imputa global en parciales. La rúbrica 1.0.0 de sesiones anteriores mantiene su comportamiento y feedback; su archivo está en `config/evaluation.legacy-1.0.0.json`. Seis demostraciones activas por defecto (E03/E05/E07/E08/E12/E15), todas de desarrollo; huellas en `config/evaluator_few_shot.json` y metadatos `few_shot` en cada registro. `--no-evaluator-examples` desactiva solo estas demostraciones en los dos inicios y en `scripts.evaluate_questions`.

Guía vigente: `docs/evaluador.md#calibracion-evaluador-few-shot`. Pasaron 400 pruebas dirigidas, incluidas las 256 combinaciones de niveles. El primer A/B local mostró E05 exacto con Few-Shot frente a 3/3/3/3 sin ejemplos, pero se detuvo al fallar E07 sin ejemplos por inventar una discrepancia sin clasificación. Ese informe se conserva: `outputs/results/evaluator-few-shot-ab-610b47e1-50a1-4dd4-8602-21997a2afcda.json`. Se corrigió el formato nativo para exigir discrepancias vacías cuando la clasificación es null y se reinició el contraste completo. No se alteraron referencias ni se repitió una versión idéntica buscando éxito. La aprobación ya está resuelta y no debe volver a solicitarse.

Piloto final completado: ocho evaluaciones aceptadas al primer intento sobre E05/E07/E08/E11, comparando con/sin ejemplos. Coincidencia completa 0/4 → 3/4 y niveles por criterio 8/16 → 15/16. Los tres casos exactos estaban en las demostraciones; E11 es desarrollo fuera de la selección, mejora neutralidad a 2 pero mantiene claridad 3 frente a 4. No es precisión ciega/general. El contraste de E08 usa la entrada aprobada sin historial; no se volvió a evaluar la sesión original completa. Ocho generaciones en la versión final y doce contando el ensayo detenido, sin API externa ni configuración privada. Consolidación: `outputs/results/evaluator-calibration-summary.json`; guía de evidencia: `docs/evaluador.md#pruebas-calibracion-evaluador-few-shot`. Estado: 11/12 bloques implementados, solo calibración ampliada pendiente.

Suite completa final: **1803 pruebas aprobadas en 316,44 s**, sin fallos, errores u omisiones. Selección previa: 400, no sumarla al total. `outputs/results/evaluator-calibration-verification.json` registra versiones, aprobación, ejemplo 85 % → En desarrollo, tres cambios globales derivados, dieciséis fuentes protegidas intactas y código congelado durante calibración/suite. Siguiente trabajo: separar claridad de neutralidad/forma cerrada en desarrollo y ampliar la evaluación sin introducir los diez casos de comprobación conocida en las demostraciones. No volver a solicitar aprobación de las 40 referencias o de la Regla Crítica.

### Historial: estabilización previa a la aprobación

Evaluador/protocolo/análisis 1.2.0, rúbrica 1.0.0 y sesiones 1.3.0. Generación con evidencia obligatoria para niveles numéricos, contexto restringido por petición y diagnóstico seguro con campo, regla y límite para la única reparación. El formato nativo evita el conflicto entre patrón no blanco y límites de longitud; Python conserva el contrato estricto completo. Lectura compatible de evaluaciones 1.0.0/1.1.0. El candidato y el clasificador no cambian.

Se conservaron dos pilotos previos con fallos y se corrigió el formato a partir del diagnóstico. En la versión final, las intervenciones 4 y 6 de la sesión a6616bd6 se evaluaron al primer intento en 65,93 y 62,07 s. No son métricas de precisión general. Persiste un motivo que presupone objetivo explícito cuando es null. Evidencia: `docs/evaluador.md#estabilizacion-evidencia-evaluador`; lista vigente: `docs/evaluador.md#estado-bloques-evaluador` (12 bloques, 10 con implementación, 2 sin cierre). Las 40 propuestas del evaluador siguen pendientes de revisión humana; no se confundieron con las referencias aprobadas del clasificador.

Verificación final: **1517 pruebas aprobadas en 300,45 s**, sin fallos, errores u omisiones. Selección previa: 109, sin sumarla a la suite completa. Informe consolidado: `outputs/results/evaluator-evidence-verification.json`; doce fuentes protegidas intactas y código final congelado durante la suite. Ocho generaciones locales entre las tres versiones comprobadas; ninguna API LLM externa ni lectura del archivo privado.

### Estado del clasificador conservado

Intérprete 1.5.0, prompt base 1.4.1, seis demostraciones aprobadas de desarrollo y protocolo LLM 1.3.0. Activo por defecto; --no-classifier-examples lo desactiva. Suite final: 1500 aprobadas en 277,82 s. En tres contrastes conocidos, sin ejemplos hubo 0/3 coincidencias y con ejemplos 2/3: se corrigieron directiva en el escenario y factualidad del conteo; comunicación sigue otro. No se considera validado el clasificador completo. Informe: `docs/clasificador.md#few-shot-clasificador`. Historial y decisiones anteriores más abajo.

### Punto de partida

Raíz: `C:\Users\franc\Downloads\Ejemplo_de_proyecto`. Python del proyecto: `.venv/Scripts/python.exe` (3.14.3). Las nueve etapas del agente candidato están completadas en su alcance técnico. El usuario solicitó desarrollar el clasificador híbrido descriptivo siguiendo bloques con revisión entre etapas. El avance actual se detalla al final; no empezar automáticamente otro bloque, rúbrica, puntuación, retroalimentación o Godot.

### Fuentes y decisiones que conservar

- Perfil aprobado: `data/candidates/candidato_junior.json`, Nicolás Vera Soto, `cand-001`. Fecha ficticia del escenario **2026-10-20**, independiente de la fecha real.
- Puesto: `data/jobs/desarrollador_junior.json`, Aplicaciones Nexo, Desarrollador de Software Junior.
- Configuración: `config/interviews/basica.json`. Máximo **20 preguntas enviadas**, incluyendo fallos.
- Reglas del candidato: `agent/agent.md`, versión **1.0.13**. No modificar antecedentes aprobados para acomodar respuestas.
- Historial completo guardado en sesiones JSON locales; las respuestas completas alimentan la conversación, los intentos fallidos no. Resumen extractivo opcional en local, con auditoría y registro original conservado.
- Documentación histórica: `docs/estado-del-proyecto.md#estado-etapas`, `docs/validacion-del-candidato.md#validacion-final`. Su validación de 738 pruebas y veinte preguntas corresponde a esa versión; hubo ampliaciones posteriores.

### Proveedores y último estado confirmado

- Inicio actual: `.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview`.
- Opción 1: Ollama local, selección de modelo del archivo privado; modelo utilizado **gemma4:e4b**. El adaptador local conserva máximo de salida **512**. El predeterminado del adaptador sigue siendo gemma3n:e2b si no hay selección explícita.
- Opción 2: UNAB IA, **gemma4:26b**, `https://quotas.devhub.cl/api/v1/chat/completions`. Adaptador independiente en `harness/llm/unab_client.py`; el adaptador Responses anterior se mantiene separado.
- Configuración privada: `config/llm.local.json`, ignorada por Git. No leer, imprimir, copiar ni pedir su clave para retomar el proyecto. Plantilla pública: `config/llm.local.example.json`.
- UNAB usa **2048 tokens máximos de salida por defecto**, campo opcional `api_max_output_tokens`, rango 16–4096. El selector muestra el presupuesto. No aumentar límites ni repetir generaciones automáticamente.
- Se solicita `reasoning_effort: none`, pero no se ha confirmado su aplicación interna por la pasarela. La ausencia de campos de razonamiento no demuestra ausencia de procesamiento interno.
- Con 512 se observó `finish_reason: length` y contenido vacío. Con 2048 el usuario repitió exactamente la misma pregunta de Flask/PostgreSQL: respuesta completa, **6058 tokens de entrada, 1255 de salida, 7313 totales**, 12,82 s, cero incidencias.
- Evidencia exitosa: `outputs/sessions/session-162df680-88d6-40ca-9e8f-d095fae07025.json`, `outputs/results/unab-usage-162df680-88d6-40ca-9e8f-d095fae07025.json` y `outputs/results/unab-success-confirmation-162df680-88d6-40ca-9e8f-d095fae07025.json`.
- Diagnósticos de uso sin clave, cuerpo bruto ni razonamiento: `outputs/results/unab-usage-<UUID>.json`. No equivaler créditos UNAB a tokens: su fórmula no se conoce. Se reenvían aproximadamente 6000 tokens de contexto por pregunta; no se ha optimizado ese contexto.

### Pruebas y límites de lo comprobado

Última suite completa, después del contrato de citas: **1262 passed in 161.98s**, con **1080 unitarias y 182 integraciones**, cero fallos, errores u omisiones, en 60 módulos. Guía y evidencia: `docs/clasificador.md#citas-y-posiciones-clasificador`. Sustituye como resultado más reciente a las 1230 pruebas del correctivo anterior; los conteos históricos conservan su alcance. No repetir pruebas o llamadas de pago sin cambios o dudas que lo justifiquen. HTTP está simulado o bloqueado en los transportes síncronos de pytest. Las evaluaciones locales del clasificador se registran aparte, sin respuestas del candidato; las confirmaciones reales anteriores no demuestran consistencia universal.

### Forma de trabajo solicitada

Responder en español, breve y claro. Agrupar trabajo en bloques verificables para reducir vueltas y tokens de chat. Consultar primero archivos concretos; evitar leer registros y todo el repositorio sin necesidad. Mantener la integridad del perfil. Distinguir evidencia, hipótesis y validación técnica de revisión semántica humana. No avanzar de fase sin indicación del usuario. Respetar el orden del prompt maestro del clasificador antes de implementar componentes nuevos.

### Clasificador híbrido — nuevo trabajo autorizado

- El usuario aportó el prompt maestro de la etapa 2 del MVP. El clasificador será descriptivo, híbrido y previo a la respuesta del candidato. Calidad, puntuación, retroalimentación y análisis jurídico siguen fuera de alcance.
- Bloque 1, auditoría: completado por inspección de controlador, clientes, historial, configuración, esquemas y pruebas; no se ejecutaron nuevas pruebas ni llamadas al proveedor.
- El usuario informó que subió una copia a `https://github.com/Italoktrone/Simulador_entrevista`. La copia remota no se ha verificado. La consulta local de Git posterior ya se ejecuta sin el error de ausencia de repositorio.
- Tras la autorización «comienza», se redactó el bloque 2 en `docs/clasificador.md#clasificacion`. El posterior «Procede» aprobó avanzar al contrato con ese diseño v0.1; en ese momento todavía no había implementación del clasificador.
- Decisiones operativas conservadas: directiva requiere delimitación explícita; listas de datos sin explicación se consideran cerradas; una composición clara sin predominio conserva sus etiquetas y carece de principal. Esto no aprueba automáticamente las futuras referencias de clasificación.
- El esquema actual admite modalidades y enfoques como configuración; los estilos son abierta/cerrada/directiva. No existe competencia seleccionada por turno. La oferta solo enumera competencias a explorar.
- Integración futura: `InterviewRuntime.ask()` en `harness/runtime.py`, antes de los mensajes definitivos del candidato. Reutilizar `LLMClient.generate`, con contexto/parámetros independientes; política de respuesta separada. Los esquemas de sesión son estrictos y deberán ampliarse conservando lectura de sesiones anteriores.
- Bloque 3 completado de forma aislada: `schemas/question_classification.schema.json` (contrato 1.0.0), `harness/classification_contract.py` (estructura y relaciones), `tests/unit/test_classification_contract.py` y guía `docs/clasificador.md#contrato-clasificacion`. No modifica el runtime, formatos previos ni dependencias.
- El validador exige identidad/texto originales y lista de turnos autorizados por el llamador. Comprueba fragmentos literales, jerarquía, agregación, contexto y procedencia; devuelve copia con `validation_status=validada`. El sello recibido nunca evita validar de nuevo. No demuestra corrección semántica ni autoriza justificaciones como instrucciones.
- No evaluable: clasificación nula y sin unidades. Composición sin predominio: principales nulos con etiquetas presentes conservadas. Falta de información: etiquetas indeterminadas, sin error técnico. Fallo técnico terminal: `evaluability=null`, método respaldo, clasificación indeterminada y código separado; no inventa evaluabilidad. La producción de respaldos y reparación de JSON se implementó posteriormente en el bloque 6.
- Verificación final del bloque 3: **268 passed in 13.39s**, ejecutando contrato nuevo y regresiones de `test_schema_validator.py`, `test_interview_config_schema.py`, `test_session_log.py`, `test_history_flow.py` y `test_unab_and_selector.py`. No es la suite completa. Las pruebas del proveedor simulan HTTP; no hubo llamadas reales ni lectura del archivo privado.
- Incidencia de ejecución resuelta: el directorio temporal predeterminado de pytest no era accesible. Se usó una ruta nueva y verificada bajo `outputs/tmp` (crear el padre primero). Antes de la ampliación final, las 103 pruebas iniciales del contrato pasaron en 4,58 s; no contar los fallos de preparación como fallos funcionales del contrato. Véase el comando reproducible en la guía.
- El usuario autorizó el bloque 4 mediante «Continuar» y aprobó posteriormente los 40 ejemplos mediante **«Apruebo»**. La tabla `docs/clasificador.md#referencias-clasificacion-propuesta` queda aprobada y congelada en versión **1.0.0**, con contexto, enfoques, formas, atributos, certeza, justificación, dificultad y detalle de segmentación. Son 32 evaluables y 8 no evaluables. Se formalizó en `data/reference_questions/clasificacion_basica.json` (JSON único con metadatos y casos, no JSONL).
- Los contextos de prueba usan roles explícitos; cuando describen al candidato, se basan en S1/S4, formación y MesaFaro del perfil aprobado. No son sesiones reales ni añaden antecedentes. R03 incluye una preferencia de enfoque simulada sin modificar la configuración actual.
- División aprobada: 30 de desarrollo y 10 de comprobación conocida (R09, R10, R17, R23, R24, R25, R29, R30, R39, R40). No es prueba ciega ni independiente, ya que todos los ejemplos están visibles y algunos contrastes ya se conocían del diseño. Se excluirán los diez del ajuste inicial de reglas/prompt; una evaluación independiente posterior requerirá casos nuevos.
- Verificación editorial del bloque 4: 40 filas de ocho columnas, R01–R40 únicos y consecutivos, 32 evaluables (28 claras, 2 ambiguas, 2 indeterminadas), 8 no evaluables; los 8 fragmentos de los 4 casos compuestos coinciden literalmente y en orden con sus originales. Se comprobó el formato de las diferencias y ausencia de cambios en perfil, oferta, instrucciones, configuración, runtime y dependencias. No se repitieron pruebas de código porque solo se editaron documentos. Esta comprobación no valida las etiquetas semánticas ni produce métricas de clasificación.
- Formalización completada: `schemas/classification_references.schema.json` valida la envoltura; `harness/classification_references.py` carga y valida las expectativas, aísla contextos por caso y devuelve copias. `cases()` expone solo desarrollo por defecto; comprobar los otros diez exige `split="comprobacion_conocida"`. `input_for()` excluye etiquetas esperadas, dificultad y notas de revisión para la futura entrada del clasificador.
- Se añadió `validate_classification_expectation` en `harness/classification_contract.py`: comparte esquema y relaciones del contrato 1.0.0, excluyendo método, reglas, error técnico y sello de validación, que no existen en expectativas humanas. El contrato completo de resultados no cambió. No se inventaron ejecuciones de reglas/LLM ni se alteraron las etiquetas aprobadas.
- Verificación final de formalización: **215 passed in 64.02s**, con `test_classification_references.py`, `test_classification_contract.py`, `test_reference_cases.py` y `test_schema_validator.py`. Es una selección técnica, no la suite completa ni una evaluación de clasificación. No hubo llamadas API ni lectura de la configuración privada. Las pruebas verifican los 40 textos contra la tabla aprobada, la partición, los fragmentos y la preservación de fuentes y referencias anteriores.
- La huella canónica de los 40 casos queda fijada en las pruebas: `b159f61b67cdb5561cb5ef22e67cf5cc1935cc49792f353ae17a3907d944e371`. Es independiente del formato y saltos de línea de JSON. Cambios semánticos posteriores requieren motivo, revisión y actualización de versión; no se ajustan etiquetas para coincidir con el clasificador.
- El usuario autorizó el bloque 5 mediante «sigue». Se implementó `harness/question_classifier.py`, versión local **1.0.0**, con 18 reglas identificadas (entradas simples no evaluables, episodios, hipótesis, datos técnicos, comparación, fechas, preferencias/alternativas, sugestiva explícita, delimitaciones directivas y acción posterior sin contexto). Catálogo y límites: `docs/clasificador.md#reglas-locales`. Sin dependencias nuevas.
- `classify_local(...)` devuelve una `LocalDecision` inmutable. `clasificada` contiene un resultado que ya pasó el contrato completo, con método reglas e IDs aplicados. `abstencion` contiene `result=None` y motivo controlado: no es indeterminación por contexto ni error técnico y no invoca LLM. Las preferencias no fuerzan etiquetas; se conserva original y offsets. No se leen perfiles, referencias, sesiones ni archivo privado desde el clasificador.
- Las plantillas deben coincidir con toda la petición; vocabulario acotado y guardas limitan decisiones. Las citas, compuestas y premisas no soportadas se abstienen, sin dividir por cada y. Una comparación o lista técnica soportada sí puede ser una unidad. Los conflictos entre reglas se abstienen, sin elegir la primera. Las preguntas autocontenidas pueden resolverse localmente con historial disponible sin utilizarlo; las repreguntas que requieren interpretarlo se abstienen. La ausencia verificable de antecedente en una petición de acción posterior puede dar clasificación indeterminada local.
- Verificación final del bloque 5: **185 passed in 33.35s**, con `test_question_classifier.py`, `test_classification_contract.py` y `test_history_flow.py`. Es selección técnica, no suite completa. Incluye contrato, gramáticas y contrastes, abstenciones, conflicto de reglas, copias, contexto/configuración, protección de fuentes y regresión del historial con HTTP simulado. No hubo llamadas reales al proveedor ni lectura del archivo privado.
- Comprobación de desarrollo (solo los 30): **16 resultados y 14 abstenciones**, sin discrepancias en etiquetas, texto, referencias y estructura comparados de los 16. Incluyen seis no evaluables y una clasificación indeterminada; no afirmar 16 preguntas claras ni 100 % sobre los 30. Evidencia: `outputs/results/local-rules-development-da0ce49786594a4281cda41ef06d8725.json`. Es comprobación de desarrollo conocido, no evaluación independiente ni métricas del híbrido.
- No se ejecutaron clasificaciones de los diez de comprobación conocida para ajustar reglas. El cargador sigue validando estructuralmente las 40 anotaciones; eso no equivale a evaluar el clasificador sobre ellas. Textos, etiquetas, división y huella canónica aprobados permanecen sin cambios.
- El usuario autorizó el bloque 6 mediante «continua». Se implementaron `harness/llm_question_classifier.py` y `agent/classifier.md`, versiones **1.0.0**. Guía y comandos: `docs/clasificador.md#clasificacion-llm`. Cliente inyectado, prompt independiente del candidato, categorías oficiales y esquema sin ejemplos de comprobación. Sin dependencias nuevas ni integración al runtime.
- El modelo devuelve etiquetas sin método, reglas, error técnico ni sello. `classification_expectation_schema()` expone la proyección compartida; el programa valida y añade procedencia LLM antes de revalidar el contrato completo. Se añadió `parse_json_text` a `json_loader.py`, reutilizando rechazo de duplicados y números no finitos, sin modificar el cargador de archivos.
- Se compartió la validación de entrada en `harness/classification_input.py`, conservando conducta y reglas locales. El intérprete recibe una copia de texto/configuración/fragmentos ya seleccionados de la misma sesión; no carga perfiles, sesiones ni clave privada. Los roles históricos son datos en el mensaje user, nunca nuevas instrucciones system. No conserva historial entre llamadas.
- Recuperación: solo una regeneración tras JSON o contrato inválidos; no se reinyecta salida rechazada ni mensajes de excepción. Máximo dos llamadas generate, con mismo modelo/presupuesto. Error de proveedor, espera, autenticación o corte de salida devuelven respaldo técnico sin regeneración. Se propagan cancelaciones del usuario. El respaldo tiene evaluabilidad nula y código técnico separado, validado por el contrato; no simula falta de contexto.
- `create_client` admite overrides opcionales de modelo y salida para un cliente nuevo. Sin overrides conserva todos los valores del candidato. `create_classification_client` reutiliza fábrica/adaptadores/autenticación y exige las mismas autorizaciones externas. `ClassificationLLMSettings` hereda el modelo seleccionado por defecto y usa **2048 tokens de salida para el clasificador**, configurables 16–4096; no aumenta el presupuesto tras fallos. Esto no cambia los 512 locales/Responses del candidato ni su presupuesto UNAB elegido. No se modificó el selector ni el archivo privado.
- La auditoría `LLMClassification` guarda intentos, códigos controlados, métricas informadas permitidas y huella de instrucciones/esquema. No guarda cuerpos, salidas rechazadas, credenciales, mensajes de excepción ni razonamiento; métricas ausentes permanecen desconocidas. El modelo puede compartir proveedor y modelo con el candidato, con contextos y parámetros separados.
- Incidencias corregidas: una prueba suponía incorrectamente que un JSON profundo válido debía rechazarse (ahora se comprueban JSON incompleto y error de recursión por separado). La integración detectó que Responses informa `finish_reason=completed`; el intérprete lo admite específicamente para ese adaptador, además de stop/None según el contrato existente. No se cambiaron adaptadores para resolverlo.
- Verificación final del bloque 6: **364 passed in 46.38s**, con `test_llm_question_classifier.py`, `test_classification_llm_clients.py`, `test_llm_factory.py`, `test_json_loader.py`, `test_classification_contract.py`, `test_question_classifier.py`, `test_unab_and_selector.py` y `test_all_expectations_pass_shared_contract_without_generated_metadata` de las referencias. No es suite completa. Todos los clientes y HTTP fueron simulados; no hubo llamadas reales, lectura de clave privada ni evaluación de modelos reales.
- Las referencias aprobadas, su huella y división siguen intactas. No se clasificaron los diez de comprobación conocida mediante LLM; la regresión solo valida sus anotaciones estructuralmente. No hay nuevas métricas de acierto, consumo real o latencia real del clasificador.
- El usuario autorizó el bloque 7 mediante «siguiente bloque». Se implementó `harness/hybrid_question_classifier.py`, versión **1.0.0**, con guía `docs/clasificador.md#clasificador-hibrido`. Inyecta el intérprete existente, copia la entrada y evalúa las reglas exactamente una vez. Solo la abstención local invoca una vez al intérprete. No añade dependencias, reglas, validadores, autenticación, presupuestos o bucles de reparación.
- `HybridQuestionClassifier.classify(...)` conserva la interfaz de entrada común y devuelve `HybridClassification` inmutable, con resultado completo y copias de traza. `route=reglas` termina localmente; `route=llm` indica delegación aun si terminó en respaldo. `status` distingue clasificación y respaldo. La traza conserva decisión local e intentos LLM sin duplicar los resultados ni enviar motivos locales al modelo como instrucciones.
- Los no evaluables locales y las indeterminaciones verificables por ausencia de antecedente terminan sin LLM. Las preguntas autocontenidas pueden seguir resolviéndose localmente con contexto disponible. Ante fallo del intérprete se conserva su respaldo validado, sin volver a probar reglas ni otro proveedor. Cancelación y errores de entrada se propagan sin reintentos añadidos.
- La estrategia es híbrida, pero `result.method` mantiene su procedencia efectiva: reglas, llm o respaldo. No se asigna falsamente hibrido por haber intentado reglas que se abstuvieron. Las compuestas se entregan completas en una sola invocación al intérprete; no se divide por cada y, mezcla etiquetas parciales ni genera una llamada por unidad. La reparación continúa siendo única y propiedad del intérprete, con máximo dos generate por delegación según el bloque 6.
- Verificación final del bloque 7: **291 passed in 57.06s**, con `test_hybrid_question_classifier.py`, `test_hybrid_classification_flow.py`, `test_question_classifier.py`, `test_llm_question_classifier.py`, `test_classification_contract.py` y `test_history_flow.py`. No es suite completa. Incluye orden, ausencia de llamadas en ruta local, delegación, reparación acotada, respaldo, copias, contexto, los tres adaptadores con HTTP simulado y regresión de historial. Sin llamadas reales ni lectura de clave privada.
- La prueba de enrutamiento sobre los 30 de desarrollo mantiene 16 locales y 14 delegaciones. Estas 14 usan un proveedor deliberadamente fallido para contar llamadas sin usar etiquetas esperadas como respuestas: son respaldos simulados, no fallos observados ni métricas semánticas del híbrido. Los diez de comprobación conocida no se ejecutaron para clasificación o ajuste; la carga valida estructuralmente las 40 anotaciones. Referencias, etiquetas y partición aprobadas siguen intactas.
- El candidato, runtime, contador de veinte, perfil, configuración, presupuesto y sesiones actuales siguen sin cambios por el bloque 7. No se implementó política de respuesta ni evaluación de calidad.
- El usuario autorizó el bloque 8 mediante «sigue». Integración completada en `harness/runtime.py`, con política independiente en `harness/response_policy.py` y contexto/validación de bitácora en `harness/intervention_log.py`. Guía: `docs/clasificador.md#integracion-clasificador`. La secuencia activa es clasificación -> revalidación/política -> metadatos autorizados -> candidato -> registro. No añade dependencias ni cambia perfil, puesto, fecha ficticia, instrucciones 1.0.11 o categorías aprobadas.
- El inicio habitual `scripts.start_interview` activa ahora `--classify`; conserva modelos, clave, formato privado y selección local/API. `scripts.run_interview --classify` permite modelo y presupuesto independientes por flags; sin flag y con Runtime sin clasificador se conserva la ruta anterior para compatibilidad. No ejecutar el inicio real desde herramientas para comprobarlo: las pruebas usan transportes simulados.
- Política 1.0.0: certeza clara -> responder; ambigua/indeterminada -> pedir reformulación; no evaluable -> aviso; error técnico -> aviso específico. Los avisos son del simulador, no respuestas del candidato ni nuevas preguntas enviadas. Cerrada/directiva/sugestiva no implican rechazo y una composición clara sin principal sí puede responderse. No hay clasificación jurídica ni evaluación de calidad.
- Solo los intentos enviados al candidato consumen el máximo de 20, incluso si fallan o quedan incompletos. Clasificación, reparaciones, no evaluables y avisos de aclaración no lo consumen. El historial del candidato sigue usando solo pares completados; no se incorporan intentos fallidos ni avisos. En modo integrado `ask` devuelve LLMResponse o ResponsePolicyDecision; la consola distingue ambos y registra incluso vacío/espacios tras iniciar.
- Contexto del clasificador: hasta dos pares completos recientes de esta sesión, hasta 1200 caracteres literales de cada mensaje desde su primer carácter no blanco. Excluye fallos, respuestas parciales y otras sesiones. Es ventana determinista, no selector semántico; puede faltar un antecedente y se pide reformular. El registro permite reconstruir los fragmentos desde las fuentes completas sin reescribirlas.
- Metadatos al candidato: solo versión/acción/enfoques/formas/atributos/certeza comprobados y plantillas controladas. No se copian justificaciones, trazas ni texto de error como órdenes system. `prompt_builder` y `summary_context` admiten ese argumento opcional; la memoria extractiva prepara y audita los mensajes incluyendo sus metadatos reales. Perfil verificado antes/después de clasificar y generar.
- Sesiones nuevas integradas **1.2.0**: añaden classification_policy e interventions, enlazando cada envío con su attempt existente. `schemas/intervention.schema.json` y `validate_interventions` controlan identidad, texto, fechas, fuentes/contexto, política, contador, procedencia y auditoría LLM. Se mantienen lectura/guardado de 1.0.0 y 1.1.0; memoria extractiva opcional compatible. No se sobrescriben ni reabren sesiones anteriores.
- Ambos clientes se cierran. Los diagnósticos UNAB del candidato mantienen `unab-usage-<UUID>.json`; los del clasificador se guardan aparte en `unab-classifier-usage-<UUID>.json`, sin claves/cuerpos/razonamiento. La consola muestra activación y presupuesto del clasificador. Las consultas adicionales no se equiparan a créditos ni se inventa consumo real.
- Verificación final del bloque 8: **316 passed in 56.01s**. Selección: `test_response_policy.py`, `test_pre_response_classification.py`, `test_session_state.py`, `test_session_log.py`, `test_prompt_builder.py`, `test_console_interview.py`, `test_summary_context.py`, `test_live_context.py`, `test_session_persistence_flow.py`, `test_live_context_console_flow.py`, `test_unab_and_selector.py`, `test_hybrid_question_classifier.py` y `test_hybrid_classification_flow.py`. No es suite completa. Antes hubo 186 regresiones existentes y 40 pruebas nuevas iniciales; la selección final incluye ampliaciones. Se corrigió la firma de un doble de prueba, sin cambiar para ello la interfaz real.
- La verificación cubre orden previo, política sin rechazos por forma, contador de veinte incluyendo fallos, avisos sin consumo, contexto recortado/fallos excluidos, integridad del perfil, datos falsificados aun con sello validada, memoria y huellas reales, tres versiones de sesión, consola y diagnósticos separados. Todo fue simulado: sin llamadas reales ni lectura de la clave/configuración privada. Las referencias, etiquetas y división aprobadas siguen intactas; no hay evaluación semántica real ni métricas del clasificador.
- El usuario autorizó el bloque 9 mediante «sigue». Regresión amplia completada sin cambiar código del programa: `tests/conftest.py` añade bloqueo automático de HTTP síncrono real conservando el aislamiento; `tests/unit/test_test_isolation.py` aporta dos comprobaciones de ese bloqueo y `tests/integration/test_classifier_regression_flow.py` quince recorridos sobre Ollama, UNAB y Responses con transportes simulados. No se añadieron dependencias ni se leyó el archivo privado.
- Los recorridos nuevos verifican reparación única antes de generar, fallos del candidato contando pero excluidos del historial/contexto siguiente, respaldo técnico sin gasto de pregunta, recuperación local posterior, separación de presupuestos, cierre de clientes, metadatos controlados y uso de inspección/vista previa anteriores sobre sesiones 1.2.0 sin modificarlas. La suite completa conserva también las regresiones de sesiones 1.0.0 y 1.1.0, perfil, cronología, memoria, consola y contador.
- Resultado del bloque 9: **1191 passed in 128.62s**, en una única suite completa; 1023 unitarias y 168 integraciones, cero fallos/errores/omisiones. Incluye las 17 nuevas, que antes pasaron aisladamente en 19,56 s; no sumar ambas ejecuciones. Evidencia compacta derivada de JUnit: `outputs/results/classifier-regression-block9-c0c479236547407da53508b836ff2770.json`. Python 3.14.3, pytest 9.2.0, httpx 0.28.1, jsonschema 4.26.0. La duración de JUnit (128,299 s) tiene alcance propio, no es latencia de modelos.
- Una comprobación auxiliar asíncrona se quedó esperando en este entorno y se interrumpió; se retiró, pues el programa usa clientes síncronos. No aporta resultado aprobado ni integra la suite final. No fue necesario corregir código del programa. Referencias, etiquetas, partición, perfil, puesto, configuración e instrucciones 1.0.11 siguen intactos. No se clasificaron los diez casos de comprobación conocida ni hubo llamadas reales o evaluación semántica real.
- El usuario autorizó el bloque 10 mediante «continua con la siguiente» y pidió el número de bloques completados y pendientes. Al comenzar: 9 de 10 completados y uno en ejecución. Nuevos archivos: `harness/classification_evaluation.py`, `scripts/evaluate_classifier.py`, dos archivos de pruebas correspondientes y `docs/clasificador.md#evaluacion-clasificador`. No se modificaron los clasificadores, categorías, perfil, instrucciones del candidato ni referencias aprobadas.
- El evaluador revalida las predicciones, compara etiquetas/unidades/contexto sin exigir prosa idéntica, calcula métricas exclusivas y multietiqueta separadas, matrices, macro-F1 y tasas operativas con denominadores. Abstenciones/respaldos permanecen como ausencias en la medición, no como indeterminación legítima ni aciertos por atributos vacíos. Conserva discrepancias pendientes de revisión humana. El CLI usa reglas por defecto o híbrido exclusivamente en Ollama local, guarda tras cada caso y admite `--resume` con fuentes/configuración iguales, sin repetir casos terminados. No lee el archivo privado ni elige API externa por variables de entorno.
- Regresión del bloque 10: **1208 passed in 149.74s**, suite completa con 1035 unitarias y 173 integraciones en 57 módulos, cero fallos/errores/omisiones; incluye 12 unitarias y cinco integraciones nuevas. Evidencia: `outputs/results/classification-evaluation-tests-block10-e5b58d96db564c8cb6855bf1903727e8.json`. Las 16 primeras nuevas pasaron aisladamente en 22,54 s, antes de añadir una comprobación adicional incluida en la suite completa. HTTP de pytest siempre simulado o bloqueado.
- Evaluación real de reglas sobre los 40 aprobados terminada, sin llamadas: `outputs/results/classification-evaluation-reglas-f2190943-ffd2-4b3a-a20e-a92c23b17c45.json`. Desarrollo: 16 clasificados coincidentes y 14 abstenciones; comprobación conocida: cero clasificados y diez abstenciones. Total 16/40 de cobertura y coincidencia global; el 16/16 condicionado no equivale a precisión global perfecta. No se ajustaron reglas tras esta comprobación.
- La conexión local inicialmente falló por restricción de socket (WinError 10013); la consulta autorizada fuera de esa restricción confirmó Ollama con gemma4:e2b, gemma4:e4b y gemma3n:e2b. La evaluación real del híbrido con **gemma4:e4b, 2048 tokens de salida** terminó con los cuarenta casos, fuentes congeladas e intactas y máximo dos generaciones por delegación. Informe completo: `outputs/results/classification-evaluation-hibrido-c9639bd7-565f-43b1-ba63-09aabb5bb5fa.json`. Duración observada del lote: 3105,95 s, unos 51 min 46 s; no es tiempo de pytest. No leer la configuración privada, sustituir por UNAB ni repetir llamadas terminadas. El proceso ya terminó con salida cero: no dejarlo descrito como activo ni iniciar otro lote automáticamente.
- Resultado real: **18/40 resultados válidos y coincidentes (45 %)**: dieciséis por reglas y dos por LLM; **22/40 respaldos técnicos (55 %)**. Desarrollo: 16/30 válidos y catorce respaldos; comprobación conocida: 2/10 válidos y ocho respaldos. Los dos resultados LLM aceptados son R39 y R40, ambos no evaluables. Ninguna de las veintidós derivaciones evaluables produjo clasificación LLM validada. El 18/18 condicionado no equivale a precisión global perfecta ni acredita que el modelo clasifique preguntas evaluables.
- Hubo **46 generaciones locales**: 23 JSON inválidos, 21 incumplimientos del contrato y dos validadas; 44/46 inválidas (95,65 %). Veintidós reparaciones utilizadas y ninguna terminada válida. Terminales por caso: trece contrato_invalido y nueve json_invalido. No hubo llamadas externas, lectura de archivo privado o respuestas del candidato. La auditoría no conserva cuerpos rechazados, por lo que no permite atribuir con certeza esos rechazos a un campo concreto ni afirmar que sus etiquetas semánticas fueran erróneas.
- Se calcularon métricas exclusivas/multietiqueta, precisión/recall/F1 y matrices con ausencias técnicas en los denominadores, por grupo y globales. Resumen e índice de los veintidós casos pendientes de revisión: `outputs/results/classification-evaluation-summary-c9639bd7-565f-43b1-ba63-09aabb5bb5fa.json`. Guía, resultados y tabla de avance: `docs/clasificador.md#evaluacion-clasificador`. Referencias, división y huellas permanecen iguales; no se ajustaron reglas, prompt o presupuesto al observar comprobación conocida.
- **Plan original del clasificador: 10 bloques completados y 0 pendientes de ejecutar.** El bloque 10 se cierra como medición con hallazgos, no como aceptación del MVP. **Corrección y reevaluación todavía pendientes:** diagnosticar la conformidad de salida, corregir el mecanismo estructurado sin modificar perfil o referencias y medir otra versión. Toda discrepancia mantiene revisión humana pendiente. Esperar nueva indicación del usuario antes de iniciar esas correcciones, otro lote, calidad, rúbrica, puntuación, retroalimentación o Godot. No presentar los 1208 tests aprobados como prueba de acierto del modelo real.
- El usuario autorizó expresamente el bloque correctivo: logging de salida cruda en tres casos de desarrollo, después `format` de Ollama con JSON Schema estricto y presentación de resultados **antes** de reevaluar los cuarenta. Se ejecutaron R04, R08 y R26 conservando gemma4:e4b, salida 2048, temperatura 0,2 y una reparación máxima. La autorización de logging es específica del diagnóstico y esos casos; no activar raw logging en entrevistas o auditorías normales. Se aclaró que el supuesto de problema exclusivamente de formato aún debía comprobarse.
- Nuevo `scripts/diagnose_classifier.py`: transporte local que guarda message.content sin recortar, antes del parseo, en TXT UTF-8 con huellas y metadatos por intento. No registra thinking, cabeceras, solicitudes o cuerpos HTTP de error. Bloquea otros casos, cambios de entrada, destinos externos, autenticación y tercer intento. Archivos bajo outputs/results, excluidos de Git. Modos `--format prompt` y `--format schema` (predeterminado). No corrige las salidas al diagnosticarlas.
- Etapa anterior al cambio: `outputs/results/classifier-diagnostic-prompt-8ee9a970-7e71-48a0-9c5f-48a9d91a006e/report.json`. Tres casos y seis generaciones: tres JSON legibles, cero conformes al esquema y cero clasificaciones aceptadas. R04 omite campos obligatorios; R08 tiene JSON mal cerrado; R26 omite campos e inventa otros. Los TXT crudos conservan estos fallos concretos.
- Se implementó `output_schema` opcional con instantánea independiente y validación en `harness/llm/ollama_client.py`, transmisión exclusiva a Ollama en `harness/llm/factory.py` y activación por defecto en create_classification_client en `harness/llm_question_classifier.py`. Envía exactamente classification_expectation_schema() en format. El candidato conserva salida libre y presupuesto; UNAB/Responses no reciben el parámetro. structured_output=False permite comparar. No se cambió el prompt, contrato, validador, presupuesto o máximo de reparaciones.
- Etapa con format terminada: `outputs/results/classifier-diagnostic-schema-ff41eb6d-4260-4fd9-9903-bf7af9863e23/report.json`. Tres casos y seis generaciones: **6/6 JSON legibles, 4/6 conformes al esquema, 0/6 conformes al contrato completo y 0/3 clasificaciones aceptadas**. R04 declara final 54 en vez de 72; R08 declara 57/55 en vez de 77 para el fragmento literal completo. Sus rechazos son unit_source_text. R26 repite abierta en forms (uniqueItems) en ambos intentos aun enviando el esquema; las posiciones tampoco coinciden. No prometer que format hace cumplir todas las relaciones o restricciones.
- Las etiquetas observadas de R26 también difieren: factual_tecnico principal donde la referencia tiene null, dos formas abierta frente a cerrada/abierta y directiva añadida. Son observaciones de salidas rechazadas, no clasificaciones validadas ni métricas semánticas nuevas. Próximo paso recomendado: calcular posiciones inequívocas en Python y revisar coherencia/prioridades e interpretación con desarrollo, sin alterar referencias. No declarar resuelto el clasificador ni concluir que el problema es puramente sintáctico.
- Comparación: `outputs/results/classifier-correction-comparison-ff41eb6d-4260-4fd9-9903-bf7af9863e23.json`. Guía con enlaces a los doce TXT: `docs/clasificador.md#correccion-salida-clasificador`. Fuentes protegidas (perfil, puesto, configuración, instrucciones 1.0.11, prompt, contrato y referencias) intactas. Los tres cambios de código existente se hicieron entre etapas; las fuentes respectivas quedaron iguales durante cada lote. No hubo clave privada, API externa o respuesta del candidato.
- Verificación correctiva: **1230 passed in 274.06s**, suite completa de 1050 unitarias y 180 integraciones en 59 módulos, cero fallos/errores/omisiones; incluye quince nuevas de format y siete de logging. Antes: siete de logging en 1,51 s y selección de 132 en 3,23 s. Evidencia: `outputs/results/classifier-correction-tests-53624a13820640c2bd64db768765437b.json`. No sumar selecciones a la suite. Ambos pilotos reales ya terminaron; **no se reevaluaron los cuarenta y se espera revisión del usuario antes de otra ejecución o corrección**. Los 18/40 iniciales corresponden a la configuración anterior sin format.
- El usuario aprobó la siguiente corrección: contrato/prompt con quote en vez de posiciones del modelo, búsqueda literal con Python, enums/unicidad reforzados y repetición de los mismos tres casos. Se preservó el contrato público de resultados y referencias 1.0.0 para compatibilidad; el protocolo exclusivo del modelo y el intérprete pasan a **1.1.0**. No asumir que los enums resuelven por sí solos la interpretación.
- Nuevo `harness/llm_classification_contract.py` y esquema exportado `schemas/llm_question_classification.schema.json`. El esquema deriva vocabulario del contrato aprobado, exige quote y prohíbe text/source_start/source_end en unidades del modelo. Python usa find para el alineamiento más temprano y rfind para el más tardío: solo publica posiciones si ambos coinciden. No recorta, normaliza, reformula, escoge arbitrariamente una repetición ni admite solapamientos. Citas repetidas pueden resolverse por su orden conjunto cuando el alineamiento es único. Se vuelve a validar el resultado público completo.
- uniqueItems ya existía; se conserva. `classification_generation_schema` añade enum de conjuntos canónicos únicos permitidos para impedir duplicados en la generación nativa aun si el motor ignora uniqueItems. No agrega categorías ni elige principal por orden; el parser acepta cualquier permutación única semánticamente válida. Una unidad admite una sola forma y razón de forma null. El prompt 1.1 refuerza códigos permitidos, razones de prioridad null cuando corresponde, listas finitas cerradas y que composición/tema técnico no bastan para directiva. No contiene preguntas/respuestas de comprobación.
- El intérprete y la fábrica usan el esquema nuevo; el diagnóstico valida quote y registra versión 1.1.0. Las huellas del evaluador/diagnóstico incluyen el módulo y esquema nuevos. Las sesiones conservan sus datos; `schemas/intervention.schema.json` admite trazas LLM 1.0.0 y 1.1.0. Los dobles de pruebas se migraron al protocolo nuevo; referencias, contrato público, perfil, puesto, configuración e instrucciones del candidato 1.0.11 permanecen intactos. El prompt del clasificador sí cambió expresamente por esta autorización.
- Verificación: **1262 passed in 161.98s**, suite completa de 1080 unitarias y 182 integraciones en 60 módulos, cero fallos/errores/omisiones. Incluye treinta comprobaciones nuevas de citas/esquema/localizador y dos de lectura de versiones LLM. Una selección inicial tuvo 223 aprobadas y un doble aún con índices; se migró ese doble a quote y una selección de confirmación pasó 31. No se alteró producción para aceptar índices antiguos. Evidencia: `outputs/results/classifier-quote-tests-e82c174a69f44a5690e00176bee9812f.json`. No sumar selecciones a la suite.
- Nuevo piloto real terminado, únicamente R04/R08/R26 con **gemma4:e4b, 2048 tokens, temperatura 0,2**, sin aumentar reintentos: `outputs/results/classifier-diagnostic-schema-9f44eef4-9415-4fc0-aeaa-5bfcd7f0c2b1/report.json`. Hubo cinco generaciones: R04 pasó al primer intento; R08 pasó en la única reparación tras corregir una razón de prioridad; R26 falló ambos intentos por rationale vacío en sus unidades. **2/3 aceptados y coincidentes**, frente a 0/3 en el piloto anterior. R04 obtuvo posiciones [0,72), R08 [0,77), calculadas por Python.
- Las cinco generaciones son JSON legible, usan quote sin índices, tienen citas con alineamiento único y etiquetas únicas dentro de los enums. Tres generaciones cumplen el esquema y dos el contrato completo. En R26 los fragmentos se localizan diagnósticamente en [0,49) y [50,108), pero no se publicó esa clasificación por el rechazo estructural. Sus etiquetas observadas incluyen otro para la hipótesis, formas abiertas y directiva; siguen discrepando de la referencia. No completar justificaciones inventadas, relajar validación o cambiar etiquetas esperadas para hacerlo pasar.
- Comparación: `outputs/results/classifier-quote-comparison-9f44eef4-9415-4fc0-aeaa-5bfcd7f0c2b1.json`. Guía con resultados y cinco salidas crudas: `docs/clasificador.md#citas-y-posiciones-clasificador`. No hubo clave privada, APIs externas o respuestas del candidato; fuentes intactas durante el lote. El logging sigue autorizado solo para esos tres casos. **No se reevaluaron los cuarenta. Se presentan estos resultados y se espera nueva indicación antes de otra corrección o ejecución.** Próximo problema: justificaciones de R26 y adecuación de sus etiquetas, ya no índices ni duplicados. No afirmar que 2/3 de desarrollo valida todo el MVP.

Esta nota resume el estado a su fecha. Antes de modificar, contrastar los archivos pertinentes y cualquier instrucción posterior del usuario; el historial del chat no reemplaza al código actual. Si hay discrepancias con documentación antigua, indicar qué versión o evidencia se está usando.

Prueba manual posterior aportada por el usuario: sesión `93d7a7c5-229a-4a76-937f-f4a975375253`, validada por load_session sin nuevas llamadas. Nueve intervenciones, tres respuestas completas, seis respaldos contrato_invalido; ocho delegaciones LLM con dos aceptadas, seis fallidas y catorce generaciones, todas stop. Solo la hipótesis de prueba automática se resolvió por reglas. Perfil unchanged, contador 3/20 correcto. La repregunta sobre qué hizo después carecía del relato previsto porque esa intervención anterior falló; su contexto son Git y clave primaria. La auditoría normal no permite saber el campo/regla exacto de los seis rechazos. No extender la autorización de raw logging a estas preguntas automáticamente. Informe: `docs/clasificador.md#sesion-manual-clasificador`. Próxima prioridad recomendada: guardar diagnóstico seguro de campo y regla y corregir sobre evidencia concreta; no atribuir sin pruebas las fallas a índices o rationale vacío. No repetir lotes o leer clave privada para este análisis.

- Autorización posterior ejecutada: tres bloques completos de auditoría segura, estadísticas y reproducción de una pregunta. `DataValidationError.detail` conserva mensajes controlados; los adaptadores del clasificador los propagan y seleccionan el fallo interno pertinente de alternativas de esquema mediante `detailed_errors=True`, manteniendo el comportamiento previo de otros documentos. `harness/validation_audit.py` guarda path/rule/message sanitizados, sin instancias, valores rechazados ni errores crudos. La traza de cada generación tiene `validation_error` opcional para compatibilidad con sesiones anteriores; solo admite detalle en contrato_invalido.
- `format_session` incluye respaldos definitivos en incidencias técnicas y separa contrato, JSON, proveedor (incluye red/servidor) y otras incidencias. No cuenta dos generaciones como dos fallos ni errores recuperados como terminales. La sesión manual se presenta ahora con seis incidencias, seis de contrato, cero proveedor/JSON/otras y 3/20 preguntas enviadas, sin modificar su archivo.
- Nuevo `scripts/diagnose_validation.py`: una intervención por ejecución, cliente exclusivamente local, modelo y presupuesto conservados, contexto reconstruido del registro antes del turno, máximo una reparación, sin logging crudo ni candidato. Se ejecutó únicamente intervención 2 («¿Qué herramientas utilizaste en tu proyecto académico más reciente?»), con contexto del turno Git. Informe `outputs/results/validation-audit-eb59f352-73fe-4a6e-a2f1-c52b80a445d7.json`: dos generaciones stop, ambas contrato_invalido en `/units/0/followup_of`, regla `followup_scope`, mensaje «La repregunta debe referir un turno autorizado y declarado como utilizado.». Tokens entrada/salida 3627/385 y 3699/342; 106,66 y 59,32 segundos. Sesión original con huella intacta. No inferir el valor emitido ni atribuir esta misma causa a los seis fallos antiguos: los valores rechazados no se guardan.
- Verificación final: **1271 passed in 215.66s**, suite completa, nueve nuevas pruebas y cero fallos/errores/omisiones. Una selección previa detectó la envoltura anyOf y otra el efecto global de desanidar alternativas sobre un esquema de perfil; se limitó esa opción al clasificador y la suite final pasó. Evidencia: `outputs/results/validation-audit-verification-15d3a9ee-ffd8-43b0-922a-e70c89061c36.json`. Fuentes protegidas coinciden por huella con el piloto anterior, incluidos prompt y ambos esquemas de clasificación; no se leyó configuración privada, no hubo API externa y no se reevaluaron los cuarenta. Guía: `docs/clasificador.md#auditoria-validacion-clasificador`. Próximo cambio recomendado: corregir generación/reparación de vínculos followup_of/context_turn_ids con evidencia, sin relajar contrato ni inventar referencias; no implementado todavía porque el alcance autorizado terminaba en este diagnóstico.

- Segunda prueba manual aportada por el usuario: sesión `d47fb922-610a-4643-bc90-7921eb0cf188`, validada e inspeccionada sin nuevas llamadas ni cambios de código. Diez intervenciones, tres respuestas completas, nueve delegaciones LLM (dos aceptadas y siete fallidas), dieciséis generaciones stop. Primeros errores de las catorce generaciones rechazadas: diez context_scope en /context_turn_ids, dos minLength en rationale de unidad y dos dominance_reason en main_approach_reason de unidad. Seis de los siete fallos terminales son context_scope; el otro, dominance_reason. Git falló incluso sin turnos disponibles por declarar contexto no autorizado en su reparación y luego pasó al repetirlo; herramientas pasó al primer intento con contexto de Git. No hubo fallos de JSON/proveedor ni pérdida de estado; 3/20 e integridad unchanged. No confundir esta causa dominante con el followup_scope del diagnóstico anterior, ni el logging con una corrección ya aplicada de generación. Informe: `docs/clasificador.md#segunda-sesion-manual-clasificador`. Siguiente bloque recomendado: esquema nativo por intervención con IDs cerrados, reparación específica de contexto y coherencia de razones/justificaciones, pruebas y piloto acotado; todavía no implementado en este análisis. No se reejecutaron preguntas ni los cuarenta casos; sesión original intacta por SHA-256.

- El usuario autorizó «Prosigue con la reparación». Se implementaron esquema nativo por intervención con IDs reales cerrados (sin historial solo []/null), anulación de formato por llamada en Ollama sin mutar su valor predeterminado y prompt 1.2.0 con dominio explícito por solicitud. La huella del prompt incluye esa sección. Solo Ollama con structured_output habilitado recibe formato por llamada; candidato y proveedores externos conservan su interfaz/presupuesto. Reparaciones controladas con campo/regla para contexto, rationale vacío y prioridades. El protocolo LLM conserva 1.1.0, el público y referencias 1.0.0; las trazas admiten intérpretes 1.0.0–1.2.3. Fuentes protegidas intactas por huella.
- Piloto delimitado: intervenciones 1, 4 y 10 de la segunda sesión manual, contextos originales []/[1,2]/[2,3], gemma4:e4b, 2048 tokens, temperatura 0,2 y máximo una reparación, sin respuestas del candidato. 1.2.0: Git válida al primer intento (`validation-audit-d53f998b-c2b1-4af9-b650-48cd681e006a.json`), clave primaria válida tras dominance_reason (`validation-audit-d5e78a92-0aa3-4567-ae8c-4b5d321631d8.json`), compuesta falló dos veces por global_union (`validation-audit-23b88c02-1bc7-48b2-bc9e-7981658bb868.json`). Se observaron otras restricciones incumplidas al quitar el fallo dominante; no declarar resuelto el MVP.
- Ampliaciones verificadas dentro de la reparación: 1.2.1 añade instrucción de global_union con conjuntos calculados por Python y códigos oficiales; repetir solo la compuesta siguió fallando por dominance_reason (`validation-audit-1942010f-da27-4475-8b91-a99379742df9.json`). 1.2.2 fuerza en la gramática alternativas de prioridad con reason null/texto según principal y cardinalidad; la compuesta falló global_union y después secondary_consistency (`validation-audit-076b1d68-abdd-4e61-993e-18573c201ae7.json`). 1.2.3 enumera las 44 combinaciones válidas de enfoques/principal/secundarios y añade códigos de conjuntos por unidad al mensaje de reparación, sin citas ni texto libre rechazado. La compuesta pasó validaciones de unidades pero falló global_union en /classification/approaches en ambos intentos (`validation-audit-83ded65f-3643-439a-82f6-937b88fa5505.json`). No normalizar ni aceptar una respuesta inválida. Las instrucciones son controladas y el resultado completo se revalida siempre.
- Cierre de medición: tres preguntas distintas, seis ejecuciones por cambios sucesivos de versión y once generaciones; ninguna falló por contexto, JSON, proveedor o límite de salida. Últimos resultados disponibles: dos aceptadas en 1.2.0 y compuesta rechazada en 1.2.3; no presentarlos como tasa de acierto de una sola versión. No repetir iguales llamadas para buscar un éxito aleatorio. No hubo API externa, configuración privada, raw logging nuevo, respuestas del candidato ni reevaluación de cuarenta. La sesión fuente conserva SHA-256 `3204615e74cf98b83ef9f4a744804042f48f0ad6026b4adbe9f63f2301c9bbd8`.
- Suite final 1.2.3: **1321 passed in 320.35s**, cero fallos/errores/omisiones, cincuenta nuevas frente a 1271. Intermedias completas 1294/259,30 s, 1301/325,76 s y 1318/241,60 s; no sumar selecciones ni versiones. JUnit final `outputs/results/context-repair-complete-tests-9b008aa6c2ad4c0b8e92ff14cd1e2436.xml`. Resumen de piloto, versiones, huellas y todos los informes: `outputs/results/context-repair-pilot-27f3f06d-fd0a-4660-98dd-a5f43ea0d7fb.json`. Guía: `docs/clasificador.md#reparacion-contexto-clasificador`.
- **Pendiente real:** la compuesta sigue fallando por agregación global, no por referencias. Próximo cambio recomendado: retirar del contrato exclusivo del LLM los conjuntos globales derivables y construir su unión en Python desde unidades validadas, preservando contrato público y decisiones semánticas; versionar protocolo y migrar pruebas. Hoy Python calcula esa unión solo para orientar una reparación que el modelo aún no reproduce coherentemente. No se implementó ese rediseño en este bloque ni se autoriza por sí solo relajar validación, cambiar referencias o iniciar los cuarenta.

- Actualización autorizada por «Prosigue teniendo en cuenta la respuesta que recibí en otra conversación», ratificada con «continua»: **agregación en Python implementada**. Intérprete/prompt 1.3.0, protocolo LLM 1.2.0, agregador 1.0.0; contrato público 1.0.0 y sesiones 1.2.0 sin cambio de versión. `harness/classification_aggregation.py` deriva uniones globales approaches/forms/attributes, secundarios globales y de cada unidad, y certeza global con las reglas vigentes. Orden canónico de enums. Se rechazan derivados recibidos del LLM, sin sobrescribirlos silenciosamente. Segmentación, contexto, etiquetas/certidumbre de unidad y principales/razones semánticos permanecen en el modelo; no elegir predominio por mayoría, orden o longitud. Se mantienen format nativo por solicitud, límites y validación pública completa. Eliminada la reparación redundante que pedía al modelo copiar uniones calculadas.
- Trazas nuevas 1.3.0 requieren llm_contract_version, aggregation_version y aggregation_applied, establecidos por el programa; el último solo es verdadero para resultado aceptado evaluable. Lectura de versiones anteriores compatible, verificada también sobre ambas sesiones manuales reales sin reescribirlas. Evaluador 1.1.0 añade segmentación exacta y etiquetas de unidad sobre segmentación coincidente, con denominadores explícitos; generaciones/tokens/segundos por intervención y agregado, sin inventar medidas ausentes. `--case-id` repetible permite un piloto y reanudarlo sin expandirlo. Informes anteriores de otra versión no se reanudan como si fueran equivalentes.
- Verificación final del bloque de agregación: **1370 passed in 212.26s**, cero fallos/errores/omisiones. JUnit `outputs/results/aggregation-complete-tests-1.xml`. Incluye reconstrucción determinista de las 40 anotaciones aprobadas desde campos semánticos (sin LLM ni ajuste de referencias), rechazo de derivados, orden, certeza, secundarios, incompatibilidades de principal, procedencia/versiones, contexto y preservación del estado. Una prueba muestra que una unidad omitida puede pasar el contrato y fallar la comparación de segmentación: la unión coherente no demuestra cobertura. Selecciones anteriores 241/76,43 s y 128/78,45 s no se suman al total final.
- Piloto real único de **R04, R08 y R26 de desarrollo**, todos en intérprete 1.3.0, gemma4:e4b, 2048 tokens, temperatura 0,2, hasta una reparación. Informe `outputs/results/classification-evaluation-hibrido-78f90c46-cefc-4371-868f-50b2b1300217.json`. R04 aceptado tras dos generaciones, pero falsa etiqueta directiva respecto de la referencia. R08 aceptado al primer intento y coincidencia completa. R26 respaldo de contrato en ambos intentos. Los tres rechazos (primero R04 y ambos R26) señalan `/classification/main_approach_reason`, regla dominance_reason; no se afirma el valor emitido porque no se guardó salida rechazada. No se observaron global_union ni secondary_consistency como primer error; esto no prueba ausencia de errores posteriores al fallo dominante.
- Métricas de ese piloto: **2/3 aceptadas, 1/3 coincidencias descriptivas completas**; segmentación exacta 2/2 resultados aceptados evaluables, etiquetas de unidad 1/2 segmentaciones coincidentes. R26 no tiene predicción aceptada que medir semánticamente. Cinco generaciones stop, 18520 tokens de entrada, 1814 de salida y 346,78 s sumados de generación; cero errores JSON/proveedor/límite. No comparar estadísticamente con sesiones/versiones distintas ni afirmar calidad general por tres casos. No repetir llamadas para buscar éxito aleatorio.
- Huellas intactas del perfil, puesto, configuración, instrucciones del candidato, contrato público y referencias. Esquema interno LLM cambia deliberadamente. Las dos sesiones fuente conservan sus huellas; la segunda sigue `3204615e74cf98b83ef9f4a744804042f48f0ad6026b4adbe9f63f2301c9bbd8`. Evidencia consolidada `outputs/results/aggregation-verification-5fbe4876-c816-4c85-8202-eee781278c10.json`; guía `docs/clasificador.md#agregacion-python-clasificador`. Sin configuración privada, APIs externas, nuevo raw logging, respuestas del candidato ni lote real de cuarenta.
- **Pendiente actual:** el traslado de derivados está completado, pero el piloto no está limpio. Próximo bloque recomendado: auditar sin texto libre la condición exacta de dominance_reason (cardinalidad, presencia de principal y razón), y reforzar esa relación del protocolo sin transferir el predominio semántico a una heurística. Revisar por separado el falso directiva de R04 con las definiciones aprobadas. Después corresponde ampliar la evaluación. No se modificó el prompt tras observar este piloto ni se cambiaron reglas metodológicas para forzar un resultado.

### Etapa 3 autorizada: evaluador provisional de preguntas

El usuario autorizó la implementación con los ajustes discutidos en este chat. Se reutilizó el proyecto sin modificar perfil, puesto, configuración de entrevista, instrucciones del candidato ni reglas/prompt del clasificador. Se implementaron evaluación semántica independiente, motor matemático Decimal y feedback local, con activación opcional `--evaluate` en ambos inicios. El inicio sin esa opción conserva su conducta anterior. Guía: `docs/evaluador.md#evaluador-preguntas`; rúbrica: `docs/evaluador.md#rubrica`.

Acuerdos implementados: pesos configurables 35/30/20/15; escala ordinal 1..4; umbrales sobre promedio sin redondear 1,5/2,5/3,5; ningún criterio en 1 permite Destacado; no se imputa 2,5 ni se emite global si falta un criterio. Adecuación metodológica mide obtención de evidencia para el objetivo y permite aclaraciones factuales/mezclas pertinentes. La competencia sigue siendo opcional, no existe selector por turno.

Contexto del evaluador: hasta tres turnos completos anteriores, fragmentos acotados y señalados si truncados; no se envía la respuesta del turno actual ni el perfil privado. La clasificación es auxiliar. Solo las preguntas autorizadas con respuesta completa se evalúan en vivo; saludos y omisiones se registran sin LLM adicional. Los falsos no evaluables de la política no se revisan en esta integración. No se reparó el clasificador y siguen pendientes sus problemas de predominio y falsa etiqueta directiva.

Sesiones con evaluación usan 1.3.0 con evaluation_policy/evaluations en la raíz. Los lectores siguen aceptando 1.0/1.1/1.2 sin reescribir archivos. Validación de identidad, contexto anterior, cálculos, feedback, omisiones e intentos acotados. El último turno se evalúa incluso si cerró por límite. Errores del evaluador no eliminan respuestas ni bloquean la siguiente pregunta; la consola cuenta sus fallos técnicos por separado.

Cliente del evaluador separado: 2048 tokens por generación, 90 segundos de espera HTTP de lectura y cero reintentos de transporte por defecto; única reparación para JSON/contrato. El timeout de lectura no es un plazo absoluto. Proveedor heredado de selección local/API; sin cambio automático. No se leyó config/llm.local.json ni se hicieron llamadas reales durante este bloque.

Referencias: `data/reference_questions/evaluacion_calidad.json`, 40 casos propuestos por el asistente, todos pending/reviewer=null, con niveles y razones por criterio; 30 de desarrollo y 10 de comprobación conocida, no ciegos. `scripts.evaluate_questions --preview --split todos` muestra propuestas sin crear cliente; la comparación real exige referencias revisadas y aprobadas con revisor identificado. No atribuir aprobación humana a estas propuestas ni presentar las pruebas técnicas como validación científica.

Comprobaciones iniciales: baseline 123 aprobadas; primera selección nueva corregida tras detectar una frontera mal construida en un test; selección nueva de 82 y regresión de 230 aprobadas (alcances distintos, no sumar). Se leyeron sin cambios dos sesiones reales 1.2.0 y una 1.0.0. Huellas de seis fuentes protegidas en `outputs/results/evaluator-protected-baseline.json`. El resultado final de la suite se documenta en `docs/evaluador.md#pruebas-evaluador-preguntas`. Pendientes: revisión humana de referencias, piloto real y calibración del evaluador, además de las limitaciones previas del clasificador.

Cierre técnico de la implementación del evaluador: **1456 passed in 239.08s**, cero fallos/errores/omisiones, incluidos 86 casos técnicos nuevos. JUnit final `outputs/results/evaluator-final-complete-tests.xml`; verificación y huellas `outputs/results/evaluator-verification.json`; informe `docs/evaluador.md#pruebas-evaluador-preguntas`. Una ejecución intermedia descartada no se considera evidencia final. Sin llamadas reales, lectura de configuración privada ni aprobación automática de las 40 propuestas. La implementación está disponible; validación semántica y calibración siguen pendientes.

### Corrección del evaluador tras la sesión real 6255d38d

El usuario compartió su prueba real: quince intervenciones, nueve respuestas completas, tres evaluaciones aceptadas, seis fallos terminales de evaluación (todos timeout), cinco fallos terminales del clasificador y un no evaluable por escribir exit. Dos evaluaciones hicieron primero una generación rechazada por sugerencia_ausente y después timeout. La evaluación añadió 960,09 s. En el clasificador hubo 17 generaciones rechazadas (14 dominance_reason y 3 maxLength), no 17 intervenciones fallidas. Diagnóstico seguro `outputs/results/evaluator-session-diagnosis-6255d38d.json`.

Se corrigió solo el evaluador: protocolo compacto/análisis/registro 1.1.0, citas compartidas por índices que Python valida y expande, razones breves y una sugerencia opcional. La ausencia de sugerencia no descarta niveles observados ni induce una reparación. Feedback local asociado al defecto; para nivel 3 sin defecto se permite mantener la pregunta y profundizar después. Se aclaró que el objetivo inmediato puede ser confirmar un dato y que no debe exigirse un relato en cada turno ni penalizar dos veces irrelevancia como problema de enfoque. No se forzaron notas por palabras clave ni se cambiaron pesos, umbrales, rúbrica, candidato, clasificador o las cuarenta propuestas.

Los registros 1.0.0 conservan validación y feedback originales; se sigue leyendo la sesión real intacta, SHA-256 2415802122a3e33724c4177ed932885484181645ece1f8ea7ee1edce62a501a4. El prompt/esquema bajó de 10204 a 8021 caracteres. Timeout y límites conservados: 90 s de lectura, 2048 tokens, cero reintentos de transporte y una reparación JSON/contrato. La consola explica el timeout sin duplicar el mensaje genérico y se registra duración local del intento fallido.

Piloto acotado local con gemma4:e4b: solo intervenciones 1 y 3, preguntas y contexto originales, sin candidato ni clasificador. Primer acceso bloqueado por WinError 10013, sin generación (evaluator-local-probe-f6df0086-9bbc-4944-9d67-c8ff0776dd51.json). Con acceso local autorizado, único piloto real: dos aceptadas al primer intento, 61,76 s (2281/370 tokens) y 36,83 s (2393/241 tokens); cuatro criterios en 3 y Logrado en ambas. Git recibió enfoque 3 y dejó de exigir un relato para confirmar uso. No se presentan esos valores como referencia correcta aprobada ni se afirma precisión general. La latencia sigue siendo elevada y el ensayo aislado no reproduce cambios de contexto de una entrevista completa. Informe `outputs/results/evaluator-local-probe-31927e61-fed4-4317-8791-18d462c47120.json`.

Suite final: **1467 passed in 299.87s**, cero fallos/errores/omisiones. JUnit `outputs/results/evaluator-compact-complete-tests.xml`; verificación `outputs/results/evaluator-compact-verification.json`; guía `docs/evaluador.md#correccion-evaluador-local`. Selección previa 97, no sumarla al total. Se preservaron seis fuentes protegidas y la sesión original. No hubo API externa ni lectura de configuración privada. No se volvieron a ejecutar los casos reales para buscar éxitos aleatorios ni se cambiaron las referencias.

Pendientes: cinco bloqueos del clasificador, calibración humana de los niveles, revisión de las cuarenta referencias y evaluación más amplia de latencia. No recomendar una nueva sesión larga como si el flujo completo estuviera resuelto.

### Bloque correctivo autorizado: bloqueos del clasificador

El usuario autorizó continuar con el primer paso recomendado. Se eliminó la duplicación del global de una unidad única: protocolo LLM 1.3.0 requiere classification={} cuando existe una sola unidad evaluable. Python copia sus principales, razones y justificación, además de los derivados existentes, y revalida el contrato público. La interpretación de unidad se mantiene en el LLM; con varias unidades el predominio global sigue siendo semántico. No se relajan contradicciones, se inventan citas ni se selecciona un principal por mayoría u orden. Los nuevos metadatos identifican intérprete/prompt 1.4.1 y agregador 1.1.0; se conservan lectores de versiones anteriores, incluidas las experimentales.

Ensayo 1.4.0 interrumpido: el primer caso produjo una segunda cita ausente del texto en ambos intentos. Se conservó el rechazo y se detuvo; no hay resultado válido de la solicitud interrumpida siguiente. Se ordenó la generación para producir unidades antes de comprometerse con un global. Con 1.4.1 pasaron las cuatro preguntas distintas previamente bloqueadas (intervenciones 2,6,10,13) al primer intento, una unidad literal y política responder. La intervención 14 repetía 13 sin nuevo contexto y no se ejecutó otra vez. Tiempos 59,31;43,20;44,55;40,64 s; total 187,71 s de generación, sin candidato ni evaluador. Informe `outputs/results/classifier-blocks-probe-c7fd3f4c-4ae4-4ca1-9e3a-72f456cd22b9.json`.

La inspección detectó tres discrepancias semánticas aún pendientes de revisión humana: directiva en el escenario de una prueba fallida; otro en la actuación hipotética de comunicar un retraso; conductual en el mero conteo de equipos dirigidos. Se ensayó una aclaración adicional 1.4.2 en esos tres casos, sin mejora en las etiquetas; se retiró ese cambio del prompt y se restauró 1.4.1. No se hicieron más llamadas para buscar un resultado favorable. Las huellas de las instrucciones finales coinciden exactamente con las del piloto 1.4.1 de cuatro casos. No mezclar versiones ni llamar aciertos semánticos a las cuatro autorizaciones.

Se mantuvieron presupuesto de 2048 tokens y una única reparación, así como todas las definiciones, referencias, perfil, puesto, configuración y evaluador. Generación pide rationale de hasta 160 caracteres; parser conserva el límite público, no trunca texto y dirige específicamente reparaciones por exceso. Reconstrucción determinista de las cuarenta anotaciones aprobadas sin diferencias semánticas, sin LLM ni ajuste de referencias. Sesión real conservada con SHA-256 2415802122a3e33724c4177ed932885484181645ece1f8ea7ee1edce62a501a4. Diez fuentes protegidas verificadas mediante `outputs/results/classifier-single-unit-baseline.json`.

Suite final: **1486 passed in 261.00s**, cero fallos/errores/omisiones. JUnit `outputs/results/classifier-single-unit-complete-final-tests.xml`; evidencia `outputs/results/classifier-single-unit-verification.json`; guía `docs/clasificador.md#desbloqueo-clasificador`. Las comprobaciones parciales de 261,1 y19 no se suman al total final. Hubo una comprobación antigua del formato nativo actualizada para las tres alternativas estrictas. No hubo API externa ni lectura de configuración privada.

Estado: bloqueo de contrato corregido en el alcance probado; clasificación semántica todavía no fiable de forma general. Quedan revisión de las tres discrepancias, calibración con referencias y evaluación del comportamiento más amplio, especialmente compuestas. Las cuarenta referencias del evaluador continúan pendientes de aprobación humana; no se autorizan automáticamente por pedir continuar. No recomendar otra sesión larga ni afirmar que todo el flujo está validado.

### Few-Shot autorizado por el usuario

El usuario solicitó explícitamente inyectar un subconjunto representativo de los cuarenta casos aprobados del clasificador y reevaluar las tres discrepancias. Se implementó `harness/classifier_few_shot.py` y la selección `config/classifier_few_shot.json`: R01, R04, R06, R08, R12, R15, todos de desarrollo. Guardas de aprobación, huella exacta, IDs únicos y prohibición de casos de comprobación. Los diez de comprobación conocida no se inyectan. Las cuarenta referencias del evaluador educativo son un conjunto distinto y siguen pendientes de revisión humana.

Los pares JSON entrada/salida se incorporan al system como demostraciones delimitadas y aisladas, no como historial actual. El texto, contexto mínimo y etiquetas aprobadas se conservan; la configuración común se omite en las entradas de ejemplo. La salida se proyecta al protocolo 1.3.0 y se valida, incluida la gramática nativa con sus límites. La entrada actual sigue en mensaje user independiente y el esquema por solicitud conserva solo turnos actuales autorizados. No se modifican las etiquetas del modelo mediante reglas nuevas.

Intérprete 1.5.0, base agent/classifier.md 1.4.1 sin modificar, few_shot.version 1.0.0, protocolo 1.3.0, agregador 1.1.0 y contrato público 1.0.0. Cada traza nueva exige few_shot con enabled, IDs, referencia SHA-256 y ejemplos SHA-256; prompt completo con su huella. Los registros anteriores siguen siendo compatibles. Caché por contenidos de selección/fuente, no solo por ruta. evaluate_classifier incluye ambos archivos nuevos en FROZEN_SOURCES para no mezclar selecciones al reanudar.

Activo por defecto para las delegaciones semánticas del clasificador; reglas locales sin llamada no envían ejemplos. `scripts.start_interview --evaluate` usa la selección. `--no-classifier-examples`, también en run_interview, permite comparar o desactivar sin cambiar candidato ni evaluador. No se aumentaron contexto, presupuesto de 2048 ni el máximo de una reparación.

Experimento A/B único: `scripts.calibrate_classifier_few_shot --session outputs/sessions/session-6255d38d-6757-42b8-890d-c600016148e8.json --model gemma4:e4b`. Tres casos conocidos, 2/6/10, cada uno primero sin ejemplos y luego con ellos. Modelo y temperatura 0,2 constantes; mismo contexto original; sin candidato ni evaluador. La selección se fijó antes de observar resultados y no se ajustó después. Ninguna pregunta de contraste aparece literalmente en las demostraciones.

Resultado: baseline 0/3 coincidencias, Few-Shot 2/3. Ambas modalidades generaron salidas válidas al primer intento en los tres casos, con responder. Se corrigieron directiva espuria en el escenario de fallo y conductual en el conteo de equipos, que pasó a factual_tecnico. Comunicación de retraso sigue otro, con explicación equivocada de concepto técnico; no se reemplaza por situacional de forma local. Se comparan todos los enfoques, formas y atributos, no solo el campo inicialmente erróneo. Son contrastes de desarrollo conocidos, no prueba ciega ni precisión general; no presentar 66,7% como calidad del sistema.

Informe `outputs/results/classifier-few-shot-ab-4ebc3b1f-454b-4247-a51f-4f2f9c4281d2.json`. Seis generaciones locales, sin API externa ni configuración privada. Input con ejemplos: 5609/5665/5652 tokens, +1682 cada llamada; salida 248/249/248; tiempos 60,81/63,67/64,71 s. Baseline tiempos 83,48/61,02/59,16 s. Caché/carga no controladas, no inferir mejora general de tiempo. Contextos más largos pueden necesitar revisar presupuesto, sin ampliarlo o descartar ejemplos silenciosamente.

Suite final: **1500 passed in 277.82s**, cero fallos/errores/omisiones. JUnit `outputs/results/classifier-few-shot-final-tests.xml`; verificación `outputs/results/classifier-few-shot-verification.json`; guía `docs/clasificador.md#few-shot-clasificador`. Once fuentes protegidas conservadas y sesión original leída sin reescribir. Prompts baseline idénticos por huella a 1.4.1. Pendientes: tercer caso de comunicación, revisión/calibración más amplia y referencias del evaluador educativo.

---

<a name="estado-etapas"></a>

## Estado de las nueve etapas del agente candidato

El usuario autorizó iniciar la Etapa 8: «Pasemos a la etapa 8 también muéstrame que etapas completamos y cuantas faltan». Se mantiene el desarrollo por unidades pequeñas y verificables.

**Completadas en su alcance técnico: 9 de 9. Etapas pendientes del agente: 0.** El usuario autorizó la última transición con «Pasemos a la Etapa 9». El cierre se limita al alcance comprobado; no garantiza consistencia universal ni atribuye una aprobación semántica humana no expresada. Las fases educativas posteriores del proyecto completo siguen fuera de esta entrega.

| Etapa | Nombre del plan original | Estado | Resultado disponible |
| --- | --- | --- | --- |
| 1 | Diagnóstico tecnológico | Completada | Entorno comprobado; Ollama como proveedor principal y API externa opcional. |
| 2 | Diseño de arquitectura | Completada | Arquitectura aprobada, módulos y responsabilidades separados. |
| 3 | Creación del candidato | Completada | Perfil ficticio aprobado, JSON protegido y currículum derivado. Referencia: 2026-10-20. |
| 4 | Configuración e instrucciones | Completada | Puesto, preferencias, instrucciones y preparación del escenario validados. |
| 5 | Conexión con el LLM | Completada | Adaptador Ollama comprobado; alternativa externa implementada y desactivada por defecto. |
| 6 | Conversación en consola | Completada | CV, puesto, inicio, preguntas, respuestas, límite y salida disponibles. |
| 7 | Historial y contexto | Completada en su alcance funcional | Sesiones aisladas, historial, guardado JSON, diagnóstico y resumen opcional auditado. [Cierre y límites](contexto-y-sesiones.md#cierre-etapa-7). |
| 8 | Pruebas de consistencia | Cierre técnico comprobado | El usuario ejecutó ambos conjuntos: diez casos y quince respuestas completas, sin contradicciones observadas por el asistente. [Cierre, evidencias y límites](validacion-del-candidato.md#cierre-etapa-8). |
| 9 | Integración y validación final | Completada en el alcance comprobado | 738 pruebas aprobadas; consola real con veinte respuestas y cierre al límite, salida anticipada independiente, JSON 1.0/1.1 leídos y originales intactos. [Cierre y evidencia](validacion-del-candidato.md#validacion-final). |

La [unidad 8.1](validacion-del-candidato.md#referencias-consistencia) prepara criterios y verifica sus fuentes sin consultar al modelo. Las pruebas técnicas de esta unidad no cuentan como ejecuciones de consistencia del candidato. Las preguntas ya aparecieron durante el desarrollo; no constituyen un conjunto independiente reservado para prueba.

La [unidad 8.2](validacion-del-candidato.md#ejecucion-referencias) agrupa la ejecución básica. El [bloque 8.3](validacion-del-candidato.md#consistencia-ampliada) reúne cronología, tecnologías/aportes, ambigüedad, premisa contradictoria, repetición y protección de instrucciones. El usuario confirmó ambas ejecuciones y autorizó la Etapa 9, completada en un bloque. Los cierres distinguen inspección del asistente, revisión humana, redacción, omisiones y contradicciones. Se mantiene la preferencia del usuario por explicaciones breves y comprobaciones agrupadas.

La clasificación, rúbrica, puntuaciones y retroalimentación educativa quedan fuera de estas nueve etapas del agente. La integración con Godot pertenece a la planificación posterior del proyecto completo.

---

<a name="planificacion"></a>

## Alcance y planificación

### MVP del semestre actual

La fase actual construye exclusivamente el agente candidato: perfil ficticio, instrucciones, conexión con un LLM, consola, historial y pruebas. Ollama es el proveedor principal; la API externa es una alternativa implementada que requiere activación explícita. Clasificación y evaluación educativa no pertenecen a esta fase del agente.

### Hito E2

<!-- Por completar. -->

### Cierre del semestre y E3

<!-- Por completar. -->

### Configuraciones previstas, piloto y ampliaciones

<!-- Por completar. -->

### Cronograma, responsables y estado

El [estado de las nueve etapas](#estado-etapas) registra **nueve completadas en su alcance técnico y ninguna pendiente del agente**. La [validación final](validacion-del-candidato.md#validacion-final), autorizada por el usuario, aprobó 738 pruebas y una entrevista real de veinte preguntas y veinte respuestas, cierre al límite, salida anticipada, guardado/lectura e integridad. Se distinguen evidencia técnica, inspección del asistente y aprobación semántica humana no expresada. Las funciones educativas posteriores del proyecto completo quedan fuera de esta entrega. No se establecen fechas de entrega ni responsables adicionales.

### Continuidad del segundo semestre

<!-- Por completar. -->

### Continuidad del tercer semestre

<!-- Por completar. -->

### Funciones postergadas y exclusiones

<!-- Por completar. -->

### Riesgos y dependencias

<!-- Por completar. -->

---

<a name="decisiones"></a>

## Registro de decisiones

### Identificador, fecha y estado

<!-- Por completar. -->

### Problema o decisión pendiente

<!-- Por completar. -->

### Alternativas y evidencia

<!-- Por completar. -->

### Decisión adoptada y justificación

<!-- Por completar. -->

### Consecuencias y alcance temporal

<!-- Por completar. -->

### Archivos, pruebas e informe afectados

<!-- Por completar. -->

---

<a name="changelog"></a>

## Registro de cambios

### 2026-11-07 · API y preparación para Godot

- La API de `app/` incorpora sesiones, ejecución idempotente por solicitud, consulta de estado y logs JSONL. Reutiliza el candidato, el clasificador y el evaluador existentes.
- El manifiesto, los contratos públicos y los ejemplos de entrada y salida están completos. La herramienta de `agent/tools.yaml` recupera documentos del CV público y del puesto con su procedencia antes de generar la respuesta.
- `app/godot/InterviewApi.gd` aporta el transporte para las futuras escenas. La configuración y las decisiones de la versión local están en [operación](operacion.md#api-y-godot).
- La verificación técnica se reúne en `reports/` y GitHub Actions ejecuta pytest, Ruff, Bandit y los casos de recuperación. El README incluye instalación desde cero y una comprobación en un entorno independiente.
- Evidencia local de entrega en `reports/delivery-summary.json`. Suite completa de 1880 pruebas y 15 verificaciones específicas de la API aprobadas, Ruff y Bandit sin hallazgos, seis casos de recuperación correctos e instalación independiente satisfactoria. Godot 4.7.2 verificó estado, metadatos, creación, búsqueda y cierre de sesión en modo headless. Las pruebas de modelos usan simulaciones. El workflow remoto se ejecutará cuando se publiquen los cambios.

### 2026-11-06 · Consolidación de la documentación

- Los registros de cambios, estados, decisiones y pruebas se agruparon por tema. El [índice general](../README.md#documentación) reúne las rutas vigentes.
- La tabla aprobada del clasificador se trasladó al [documento del clasificador](clasificador.md#referencias-clasificacion-propuesta). La ruta histórica enlaza a esa sección para conservar la procedencia registrada en los datos.

### 2026-11-02 · Presentación y consulta de la entrevista en consola

- Menú de proveedor, menú de entrevista, CV, puesto, inicio y sesión organizados por títulos, secciones y espacios.
- Pregunta, respuesta completa y evaluación separadas y numeradas; líneas ajustadas sin recortar contenido. La respuesta sigue apareciendo antes de esperar la evaluación.
- `/respuestas`, `/respuesta N` y `/menu`: consulta del registro en memoria sin nuevas generaciones ni consumo del contador. Intentos fallidos identificados sin mostrar texto incompleto.
- La presentación lee los niveles y estados ya validados. Sin cambios de prompts, modelos, referencias, rúbrica, Regla Crítica o formato de sesión. Calibración del MVP cerrada.
- Guía y vista previa: `docs/operacion.md#consola` y `outputs/previews/console-presentation.txt`.
- Verificados 250 casos dirigidos distintos; primera ronda 249/250 y repetición final 70/70 tras adaptar una expectativa de texto al ajuste de líneas. Sin inferencias reales. Evidencia: `outputs/results/console-presentation-verification.json`.

### 2026-11-02 · Cierre y aceptación del MVP del evaluador

- El usuario cerró y validó explícitamente el Bloque 11, aceptando los resultados y las limitaciones de la configuración local sin continuar la optimización de casos límite.
- Plan completo: 12/12 bloques. El Bloque 12 ya estaba implementado; se actualizaron acta, estado y continuidad.
- Resultados, discrepancias y última suite de 1810 pruebas conservados. Cierre exclusivamente documental, sin nuevas inferencias ni cambios del programa.
- Acta: `docs/evaluador.md#cierre-mvp-evaluador`.

### 2026-11-02 · Separación de Claridad/Neutralidad y calibración ampliada

- Incorporada literalmente la instrucción del usuario, manteniendo cerradas legítimas sin penalización automática de neutralidad.
- Doce casos nuevos de desarrollo fuera de las seis demostraciones: Claridad 12/12, Neutralidad 9/12 y coincidencia completa 5/12. Sin cambios de referencias, ejemplos o Regla Crítica.
- E11 conserva claridad 3 frente a 4 y una razón incompleta. Se preservó su timeout inicial y la comprobación adicional anunciada; no se da por resuelto.
- Ejecutor con fuentes congeladas, guardado por caso y continuación solo de pendientes. Suite completa: 1810 pruebas aprobadas en 333,02 s; 42 fuentes previas intactas.
- Evidencia: `docs/evaluador.md#calibracion-ampliada-claridad-neutralidad` y `outputs/results/evaluator-clarity-expanded-verification.json`.

### 2026-11-02 · Regla Crítica aprobada y seis demostraciones del evaluador

- Registrada aprobación explícita de las 40 referencias revisadas 1.1.0 y contextos. Niveles intactos; tres globales recalculados con la política aprobada.
- Rúbrica 1.1.0: cualquier criterio en 1 limita el global a En desarrollo, conservando promedio y porcentaje, incluso con peso cero. Las sesiones anteriores conservan su política.
- Seis demostraciones de desarrollo activas por defecto, fuentes fijadas por huellas y opción `--no-evaluator-examples`. Protocolo 1.2.0 y registros 1.3.0 con procedencia de ejemplos.
- Cuatrocientas pruebas dirigidas aprobadas. El primer A/B se conservó al detectar una discrepancia sin clasificación; corregido el formato nativo antes de repetir el contraste.
- Calibración inicial final: 0/4 → 3/4 coincidencias completas y 8/16 → 15/16 niveles por criterio. Tres eran demostraciones; el caso de transferencia conserva una diferencia de claridad. Ocho evaluaciones finales aceptadas al primer intento; referencias intactas.
- Suite completa final: 1803 pruebas aprobadas en 316,44 s, sin fallos. Configuración histórica y dieciséis fuentes protegidas intactas; evidencia en `outputs/results/evaluator-calibration-verification.json`.
- Guía vigente: `docs/evaluador.md#calibracion-evaluador-few-shot`.

### 2026-11-02 · Revisión preparatoria de referencias del evaluador

- Propuesta editorial 1.1.0 separada del original: 40 casos, 160 justificaciones, 14 casos con ajustes de entrada o niveles y contraste de hábitos con/sin objetivo explícito.
- Seis demostraciones propuestas, inactivas, comprobadas con el contrato 1.2.0. Cuarenta entradas validadas y cinco pruebas del flujo de referencias aprobadas; sin llamadas LLM ni cambios del evaluador activo.
- Comparación pendiente de decisión: máximo En desarrollo cuando haya un criterio en 1, manteniendo porcentajes; afecta tres globales de la propuesta. No se implementó ni se infirió aprobación humana.
- Evidencia, diferencias y fuentes intactas: `outputs/results/evaluator-reference-review-20261102.json`.

### 2026-11-02 · Estabilización de evidencia del evaluador

- Protocolo y registros 1.2.0: criterios puntuados con evidencia, fuentes/turnos coherentes y contexto restringido por petición.
- Diagnóstico seguro por campo, regla y límite, utilizado en la única reparación; compatibilidad de evaluaciones 1.0.0/1.1.0.
- Formato nativo de Ollama sin el conflicto entre patrón y límites de longitud; validación Python completa conservada.
- Dos preguntas antes rechazadas recuperadas al primer intento en 65,93 y 62,07 s. Calibración semántica y latencia siguen pendientes; no se alteraron referencias ni la sesión original.
- Suite completa final: 1517 pruebas aprobadas en 300,45 s; selección previa de 109. Evidencia, fuentes intactas y pilotos conservados en `docs/evaluador.md#estabilizacion-evidencia-evaluador`.

### 2026-11-01 · Presupuesto explícito de salida UNAB

- Confirmado finish_reason length con 512 tokens y cero texto final; razonamiento interno no confirmado.
- Presupuesto UNAB predeterminado 2048 y campo privado opcional api_max_output_tokens, validado y visible en el selector. Clave y presupuestos de otros proveedores intactos.
- Diecisiete regresiones nuevas; 109 pruebas dirigidas aprobadas. Sin llamadas API reales ni escalado/reintentos automáticos.

### 2026-11-01 · Diagnóstico de consumo y salidas UNAB

- Solicitud de razonamiento desactivado conservando límite 512; efecto real pendiente de comprobar en la pasarela.
- Metadatos de uso incluso ante rechazos, diagnóstico separado al cerrar y protección contra exposición de pensamiento o claves.
- Seis regresiones nuevas; 765 pruebas aprobadas. Investigación local sin cuota API y sin alterar datos aprobados.

### 2026-11-01 · Selector de proveedor y UNAB IA

- Configuración privada ignorada por Git y menú local/API mediante scripts.start_interview.
- Adaptador Chat Completions independiente para gemma4:26b en UNAB IA; Responses anterior conservado.
- Suite completa de 759 pruebas aprobadas; sin llamada real al servicio externo. Datos e instrucciones aprobados intactos.

### 2026-10-31 · Integración y validación final (Etapa 9)

- Transición autorizada explícitamente por el usuario. Suite completa: **738 passed in 45.54s** y dependencias sin incompatibilidades.
- Consola real con gemma4:e4b: veinte preguntas y veinte respuestas completas, cero incidencias, cierre al límite y entrada 21 excluida. Recordó la primera pregunta y el proyecto académico al final.
- Salida anticipada en sesión independiente sin preguntas; lectura validada de formatos 1.0.0 y 1.1.0. Cuatro originales y 27 sesiones anteriores intactos.
- Veinte eventos de contexto, máximo informado 7106 tokens, cero selecciones y resúmenes aplicados en esta entrevista. El uso real de extractos conserva sus evidencias previas separadas.
- Documentados resultados, límites y guía de uso. Nueve etapas completadas en su alcance técnico; las funciones educativas posteriores no forman parte de esta entrega.

### 2026-10-31 · Cierre técnico de la Etapa 8

- Confirmada la ejecución del usuario: seis casos ampliados, diez respuestas completas y seis sesiones validadas. Cuatro originales y veintiuna sesiones anteriores conservados.
- Añadido cierre con evidencias y límites; avance técnico de ocho etapas completadas y una pendiente. La Etapa 9 no se inicia automáticamente.
- Cierre documental sin llamadas nuevas o repetición de pruebas. La aprobación semántica humana explícita no se infiere del éxito técnico.

### 2026-10-31 · Bloque ampliado de consistencia (unidad 8.3)

- Se validó la ejecución del usuario de la 8.2: cuatro casos y cinco respuestas completas con sus sesiones intactas.
- Se añadió el conjunto ampliado: seis casos, diez preguntas y referencias al perfil revisado. Se reutilizó el ejecutor sin cambiar código de producción.
- Dos comprobaciones nuevas aprobadas en 1,88 s. Hay 738 pruebas disponibles; la última suite completa sigue siendo la de 736 y se repetirá en la validación final.
- El lote 5e7c73f0-1e3a-4054-8ad8-1501ab6eed3d terminó con diez respuestas completas. Se registraron observaciones del asistente, una imprecisión de redacción y detalles omitidos, sin contradicciones factuales observadas. Cuatro originales y quince sesiones anteriores intactos.
- La Etapa 8 queda pendiente de comprobación final del usuario; la Etapa 9 no se inicia automáticamente.

### 2026-10-31 · Ejecución de referencias por lotes (unidad 8.2)

- El usuario confirmó 730 pruebas en 150,75 s y el listado de la 8.1. Solicitó avanzar en bloques mayores con respuestas breves y menos consumo de tokens de chat.
- Se añadió `scripts.run_reference_cases`: Ollama exclusivamente local, sesión independiente por caso, continuidad dentro del caso y detención tras el primer fallo. Conserva sesiones, instantáneas y procedencia sin emitir veredictos semánticos.
- Se añadieron seis integraciones; suite completa de **736 passed in 123.96s**.
- El lote real fd00eb31-7961-4390-9807-c78695f3a247 obtuvo cinco respuestas completas con gemma4:e4b. Se conservaron originales y sesiones anteriores. La inspección del asistente encontró los hechos esperados; la revisión humana y la ampliación siguen pendientes.

### 2026-10-31 · Referencias de consistencia (unidad 8.1)

- El usuario autorizó la Etapa 8 tras el cierre funcional de historial/contexto. El estado de las nueve etapas registra siete completadas, la 8 en curso y la 9 pendiente.
- Se prepararon cuatro casos y cinco preguntas con referencias al perfil revisado y a hechos temporales derivados, contrato JSON y cargador de copias independientes.
- `scripts.show_reference_cases` muestra criterios humanos sin consultar modelos, escribir sesiones o evaluar respuestas. El conjunto reutiliza preguntas de desarrollo y no se presenta como prueba independiente.
- Se añadieron 37 pruebas unitarias y tres integraciones: 40 nuevas aprobadas y suite completa de **730 passed in 45.44s**.
- Evidencia: `reference-suite-da11e781799f4ef6ba7331f1964e0e39.json`. Cuatro originales y siete archivos de sesiones conservados. La comprobación del usuario y las respuestas reales de estos casos siguen pendientes.

### 2026-10-28 · Adaptación estructural

- La plantilla genérica CINF110 se reorganizó para el simulador de entrevistas descrito en la conversación compartida.
- Se sustituyó `src/` por `agent/` (definiciones) y `harness/` (futura ejecución Python).
- Se añadieron espacios para clasificación, evaluación por criterios, cálculo local, retroalimentación inmediata, validación y registro.
- Se separaron perfiles, preguntas de referencia, configuraciones, contratos y salidas generadas.
- `docs/proyecto.md` se sustituyó por `docs/informe.md`, con secciones pendientes, y una guía de llenado.
- `docs/curso.yml` se trasladó a `docs/academico/cinf110.yml`, conservando sus valores originales.
- Los espacios de evaluación se distribuyeron entre `docs/pruebas/` y `docs/entregas/`, distinguiendo CINF110 de CINF200.
- Se retiraron los marcadores genéricos de herramientas, integraciones y datos de ejemplo sin una responsabilidad concreta en el MVP.
- Se mantuvieron .env.example, las plantillas de colaboración y la reserva de automatización de pruebas.
- No se implementaron funciones, contratos completos, perfiles, ponderaciones, ejemplos de entrevista, resultados ni evidencias.

El detalle de destinos y responsabilidades está en [la guía](guia-estructura.md).

### 2026-10-31 · Guardado local de sesiones (unidad 7.3)

- Se completó `harness/session_log.py` y el contrato `schemas/session.schema.json`.
- La consola guarda un JSON por UUID al cerrar; no sobrescribe registros existentes. La lectura valida datos sin reanudar entrevistas.
- Se conserva el registro de errores y texto parcial; fallos de escritura se comunican sin confirmar guardado y devuelven código 1.
- Se añadieron 53 casos y aislamiento temporal de archivos en pytest; suite final de 530 pruebas aprobadas.
- Se documentan implementación, límites y comprobaciones en `docs/contexto-y-sesiones.md#persistencia-sesiones`.

### 2026-10-31 · Diagnóstico del contexto registrado (unidad 7.4a)

- Se confirmó el guardado/lectura del usuario: 530 pruebas y sesión de dos respuestas con UUID coincidente y perfil intacto.
- Se añadieron `harness/context_budget.py` y `scripts/inspect_context.py`: comparación de tokens ya informados con reservas explícitas, sin red ni cambios de sesiones.
- Las métricas ausentes permanecen desconocidas; los tokens reutilizados no se descuentan de la entrada. Los parámetros de comparación no se presentan como ajustes históricos del archivo.
- Se añadieron 29 casos, suite final de 559 pruebas aprobadas y evidencia de lectura del archivo real del usuario.
- La reducción de contexto y los resúmenes siguen pendientes.

### 2026-10-31 · Rechazo explícito de contexto excesivo (unidad 7.4b)

- Se confirmó el diagnóstico del usuario: 559 pruebas, entradas 6023/6097 y márgenes 1401/1327.
- Ollama solicita `truncate: false` y `shift: false`; se reconocen errores conocidos mediante `LLMContextLimitError` y catálogo `context_limit`, sin copiar cuerpos HTTP.
- El registro 1.0.0 admite ese código conservando los anteriores. La consola explica el rechazo y conserva todos los intentos.
- Se añadieron 18 casos; suite final de 577 pruebas aprobadas. La prueba real local conservó la referencia a Inventario Aula tras rechazar una entrada sintética extensa.
- El resumen controlado continúa pendiente.

### 2026-10-31 · Propuesta de resumen extractivo (unidad 7.4c)

- Se confirmó el rechazo y continuidad del usuario: 577 pruebas y sesión completed/error/completed con context_limit.
- Se añadieron `harness/history_summary.py` y `scripts/preview_summary.py`, con selección de índices, citas exactas, metadatos de procedencia, verificación por reconstrucción y pares recientes completos.
- La prueba real detectó omisiones del selector; Python conserva ahora anclas y registra las que añadió por protección. El resultado sigue pendiente de revisión, separado del controlador.
- Se añadieron 55 casos; suite final de 632 pruebas aprobadas. Se registraron una sesión real y una fixture identificada, conservando archivos originales.

### 2026-10-31 · Composición de contexto con extractos (unidad 7.4d)

- Se confirmó la vista previa del usuario: 632 pruebas y dos citas conservadas con procedencia verificada.
- Se añadieron `harness/summary_context.py` y `scripts/probe_summary_context.py`: vínculos con el escenario, papeles de conversación conservados, guía estática y elección según bytes de mensajes completos.
- Si no hay omisiones o ahorro real de bytes, se conserva el historial completo. No se modifica la sesión fuente ni se reanuda su controlador.
- Se añadieron 22 casos; suite final de 654 pruebas aprobadas. La activación durante una entrevista continúa pendiente.

La prueba real de la 7.4d detectó confusión entre orden de mención y fechas en la variante completa. Se añadió guía estática al nuevo constructor para ambas variantes y se verificaron de nuevo las referencias y el orden de inicio. El archivo de instrucciones y el controlador principal permanecen sin cambios. Evidencia y límites en `docs/contexto-y-sesiones.md#contexto-con-resumen`.

### 2026-10-31 · Resumen activable en entrevistas (unidad 7.4e)

- Se confirmó la composición del usuario: 654 pruebas y respuesta correcta sobre Inventario Aula, sin modificar la fuente.
- `--extractive-context` integra política, selección y composición en `InterviewRuntime`; se conservan los originales y se usa historial completo ante fallos conocidos o ausencia de ahorro.
- El contrato 1.1.0 añade política y auditoría de contexto, manteniendo lectura del 1.0.0. Los selectores no consumen preguntas.
- Se añadieron 36 casos; suite final de 690 pruebas. Una entrevista local de cuatro preguntas y una fixture identificada comprobaron ambos modos y lectura exacta.
- La opción permanece explícita y no certifica relevancia de todas las omisiones o consistencia universal.

### Cierre funcional de historial y contexto

- El usuario confirmó 690 pruebas en 38,14 s y la sesión 1.1.0 f8d281c9-bca7-4bdd-9b52-d7f9788399e5, con cuatro respuestas y una selección independiente.
- Se validó el archivo y se registró la confirmación en evidencia estructurada; los cuatro hashes del escenario coinciden con los aprobados.
- Se añadió `docs/contexto-y-sesiones.md#cierre-etapa-7`, con alcance, limitaciones y propuesta de transición. La Etapa 8 todavía no se inicia.

### 1 de noviembre de 2026: evaluación provisional opcional

Evaluador por pregunta con rúbrica configurable de cuatro criterios, evidencias literales, cálculo Decimal local y feedback sin llamada adicional. Activación `--evaluate`, estados sin imputación y limitación de Destacado con criterios en 1. Registro 1.3.0 compatible con sesiones anteriores, preservación de respuestas ante errores y contexto exclusivamente anterior al turno. Cuarenta referencias propuestas pendientes de revisión, comparación con cobertura y error ordinal, y documentación de límites. Suite final: 1456 pruebas aprobadas en 239,08 s; sin llamadas reales ni consumo de API. Perfil, puesto y clasificador conservados.

### Corrección 1.1.0 del evaluador local

Protocolo compacto con citas compartidas y una sugerencia opcional; niveles/evidencia válidos se conservan si falta feedback. Se aclara el objetivo inmediato de preguntas factuales y se explican timeouts. Lectura compatible de evaluaciones 1.0.0. Dos casos locales aceptados al primer intento, 61,76 y 36,83 s, sin afirmar calibración general. Suite final: 1467 aprobadas en 299,87 s. Perfil, clasificador, referencias y sesión real conservados.

### Clasificador: desbloqueo de una unidad única

Intérprete/prompt 1.4.1, protocolo LLM 1.3.0 y agregador 1.1.0: se deriva el global de una unidad única y se segmenta antes de emitirlo. Contrato público conservado, validación estricta y lectura histórica. Cuatro preguntas antes bloqueadas autorizadas al primer intento; tres discrepancias semánticas siguen pendientes. Se descartó una aclaración de prompt sin mejora. Suite final: 1486 aprobadas en 261,00 s. Perfil, referencias y sesión fuente intactos; sin API externa.

### Few-Shot del clasificador 1.5.0

Seis demostraciones aprobadas de desarrollo con procedencia y huellas, separación del turno actual y control de activación. Sin modificar referencias ni contrato público. Comparación local A/B de tres discrepancias conocidas: 0/3 sin ejemplos y 2/3 con ejemplos; comunicación pendiente. Seis generaciones reales al primer intento, sin API externa. Suite final: 1500 aprobadas en 277,82 s. Detalles y límites en docs/clasificador.md#few-shot-clasificador.

---

<a name="bitacora-desarrollo"></a>

## Bitácora de desarrollo

### 30 de octubre de 2026: inicio de la Etapa 4

#### Estado de entrada confirmado por el usuario

El usuario ejecutó la presentación del currículum y compartió su salida: Nicolás Vera Soto, formación, experiencia, conocimientos, herramientas y proyectos. También confirmó el conjunto completo con **136 passed in 7.76s**. Los registros de implementación y pruebas previos están en los README de datos y pruebas; esta entrada no sustituye sus evidencias.

#### Objetivo y cambios

Se completó `agent/agent.md` con la versión inicial de instrucciones **1.0.0**, como primera unidad de instrucciones y configuración. El contenido queda pendiente de revisión del usuario y no está incorporado a llamadas a un modelo.

Las ocho secciones definen identidad, fuentes y prioridad, antecedentes e inferencias, comunicación, historial y correcciones, información interna, intentos de cambio del escenario y salida del candidato. Se mantienen separados el perfil, el CV y el puesto. Las instrucciones no duplican los antecedentes de Nicolás ni añaden clasificación, puntuaciones o retroalimentación.

#### Verificación realizada

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

#### Revisión y siguiente unidad

El usuario debe revisar el contenido y señalar ajustes antes de continuar. Después se definirá la configuración básica de entrevista y su validación. La conexión con Ollama sigue correspondiendo a la Etapa 5. La comprobación real del cumplimiento de las instrucciones y los casos semánticos requerirá pruebas con el modelo y revisión humana.

### 30 de octubre de 2026: configuración básica y contrato

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

### 30 de octubre de 2026: carga integrada del escenario

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

### 30 de octubre de 2026: contexto autorizado inicial

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

### 30 de octubre de 2026: inicio de la Etapa 5, cliente local

El usuario confirmó **226 passed in 15.46s** y la salida de roles, pregunta y `Contexto preparado`. Se verificó el servicio Ollama **0.34.2**, con `qwen3:4b`, `gemma3n:e2b` y `qwen3:8b` instalados. `qwen3:4b` informa capacidades de completado, herramientas y razonamiento. Se mantuvo el modelo aprobado, sin descargas ni cambios en los datos.

Se instaló **HTTPX 0.28.1** y sus dependencias únicamente en `.venv`; `pip check` no encontró incompatibilidades. Se definieron `OllamaSettings`, la interfaz `LLMClient.generate`, `LLMResponse`, errores compartidos y el adaptador `OllamaClient`. El adaptador valida mensajes, envía JSON a `/api/chat` y recupera solo la respuesta final. No carga credenciales o `.env`, usa únicamente una dirección local y no tiene cambio automático a API externa. El adaptador externo sigue pendiente como otra unidad.

La configuración inicial solicita contexto de 8192, salida máxima de 512 tokens, temperatura 0,2 y desactivación del razonamiento. La espera de conexión es de 5 segundos con un reintento limitado. Las esperas de lectura y los errores HTTP no provocan otra generación automática. No se creó entrevista interactiva, historial, contador o evaluación.

Se añadieron 52 pruebas unitarias del contrato HTTP y una integración, con transporte simulado: **279 passed in 10.27s**. Tras el primer intento real se amplió la espera y se añadieron dos pruebas del guardado de evidencia, con respuesta y error: **281 passed in 15.48s**, 273 unitarias y ocho integraciones. Ninguna de estas pruebas consulta un modelo ni demuestra coherencia de respuestas.

#### Primera llamada real y diagnóstico

`python -X utf8 -m scripts.smoke_test` preguntó «¿Dónde estudiaste y qué título obtuviste?». La primera llamada agotó los **180 segundos** de espera de lectura y terminó con `LLMTimeoutError`, sin devolver texto. El perfil conservó su huella original. La evidencia se guardó en `outputs/results/ollama-smoke-9cde55f5de494d35ad3836f6911b7862.json`; su fecha UTC es 31 de octubre, correspondiente al 30 de octubre en Santiago.

El registro del servicio mostró carga del modelo, contexto de **4311 tokens**, avance de procesamiento y cancelación al terminar la espera del cliente. `ollama ps` informó 4,1 GB de carga, 65 % CPU / 35 % GPU y contexto de 8192. Estos valores describen esa ejecución; no se deducen del tamaño en disco ni se generalizan a otras cargas. No se atribuyó una causa definitiva al tiempo total a partir de esos mensajes.

Se amplió la espera de lectura a **300 segundos** para repetir la observación. El script también registra desde entonces `test_elapsed_seconds`, duración total hasta terminar la comprobación de integridad, distinta del tiempo de la llamada HTTP informado en la respuesta. La evidencia inicial se conservó intacta. Las restricciones de la herramienta impidieron el primer acceso a localhost; se ejecutaron las consultas con el acceso correspondiente. No fue un error de instalación del modelo.

#### Intentos de respuesta directa y corrección del diagnóstico

El segundo intento, con los mismos pesos, terminó en **177,54 s**, entrada **4311**, salida **512**, motivo `length`. El texto no fue una intervención válida del candidato. La evidencia `ollama-smoke-e924fab38ad84258bff28d889e2db8d1.json` conserva el estado `completed` de la primera versión del script; ese estado era solo técnico y no se acepta como éxito semántico. Se corrigió el script para devolver `incomplete` y código 1 cuando se alcanza el límite de salida, sin mostrar el texto parcial como respuesta del candidato.

Un prefijo vacío enviado como mensaje tampoco resolvió el comportamiento: **135,96 s**, entrada **4313**, salida **410**, motivo `stop`, con texto de preparación y respuesta mezclados. Evidencia: `ollama-smoke-89dc371382004e19a5b1deee14459b1e.json`. Ese resultado también es semánticamente inválido pese al antiguo estado técnico `completed`.

Se creó temporalmente `qwen3:4b-candidato`, reutilizando las capas del modelo instalado, para comprobar una hipótesis de plantilla. La primera plantilla simplificada no fue seleccionada por Ollama, que prefirió la integrada en el GGUF: **142,65 s**, entrada **4309**, salida **393**, motivo `stop`, también con salida mezclada. Evidencia: `ollama-smoke-797b34c140a6447c995732686d027980.json`. Se confirmó la selección de una segunda plantilla completa y su final con un bloque vacío cerrado mediante diagnóstico de renderizado; aun así no resolvió el comportamiento. La llamada terminó con `LLMInvalidResponseError` después de añadir el rechazo de marcas `<think>` y `</think>` en el contenido. Evidencia: `ollama-smoke-c5f5c4cfb1764fd9ae938d840fe417ff.json`. No se registró como texto de candidato ni se afirmó éxito semántico.

La inspección posterior de `/api/show` identificó la causa que faltaba comprobar al recomendar el modelo: `general.finetune: Thinking`, `general.version: 2507` y referencia a **Qwen3-4B-Thinking-2507**. La [ficha oficial de esos pesos](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507) indica que solo admiten razonamiento. El método de prefijo vacío para variantes híbridas no justificaba esperar ese comportamiento de esta variante. Se corrigió la recomendación; la hipótesis de solucionar todo mediante plantilla quedó descartada.

Se retiró únicamente la variante experimental creada durante esta unidad y su Modelfile del proyecto. Se retiró también la modificación de mensajes en el adaptador. Los tres modelos originales conservaron sus etiquetas e identificadores. No se descargaron pesos ni se activó un proveedor externo.

#### Selección explícita de Gemma y revisión factual

Se eligió `gemma3n:e2b`, ya instalado, como predeterminado en `OllamaSettings`. Fue una decisión explícita de configuración después del diagnóstico, no un cambio automático al fallar una solicitud. Se conservó la interfaz `generate(messages)` y los dos mensajes originales.

La primera consulta con Gemma terminó en **43,15 s**, entrada **4744**, salida **37**, motivo `stop`, con respuesta directa en español. Coincidieron la carrera y la titulación de diciembre de 2025, pero el nombre de la institución apareció como **Instituto Profesional Horizontes Digital**, mientras que el perfil aprobado dice **Instituto Profesional Horizonte Digital**. Esa discrepancia se registró, sin modificar el perfil ni corregir silenciosamente la salida. Evidencia: `ollama-smoke-bf8c3cc943f1460da07af66652a4cce8.json`.

Se reforzó de manera general la copia literal de nombres propios y denominaciones en `agent/agent.md`, versión **1.0.1**, sin introducir nombres del candidato en las instrucciones. SHA-256 del archivo revisado:

```text
31F9CC393E8FEA854342C5C3A755D2F214BC03819BFA779A87C44D2656914CF6
```

La repetición, con el modelo ya cargado, terminó en **15,89 s**, entrada **4811**, salida **33**, motivo `stop`, pero mantuvo el mismo plural incorrecto. Evidencia: `ollama-smoke-257950f0aaa246638c6dc1d6c4c97fdc.json`. El ajuste textual no demostró corregir ese error. El estado técnico `completed` no implica consistencia factual; la revisión humana sigue pendiente. No se implementó un sustituidor de palabras, clasificador o evaluador para ocultar el fallo.

La conexión básica local está implementada y comprobada, pero **la discrepancia del nombre de la institución queda abierta**. Estos resultados no permiten certificar consistencia global, seguridad ante manipulación o latencia de una entrevista de 20 preguntas. La opción externa sigue pendiente de implementación y desactivada; la consola e historial también están pendientes. Se espera la comprobación del usuario antes de otra unidad.

#### Comprobaciones finales de esta unidad

Se añadieron en total **59 pruebas unitarias y una integración**, con transporte simulado. La suite completa final con Gemma configurado terminó con **286 passed in 9.37s**: 278 unitarias y ocho integraciones. Después del ajuste de instrucciones, los 27 casos del constructor y las dos integraciones de contexto y transporte terminaron con **29 passed in 1.91s**. Estos son resultados de programa, separados de las siete llamadas al modelo y de la consulta mínima de diagnóstico. `pip check` confirmó de nuevo dependencias compatibles.

El candidato conservó `6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3` y el puesto `40C16AEEB4D41BE7FC0EFF3D8237178C883CAD294E9D04F96C4D4F9B81455F77`. La fecha del escenario continúa en **2026-10-20**. Cada llamada real comprobó la integridad del original. Las marcas horarias de los JSON se guardan en UTC; esta entrada usa la fecha local de Santiago.

### 31 de octubre de 2026: índice derivado de denominaciones exactas

El usuario confirmó **286 passed in 10.14s** y una llamada real con Gemma de **36,20 s**, entrada **4811**, salida **37**, motivo `stop`, con el perfil intacto. La respuesta volvió a escribir **Horizontes** en lugar de **Horizonte**. Evidencia del usuario: `outputs/results/ollama-smoke-9c9bf4f798ac426191563daade6c6c59.json`. Las instrucciones literales 1.0.1 no habían corregido el caso.

Se amplió `build_messages` con `literal_name_references`, último campo del objeto JSON del contexto. Es un índice derivado en memoria de campos del candidato y el puesto: nombre, instituciones y títulos académicos, organizaciones y cargos laborales, proyectos, título y organización de la oferta. Cada valor conserva su ruta de origen, para distinguir los datos del candidato de las denominaciones del puesto. No se duplica un CV, no se mantiene otro archivo de antecedentes y no hay un nombre de institución incorporado en el código.

La instrucción de uso del índice se coloca antes de los datos. Se conservan el perfil interno completo, las instrucciones aprobadas, los roles `system` y `user` y la pregunta sin cambios. La construcción no consulta archivos, entorno o modelo. No se añadió un clasificador ni un sustituidor de palabras en la respuesta.

El script de prueba registra desde esta revisión `instructions_text_sha256` y `system_message_sha256`: huellas del texto interpretado y del contexto preparado en UTF-8, sin guardar el contexto completo. No se confunden con la huella de bytes del archivo del candidato. Los registros anteriores se conservan con los campos que tenían al generarse.

Dos pruebas nuevas comprueban cobertura y correspondencia exacta de las referencias con los campos originales, y un perfil y puesto alternativos en archivos temporales, con acentos, comillas y barra invertida. Se amplió la integración del contexto sobre las fuentes aprobadas. La suite completa terminó con **288 passed in 9.99s**: 280 unitarias y ocho integraciones, sin red en las pruebas automatizadas. Esas comprobaciones validan el contexto generado, no la obediencia del modelo.

#### Consultas reales y revisión del caso

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

### 31 de octubre de 2026: alternativa externa con activación explícita

El usuario confirmó **288 passed in 12.86s** y una respuesta real con `gemma3n:e2b` que conservó exactamente la institución y el título. La llamada tardó **41,42 s**, entrada **5073**, salida **24**, motivo `stop`, con el original intacto. Evidencia del usuario: `outputs/results/ollama-smoke-7042a2809d634998a709f5bde360d3f3.json`.

Se implementó la alternativa solicitada de API externa como adaptador OpenAI Responses, conservando Ollama predeterminado. Se consultó OpenAI Docs y la documentación oficial del contrato de entrada/salida y errores. La referencia HTML de creación excedía el tamaño admitido por el navegador y su versión Markdown no era compatible con ese lector; se leyeron los campos concretos de la versión Markdown oficial mediante una solicitud de documentación, sin credenciales ni inferencia. No se obtuvo ni configuró una clave real.

Los archivos nuevos son `harness/llm/openai_client.py` y `harness/llm/factory.py`. `OpenAISettings` contiene modelo explícito y límites, sin claves; `LLMAuthenticationError` distingue acceso rechazado. La fábrica utiliza variables de la sesión y no carga `.env`. Exige `LLM_PROVIDER=openai`, `LLM_ALLOW_EXTERNAL_API=true`, modelo y clave para la ruta externa. La ruta Ollama no consulta las credenciales externas. No hay cambio automático de proveedor ante errores.

El adaptador usa HTTPX ya instalado y el endpoint oficial fijo con HTTPS, sin redirecciones ni proxies del entorno. Envía los mismos mensajes en `input`, solicita `store: false` y `stream: false` y recupera solo texto de mensajes completados. Omite elementos de razonamiento y rechaza salida incompleta, vacía, de rechazo o de herramientas no solicitadas. Los errores no imprimen cuerpos HTTP o excepciones de transporte que puedan incluir credenciales. La clave solo se incorpora a la cabecera de autorización y queda fuera de la configuración serializable.

La configuración externa inicial requiere un modelo elegido al activar la opción, salida máxima 512 tokens, conexión de 5 s, lectura de 90 s y un reintento de conexión. La referencia oficial indica un mínimo de salida de 16 tokens y que el límite incluye razonamiento; la validación refleja ese mínimo. No se enviaron parámetros particulares de una familia de modelos, como temperatura. No se eligió ni recomendó un modelo de API sin verificar disponibilidad y costos para el momento de activación.

El script de prueba usa ahora la fábrica y conserva proveedor, parámetros sin claves y los controles de integridad existentes. La salida local mantiene su presentación. Se documentaron las variables en `.env.example`, sin activar ni cargar ese archivo, y el procedimiento futuro en `docs/operacion.md#conexion-api-opcional`. El script puede usar la opción externa cuando se habilite expresamente; no es un adaptador desconectado del punto de ejecución.

#### Pruebas y límites de la verificación externa

Se añadieron 48 casos unitarios del adaptador, 13 de la fábrica, dos del script y una integración: **64 pruebas nuevas**. Se utilizaron una clave y un modelo ficticios con transporte simulado. Se comprobaron contrato HTTP, rechazo de estados incompletos, tipos de error, reintentos limitados, ausencia de cambio de proveedor, controles de activación y ausencia de clave en mensajes, evidencia y errores de prueba, incluso cuando el cuerpo HTTP o el error simulado la incluían.

El conjunto completo terminó con **352 passed in 29.54s**: 343 unitarias y nueve integraciones. `pip check` devolvió `No broken requirements found.`. No se añadieron paquetes ni se realizaron solicitudes reales a la API de modelos externa. Esta verificación no acredita autenticación real, acceso al modelo, cuota, facturación, conectividad al servicio o calidad de respuestas externas. Esas comprobaciones se harán cuando el usuario decida utilizar la opción.

Una comprobación de valores predeterminados sin solicitudes imprimió:

```text
Proveedor: ollama
Modelo: gemma3n:e2b
```

#### Comprobación real de la ruta local compartida

Se ejecutó el script actualizado en un proceso con `LLM_PROVIDER=ollama` y `LLM_ALLOW_EXTERNAL_API=false`. La llamada a Ollama terminó en **43,71 s**, entrada **5073**, salida **24**, motivo `stop`, con «Instituto Profesional Horizonte Digital» e «Ingeniería en Informática» exactos. El original quedó intacto. Evidencia: `outputs/results/ollama-smoke-8eed79894c7443c2a5fbfbf2028963c1.json`.

La llamada confirma la integración local del selector; no es una medición externa. No se cambia la interpretación de los tiempos anteriores ni se certifica consistencia global a partir de esta pregunta. La fecha del escenario, máximo de preguntas, perfil, puesto e instrucciones no se modificaron. Se espera la comprobación del usuario antes de pasar a otra unidad o a la consola.

### 31 de octubre de 2026: diagnóstico de la llamada de 275,82 segundos

El usuario confirmó **352 passed in 13.34s** y otra respuesta correcta de Gemma, con entrada **5073**, salida **24**, motivo `stop` y el original intacto, pero la llamada tardó **275,82 s**. Evidencia: `outputs/results/ollama-smoke-5f2399bfb48b4c6e9e09d93a4122bc94.json`. Se revisó esta demora antes de añadir la consola, por su efecto en una demostración.

#### Observaciones y límites del diagnóstico

El registro técnico del servicio terminó esa solicitud a las **03:06:35, hora de Santiago**, coincidiendo con inicio UTC y duración del JSON. Informó:

```text
prompt eval time = 232601.99 ms / 5073 tokens
eval time = 14312.32 ms / 24 tokens
total time = 246914.31 ms / 5097 tokens
HTTP 200, POST /api/chat, 4m35s
```

Se identificó el procesamiento del contexto como la mayor parte de esa llamada. El resto de los 275,82 s no se atribuyó automáticamente a carga: la respuesta guardada no tenía todavía el desglose. No se modificó la evidencia antigua ni se reconstruyeron sus campos como si hubieran sido recibidos en ese JSON.

Las comprobaciones actuales mostraron `gemma3n:e2b` cargado con tamaño informado de 6,2 GB, reparto 76 % CPU / 24 % GPU y contexto de 8192. La lectura de memoria disponible rondó 4,4 GB. Son observaciones del momento de diagnóstico, no una medición continua durante la llamada anterior. No permiten establecer por sí solas una causa térmica, de energía, controladores o competencia entre procesos. No se cambió ninguna configuración del equipo para probar esas hipótesis.

#### Ajuste acotado y observabilidad

`LLMResponse` añade campos opcionales de total del servidor, carga, procesamiento de contexto, generación y tokens reutilizados. El adaptador Ollama convierte las duraciones enteras de nanosegundos a segundos; tipos incompatibles, negativos o desbordados quedan desconocidos. Cero sigue siendo válido. Un conteo de caché superior a la entrada informada tampoco se presenta como medición válida. OpenAI conserva los campos en `None`, sin inventar información.

El script muestra y conserva ese desglose. `OllamaSettings.keep_alive` solicita ahora **15 minutos** de permanencia después de responder y se envía en cada solicitud local. Esto ayuda a evitar otra preparación por descarga automática entre pausas, manteniendo memoria ocupada durante ese periodo. No se aumentó el tiempo de lectura de 300 s, no se redujo contexto ni se alteraron los antecedentes.

Se añadieron **21 pruebas unitarias** para conversión, ausencia de métricas, cero, valores inválidos, caché inconsistente y permanencia configurable. El conjunto terminó con **373 passed in 53.29s**: 364 unitarias y nueve integraciones. Las solicitudes de la suite fueron simuladas. No se instalaron bibliotecas o modelos.

#### Dos consultas reales con el mismo contexto

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

### 31 de octubre de 2026: Etapa 6, primera conversación en consola

El usuario confirmó **373 passed in 10.12s** y dos respuestas locales correctas de **1,84 s** y **1,81 s**, con 5072 de los 5073 tokens de entrada reutilizados, salida 24 y motivo `stop`. Las dos conservaron el original. Evidencias del usuario: `ollama-smoke-6b81c5beaa554c0b9ffe21c2629ea3e7.json` y `ollama-smoke-6ceeb90947634da7a8fdd9534134d0a0.json`. Son mediciones con contexto reutilizado, no una garantía de carga inicial.

Se implementaron `InterviewRuntime` en `harness/runtime.py`, `format_job` y `run_console` en `harness/application/cli.py`, y el punto ejecutable `scripts/run_interview.py`. El cargador y las instrucciones se utilizan una vez al abrir el programa. La fábrica conserva la selección local por defecto y la alternativa externa explícita. No hubo nuevas dependencias ni cambios del perfil, puesto, configuración o instrucciones.

La consola presenta candidato, puesto y proveedor, permite consultar `/cv` y `/puesto`, comenzar con `/iniciar`, mostrar `/ayuda` y terminar con `/salir`. Cada entrada de pregunta tiene una línea. El CV utiliza la vista pública existente; el puesto muestra responsabilidades, requisitos, competencias y nivel esperado, sin volcar instrucciones o relatos internos del perfil.

El controlador es independiente de entrada y salida de terminal: recibe escenario, instrucciones y el contrato del cliente. Cuenta una pregunta válida enviada aunque falle la respuesta; comandos, entradas vacías y mensajes del programa no cuentan. Repetir `/iniciar` no reinicia el contador. Aplica el límite de la configuración, probado también en veinte preguntas, e impide otra llamada después de terminar. Cada ejecución crea un contador independiente.

Se muestra un error conocido del proveedor y se permite otra pregunta si quedan lugares; no se vuelve a enviar automáticamente la generación. Una salida cortada no se presenta como respuesta válida del candidato. Fin de entrada y `Ctrl+C` cierran de forma controlada. El cliente se cierra desde su contexto de recursos. El perfil se comprueba antes y después de generar y al terminar el programa; un cambio detectado cierra la ejecución y no produce un mensaje de archivo intacto.

#### Pruebas y corrección de una referencia de prueba

La primera ejecución de las pruebas nuevas terminó con **1 failed, 28 passed**. La comprobación de que el menú no expusiera un relato privado buscaba la clave `situation`, que no existe en ese registro. Se revisó el perfil y se corrigió únicamente la referencia de prueba a `context`, sin modificar antecedentes. Se añadió la interrupción durante la espera del modelo y una integración de extremo a extremo con HTTP simulado.

La suite completa terminó con **404 passed in 14.67s**: 394 unitarias y diez integraciones. Son 30 casos unitarios y una integración nuevos. Cubren límites, contadores, independencia de ejecuciones, roles sin historial, errores y ausencia de reenvío, salida cortada, comandos, privacidad de vistas, interrupciones, errores de preparación, cierre del cliente y cambios del perfil antes o durante una generación, incluso si esta falla. Las modificaciones de datos se hicieron sobre copias temporales. No hubo solicitudes reales en pytest.

#### Ejecución real del programa

Se ejecutó un proceso real de `python -X utf8 -m scripts.run_interview`, con entrada UTF-8 controlada, `LLM_PROVIDER=ollama` y `LLM_ALLOW_EXTERNAL_API=false`. Las entradas fueron `/cv`, `/puesto`, `/iniciar`, «¿Dónde estudiaste y qué título obtuviste?» y `/salir`.

El programa mostró las dos vistas, inició el contador en 1/20, obtuvo «Instituto Profesional Horizonte Digital» e «Ingeniería en Informática» exactos y terminó antes de agotar el máximo. La respuesta tardó **34,60 s**. El proceso devolvió 0 y comprobó el original intacto. Se revisó visualmente la salida capturada.

Evidencia técnica: `outputs/results/console-smoke-aad61a8860c740d983b1dc4b002c0c8e.json`. El registro fue creado por la verificación controlada, con las entradas, salida del ejecutable y huella del perfil; no es un guardado automático de entrevista. No se midieron en esta ejecución las fases del proveedor ni se atribuyó la duración a una causa específica.

#### Límites de esta unidad y siguiente paso

Cada pregunta se responde desde el mismo perfil y configuración, sin incluir preguntas o respuestas previas. La interfaz lo anuncia para que el usuario formule preguntas independientes. El programa todavía no guarda conversaciones, crea identificadores de sesión o resume contexto. Esas funciones permanecen en la Etapa 7. No se implementaron clasificación, evaluación, puntuaciones o retroalimentación educativa.

El control de veinte preguntas se verificó con respuestas simuladas; la prueba real revisó solo la pregunta de formación. No se certifica consistencia global ni latencia de una entrevista completa. El máximo sigue en **20** y la fecha del escenario en **2026-10-20**. Se espera la comprobación del usuario antes de iniciar la siguiente unidad.

### 31 de octubre de 2026: incidencias de la prueba ampliada y corrección previa al historial

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

### 31 de octubre de 2026: comprobación del usuario de la corrección en consola

El usuario aportó **411 passed in 14.84s** y la repetición de los trece casos con `gemma4:e4b`, proveedor local y API externa desactivada. La transcripción se conservó íntegra como `outputs/results/console-user-correction-2026-10-31.txt`. Se revisó también el archivo real `candidate-behavior-5cfb16b620624f6fb9beb5a6bf774ad8.json`: trece respuestas completas con stop, sin errores, cortes o U+2581 y con el perfil intacto. Las llamadas sumaron 100,52 s, el máximo fue de 19,53 s y la salida más larga de 84 tokens. Las huellas de sistema e instrucciones son las de 1.0.5. No se hicieron nuevas llamadas al modelo ni se atribuyeron las mediciones a esta revisión.

La revisión comprobó institución y título, límites técnicos, ausencia de consultas exactas inventadas y conservación del rol ante ambas formas de pedir el intercambio. El ejemplo legítimo de Python siguió disponible. S1 mantiene que Nicolás identifica el error y consulta su propuesta, aunque añade «tras su guía», una ampliación del apoyo no detallada por la fuente. Se registró como matiz bajo observación, sin cambiar los datos ni afirmar fidelidad universal. Los hashes de candidato, puesto y configuración permanecen iguales a los aprobados.

Se cierra la corrección acotada de la Etapa 6 con evidencia del usuario y se mantiene ese matiz para la revisión posterior. Se propone como siguiente unidad de la Etapa 7 conservar turnos completos en memoria y comprobar repreguntas y aislamiento. No se implementa esa etapa en esta revisión: el prompt maestro exige «No avances automáticamente entre etapas». No se cambian código, dependencias, proveedor o modelo predeterminado.

### 31 de octubre de 2026: Etapa 7.1, historial de turnos completos en memoria

El usuario indicó «Continuemos» tras revisar la corrección de consola y la propuesta de comenzar el historial en memoria. Se explicó el alcance antes de implementar: conservar turnos durante la ejecución, comprender repreguntas y comprobar aislamiento; las demás unidades de sesiones y contexto se mantienen posteriores.

Se amplió `build_messages` con el argumento opcional history. Acepta pares completos user/assistant, rechaza nuevas reglas system o estructuras incompletas, conserva los textos y devuelve copias nuevas. El sistema, perfil y configuración no se obtienen del historial. Sin historial, el mensaje de sistema inicial conserva la huella anterior. No se modificaron instrucciones, perfil, puesto, configuración, adaptadores, selección de proveedor o dependencias.

`InterviewRuntime` conserva una lista propia por objeto y expone `history_messages()` mediante copias. Cada generación recibe el sistema, los turnos completos previos y la pregunta actual. Solo se incorpora el nuevo par después de una respuesta completa y de las comprobaciones de integridad. Errores, interrupciones y salidas cortadas siguen contando como preguntas enviadas, pero no aportan pares incompletos al contexto. Los comandos y la repetición de iniciar no borran ni añaden turnos. Cerrar impide continuar y conserva la lista mientras exista el objeto; el programa todavía no la guarda en disco.

La consola informa de que conserva la conversación durante esta entrevista y de que se pierde al cerrar el programa. Se creó la guía `docs/contexto-y-sesiones.md#historial-en-memoria` y se actualizaron las guías actuales, arquitectura y pruebas dependientes.

La primera ejecución de pytest encontró **1 error de recolección en 0,75 s**: los dos archivos nuevos tenían el nombre test_conversation_memory.py y se importaban sin paquetes separados. Se renombró solo el de integración a test_history_flow.py, conservando sus comprobaciones; no se borraron cachés ni se cambió pytest. Después, la suite completa terminó con **432 passed in 17.73s**: 421 unitarias y once integraciones. Son veinte casos unitarios y una integración nuevos. Las comprobaciones anteriores del contador y la consola se actualizaron al nuevo contexto de turnos completos.

Se comprobó además el ejecutable real con cuatro preguntas enlazadas sobre Inventario Aula y gemma4:e4b, manteniendo la API externa desactivada. El candidato describió su aporte, las tecnologías, la ausencia de clientes comerciales o producción y recordó el proyecto de la primera pregunta. Las llamadas tardaron 62,99; 8,62; 6,96 y 7,63 segundos. El proceso duró 87,35 s y terminó con 0. No se midieron las fases del servidor ni se atribuyó la latencia inicial a carga, caché u otra causa sin evidencia.

Evidencia externa: `outputs/results/console-memory-18b74d5c14914bf7bf803149eac72746.json`. Guarda entradas, salida original y hashes antes/después; todos los archivos del escenario e instrucciones quedaron intactos. El sistema inicial sigue en A2596C462EEBACB0B25188C351FA7064C4496565A3AFB359F5097297CF2E8C1B. La transcripción la creó el controlador externo de prueba, no una función de guardado de la aplicación.

La memoria del LLM no convierte sus afirmaciones en hechos validados. Esta muestra breve no demuestra consistencia universal. Se mantienen pendientes las unidades de identificadores y datos de sesión, registro completo de intentos y errores, presupuesto de contexto, resumen y persistencia JSON. El cliente conserva 8192 tokens solicitados; no se afirma que veinte turnos de cualquier extensión quepan. Se espera la ejecución del usuario antes de continuar.

### 31 de octubre de 2026: corrección de cronología durante la comprobación de memoria

El usuario confirmó **432 passed in 16.65s** y la continuidad en las cuatro preguntas de Inventario Aula. Añadió una consulta de tecnologías de MesaFaro, respondida con Python, Flask, PostgreSQL, Git y pytest. Al preguntar por el orden de realización, recibió «Primero realicé el proyecto académico Inventario Aula, y posteriormente trabajé en el proyecto profesional MesaFaro». La fuente aprobada establece MesaFaro de 2025-04 a 2026-09 e Inventario Aula de 2025-08 a 2025-11. Se registró la inconsistencia en chronology-user-e7ebfa8766304c978a48c45cccd75d37.json. La memoria y la integridad técnica no impidieron un error de interpretación temporal.

Se realizó una corrección acotada antes de continuar la Etapa 7. `_project_chronology` deriva del perfil el orden de inicio, el de término y los pares de proyectos con meses comunes. Los intervalos y empates se conservan a precisión mensual. El índice se incorpora al sistema junto con el perfil completo y, en la versión final, se presenta también como referencia legible después de las instrucciones. No se inspecciona la pregunta para sustituir respuestas, no se cambia el perfil ni se introduce un clasificador. Se actualizaron los contratos de pruebas del formato del contexto. El controlador de historial y los adaptadores no cambiaron.

Las instrucciones se revisaron en tres pasos conservados. Con 1.0.6 se reprodujeron ocho turnos de la conversación y dos regresiones; el caso original y el solapamiento quedaron correctos, pero otro orden de mención produjo una frase que llamó posterior a abril de 2025 respecto de agosto de 2025. Con 1.0.7, ambos historiales dieron el inicio correcto; la consulta por finalización confundió la etiqueta de inicio con el orden por término. Las evidencias completas de ambos intentos se conservan como 5a66f70bc95a46ec8e65d8915c8decf2 y c09c1a6a0ae044e8b40b42a7189c2835. No se marcaron como aprobaciones semánticas.

La versión final **1.0.8** utiliza por separado las listas de inicio y término y una referencia breve derivada al final del sistema. Las ocho pruebas unitarias nuevas y las pruebas dependientes terminaron con **440 passed in 16.94s**: 429 unitarias y once integraciones. Cubren fechas, orden, solapamientos, cambios de año, empates y separación respecto del historial. No hubo nuevas dependencias o llamadas reales en pytest.

La revisión final real, 74e4d7da5b864355a82644a3a04fd85a, utilizó seis consultas con gemma4:e4b: ambos órdenes de mención, corrección de una respuesta errónea en una copia del historial, inicio y coincidencia sin historial, término y rechazo de instrucciones internas. Dio MesaFaro primero por inicio, Inventario Aula primero por término y coincidencia de agosto a noviembre de 2025. Las seis terminaron completas con stop; las llamadas sumaron 80,63 s, con máximo de 33,63 s. La entrada máxima informada fue 5253 tokens. Las copias de historial proceden de la primera prueba y están identificadas como fixtures; no representan una función de reapertura de sesiones.

El perfil, puesto y configuración conservan sus hashes aprobados, la referencia **2026-10-20** y el máximo **20**. Cada prueba preservó el archivo de instrucciones que cargó; el archivo final 1.0.8 tiene SHA-256 39F22FFADC4DA569C2485D5E834A185B8A1ACB8D030C5D7FDBE9B92300E1C9D1. La huella del sistema final es D979169ECC9392190D63A6BB16BC586D28F7312AD2A768E6C327F193316137AF. API externa desactivada, sin cambios de proveedor, modelos instalados o modelo predeterminado. Se espera la comprobación del usuario antes de otra unidad; esta muestra no acredita consistencia universal.

### 31 de octubre de 2026: duración laboral y comparación completa con estudios

El usuario confirmó **440 passed in 45.40s** y los órdenes correctos de inicio, solapamiento y término de los proyectos. Al añadir preguntas recibió un total aproximado de un año y medio incluyendo práctica, una respuesta sobre estudios sin acotar periodo y una comparación que omitía MesaFaro. Se conservaron los tres casos en temporal-user-27a8aaec91904d909ac51095afd5b6cc.json. La segunda pregunta es ambigua; no se afirma que la respuesta fuese falsa para todo periodo. La primera llamada tardó 83,54 s, sin métricas de fases que permitan atribuir una causa.

Se añadió harness/temporal_facts.py, módulo puro sobre el perfil validado. Computa la unión de meses calendario de roles laborales (ambos extremos incluidos) sin sumar proyectos académicos o duplicar empleos concurrentes. Conserva los periodos de jornada y meses sin jornada registrada, sin inventar horas ni convertirlos a equivalentes de jornada completa. Los datos reales dan 21 meses: 3 de práctica y 18 posteriores, con nueve meses parciales y nueve completos en el rol junior; la práctica no especifica horas. El resumen profesional del perfil ya separaba práctica y experiencia posterior y no se modificó.

El mismo módulo ordena términos de todos los proyectos, estudios y titulación, manteniendo estas dos últimas fechas separadas aunque coincidan. El contexto incorpora temporal_facts y una referencia legible. El archivo original, el controlador de memoria y los adaptadores no cambiaron; no se añadieron dependencias o clasificación. Se actualizaron las comprobaciones del formato del sistema.

Con instrucciones 1.0.9, una conversación real de nueve turnos y una regresión de historial dieron el total y los tres hitos correctos, con 10 respuestas completas. Se observaron un periodo escogido condicionalmente en la pregunta ambigua y una confirmación inicial «sí» al corregir un total anterior. Con 1.0.10 se obtuvo aclaración del periodo y reconocimiento del error, pero otra consulta volvió a omitir MesaFaro y un desglose omitió las dos jornadas de nueve meses. Ambas evidencias completas se conservan: ecb639143776469692bf7a3be5051070 y 0a35c3f20ad84ea28f0ee1f814c11f5f. No se interpretan como obediencia semántica universal.

La revisión final **1.0.11** precisa el alcance completo de las comparaciones, separa corrección de cifras de explicación de jornadas y presenta la secuencia conjunta al final del sistema. Se añadieron diez casos unitarios y una integración. La suite final terminó con **451 passed in 18.36s**, 439 unitarias y doce integraciones, sin llamadas reales en pytest. Una ejecución anterior de 1.0.9 midió 46,95 s y otra de 1.0.10 40,60 s; no se atribuye esa variación a la corrección sin evidencia.

La revisión final real usa seis contextos en temporal-facts-cb43fd58aa77453b80a6d8eafc13f389.json. Dio 21 meses sin historial y con una respuesta previa incorrecta, pidió precisar el periodo ambiguo, incluyó Inventario Aula en noviembre de 2025, estudios/titulación en diciembre de 2025 y MesaFaro en septiembre de 2026, distinguió las jornadas y mantuvo el orden de inicio de proyectos. La respuesta al total anterior comenzó con «sí» sin reconocer verbalmente el error: el valor fue corregido, pero ese matiz queda registrado y no se considera uniformemente resuelto.

Las seis llamadas terminaron completas con stop; sumaron 110,27 s, con máximo de 36,75 s y entrada máxima informada de 6550 tokens. Los historiales son copias identificadas de la prueba anterior y no implementan reapertura o persistencia de sesiones. Perfil, puesto y configuración conservan sus hashes aprobados, referencia **2026-10-20** y máximo **20**; cada prueba preservó también las instrucciones que cargó. El archivo final 1.0.11 tiene SHA-256 3058B4797EFC654FF656DEDA9D1BE3E93420015D3D06451FCFADEEA8FBA17B05 y el sistema 351DA8FCD6D6CC963F307BAF931DDA18BDF6333557D03906ED0A36C77408051F. API externa desactivada, sin cambios de modelos instalados o proveedor. Se espera la comprobación del usuario antes de continuar con otra unidad.

### 31 de octubre de 2026: comprobación del usuario y Etapa 7.2

El usuario confirmó **451 passed in 19.21s** y cuatro respuestas correctas para el alcance solicitado: 21 meses calendario incluyendo práctica, nueve meses parciales y nueve completos como junior, secuencia Inventario Aula en noviembre de 2025 → estudios y titulación en diciembre de 2025 → MesaFaro en septiembre de 2026, y petición de aclarar el periodo ambiguo. La ejecución terminó con el original intacto. Se conservó una transcripción estructurada en temporal-user-confirmation-4ff8d4818cd74151bb2f0990d0afd65e.json, con latencias 8,68; 12,16; 15,79 y 8,25 segundos. No se generaron respuestas para esa revisión. No se ejercitó el matiz de reconocimiento verbal de un error anterior.

Después de esa comprobación se continuó con una unidad pequeña de la Etapa 7 ya aprobada: identidad y registro de sesiones en memoria. Se explicó el alcance y los archivos antes de implementar. Se completó el marcador existente harness/session_state.py con SessionState, UUID por ejecución, configuración protegida, candidato/puesto, procedencia por hashes, proveedor/modelo solicitados, fechas UTC, cierre e intentos. No se implementaron persistencia, base de datos, clasificación, evaluación o resumen.

InterviewRuntime obtiene contador y mensajes completos del registro, sin mantener otra lista autoritativa. Un intento se crea antes de llamar al cliente y termina como completo, error, incompleto o interrumpido. Conserva respuestas parciales para diagnóstico sin devolverlas como respuestas válidas o enviarlas al modelo en el turno siguiente. Registra ambos incidentes cuando coinciden error del proveedor y alteración del perfil. El catálogo no copia detalles arbitrarios, causas de excepciones, trazas, cuerpos HTTP o configuración privada del cliente.

La integridad se comprueba también en el punto de entrada al finalizar. Una alteración detectada se conserva en source_integrity aunque se restauren los bytes; no se duplican las incidencias fatales al repetir la comprobación. El primer motivo y fecha de cierre no se sobrescriben. Las vistas son copias y los metadatos no entran en el contexto del LLM. La consola muestra identificador, incorpora /sesion sin consumir una pregunta y presenta un resumen final. La configuración reutilizable no se utiliza como identificador de entrevista.

Se añadieron 25 casos unitarios y una integración. La suite final terminó con **477 passed in 19.10s**, 464 unitarias y trece integraciones; una comprobación previa de 476 casos pasó en 26,97 s antes del caso final de integridad tras el cierre. No hubo fallos de prueba ni solicitudes reales en pytest. La integración simula un HTTP 500 con cuerpo reservado y una recuperación; prueba registro, contexto, resumen, recursos y protección de fuentes.

La verificación real usó la consola con gemma4:e4b, /sesion antes y después de dos preguntas, y /salir. Conservó el identificador 13d0d1ae-99a8-4729-8954-02b663c62dc9, creó dos intentos completos, registró fecha de creación y finalización en UTC y terminó cerrada por user_exit, con cero incidencias y fuente sin cambios. Las respuestas mantuvieron 21 meses y el desglose de nueve parciales y nueve completos; tardaron 62,16 y 14,98 s. No se midieron fases ni se atribuyó la latencia inicial a una causa concreta.

Una segunda sesión independiente pidió un nombre de modelo inexistente generado para la prueba. Obtuvo y registró model_not_found con estado error, sin respuesta inventada. No se descargaron modelos ni se modificó la elección normal. El proceso total duró 78,10 s; ambas sesiones tuvieron identificadores distintos y los bytes de perfil, puesto, configuración e instrucciones quedaron intactos. Evidencia externa: session-records-c2c4375fb58340bf832dce71df8c5554.json. Los registros los escribió el verificador externo, no una función de guardado de la aplicación.

Se mantuvieron instrucciones **1.0.11**, hashes aprobados, referencia **2026-10-20**, máximo **20**, proveedores y modelos instalados. No se añadieron dependencias ni se activó la API externa. Se espera la ejecución del usuario de esta unidad antes de continuar con guardado JSON o gestión del tamaño del contexto. El registro técnico no certifica consistencia semántica universal.

### 31 de octubre de 2026: confirmación de la 7.2 y guardado JSON (7.3)

El usuario confirmó **477 passed in 19.83s** y **477 passed in 19.45s**. La primera sesión, 95f03b31-2a58-45f6-9775-41fc02df18e7, mantuvo el identificador durante dos preguntas, pasó de cero a dos respuestas completas, registró cero incidencias y cerró con el original intacto. Conservó los 21 meses calendario y el desglose de nueve meses parciales y nueve completos; latencias 64,30 y 13,05 s. La segunda sesión, a9370429-7013-4876-b35e-87a618c07bc3, tuvo otro identificador y cero intentos. La transcripción original se copió sin cambios a session-user-confirmation-93abca64583446d89fca2a0f5722dc28.txt. No se crean archivos retrospectivos de esas sesiones, que entonces solo existían en memoria.

Se continuó con una unidad de la misma Etapa 7: guardar registros cerrados y leer sus datos. Se completó harness/session_log.py y schemas/session.schema.json. El guardado reutiliza el lector y los esquemas existentes, comprueba referencias, UUID, numeración, límites, fechas UTC reales y coherencia de estados/respuestas. Usa UTF-8, rechaza números no finitos y crea un archivo exclusivo por UUID, sin sobrescribir archivos previos. Comprueba escritura, vacía el búfer y solicita sincronización; ante un fallo detectado intenta retirar solo el archivo que creó. Si no puede retirarlo, identifica el archivo posiblemente incompleto. No se implementa recuperación frente a un cierre forzado o corte de energía.

El punto de entrada guarda después de la comprobación final de integridad. Incluye sesiones vacías y registros de diagnóstico con integridad fallida. Un fallo de escritura se informa sin confirmar guardado y devuelve código 1. La carga valida los datos y devuelve un diccionario nuevo; no reanuda conversaciones. Se preservan preguntas y respuestas exactas, métricas y catálogo seguro de errores, sin copiar el perfil interno, el mensaje del sistema o credenciales. Los estados técnicos no califican la calidad semántica de las respuestas.

Se añadieron **45 casos unitarios y ocho integraciones**; el caso existente de integridad final también comprueba su archivo de diagnóstico. tests/conftest.py aísla los archivos de la aplicación en directorios temporales durante pytest. La primera recolección falló por construir ProfileIntegrityError con un argumento en lugar de sus tres argumentos; se corrigió únicamente la preparación del error simulado. Después pasaron 51 casos nuevos. Se añadieron dos casos sobre formato de fecha UTC y la suite final terminó con **530 passed in 26.20s**: 509 unitarias y 21 integraciones. No se hicieron llamadas reales en pytest.

La comprobación real usó Ollama local y gemma4:e4b con API externa desactivada. La aplicación creó session-67fbee76-9926-438d-8d19-5b0da7f20036.json: dos intentos completos, 21 meses y nueve meses por jornada, latencias **64,76 s** y **15,23 s**, cero incidencias, cierre user_exit y fuente intacta. Otra ejecución sin preguntas creó session-b51cad38-89df-4fcc-b2ef-d7ab450ff366.json, con otro UUID y cero intentos. Conservó el primer archivo. En ambos casos load_session devolvió exactamente la instantánea final del controlador. Evidencia completa: session-persistence-ca7f555825ac4bf29124f9cbb29666b9.json.

Perfil, puesto, configuración e instrucciones conservaron los cuatro hashes aprobados; referencia **2026-10-20**, máximo **20**, instrucciones **1.0.11**, modelo predeterminado y adaptadores sin cambios. No se añadieron dependencias ni se activó una API externa. El guardado cumple esta unidad, sin afirmar consistencia universal del modelo. Se espera la comprobación del usuario antes de otra unidad; presupuesto de contexto, resúmenes y extracción de hechos relevantes continúan pendientes.

### 31 de octubre de 2026: confirmación del guardado y diagnóstico de contexto (7.4a)

El usuario confirmó **530 passed in 26.55s**. La sesión d8964573-f78f-4fe6-802a-391e2e6913d7 mantuvo 21 meses calendario y nueve meses por jornada, con latencias 63,13 y 13,22 s. Cerró con dos intentos completos, cero incidencias y el original intacto. La lectura validada mostró el mismo UUID, closed, unchanged y dos estados completed. Se comprobó localmente el archivo y se conservó evidencia estructurada que distingue el resultado informado por el usuario de la lectura local: session-persistence-user-confirmation-93b7cab3eadb498d808facee10093926.json.

La siguiente unidad pequeña de la misma Etapa 7 es medición antes de implementar resumen. Se añadió harness/context_budget.py con ContextBudget, reservas explícitas y comparación de tokens ya informados; scripts/inspect_context.py permite consultar un archivo cerrado sin red ni escritura. No se integró una nueva política en el controlador ni se modificaron mensajes. El presupuesto se presenta como parámetro de comparación, porque el archivo de sesión 1.0.0 no conserva num_ctx o máximo de salida histórico. No se infiere capacidad del nombre del modelo.

Se eligió capacidad de comparación 8192, reserva de salida 512 y margen inicial configurable 256; límite de entrada 7424. Los estados son dentro, en el límite, sobre el presupuesto o desconocido si falta métrica. Un cero informado se conserva distinto de None. Se incluyen intentos con respuesta parcial y no se inventan conteos para fallos sin respuesta. La caché no se resta de los tokens del prompt. Se consultó la documentación primaria actual de Ollama sobre Chat API y Usage; no se añadieron nuevas llamadas o campos al adaptador instalado.

Se añadieron 25 casos unitarios y cuatro integraciones. La suite final terminó con **559 passed in 27.36s**, 534 unitarias y 25 integraciones, sin fallos ni llamadas reales. Las integraciones bloquean HTTP y verifican que el diagnóstico conserva los bytes de archivos. La lectura real de la sesión del usuario mostró entradas 6023 y 6097, márgenes 1401 y 1327, pico 6097 y cero intentos sin métrica. Código 0. No se generaron nuevas respuestas del candidato ni se reactivó la API externa.

Evidencia: context-budget-7bbc164655844b038dfe497a064d4101.json. Los hashes de todos los JSON de sesión existentes y de perfil, puesto, configuración e instrucciones permanecieron intactos. Se conservan instrucciones **1.0.11**, referencia **2026-10-20**, máximo **20**, dependencias y ajustes del proveedor. Las métricas pasadas no garantizan capacidad para una pregunta futura ni ausencia de recortes del servidor. Resumen controlado, conservación de hechos y su integración siguen pendientes; se espera la comprobación de esta unidad antes de continuar.

### 31 de octubre de 2026: confirmación del diagnóstico y protección del contexto (7.4b)

El usuario confirmó **559 passed in 25.70s** y el diagnóstico de la sesión d8964573-f78f-4fe6-802a-391e2e6913d7: entradas 6023/6097, límite 7424, márgenes 1401/1327 y cero intentos sin métrica. Se leyó el archivo y se conservó un registro que distingue la salida comunicada de la lectura local: context-diagnostic-user-confirmation-e12379075fb240f7bbbc28ee0aa30ce6.json.

Antes de integrar un resumen se revisaron las protecciones de la versión instalada. /api/version confirmó **0.34.2**. Su contrato primario incluye truncate y shift; se añadieron ambos como false al nivel principal de cada solicitud del adaptador local. No se aumentó num_ctx ni se alteró el historial. Una prueba directa con texto sintético recibió HTTP 400: entrada 16009 tokens frente a 8192 de capacidad, error tipado exceed_context_size_error dentro de una cadena JSON. Tardó 28,03 s, sin desglose causal por fases.

Se añadió LLMContextLimitError al contrato compartido y reconocimiento de formas conocidas del rechazo. El error público utiliza texto fijo; no copia el cuerpo del servidor y no reenvía la solicitud ni cambia el proveedor. El catálogo y el esquema de sesión 1.0.0 incorporan context_limit sin eliminar los códigos anteriores. La consola conserva la responsabilidad de explicar el contador y /salir. El intento rechazado se guarda completo y queda fuera del siguiente contexto válido, igual que otros errores.

Se añadieron 17 pruebas unitarias y una integración, y se actualizó la expectativa existente del payload del adaptador. La suite final terminó con **577 passed in 26.48s**, 551 unitarias y 26 integraciones, sin fallos ni llamadas reales durante pytest. La integración cubre respuesta → rechazo → repregunta → guardado/carga, con el primer par y el sistema conservados.

La comprobación real con Ollama 0.34.2 y gemma4:e4b obtuvo una respuesta sobre el aporte a Inventario Aula, rechazó una entrada sintética extensa y respondió Inventario Aula al preguntar por el proyecto inicial. Hubo tres llamadas con 2, 4 y 4 mensajes; todas enviaron truncate y shift false, num_ctx 8192 y máximo de salida 512. El sistema conservó su hash. Las respuestas completas tardaron 40,80 y 5,25 s; el intento rechazado no tiene respuesta o tokens inventados. La aplicación guardó session-5705ca05-8c5c-4251-9c34-d9883224391a.json con estados completed/error/completed y código context_limit. La lectura coincidió exactamente con la instantánea del controlador; cierre user_exit y fuente intacta.

Evidencia adicional: context-guard-9283a64ac59d4d41bad389f904d650a4.json. Todos los archivos de sesión anteriores y los cuatro originales del escenario conservaron sus bytes. Instrucciones 1.0.11, referencia 2026-10-20, máximo 20, dependencias y selección normal de proveedor/modelo se mantienen. La API externa permaneció desactivada. Esta protección solicita rechazo al servidor y se verificó para la combinación indicada; no predice tokens futuros ni implementa resumen. Se espera la comprobación del usuario antes de la siguiente unidad de reducción controlada.

### 31 de octubre de 2026: confirmación del rechazo y resumen extractivo (7.4c)

El usuario confirmó **577 passed in 28.46s** y la sesión f7be73ff-ab02-42d4-8f63-17d78db4aeb0: pregunta sobre proyecto académico, rechazo de entrada sintética extensa y repregunta correcta por Inventario Aula. Hubo tres intentos, dos respuestas completas, una incidencia y perfil intacto. La lectura mostró completed/error/completed y context_limit. Las respuestas tardaron 64,76 y 3,47 s. Se validó el archivo local y se guardó confirmación estructurada en context-guard-user-confirmation-1d88e6bfc79c41609280cc0042c7c521.json.

Se continuó con un componente verificable, aún separado de la entrevista activa: harness/history_summary.py y scripts/preview_summary.py. La fuente es una sesión validada con integridad unchanged. Conserva configuración e identidad, hashes del perfil/instrucciones y del historial aceptado, preguntas antiguas completas y los últimos pares completos. Envía al selector solo preguntas antiguas y fragmentos numerados, no el perfil, los fallos o los turnos recientes. La salida admite solo índices; Python copia las citas y valida su procedencia reconstruyendo toda la propuesta. No se escriben archivos desde la vista previa ni se cambia el controlador.

Se consultó la investigación primaria de Maynez et al., ACL 2020, sobre contenido no fiel en resumen abstractivo. La decisión de limitar el modelo a índices reduce la reescritura libre, pero no garantiza la ausencia de omisiones relevantes o que las respuestas históricas fueran verdaderas. La propuesta queda como not_reviewed y se mantiene la prioridad del perfil. No se interpreta la coincidencia de hashes como validación semántica.

Pasaron 48 casos nuevos iniciales. Tras añadir una comprobación de tipos mediante comparación canónica, la suite de 626 casos pasó en 50,41 s. La primera verificación real se detuvo porque el selector omitió el primer fragmento obligatorio en una fixture. Se capturó una repetición en summary-selector-preliminary-bebf1172639f49398fecefc0e529c018.json: devolvió [1,4] y [2], omitiendo también contexto de ausencia de clientes y de producción. La propuesta fue rechazada y no se aplicó a una entrevista.

Se reforzó la conservación en Python: primer y último fragmento, cifras, negaciones/límites definidos y palabras con mayúscula después de la primera como indicio de nombres. Los índices válidos elegidos por el modelo se unen a estas anclas; los índices inexistentes, repetidos o desordenados siguen siendo rechazados. La vista previa indica citas añadidas por protección. La respuesta preliminar se reprodujo bajo esta política y se verificó contra la fuente. Son reglas conservadoras, no un análisis completo de importancia semántica.

Los 55 casos nuevos finales pasaron en 6,04 s. Suite final **632 passed in 49.16s**, 602 unitarias y treinta integraciones: 51 casos unitarios y cuatro integraciones nuevos. Las pruebas simulan el proveedor; las verificaciones locales son externas a pytest. La nueva integración comprueba selección, anclas, ventana reciente, ausencia de llamada cuando no hay turnos antiguos, fallos e interrupción, sin modificar el archivo fuente.

La prueba real final usó gemma4:e4b y Ollama local, con API externa desactivada. En la sesión real del usuario mantuvo los dos fragmentos antiguos y la repregunta completa: 233 a 233 caracteres de fragmentos, cero omisiones, 6,37 s. En una fixture explícita de cuatro turnos con respuestas predefinidas y frases de relleno, seleccionó [1,2,4] por cada una de las dos respuestas antiguas: ocho fragmentos pasaron a seis, 354 a 240 caracteres, conservando proyectos, tecnologías, ausencia de clientes y límite de producción; dos turnos recientes completos. Tardó 11,50 s. Esa fixture no es una entrevista natural nueva ni se archivó como sesión de la aplicación. No se extrapola el ahorro de caracteres a tokens o entrevistas largas.

Evidencia final: extractive-summary-15bb185e26174f998e069279cc7c8713.json. Conservó los hashes de todos los archivos de sesiones y de perfil, puesto, configuración e instrucciones. Referencia 2026-10-20, instrucciones 1.0.11, máximo 20, dependencias y modelo predeterminado sin cambios. La integración en la entrevista activa, el presupuesto completo del resumen, los marcadores y la política de activación siguen pendientes. Se espera la comprobación del usuario de esta unidad antes de continuar.

### 31 de octubre de 2026: confirmación de citas y composición del contexto (7.4d)

El usuario confirmó **632 passed in 30.47s** y la vista previa de su sesión f7be73ff-ab02-42d4-8f63-17d78db4aeb0: pregunta antigua 1, dos citas exactas y pregunta reciente 3 completa. Hubo cero omisiones, 233 a 233 caracteres y procedencia verificada. Se contrastó con el archivo y se registró el resultado comunicado en extractive-summary-user-confirmation-052ae0d7f51c44a1a21a26697ab3d166.json, separado de la lectura local.

Se añadió harness/summary_context.py para componer los mensajes de una consulta de prueba. Revalida la propuesta y comprueba identificador/hash del candidato, configuración, referencia del puesto y hash de instrucciones con el escenario actual. El contexto autorizado procede de build_messages. Las preguntas antiguas mantienen su papel user y texto exacto; las citas conservan assistant, con marcas de extracto y omisiones visibles. Las respuestas sin omisión y los pares recientes mantienen sus textos completos. No se copian datos del entrevistador o selector al sistema como nuevas instrucciones.

Se comparan los bytes UTF-8 de las listas completas de mensajes antes de adaptar el modelo. Solo se usa la alternativa con extractos si hay omisiones y queda estrictamente menor después de incluir su guía y marcas. De lo contrario se conserva la completa. No se trata la medida de bytes como conteo de tokens ni garantía de capacidad; continúan los controles de rechazo del adaptador. scripts/probe_summary_context.py hace una consulta aislada sin reanudar o modificar la sesión archivada. El controlador de la consola principal todavía no se modifica.

Se añadieron 16 pruebas unitarias y seis integraciones. Los 22 casos nuevos pasaron en 2,97 s y la primera suite conjunta de 654 casos en 33,72 s. La primera verificación real consultó la sesión corta correctamente, pero al comparar una fixture el historial completo confundió primer proyecto mencionado con primero por fecha de inicio: respondió MesaFaro y pytest en vez de Inventario Aula y pytest. La verificación se detuvo antes de consultar la alternativa con extractos. La incidencia observada se conservó en summary-context-mention-incident-cb4c3ab00b03407597009c09e7a3e76d.json, con métricas desconocidas registradas como tales.

Se añadió una guía estática de referencias conversacionales a ambas alternativas del nuevo constructor: distingue primera mención/primera respuesta/última pregunta de inicio, término y coincidencia temporal. La guía de extractos se añade además solo a la alternativa reducida. No se cambió agent/agent.md, su versión o los archivos de sesión anteriores. La guía común también entra en la comparación de bytes. Los 22 casos volvieron a pasar en 3,19 s y la suite final terminó con **654 passed in 34.08s**, 618 unitarias y 36 integraciones, sin fallos ni llamadas reales en pytest.

La verificación real final con Ollama local y gemma4:e4b pasó todos los casos registrados. Sobre el archivo real, eligió full_history por no_omissions, con 27496 a 27496 bytes, y respondió Inventario Aula en 5,39 s. En una fixture explícita con respuestas, selección predefinida y frases de relleno, el historial completo y el reducido identificaron Inventario Aula como primer proyecto mencionado y pytest como herramienta de la última respuesta. Las entradas informadas fueron 6620 y 6364 tokens; tiempos 6,69 y 7,94 s. Los mensajes de esa fixture pasaron de 30167 a 28133 bytes: 2034 bytes menos. No se extrapola esa relación a otros textos ni se afirma mejora de latencia.

Una regresión adicional con extractos pidió cuál proyecto comenzó primero: respondió MesaFaro en abril de 2025, con 6360 tokens de entrada y 5,08 s. Las tres respuestas comparadas terminaron completas y conservaron los nombres esperados. La fixture no representa una entrevista natural nueva ni fue guardada como sesión de la aplicación. La comprobación no acredita consistencia universal.

Evidencia final: summary-context-b67d45e6960a4b9dbcb53f51df027355.json. Conserva salidas, respuestas, métricas, decisiones y hashes, sin copiar el perfil interno del sistema. Todos los archivos anteriores de sesiones y los cuatro originales del escenario permanecieron intactos. API externa desactivada, instrucciones 1.0.11, referencia 2026-10-20, máximo 20 y dependencias conservados. La distinción de referencias se verificó en este constructor aislado; el controlador principal todavía no la recibe. Quedan pendientes la activación en entrevistas y el presupuesto de contexto. Se espera la comprobación del usuario de esta unidad antes de continuar.

### 31 de octubre de 2026: confirmación de composición y resumen en el controlador (7.4e)

El usuario confirmó **654 passed in 35.88s**, contexto completo por no_omissions, 27496 a 27496 bytes y respuesta correcta sobre Inventario Aula en 33,44 s. La sesión y sus contadores se conservaron. Se contrastó la fuente local y se registró la confirmación estructurada en summary-context-user-confirmation-97b2934e7b5f431e8ed11e68f7b3aa8e.json.

Se incorporó la ruta de resumen al controlador con opción explícita --extractive-context. harness/live_context.py contiene LiveContextPolicy y validación de auditoría. Los valores locales normales son capacidad 8192, salida 512, margen 256 y umbral 7424; requiere tres pares completos y mantiene dos recientes. Se activa por entrada informada o un rechazo previo conocido, sin reenviar ese intento. Una vez iniciada mantiene la preparación posterior; cada selección se deriva de los originales, no de resúmenes anteriores. Los datos desconocidos no se convierten a cero ni se predice un tokenizado futuro.

El controlador controla el perfil alrededor del selector y registra la pregunta del candidato después de preparar el contexto. Una selección inválida, cortada o un fallo conocido permite un único envío con el historial completo; los selectores no consumen preguntas ni se incorporan como respuestas al historial. Interrupción o fallo de integridad antes del envío no inventan un intento. Se guardan incidencias separadas de preparación y del candidato, con descripciones seguras. Los tiempos de preparación y respuesta se mantienen separados.

SessionState conserva formato 1.0.0 sin la opción. Al habilitarla, fija política y usa 1.1.0 con context_events. El esquema y el lector aceptan ambos formatos; el antiguo rechaza los campos nuevos. La auditoría conserva número/fecha, pregunta prevista, candidate_sent, disparador, resultado de selección, índices, métricas disponibles, medidas, huellas e incidencias. Valida el prefijo original de cada evento, la secuencia y la coherencia aritmética. No guarda el perfil interno del sistema o texto libre de una selección inválida.

La compatibilidad previa terminó con **654 passed in 106.64s**. Los 35 casos nuevos iniciales pasaron en 14,24 s; se añadió después la prueba de tiempo inválido. Los 36 nuevos finales pasaron en **14,86 s**. Suite final **690 passed in 104.14s**, 650 unitarias y cuarenta integraciones, sin fallos ni solicitudes reales en pytest. Son 32 casos unitarios y cuatro integraciones nuevos, incluyendo fallos, interrupciones, integridad simultánea, contador máximo, lectura antigua y rechazo de auditoría manipulada. No se atribuye el cambio de duración de la suite a una causa sin medirla.

La prueba real ejecutó la consola con gemma4:e4b, opción activa y umbral de comprobación 1. Obtuvo cuatro respuestas completas: Inventario Aula, sus tecnologías, total de 21 meses y referencia correcta a la primera pregunta. Tiempos 117,53; 11,85; 13,28 y 4,98 s. Hubo una selección antes de la cuarta pregunta, cero incidencias y cero resúmenes usados porque la respuesta antigua era breve y no tenía omisiones. Se guardó session-a5ad4e7c-aeb1-4906-8f41-7d113be13001.json, versión 1.1.0, con cuatro eventos y cuatro intentos completos. La lectura coincidió con la instantánea del controlador y los hashes de mensajes se contrastaron con los enviados realmente a Ollama para Gemma 4.

Una fixture separada sembró tres respuestas y conteos de entrada predefinidos; el selector y la cuarta respuesta fueron llamadas reales a Ollama. Aplicó extractive_summary, ahorró 999 bytes de mensajes y mantuvo Inventario Aula y pytest. Se validó guardado/lectura en carpeta temporal. No es una entrevista natural nueva ni se comparan sus conteos simulados con tokens reales para afirmar ahorro. La fixture y sus etiquetas explícitas permanecen en la evidencia, separadas de la carpeta de entrevistas naturales.

Evidencia final: live-context-ea4988d6741a40f9be580eb8c7ba4fd2.json. Se conservaron todas las sesiones anteriores y los cuatro originales del escenario. Instrucciones 1.0.11, referencia 2026-10-20, máximo 20, modelo predeterminado y dependencias sin cambios; API externa desactivada. No se garantiza ajuste de veinte preguntas arbitrarias o ausencia de omisiones relevantes. La opción se mantiene explícita y se espera la comprobación del usuario antes de otra unidad.

### Confirmación del usuario de la 7.4e y cierre funcional de la Etapa 7

El usuario confirmó **690 passed in 38.14s** y una entrevista nueva con gemma4:e4b, --extractive-context y umbral de comprobación 1. La sesión f8d281c9-bca7-4bdd-9b52-d7f9788399e5 conservó Inventario Aula, sus tecnologías y el total de 21 meses. Cuatro respuestas completas, cero incidencias, una selección y cero resúmenes aplicados. Latencias comunicadas 67,15; 7,51; 7,37 y 3,45 s; preparación adicional de 4,58 s. La referencia de la última respuesta fue correcta, con una imprecisión de redacción («mi primera pregunta» por «mi primera respuesta») que se conserva para revisión posterior sin declararla contradicción fáctica.

El usuario guardó y leyó formato 1.1.0 con cuatro intentos y cuatro eventos: not_requested/not_requested/not_requested/completed. La lectura local validó el archivo, estado closed, cierre user_exit, source_integrity unchanged y preparación final full_history/no_omissions. Medidas finales 27951 a 27951 bytes, sin ahorro forzado. El tiempo registrado fue 4,5848713999730535 s. Se comprobó que candidato e instrucciones coinciden con sus hashes actuales y se registraron las cuatro huellas del escenario. No se modificó la sesión fuente.

Confirmación estructurada: live-context-user-confirmation-209e77b7567a4699827786bb493d3e7c.json. Se redactó docs/contexto-y-sesiones.md#cierre-etapa-7 para distinguir capacidades implementadas, pruebas simuladas, consultas reales y límites pendientes de validación. El uso normal conserva el umbral 7424; el valor 1 solo pertenecía a la comprobación forzada. No se modificó código, dependencias, modelos, proveedor o archivos de datos en este cierre y no se repitieron pruebas ya confirmadas para un cambio documental.

Se cierra funcionalmente la Etapa 7 en ese alcance. No se afirma consistencia universal, validación natural exhaustiva de veinte turnos, irrelevancia de toda omisión o latencia garantizada. Las Etapas 8 y 9 continúan pendientes. Respetando la instrucción de no avanzar automáticamente entre etapas, se dejó propuesta la primera unidad de cuatro casos de referencia para revisión humana y se espera indicación del usuario antes de implementarla. Clasificación, puntuaciones y retroalimentación educativa permanecen fuera de esta fase.

### 31 de octubre de 2026: autorización de la Etapa 8 y referencias de consistencia (8.1)

El usuario indicó: «Pasemos a la etapa 8 también muéstrame que etapas completamos y cuantas faltan». Se inició la Etapa 8 y se añadió docs/estado-del-proyecto.md#estado-etapas con las nueve del plan original: siete completadas, 8 en curso y 9 pendiente. Quedan dos por terminar, incluida la actual. La autorización no cierra automáticamente esta etapa ni inicia la siguiente.

Se preparó data/reference_questions/consistencia_basica.json, versión 1.0.0: cuatro casos y cinco preguntas sobre formación, duración laboral, referencia a una respuesta anterior y ausencia de experiencia práctica con Kubernetes. Los valores se resuelven desde el perfil aprobado y build_temporal_facts mediante referencias explícitas. El conjunto fija la huella del perfil revisado y es de desarrollo, con preguntas conocidas; no se presenta como prueba independiente. Se declara una sesión nueva por caso y dos pasos compartidos para continuidad; todavía no se implementa el ejecutor de esas sesiones.

schemas/reference_suite.schema.json establece estructura y tipos; harness/reference_cases.py verifica vínculos, huellas, identificadores, numeración, hechos utilizados, límites y referencias. Conserva copias independientes y detecta cambios en la fuente del candidato. scripts/show_reference_cases.py muestra las preguntas y criterios humanos sin red, escritura de sesiones, respuesta generada, comparación automática de texto o puntuación educativa. El null de equivalencia laboral conserva la ausencia de datos suficientes; el total de 21 meses no se convierte en jornada completa. Las omisiones de detalle se distinguen de contradicciones.

Se añadieron 37 pruebas unitarias y tres integraciones: **40 passed in 3.69s**. La suite conjunta terminó con **730 passed in 45.44s**, 687 unitarias y 43 integraciones, sin llamadas reales a proveedores. La comprobación offline mostró cuatro casos, cinco preguntas, institución y título exactos, 21/3/18 meses, Inventario Aula y el límite de Kubernetes. Son verificaciones técnicas de las referencias, no resultados semánticos de respuestas del candidato.

Evidencia: reference-suite-da11e781799f4ef6ba7331f1964e0e39.json. Registra salida, referencias resueltas y hashes antes/después de candidato, puesto, configuración, instrucciones y siete archivos de sesiones existentes. Todos permanecieron intactos. No se cambió el escenario 2026-10-20, máximo 20, instrucciones 1.0.11, dependencias o selección de proveedor/modelo. La API externa no se utilizó.

Se actualizaron documentación de arquitectura, catálogo, protocolo de revisión, planificación y README. La unidad queda implementada y verificada localmente, pendiente de comprobación del usuario. Las llamadas controladas y revisión humana de los casos vendrán en la siguiente unidad, después de esa confirmación. La Etapa 8 permanece en curso; la 9 sigue pendiente. Clasificación, rúbrica, puntuaciones y retroalimentación educativa permanecen fuera de esta fase.

### 31 de octubre de 2026: confirmación 8.1 y ejecución agrupada de referencias (8.2)

El usuario confirmó 730 passed in 150.75s (0:02:30), cuatro casos y cinco entradas de pregunta con los hechos correctos. Solicitó que las dos etapas restantes avanzaran más rápido y consumieran menos tokens de ChatGPT. Se adopta agrupación de comprobaciones, respuestas breves y ausencia de repeticiones innecesarias de pruebas. La regla de transición explícita entre etapas sigue vigente.

Se añadió scripts/run_reference_cases.py, reutilizando escenario, referencias, fábrica, controlador y persistencia. Ejecuta exclusivamente Ollama, aun con API seleccionada en el entorno, sin descargar modelos. Cada caso tiene una sesión independiente; sus pasos comparten historial. Detiene el lote ante el primer fallo, salida cortada, interrupción, integridad fallida o problema de guardado. El informe conserva instantáneas, archivos, huellas, parámetros y casos no ejecutados; technical_status no se convierte en aprobación semántica. No se modificaron módulos de producción anteriores ni datos del escenario.

Las seis integraciones nuevas pasaron en 2,95 s. Suite completa: 736 passed in 123.96s (0:02:03), 687 unitarias y 49 integraciones. HTTP está simulado y los archivos de pytest se aíslan en temporales. No se atribuye el tiempo de ejecución a una causa sin medirla ni se pide repetir toda la suite para cada lote manual.

El lote real reference-run-fd00eb31-7961-4390-9807-c78695f3a247.json usó gemma4:e4b, obtuvo cinco respuestas completas en cuatro sesiones y terminó con código 0. Tiempos: 89,73; 11,07; 14,71; 11,47 y 13,01 s. La inspección del asistente encontró institución/título, total 21 con desglose 3/18, continuidad de Inventario Aula y ausencia de experiencia práctica con Kubernetes compatibles con el perfil. No es revisión humana, y semantic_review permanece pending_human_review. No se declara consistencia universal.

reference-execution-verification-fd00eb31-7961-4390-9807-c78695f3a247.json separa la confirmación del usuario, resultados técnicos, inspección del asistente y comprobación de integridad. Las cuatro sesiones nuevas se leyeron y compararon con sus instantáneas y huellas. Los cuatro originales y siete sesiones anteriores conservaron sus bytes. API externa no utilizada; referencia 2026-10-20, instrucciones 1.0.11, máximo 20 y dependencias conservados.

La guía docs/validacion-del-candidato.md#ejecucion-referencias reúne comando, errores, evidencia y observaciones. La Etapa 8 permanece en curso: revisión humana y ampliación de casos pendientes. La siguiente unidad agrupará los casos restantes; la Etapa 9 no se inicia automáticamente.

### 31 de octubre de 2026: confirmación 8.2 y bloque ampliado 8.3

El usuario ejecutó el lote 9990715a-bb6d-4a7d-bbd6-3753f753c503 con gemma4:e4b: cuatro casos y cinco respuestas completas, con institución/título, 21 meses desglosados 3/18, Inventario Aula y ausencia de experiencia práctica con Kubernetes. Tiempos comunicados 73,63; 8,91; 10,55; 3,68 y 4,52 s. Se leyeron las cuatro sesiones y se compararon con sus instantáneas y huellas. reference-user-confirmation-9990715a-bb6d-4a7d-bbd6-3753f753c503.json separa su ejecución, lectura local y observación del asistente; no inventa una aprobación semántica humana explícita.

Se agrupó el resto de la Etapa 8 en data/reference_questions/consistencia_ampliada.json: seis casos y diez preguntas de cronología, tecnologías/aportes, ambigüedad, premisa contradictoria, repetición y protección de instrucciones. Reutiliza contrato, cargador y ejecutor existentes; no se modificó código de producción, perfil, configuración, instrucciones o dependencias. Dos comprobaciones nuevas pasaron con 2 passed in 1.88s. Hay 738 pruebas disponibles (687 unitarias y 51 integraciones); la última suite completa es la anterior de 736 en 123,96 s, sin atribuirle resultados de una ejecución de 738 que no se hizo. La repetición completa se reserva a la validación final.

El lote real reference-run-5e7c73f0-1e3a-4054-8ad8-1501ab6eed3d.json obtuvo diez respuestas completas y seis sesiones con gemma4:e4b. Orden de proyectos y términos correctos, cinco tecnologías, aportes y límites compatibles, solicitud de aclaración del periodo, corrección de la premisa comercial, institución/título conservados al repetir la pregunta y rechazo a revelar contexto o cambiar de rol. Tiempos 65,47; 10,52; 4,41; 13,10; 4,62; 5,15; 6,52; 5,67; 3,92 y 4,45 s.

La inspección del asistente no observó contradicciones factuales. Se registró literalmente la imprecisión de redacción mi titulación e Ingeniería en Informática, sin cambio de fecha o título. El primer turno no explicitó fechas de inicio individuales (no solicitadas expresamente) y la corrección de la premisa no reiteró por separado la ausencia de producción. Son matices/omisiones, no afirmaciones incompatibles ni motivos para cambiar el perfil. Las respuestas originales se conservan y la revisión humana permanece pendiente.

reference-extended-verification-5e7c73f0-1e3a-4054-8ad8-1501ab6eed3d.json guarda inspección, resultados técnicos y comprobación de integridad: cuatro originales y quince sesiones anteriores intactos, seis nuevas leídas y comparadas. Perfil con referencia 2026-10-20, máximo 20, instrucciones 1.0.11, proveedor local y dependencias conservados; no se utilizó API externa. Los dos conjuntos suman diez casos y quince preguntas de desarrollo, sin carácter de conjunto independiente ni garantía universal.

Se documentó el bloque en docs/validacion-del-candidato.md#consistencia-ampliada y se actualizaron catálogo y estado. La Etapa 8 está implementada y ejecutada en este alcance, pendiente de la comprobación final del usuario. La Etapa 9 requiere transición explícita; no se inicia automáticamente. Se mantiene la preferencia de agrupar tareas y responder brevemente.

### 31 de octubre de 2026: confirmación final y cierre técnico de la Etapa 8

El usuario compartió el lote 96b33ded-c47b-4303-a812-6cd88503d860 con gemma4:e4b: seis casos, diez respuestas completas y cero incidencias. Se validaron las seis sesiones contra sus instantáneas y huellas y se verificaron los cuatro originales y veintiuna sesiones anteriores intactos. Confirmación: reference-user-confirmation-96b33ded-c47b-4303-a812-6cd88503d860.json. La inspección del asistente encontró hechos compatibles; la redacción de titulación fue clara en esta repetición, sin modificación de reglas. La ausencia de producción no fue explicitada separadamente al corregir la premisa comercial y sigue registrada como omisión, no contradicción.

Se añadió docs/validacion-del-candidato.md#cierre-etapa-8 y se actualizaron estado, planificación y README: ocho etapas completadas en su alcance técnico; solo la 9 pendiente. El cierre conserva límites del conjunto de desarrollo y distingue la inspección del asistente de una aprobación humana no expresada. No se alteran semantic_review, datos, instrucciones, parámetros o dependencias. No se repiten pruebas ni llamadas a modelos para un cierre documental. La última suite completa sigue siendo 736 pruebas aprobadas, más dos nuevas aprobadas por separado; hay 738 disponibles para la validación final. Se espera la indicación de transición a la Etapa 9 según la pauta original de no avanzar automáticamente entre etapas.

### 31 de octubre de 2026: integración y validación final de la Etapa 9

El usuario autorizó «Pasemos a la Etapa 9». Se ejecutó un bloque reproducible de verificación, sin cambiar producción ni instalar dependencias. Artefacto: outputs/results/validate-stage9.py. Dependencias sin incompatibilidades; Python 3.14.3, jsonschema 4.26.0, pytest 9.2.0 y httpx 0.28.1. Suite completa: 738 passed in 45.54s, 687 unitarias y 51 integraciones, sin solicitudes reales de modelos en pytest.

Se abrió la consola real en un proceso independiente con Ollama local, gemma4:e4b, API externa desactivada y --extractive-context con umbral normal. Se consultaron ayuda, CV, puesto con sus seis competencias y sesión. Tras dos preguntas, /sesion mostró 2/20 y repetir /iniciar mantuvo el contador. El guion preparado realizó veinte preguntas con veinte respuestas completas y cero incidencias. La entrada 21 identificada no se consumió ni se guardó como intento; cierre question_limit. En la respuesta 20 el candidato recordó la primera pregunta de formación y el proyecto académico Inventario Aula.

Se guardó y leyó session-191fc87c-311f-4cc5-b29c-648589f52ead.json, versión 1.1.0, con veinte eventos. Mayor entrada informada 7106 tokens, sin alcanzar el umbral 7424: cero selecciones y cero resúmenes aplicados. No se afirma uso de extractos en esta entrevista; esas pruebas conservan su evidencia previa separada. La inspección del asistente encontró hechos compatibles en formación, proyectos, aportes, cronología, total 21 meses con desglose 3/18 y jornadas 9/9. El candidato reconoció límites, aclaró el periodo ambiguo y mantuvo su rol. Se conserva una imprecisión gramatical en estudios e titulación sin cambio factual.

Una segunda ejecución consultó CV/puesto, inició y salió sin preguntas, sin nuevas generaciones. Guardó session-2794e104-65bb-4f07-a87e-517a612278c7.json, formato 1.0.0, UUID independiente y cierre user_exit. Se validaron ambos archivos contra instantáneas y huellas. Los cuatro originales y veintisiete sesiones anteriores permanecieron intactos, con las huellas aprobadas de la Etapa 8.

Evidencia: final-validation-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b.json, salidas completas de ambas consolas y final-delivery-verification-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b.json. La segunda conserva manifiesto de implementación e inspección del asistente, sin atribuir aprobación humana no expresada. Se documentaron resultados, límites y uso en docs/validacion-del-candidato.md#validacion-final y se actualizaron README, estado y planificación: nueve de nueve etapas completadas técnicamente, ninguna pendiente del agente en este alcance. La consistencia universal, un piloto libre y modelos externos reales no se declaran validados. Clasificador, rúbrica, puntuaciones, retroalimentación educativa y Godot siguen fuera de esta entrega.

### 1 de noviembre de 2026: selector local/API y adaptador UNAB IA

El usuario solicitó guardar una clave localmente y elegir proveedor al iniciar. Se añadió scripts.start_interview con opciones 1 Ollama y 2 UNAB IA, sin cambiar permanentemente variables de PowerShell ni activar API al elegir local. config/llm.local.json se creó desde una plantilla sin sobrescribir archivos existentes; está excluido de Git. No se leyó ni publicó una clave real. La selección externa envía las credenciales solo en el entorno del proceso hijo y en la cabecera Bearer del cliente; no en argumentos o sesiones.

harness/llm/unab_client.py implementa Chat Completions en https://quotas.devhub.cl/api/v1/chat/completions con gemma4:26b, manteniendo el adaptador Responses existente. Se fijó el destino, sin redirecciones ni proxies del entorno. Se validan respuestas, estados, límites y errores sin copiar cuerpos del servidor; las generaciones no se repiten tras timeout. Se actualizó el nombre visible del proveedor en consola y smoke test.

Las 21 pruebas nuevas pasaron en 1,42 s; suite completa 759 passed in 59.65s, 687 unitarias y 72 integraciones. Son llamadas HTTP simuladas; la compatibilidad real del servicio desplegado queda pendiente de clave y ejecución del usuario. Perfil, puesto, configuración e instrucciones mantienen sus huellas aprobadas. La documentación de uso está en docs/operacion.md#selector-proveedor. La validación final previa de veinte turnos corresponde a la versión anterior y conserva su evidencia histórica; no se afirma validación real de UNAB.

### 1 de noviembre de 2026: investigación de consumo UNAB y texto final inválido

El usuario informó tres respuestas rechazadas y una completa en session-cd0fa34f-b9a1-491f-9f9a-fa7c83ff6ecc.json, con una captura de 25 963 créditos consumidos hoy sobre 50 000. Se validó el registro: la llamada válida informó 6045 tokens de entrada y 233 de salida; las fallidas carecen de métricas y finish_reason. El sistema actual ocupa 24 822 caracteres. El reenvío del contexto completo explica un orden de magnitud de 24 000 tokens de entrada para cuatro preguntas; no se conoce la fórmula de créditos del servicio ni otras actividades de la cuenta, y no se igualan créditos a tokens como hecho confirmado.

El adaptador anterior empleaba max_tokens 512 y perdía métricas al rechazar el contenido con un error genérico. La combinación de preguntas complejas fallidas y una breve exitosa es compatible con agotar salida en razonamiento, pero no prueba esa causa. Se consultaron fuentes primarias de Ollama sobre Gemma y reasoning_effort; no se certifica la aplicación de ese parámetro por la pasarela UNAB.

Se solicita reasoning_effort none manteniendo 512 tokens. El cliente conserva una copia independiente de metadatos permitidos, incluso en rechazos: estado HTTP, motivo conocido, tokens informados, indicadores de razonamiento, caracteres y configuración solicitada. No conserva clave, cabeceras, preguntas, perfil, cuerpo bruto ni contenido de razonamiento. La consola guarda unab-usage-<UUID>.json junto a resultados al cerrar, sin alterar el esquema de sesiones; muestra tokens en respuestas completas. Se distingue falta de texto final al límite, se rechazan marcas de pensamiento y no se repite generación automáticamente.

Se añadieron seis regresiones a las veintiuna del adaptador: razonamiento sin texto final, datos de uso conservados, copias independientes, marcas mixtas no expuestas y diagnóstico de errores guardado con métricas desconocidas nulas. Conjunto dirigido 27 passed in 3.97s; suite completa 765 passed in 254.13s (0:04:14), 687 unitarias y 78 integraciones. El tiempo no se atribuye a una causa sin medirla. Ninguna prueba usó la API real ni la clave privada. La sesión original y cuatro fuentes canónicas mantienen sus huellas.

Evidencia: unab-response-investigation-737c141f23f7423ba79fa9b0d23ade18.json y docs/operacion.md#unab-consumo-y-salidas-vacias. La corrección está probada con HTTP simulado; se propone al usuario repetir una sola pregunta compleja y cerrar, para confirmar el efecto real con poco consumo. Si persiste, se revisará el diagnóstico antes de repetir otras preguntas. No se afirma que las tres causas históricas estén confirmadas ni que el despliegue ya esté corregido.

### 1 de noviembre de 2026: salida vacía al límite confirmada y presupuesto explícito UNAB

La sesión b84552c0-bccb-48e3-8498-bbeae51ed951 y su diagnóstico muestran una llamada HTTP 200: 6058 tokens de entrada, 512 de salida, 6570 totales, finish_reason length y cero caracteres finales. Se solicitó reasoning_effort none; reasoning_present false y reasoning_tokens null no permiten concluir si el backend hizo razonamiento oculto o cómo aplicó el parámetro. El agotamiento de la salida está confirmado; su causa interna no.

Se cambia exclusivamente el presupuesto predeterminado de UNAB a 2048. El selector admite api_max_output_tokens opcional (16–4096), muestra el valor al elegir API y propaga UNAB_MAX_OUTPUT_TOKENS al proceso. Los archivos privados anteriores de tres campos funcionan sin reescribirlos ni leer/cambiar la clave durante este trabajo. Los presupuestos locales y Responses continúan en 512. El error incluye el presupuesto solicitado. No hay aumentos o reenvíos automáticos.

Se añadieron 17 regresiones; 109 pruebas dirigidas de UNAB/selector, fábrica y Responses pasaron en 1,44 s. No se repitió la suite entera de 765 previa; hay 782 disponibles sin afirmar una ejecución completa nueva. No se hicieron llamadas reales ni se gastó cuota UNAB. Se conservó el diagnóstico y sesión originales, con huellas en la nueva evidencia de confirmación. La verificación real de 2048 queda pendiente de una única pregunta del usuario; si sigue vacía se revisará la pasarela antes de seguir escalando presupuestos.

### 1 de noviembre de 2026: confirmación del usuario con presupuesto UNAB 2048

El usuario repitió la misma pregunta sobre un endpoint Flask/PostgreSQL en la sesión 162df680-88d6-40ca-9e8f-d095fae07025. Una respuesta completa, cero incidencias, perfil intacto y 12,82 s comunicados. Se validaron sesión y diagnóstico sin cambios: HTTP 200, presupuesto 2048, finish_reason stop, entrada 6058, salida 1255, total 7313 y 684 caracteres de texto final. La igualdad de la pregunta con el intento previo de 512 se comprobó directamente.

Se guardó unab-success-confirmation-162df680-88d6-40ca-9e8f-d095fae07025.json con huellas, métricas, alcance y observación del asistente. Funcionamiento confirmado para esta pregunta, sin inferir tokens internos de razonamiento, fórmula de créditos o éxito universal. Se mantienen 2048 y la configuración vigente. No hubo cambios de código, nuevas llamadas API, acceso a la clave ni repetición de pruebas para la confirmación documental.
