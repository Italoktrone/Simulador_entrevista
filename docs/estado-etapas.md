# Estado de las nueve etapas del agente candidato

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
| 7 | Historial y contexto | Completada en su alcance funcional | Sesiones aisladas, historial, guardado JSON, diagnóstico y resumen opcional auditado. [Cierre y límites](cierre-etapa-7.md). |
| 8 | Pruebas de consistencia | Cierre técnico comprobado | El usuario ejecutó ambos conjuntos: diez casos y quince respuestas completas, sin contradicciones observadas por el asistente. [Cierre, evidencias y límites](cierre-etapa-8.md). |
| 9 | Integración y validación final | Completada en el alcance comprobado | 738 pruebas aprobadas; consola real con veinte respuestas y cierre al límite, salida anticipada independiente, JSON 1.0/1.1 leídos y originales intactos. [Cierre y evidencia](validacion-final.md). |

La [unidad 8.1](pruebas/referencias-consistencia.md) prepara criterios y verifica sus fuentes sin consultar al modelo. Las pruebas técnicas de esta unidad no cuentan como ejecuciones de consistencia del candidato. Las preguntas ya aparecieron durante el desarrollo; no constituyen un conjunto independiente reservado para prueba.

La [unidad 8.2](pruebas/ejecucion-referencias.md) agrupa la ejecución básica. El [bloque 8.3](pruebas/consistencia-ampliada.md) reúne cronología, tecnologías/aportes, ambigüedad, premisa contradictoria, repetición y protección de instrucciones. El usuario confirmó ambas ejecuciones y autorizó la Etapa 9, completada en un bloque. Los cierres distinguen inspección del asistente, revisión humana, redacción, omisiones y contradicciones. Se mantiene la preferencia del usuario por explicaciones breves y comprobaciones agrupadas.

La clasificación, rúbrica, puntuaciones y retroalimentación educativa quedan fuera de estas nueve etapas del agente. La integración con Godot pertenece a la planificación posterior del proyecto completo.
