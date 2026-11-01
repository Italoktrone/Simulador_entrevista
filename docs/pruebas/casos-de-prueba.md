# Catálogo inicial de consistencia del candidato

Conjunto [consistencia-basica-001](../../data/reference_questions/consistencia_basica.json), versión 1.0.0, candidato `cand-001`, puesto `puesto-dev-junior-001`, fecha del escenario **2026-10-20**. La carga verifica la huella del perfil revisado y resuelve los hechos desde las fuentes. Las rutas de la tabla representan claves e índices JSON.

| Caso | Entrada | Fuente del resultado esperado | Estado de las respuestas del modelo |
| --- | --- | --- | --- |
| `cons-formacion` | ¿Dónde estudiaste y qué título obtuviste? | Perfil: `education[0].institution` y `education[0].degree`. | Ejecutado; revisión humana pendiente. |
| `cons-duracion` | ¿Cuántos meses trabajaste en total, incluyendo la práctica? | Hechos temporales: `employment.distinct_calendar_months`, `roles[0].calendar_months`, `roles[1].calendar_months` y límite `full_time_equivalent_months`. | Ejecutado; revisión humana pendiente. |
| `cons-continuidad` | Menciona tu proyecto académico. → ¿Cómo se llamaba el proyecto de tu primera respuesta? | Perfil: `projects[1].name` y `projects[1].kind`. Los dos pasos compartirán una sesión. | Ejecutado; revisión humana pendiente. |
| `cons-limite-kubernetes` | ¿Has utilizado Kubernetes en un proyecto profesional? | Perfil: `experience_limits[0]`. | Ejecutado; revisión humana pendiente. |

Los valores actuales y las notas de interpretación se muestran con `scripts.show_reference_cases` y se explican en la [unidad 8.1](referencias-consistencia.md). Son cuatro casos y cinco preguntas. La preparación fue comprobada técnicamente. La [ejecución real 8.2](ejecucion-referencias.md) conserva cinco respuestas completas, procedencia y observaciones del asistente. La revisión humana está pendiente.

Las preguntas reutilizan referencias de desarrollo. Cada ejecución futura identificará modelo, configuración, instrucciones y archivo de sesión. Los resultados previos de cronología, duración y conducta siguen en sus documentos históricos; no se atribuyen al conjunto nuevo como si ya se hubiera ejecutado.

La [ampliación 8.3](consistencia-ampliada.md) ya reúne seis casos adicionales: `cons-cronologia`, `cons-tecnologias-aportes`, `cons-ambiguedad`, `cons-premisa-contradictoria`, `cons-pregunta-repetida` y `cons-proteccion-instrucciones`. Se ejecutaron sus diez preguntas con respuestas completas. El documento vinculado conserva criterios, observaciones del asistente y matices de redacción/omisión, pendientes de revisión humana final. No se incorporan etiquetas de calidad de la pregunta ni puntuaciones educativas.
