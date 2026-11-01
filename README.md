# Simulador de entrevistas con candidato virtual

Para elegir **modelo local o API UNAB IA** al iniciar, ejecutar `python -m scripts.start_interview` usando el Python de `.venv`. Colocar la clave únicamente en `config/llm.local.json`, excluido de Git. Véase la [configuración y uso del selector](docs/selector-proveedor.md).

Proyecto universitario en desarrollo incremental para construir un candidato virtual de entrevistas. Incluye el perfil ficticio aprobado, puesto, esquemas y validaciones. Ya permite abrir una consola, consultar el CV público y el puesto, iniciar la entrevista y enviar hasta 20 preguntas desde el escenario protegido. Conserva en memoria las preguntas y respuestas completas para entender repreguntas. Cada ejecución tiene una sesión identificada y registra todos los intentos, incluidos los fallidos. Al cerrar guarda el registro completo en un JSON local y permite leerlo para revisión.

**Agente candidato completado en su alcance técnico: 9 de 9 etapas.** La validación final aprobó las 738 pruebas y una consola real de veinte preguntas/respuestas con cierre al límite, guardado/lectura e integridad. La revisión de contenido permanece diferenciada del éxito técnico. Véanse la [validación final y guía de uso](docs/validacion-final.md) y el [estado de las nueve etapas](docs/estado-etapas.md).

Ollama es el proveedor principal. El modelo predeterminado sigue siendo `gemma3n:e2b`; `OLLAMA_MODEL` permite elegir explícitamente otro modelo local instalado. La prueba ampliada de consola detectó fallos de rol y antecedentes: véase el [registro de incidencias y repetición](docs/pruebas/correccion-conducta.md). Las instrucciones de `agent/agent.md`, versión 1.0.11, se combinan con el escenario validado. Se puede comprobar una pregunta mediante `scripts/smoke_test.py`. La alternativa OpenAI Responses está implementada, con activación explícita y desactivada por defecto; se verificó con respuestas simuladas, sin llamadas reales a la API externa.

## Mapa del proyecto

| Ruta | Propósito |
| --- | --- |
| `agent/` | Instrucciones 1.0.11 incorporadas al contexto del modelo. |
| `harness/` | Datos protegidos, contexto, adaptadores, controlador de preguntas y consola. |
| `schemas/` | Contratos de candidato, puesto, configuración, sesión y referencias de consistencia. |
| `config/` | Configuración de entrevista; evaluación reservada para otra etapa. |
| `data/` | Perfil de Nicolás Vera Soto, puesto y diez casos de referencia para revisión humana. |
| `tests/` | 687 pruebas unitarias y 95 de integración disponibles; las solicitudes HTTP son simuladas o se bloquean. |
| `outputs/` | Evidencias técnicas y archivos JSON locales de sesiones cerradas. |
| `scripts/` | Consola, prueba de una pregunta y diagnóstico de archivos de sesión; Ollama por defecto. |
| `docs/` | Informe, metodología, planificación y evidencias académicas. |

## Documentos de entrada

- [Instrucciones del candidato](agent/agent.md).
- [Estado de las nueve etapas](docs/estado-etapas.md).
- [Etapa 9: entrega, validación final y uso del agente](docs/validacion-final.md).
- [Etapa 8.1: casos de referencia y fuentes esperadas](docs/pruebas/referencias-consistencia.md).
- [Etapa 8.2: ejecución local de los casos por lotes](docs/pruebas/ejecucion-referencias.md).
- [Etapa 8.3: bloque ampliado y resultados reales](docs/pruebas/consistencia-ampliada.md).
- [Configuración básica y alcance de su validación](config/interviews/README.md).
- [Entorno de Python y comprobaciones reales](docs/entorno-python.md).
- [Arquitectura y componentes implementados](docs/arquitectura/README.md).
- [Conexión local y prueba con Ollama](docs/conexion-ollama.md).
- [API externa opcional, selección y comprobaciones](docs/conexion-api-opcional.md).
- [Tiempos de Ollama y preparación para la demostración](docs/rendimiento-local.md).
- [Uso de la consola y límites de esta versión](docs/consola.md).
- [Etapa 7.1: historial en memoria y repreguntas](docs/historial-en-memoria.md).
- [Etapa 7.2: sesiones y registro de intentos](docs/sesiones-en-memoria.md).
- [Etapa 7.3: guardado y lectura de sesiones JSON](docs/persistencia-sesiones.md).
- [Etapa 7.4a: diagnóstico del contexto registrado](docs/diagnostico-contexto.md).
- [Etapa 7.4b: rechazo explícito de contexto excesivo](docs/proteccion-contexto.md).
- [Etapa 7.4c: propuesta de resumen extractivo verificable](docs/resumen-extractivo.md).
- [Etapa 7.4d: composición de contexto y consulta aislada](docs/contexto-con-resumen.md).
- [Etapa 7.4e: resumen activable y auditoría del controlador](docs/resumen-en-entrevista.md).
- [Cierre funcional de la Etapa 7 y siguiente paso propuesto](docs/cierre-etapa-7.md).
- [Corrección del orden cronológico de proyectos](docs/pruebas/correccion-cronologia.md).
- [Duración laboral y términos de estudios/proyectos](docs/pruebas/correccion-duracion-y-estudios.md).
- [Incidencias del candidato y repetición controlada](docs/pruebas/correccion-conducta.md).
- [Pruebas del módulo de validación](tests/unit/README.md).
- [Pruebas de integración de lectura y validación](tests/integration/README.md).
- [Perfil aprobado y evidencia de comprobación](data/candidates/README.md).
- [Puesto aprobado y evidencia de comprobación](data/jobs/README.md).
- [Guía de cada carpeta y archivo](docs/guia-estructura.md).
- [Esqueleto del informe](docs/informe.md).
- [Planificación del semestre y continuidad](docs/planificacion.md).
- [Protocolo de pruebas](docs/pruebas/protocolo.md).
- [Registro de cambios de estructura](CHANGELOG.md).

`harness/json_loader.py` lee los archivos y `harness/schema_validator.py` aplica sus esquemas. `harness/profile.py` valida y protege al candidato y deriva su CV. `harness/interview_config.py` valida el escenario. `harness/prompt_builder.py` reúne reglas, datos e índices derivados de nombres, proyectos, cronología y duración laboral, con la pregunta en otro mensaje. El adaptador reúne el par inicial solo para el formato de Gemma 3n. La fábrica selecciona proveedor y modelo local explícitos. `harness/session_state.py` conserva identidad, configuración e intentos; `harness/runtime.py` coordina el límite y la integridad; `harness/application/cli.py` presenta la consola. `harness/session_log.py` valida, guarda y lee los registros cerrados. La última suite completa aprobó 765 pruebas en 254,13 s; después se verificaron 109 pruebas relevantes para el presupuesto configurable de UNAB, incluidas 17 nuevas; los turnos completos se conservan en memoria durante la entrevista y se archivan al cerrar. `harness/context_budget.py` y `scripts/inspect_context.py` permiten comparar las métricas guardadas con reservas explícitas, sin consultar al modelo. El cliente local solicita rechazar el exceso de contexto sin recortes automáticos y registra `context_limit`; se verificó con Ollama 0.34.2 y gemma4:e4b. `harness/history_summary.py` prepara propuestas extractivas con citas verificables y turnos recientes completos; `scripts/preview_summary.py` permite revisarlas sin modificar una entrevista. `harness/summary_context.py` construye mensajes con extractos y turnos recientes cuando el JSON completo disminuye; `scripts/probe_summary_context.py` permite una consulta aislada sin modificar la sesión fuente. `--extractive-context` activa la política de `harness/live_context.py` en la consola: conserva los pares recientes y registra las preparaciones en sesiones 1.1.0. Sin esa opción se mantiene el comportamiento y formato anteriores. El umbral usa métricas pasadas; no garantiza que cualquier pregunta nueva quepa.

Para abrir la consola desde PowerShell, en la raíz del proyecto:

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

Dentro del programa, usar `/cv`, `/puesto`, `/sesion` y `/iniciar`; después escribir una pregunta de una línea. `/salir` termina la ejecución. Esta versión recibe el perfil y los turnos completos anteriores. Cada entrevista empieza con memoria independiente. Al cerrar se guarda `outputs/sessions/session-<UUID>.json`; la lectura del archivo valida datos y no reanuda la conversación.

Para mostrar el currículum desde PowerShell, en la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from harness.profile import load_profile; from harness.application.cli import format_resume; perfil = load_profile('data/candidates/candidato_junior.json'); print(format_resume(perfil)); perfil.assert_source_unchanged()"
```

El entorno `.venv` contiene Python 3.14.3, `jsonschema` 4.26.0, `httpx` 0.28.1 y `pytest` 9.2.0, con sus dependencias. La clasificación, puntuación y retroalimentación educativa quedan para una fase posterior; los archivos reservados de la plantilla no representan funcionalidades implementadas.

El usuario confirmó el currículum, las 136 pruebas y la lectura de las instrucciones. Se creó `config/interviews/basica.json`: modalidad general, enfoque mixto, tres estilos preferidos y máximo de 20 preguntas. El contrato admite límites de 1 a 20 y el controlador ya aplica el contador. La consistencia completa de las respuestas del LLM todavía no está evaluada.

El usuario confirmó después las 176 pruebas y la configuración. `load_interview_setup()` ya prepara los tres documentos iniciales sin iniciar una sesión ni consultar un modelo. Devuelve instantáneas de preferencias y puesto con copias de acceso, junto con el candidato protegido.

El usuario confirmó las 198 pruebas y la carga integrada. `load_instructions()` lee el texto confiable para conservarlo en memoria; `build_messages(setup, question, instructions=...)` construye mensajes nuevos sin acceder a archivos ni al entorno. El contrato `ChatMessage` de `harness/llm/messages.py` usa diccionarios serializables, independientes del proveedor. El contexto completo incluye datos internos del candidato y no se debe presentar como CV al entrevistador. Historial y resúmenes se incorporaron después en la Etapa 7.

El 31 de octubre, tras confirmar el usuario las 286 pruebas y la discrepancia de la institución, se añadió un índice de nombres exactos derivado del perfil y del puesto. La suite terminó con 288 pruebas aprobadas. En tres consultas reales de la misma pregunta, Gemma conservó «Instituto Profesional Horizonte Digital» e «Ingeniería en Informática», sin modificar la salida ni los datos de origen. Es una verificación de ese caso, pendiente de repetición por el usuario, no una garantía de consistencia global. El registro de prueba incluye ahora huellas del texto de instrucciones y del mensaje de sistema para distinguir los contextos utilizados.

Tras confirmar el usuario las 352 pruebas y una consulta de 275,82 s, se añadieron métricas por fase y tokens reutilizados al resultado de Ollama. El cliente solicita conservar el modelo en memoria durante 15 minutos. Dos llamadas medidas tardaron 55,54 y 2,18 s; la repetición reutilizó 5072 tokens. La preparación inicial sigue siendo variable y estos valores no garantizan la latencia de una entrevista. Véase la guía de rendimiento antes de la demostración.
