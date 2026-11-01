# Guía de estructura y llenado

## Alcance de esta reorganización

Esta guía explica qué deberá contener cada parte cuando comience el desarrollo. El informe, la metodología y los módulos permanecen pendientes. Los comentarios `Por completar` y las descripciones de responsabilidad son instrucciones de plantilla, no resultados del proyecto.

La referencia es la [conversación compartida](https://chatgpt.com/share/6ae1709b-e834-83e9-9881-38ac93c893b2), especialmente la síntesis del informe actualizado y la propuesta de adaptar CINF110 al proyecto CINF200. Se pudo leer el texto de esa conversación; no se inspeccionaron directamente el Word consolidado ni las plantillas y PDF adjuntos originales. La correspondencia con la pauta oficial deberá revisarse al disponer de esos documentos. La numeración del informe es una organización de trabajo, ajustable a esa plantilla.

La organización contempla las decisiones expresadas allí: candidato configurable, separación entre tipo y calidad de pregunta, evaluación provisional con puntuación interna y cuatro niveles visibles, y retroalimentación después de cada respuesta, antes de continuar. Godot queda para continuidad; las mentiras y omisiones intencionales no forman parte del MVP. Las modalidades previstas son laboral general, técnica y por competencias; los enfoques son conductual, situacional y mixto. La mezcla pertinente de preguntas debe poder representarse sin penalizarla solo por cambiar de categoría.

La primera combinación sugerida en el chat —por competencias, conductual y estilo mixto— sigue siendo una propuesta. No hay un piloto configurado ni rangos, pesos o proveedor de modelo fijados. Una evaluación por pregunta no debe presentarse como una calificación validada de la sesión completa.

## Árbol principal

```text
Ejemplo_de_proyecto/
├── agent/                     Especificación declarativa
├── harness/                   Futura ejecución Python
│   ├── application/           Consola y posible API
│   ├── config/                Carga de ajustes
│   └── llm/                   Comunicación con el modelo
├── schemas/                   Contratos compartidos
├── config/
│   ├── interviews/            Combinaciones de entrevista
│   └── evaluation/            Parámetros de puntuación
├── data/
│   ├── candidates/            Perfiles ficticios
│   └── reference_questions/   Preguntas etiquetadas
├── outputs/
│   ├── sessions/              Registros generados
│   └── results/               Mediciones generadas
├── tests/                     Pruebas y datos controlados
├── scripts/                   Futuros accesos de ejecución
├── docs/
│   ├── academico/             Metadatos por asignatura
│   ├── arquitectura/          Diseño y flujo
│   ├── metodologia/           Clasificación, rúbrica y datos
│   ├── pruebas/               Protocolo y casos
│   ├── entregas/              Evidencias por ramo e hito
│   ├── decisiones/            Justificaciones técnicas
│   └── bitacora/              Avance real
└── .github/                   Plantillas y reserva de pruebas
```

## Archivos de entrada y configuración general

| Archivo | Qué deberá contener |
| --- | --- |
| [README.md](../README.md) | Presentación del proyecto, mapa de carpetas y, cuando exista implementación, instalación, configuración y ejecución comprobadas. |
| [CHANGELOG.md](../CHANGELOG.md) | Cambios por fecha o versión y su efecto. Ya registra esta reorganización. |
| [.env.example](../.env.example) | Nombres de variables y valores de muestra sin secretos. Actualmente conserva LLM_API_KEY y LLM_MODEL de la plantilla; ajustar al proveedor elegido. |
| [.gitignore](../.gitignore) | Exclusiones de credenciales, archivos temporales y salidas locales generadas. |
| [requirements.txt](../requirements.txt) | Dependencias realmente utilizadas y sus versiones cuando se elijan. Está sin dependencias. |

## Definición del agente y contratos

| Archivo | Qué deberá contener |
| --- | --- |
| [agent/agent.md](../agent/agent.md) | Rol del candidato, límites, fuentes de información, reglas de consistencia, manejo del historial y respuesta ante información faltante. No es el perfil concreto de una persona. |
| [agent/manifest.yaml](../agent/manifest.yaml) | Identidad y versión del agente, rutas de instrucciones y contratos, capacidades declaradas y parámetros de carga. Actualmente solo tiene comentarios. |
| [agent/input.schema.json](../agent/input.schema.json) | Campos y restricciones de la entrada de un turno: identificadores, pregunta y referencias de contexto/configuración. |
| [agent/output.schema.json](../agent/output.schema.json) | Campos y restricciones de la respuesta del candidato, separados de la evaluación del entrevistador. |
| [schemas/candidate.schema.json](../schemas/candidate.schema.json) | Estructura de perfiles ficticios: antecedentes, experiencias, competencias y restricciones necesarias. |
| [schemas/interview_config.schema.json](../schemas/interview_config.schema.json) | Modalidad, enfoque, estilo preferido, perfil, cargo, competencias y referencias de rúbrica; combinaciones permitidas. |
| [schemas/turn_evaluation.schema.json](../schemas/turn_evaluation.schema.json) | Dimensiones de clasificación, evidencias por criterio, puntuación interna, nivel visible, explicación, sugerencia y versión de rúbrica. |

Los cinco JSON Schema son marcadores válidos como JSON, pero no tienen propiedades ni restricciones. Su existencia no demuestra validación: habrá que completar contratos y validadores antes de utilizarlos. El contrato de evaluación está separado de la salida del candidato para mantener distintas responsabilidades.

## Código futuro en harness

`harness` es la capa Python que ejecutará el comportamiento definido en `agent/`. Los archivos actuales solo contienen una descripción; no realizan llamadas a modelos ni calculan evaluaciones.

| Archivo | Qué deberá implementar |
| --- | --- |
| [harness/runtime.py](../harness/runtime.py) | coordinar configuración, pregunta, respuesta validada, evaluación, retroalimentación inmediata y registro de cada turno. |
| [harness/candidate.py](../harness/candidate.py) | generar la respuesta del candidato a partir del perfil ficticio y el contexto permitido. |
| [harness/prompt_builder.py](../harness/prompt_builder.py) | construir instrucciones y contexto sin mezclar el rol del candidato con el evaluador. |
| [harness/question_classifier.py](../harness/question_classifier.py) | clasificar enfoque metodológico y tipo de pregunta en dimensiones separadas de su calidad. |
| [harness/question_evaluator.py](../harness/question_evaluator.py) | obtener evidencias por criterio de calidad, sin delegar al modelo el cálculo libre de la puntuación final. |
| [harness/scoring.py](../harness/scoring.py) | calcular localmente puntuación interna y nivel visible mediante criterios, pesos y umbrales versionados. |
| [harness/feedback.py](../harness/feedback.py) | preparar nivel, explicación y sugerencia para mostrar después de la respuesta y antes de la siguiente pregunta. |
| [harness/schema_validator.py](../harness/schema_validator.py) | validar entradas y salidas contra contratos completos; los marcadores actuales no validan contenido. |
| [harness/response_validator.py](../harness/response_validator.py) | comprobar consistencia de la respuesta respecto del perfil y gestionar contradicciones o datos no respaldados. |
| [harness/session_state.py](../harness/session_state.py) | mantener configuración, historial y estado temporal de la entrevista. |
| [harness/session_log.py](../harness/session_log.py) | registrar configuración, pregunta, respuesta, clasificación, criterios, puntuación, nivel, retroalimentación, versión y latencia. |
| [harness/llm/client.py](../harness/llm/client.py) | comunicarse con el proveedor de LLM y gestionar tiempos de espera, errores y reintentos. |
| [harness/llm/config.py](../harness/llm/config.py) | definir parámetros del modelo y conexión, sin incluir credenciales. |
| [harness/llm/messages.py](../harness/llm/messages.py) | representar mensajes y roles enviados al modelo. |
| [harness/application/cli.py](../harness/application/cli.py) | ofrecer una interacción inicial por consola que muestre retroalimentación después de cada pregunta. |
| [harness/application/api.py](../harness/application/api.py) | exponer el flujo mediante una API si se decide usar web o integrar Godot en una etapa posterior. |
| [harness/config/settings.py](../harness/config/settings.py) | cargar variables de entorno y rutas de configuración, separadas de los datos de la entrevista. |

Los cuatro `__init__.py` de `harness/`, `harness/llm/`, `harness/application/` y `harness/config/` solo marcan paquetes Python y pueden permanecer vacíos.

La secuencia que se deberá implementar es: validar configuración → recibir pregunta → generar y validar respuesta del candidato → clasificar pregunta → evaluar criterios → calcular puntuación y nivel → mostrar respuesta y retroalimentación → registrar → permitir la siguiente pregunta. Las ramas de error deben definirse antes de considerar completo el flujo.

`question_classifier.py` describe qué clase de pregunta se hizo; `question_evaluator.py` determina qué evidencias sustentan su calidad; `scoring.py` transforma esas evidencias en puntuación y nivel mediante reglas locales. Ser abierta, cerrada o directiva no determina automáticamente la calidad. Estos módulos no implican agentes autónomos distintos.

`harness/config/` carga ajustes técnicos del programa; `config/` guarda las futuras configuraciones del dominio. La API es una reserva opcional y no está habilitada. Godot podrá integrarse más adelante con este flujo cuando se decida la interfaz.

## Configuraciones, datos y salidas

Cada carpeta contiene un README que explica su futuro contenido. No se han creado perfiles ni ejemplos ficticios.

| Carpeta | Qué deberá contener |
| --- | --- |
| [config/interviews/](../config/interviews/README.md) | Configuraciones reutilizables, identificadores de perfil y rúbrica, competencias y combinaciones habilitadas. Mantener separadas las posibilidades diseñadas de las que realmente se pueden ejecutar. |
| [config/evaluation/](../config/evaluation/README.md) | Criterios, escalas, pesos, rangos, niveles y tratamiento de criterios no observables. Mantener coherencia con la metodología y una versión identificable. |
| [data/candidates/](../data/candidates/README.md) | Perfiles JSON ficticios compatibles con el contrato, sin modificar sus antecedentes al generar respuestas. |
| [data/reference_questions/](../data/reference_questions/README.md) | Preguntas, contexto y etiquetas humanas de referencia; registrar procedencia y separación entre ajuste y evaluación. |
| [outputs/sessions/](../outputs/sessions/README.md) | Registros de entrevistas con configuración, turnos, puntuación, nivel, retroalimentación, versiones y tiempos. |
| [outputs/results/](../outputs/results/README.md) | Métricas, comparaciones y resultados realmente generados al ejecutar pruebas. |

Las salidas locales quedan excluidas de Git. Para el informe, seleccionar evidencias revisadas y copiarlas a la entrega correspondiente, manteniendo un vínculo con versión y fecha.

## Pruebas y accesos de ejecución

| Ruta | Qué deberá contener |
| --- | --- |
| [tests/unit/](../tests/unit/README.md) | Pruebas de componentes aislados, sobre todo puntuación, límites entre niveles, contratos y contexto. |
| [tests/integration/](../tests/integration/README.md) | Pruebas de comunicación entre módulos y proveedor; errores, tiempos de espera, formatos inválidos y registro. |
| [tests/scenarios/](../tests/scenarios/README.md) | Entrevistas completas, conservación del perfil y orden de retroalimentación por turno. |
| [tests/fixtures/](../tests/fixtures/README.md) | Datos mínimos y respuestas simuladas reproducibles para las pruebas. |
| [scripts/run_interview.py](../scripts/run_interview.py) | Punto de inicio del futuro flujo de entrevista. |
| [scripts/smoke_test.py](../scripts/smoke_test.py) | Comprobación básica de un turno cuando el sistema exista. |
| [scripts/validate_repository.py](../scripts/validate_repository.py) | Comprobación futura de archivos y contratos completos. Hoy no ejecuta validación. |

No se añadieron pruebas vacías con apariencia de pruebas aprobadas. Cuando se implemente, deben comprobar comportamiento y errores observables.

## Qué escribir en cada parte del informe

[docs/informe.md](informe.md) conserva únicamente encabezados y comentarios pendientes. Los archivos de metodología y arquitectura sirven como material de trabajo; el informe deberá sintetizarlos y citar la evidencia, evitando mantener versiones contradictorias.

| Parte | Contenido esperado |
| --- | --- |
| Portada | Título definitivo, autoría, institución, sede, asignatura, docente, fecha y versión. |
| Resumen y palabras clave | Problema, propósito, método, alcance y estado real. El chat menciona 150–250 palabras; contrastar con la plantilla oficial. No anticipar resultados como si ya existieran. |
| Índices | Secciones, tablas y figuras efectivamente utilizadas, con numeración y páginas de la versión de entrega. |
| 1. Introducción | Contexto de entrenamiento de entrevistadores y presentación del simulador educativo. |
| 2. Problema | Necesidad, delimitación, justificación y manejo responsable de los datos. Fundamentar con fuentes la calidad de entrevistas y su práctica; mantener coherencia con el alcance adoptado. |
| 3. Objetivos | Objetivo del semestre y objetivos específicos verificables; distinguirlos de la proyección completa a tres semestres y asociarlos a evidencias. |
| 4. Estado del arte | Comparación crítica de entrevistas estructuradas, simulación, LLM y consistencia; explicar cómo las fuentes sustentan decisiones y cuál es la brecha abordada. |
| 5. Metodología | Diseño de escenarios, dimensiones de configuración, clasificación, criterios de calidad, puntuación provisional, niveles, retroalimentación inmediata y validación. Distinguir propuesta de instrumento validado. |
| 6. Requisitos y planificación | Requisitos identificables, alcance de E2 y cierre, configuraciones implementables, cronograma con responsables, riesgos y continuidad de segundo y tercer semestre. |
| 7. Diseño y arquitectura | Diagrama, componentes, interfaces, contratos, estado de sesión, flujo por turno, controles de consistencia y recuperación de fallos. |
| 8. Implementación y MVP | Versiones y entorno realmente utilizados, configuración ejecutada, funciones existentes, estructura real, repositorio o commit, demostración y limitaciones. Completar cuando haya implementación. |
| 9. Evaluación y resultados | 9.1: protocolo, datos y criterios de aceptación. 9.2: mediciones observadas de clasificación, consistencia, puntuación, latencia y errores. 9.3: valor, impacto y limitaciones justificables. |
| 10. Discusión | Interpretar los resultados frente a objetivos y literatura, explicar errores y límites de las conclusiones. |
| 11. Conclusiones y trabajo futuro | Qué se logró con evidencia, qué falta y cómo continúa el proyecto. Distinguir el cierre del curso de los siguientes semestres. |
| Referencias | Fuentes realmente consultadas y citadas, con un estilo uniforme conforme a la pauta. No se ha copiado ni validado una bibliografía del otro chat. |
| Anexos A, B y C | Contratos y configuraciones utilizados, casos de prueba y evidencias verificables de implementación, respectivamente. |

## Documentación de apoyo y evidencia académica

| Archivo o carpeta | Qué deberá contener |
| --- | --- |
| [docs/metodologia/clasificacion.md](metodologia/clasificacion.md) | Definiciones y ejemplos futuros por dimensión, reglas multietiqueta, ambigüedad y procedimiento de etiquetado humano. |
| [docs/metodologia/rubrica.md](metodologia/rubrica.md) | Criterios observables, evidencia, escala interna, pesos, conversión a cuatro niveles, explicación inmediata, validación y límites. No fija valores todavía. |
| [docs/metodologia/datos.md](metodologia/datos.md) | Diseño, procedencia, versionado y privacidad de perfiles, configuraciones, preguntas y registros. |
| [docs/planificacion.md](planificacion.md) | Plan del semestre, E2, E3, ampliación de configuraciones, continuidad de tres semestres y funciones postergadas. |
| [docs/arquitectura/README.md](arquitectura/README.md) | Diagrama y responsabilidades de componentes, contratos y extensiones futuras. |
| [docs/arquitectura/flujo-de-entrevista.md](arquitectura/flujo-de-entrevista.md) | Secuencia de un turno, condiciones de paso y rutas ante errores. |
| [docs/pruebas/protocolo.md](pruebas/protocolo.md) | Qué medir, con qué conjunto de datos, versiones, métodos de comparación, métricas y criterios de aceptación. |
| [docs/pruebas/casos-de-prueba.md](pruebas/casos-de-prueba.md) | Casos identificados con entrada, esperado, observado, estado, versión y evidencia. Dejar sin observado lo aún no ejecutado. |
| [docs/decisiones/README.md](decisiones/README.md) | Plantilla para justificar cada decisión, registrar alternativas y diferenciar decisiones pendientes de adoptadas. |
| [docs/bitacora/bitacora-desarrollo.md](bitacora/bitacora-desarrollo.md) | Avance real por fecha, autoría, cambios, problemas, comprobaciones y siguiente paso. |
| [docs/academico/cinf110.yml](academico/cinf110.yml) | Metadatos originales de CINF110, conservados sin reinterpretarlos como datos de CINF200. El grupo sigue pendiente. |
| [docs/academico/cinf200.yml](academico/cinf200.yml) | Metadatos de CINF200, por confirmar con documentación oficial. Solo tiene comentarios. |
| [docs/entregas/README.md](entregas/README.md) | Criterio para organizar entregas, fechas y correspondencia con pautas cuando se conozcan. |
| [docs/entregas/cinf110/evaluacion-01/](entregas/cinf110/evaluacion-01/README.md) | Evidencias que solicite esa evaluación de CINF110; conserva el espacio heredado sin asumir equivalencia con CINF200. |
| [docs/entregas/cinf200/e2/](entregas/cinf200/e2/README.md) | Evidencias del avance inicial: ejecución, configuración, turnos, pruebas y versión real. |
| [docs/entregas/cinf200/e3/](entregas/cinf200/e3/README.md) | Evidencias del cierre del semestre, diferenciadas de E2 y del trabajo futuro. |

Las carpetas de entrega solo contienen README. La estructura no supone aprobación para usar el mismo trabajo en ambas asignaturas ni certifica requisitos de sus pautas.

## Plantillas de colaboración

| Archivo | Qué deberá contener al utilizarse |
| --- | --- |
| [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md) | Propósito del cambio, archivos afectados, relación con informe/requisitos y verificaciones realizadas. |
| [.github/ISSUE_TEMPLATE/bug.md](../.github/ISSUE_TEMPLATE/bug.md) | Problema reproducible, versión, resultado esperado y observado. |
| [.github/ISSUE_TEMPLATE/mejora.md](../.github/ISSUE_TEMPLATE/mejora.md) | Necesidad, propuesta, alcance y criterios de aceptación. |
| [.github/ISSUE_TEMPLATE/evidencia-evaluacion.md](../.github/ISSUE_TEMPLATE/evidencia-evaluacion.md) | Asignatura, hito, criterio, versión y ruta de evidencia. |
| [.github/workflows/tests.yml](../.github/workflows/tests.yml) | Automatización cuando existan pruebas reales. Actualmente es una reserva comentada, sin workflow habilitado. |

## Correspondencia con la plantilla anterior

Todos los archivos originales de código contenían únicamente una descripción genérica; los documentos también eran marcadores. No había lógica implementada ni informes desarrollados que migrar.

| Ruta anterior | Destino o tratamiento |
| --- | --- |
| `src/agent/agent.py` | `harness/candidate.py`. |
| `src/agent/orchestration.py` | `harness/runtime.py`. |
| `src/agent/prompts.py` | `harness/prompt_builder.py` y especificación en `agent/agent.md`. |
| `src/agent/schemas.py` | Contratos separados en `agent/` y `schemas/`, pendientes de completar. |
| `src/llm/` | `harness/llm/`. |
| `src/memory/session.py`, `chat_memory.py` | `harness/session_state.py`; se separó el registro en `harness/session_log.py`. |
| `src/application/`, `src/config/` | Mismos grupos bajo `harness/`. |
| `src/tools/`, `src/integrations/` | Marcadores retirados: sin responsabilidad necesaria en el MVP definido. Documentar futuras necesidades antes de recrearlos. |
| `data/examples/`, `data/sample/` | Sustituidos por carpetas específicas de perfiles y preguntas; datos controlados en `tests/fixtures/`. |
| `docs/proyecto.md` | `docs/informe.md`, complementado con metodología y planificación. |
| `docs/curso.yml` | `docs/academico/cinf110.yml`, con sus datos originales. |
| `docs/arquitectura/flujo-del-agente.md` | `docs/arquitectura/flujo-de-entrevista.md`. |
| `docs/evaluaciones/` | Separación entre `docs/pruebas/` y `docs/entregas/`, con asignatura e hito explícitos. |
| `scripts/run_agent.py` | `scripts/run_interview.py`. |
| README genéricos y marcadores vacíos | Sustituidos por títulos específicos, espacios pendientes o instrucciones de llenado. |

## Orden sugerido al comenzar a completar

1. Confirmar la pauta y completar el alcance, los requisitos y la planificación.
2. Definir dimensiones, datos, contratos y criterios de evaluación en la documentación.
3. Crear un perfil y una configuración piloto; completar instrucciones y manifiesto.
4. Implementar un turno del candidato, la validación y el estado.
5. Incorporar clasificación, evaluación, cálculo local y retroalimentación inmediata.
6. Añadir pruebas significativas, ejecutar y registrar resultados.
7. Completar implementación y resultados del informe a partir de evidencia real.

## Actualización de implementación: unidad 7.2

La descripción original de esta guía pertenece a la plantilla de planificación. `harness/session_state.py` ahora está implementado: identidad, configuración y registro técnico en memoria. `harness/session_log.py` está implementado desde la unidad 7.3: valida, guarda y lee el registro técnico cerrado en JSON local, sin campos de evaluación futura. La clasificación y evaluación continúan fuera del alcance actual. El estado actualizado y las pruebas están en el [README principal](../README.md), [sesiones en memoria](sesiones-en-memoria.md) y [persistencia de sesiones](persistencia-sesiones.md).

Desde la unidad 7.3 están definidos los esquemas de candidato, puesto, configuración y sesión; el contrato de evaluación sigue reservado. La descripción inicial de contratos vacíos corresponde a la plantilla histórica.

La unidad 7.4a añade `harness/context_budget.py` y `scripts/inspect_context.py` para comparar métricas ya guardadas con reservas explícitas. El comando es de lectura, sin llamadas al modelo, y no cambia el flujo de conversación. El resumen controlado continúa pendiente. Véase [diagnóstico de contexto](diagnostico-contexto.md).

La unidad 7.4c añade `harness/history_summary.py` y `scripts/preview_summary.py` para preparar una propuesta extractiva verificable y revisarla. El módulo copia citas a partir de índices, conserva anclas por código y mantiene completos los pares recientes. No se integra todavía en el controlador ni sustituye el registro de sesión. Véase [resumen extractivo](resumen-extractivo.md).
