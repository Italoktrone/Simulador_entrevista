# Preguntas de referencia

El conjunto adicional [consistencia_ampliada.json](consistencia_ampliada.json) reúne seis casos y diez preguntas: cronología, tecnologías/aportes, ambigüedad, contradicciones, repetición y protección de instrucciones. Utiliza el mismo esquema y ejecutor. El [bloque 8.3](../../docs/validacion-del-candidato.md#consistencia-ampliada) documenta comando, criterios, ejecución real y observaciones. Entre ambos conjuntos hay diez casos y quince preguntas; la revisión humana final está pendiente.

[consistencia_basica.json](consistencia_basica.json) contiene cuatro casos de consistencia factual del candidato y cinco preguntas. Incluye fuentes de hechos, notas para revisión humana y el requisito de una sesión nueva por caso. El caso de continuidad conserva sus dos pasos en la misma sesión.

Los valores esperados se resuelven desde el perfil aprobado y sus cálculos temporales; la huella del perfil vincula el conjunto a la fuente revisada. El contrato está en [reference_suite.schema.json](../../schemas/reference_suite.schema.json). Se puede comprobar y mostrar sin consultar al modelo:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.show_reference_cases
```

Ejecutar desde la raíz del proyecto. Véase la [guía 8.1](../../docs/validacion-del-candidato.md#referencias-consistencia). Los casos se ejecutaron con Ollama local en la [unidad 8.2](../../docs/validacion-del-candidato.md#ejecucion-referencias); la revisión humana permanece pendiente. Son referencias de desarrollo con preguntas conocidas; no un conjunto independiente reservado para prueba.

Los dos conjuntos de consistencia no contienen clasificación de preguntas, etiquetas de calidad, rúbrica ni puntuaciones educativas.

## Clasificación descriptiva: referencias aprobadas

[`clasificacion_basica.json`](clasificacion_basica.json) es un conjunto separado,
versión 1.0.0, con las 40 intervenciones aprobadas por el usuario: 30 de desarrollo
y 10 de comprobación conocida. La [tabla y guía](../../docs/clasificador.md#referencias-clasificacion-propuesta)
registran textos, contextos, etiquetas, segmentación, límites y comandos locales.

Su esquema es `schemas/classification_references.schema.json` y su cargador
`harness/classification_references.py`. Las expectativas se comprueban con
las relaciones compartidas del contrato descriptivo, sin inventar métodos de
ejecución. No utiliza el esquema ni el ejecutor de consistencia del candidato.
No contiene respuestas generadas, calidad ni puntuaciones. La comprobación
conocida no es una evaluación independiente; los 40 casos ya son visibles.

El bloque 10 añade un [evaluador con métricas y discrepancias](../../docs/clasificador.md#evaluacion-clasificador).
Ejecuta grupos por separado y conserva las etiquetas aprobadas. Por defecto
usa solo desarrollo y reglas sin red; evaluar los cuarenta o usar el híbrido
local requiere opciones explícitas. Los informes reales y las pruebas con
transportes simulados se documentan por separado.

## Calidad de preguntas: referencias aprobadas

`evaluacion_calidad_aprobada.json` es el conjunto activo: 40 referencias revisadas 1.1.0 y contextos aprobados explícitamente por el usuario. Su rúbrica 1.1.0 aplica la Regla Crítica aprobada, conservando niveles y recalculando tres globales. `evaluacion_calidad.json` y `evaluacion_calidad_revision_propuesta.json` preservan las dos etapas anteriores sin reescribirlas. La [guía de revisión](../../docs/evaluador.md#revision-referencias-evaluador) muestra casos y cambios; la [guía de calibración](../../docs/evaluador.md#calibracion-evaluador-few-shot) explica las seis demostraciones de desarrollo.

El conjunto activo puede inspeccionarse con `scripts.evaluate_questions --preview --split todos`. Las referencias pendientes no crean un cliente para calibrar. `evaluator_demonstrations.json` contiene los seis ejemplos aprobados fijados por `config/evaluator_few_shot.json`; los diez casos de comprobación conocida no se inyectan. Son independientes de las 40 etiquetas descriptivas del clasificador.
