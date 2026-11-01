# Cierre técnico de la Etapa 8: pruebas de consistencia

La Etapa 8 queda implementada y comprobada en el alcance descrito aquí. El usuario ejecutó ambos conjuntos con **gemma4:e4b** y compartió las respuestas completas. Se conservan las ejecuciones y la inspección del asistente; no se atribuye al usuario una aprobación semántica explícita que no haya expresado. Posteriormente autorizó «Pasemos a la Etapa 9»; su resultado está en la [validación final](validacion-final.md).

## Alcance comprobado

| Conjunto | Casos | Preguntas | Ejecución del usuario |
| --- | --- | --- | --- |
| Básico | 4 | 5 | [9990715a-bb6d-4a7d-bbd6-3753f753c503](../outputs/results/reference-run-9990715a-bb6d-4a7d-bbd6-3753f753c503.json) |
| Ampliado | 6 | 10 | [96b33ded-c47b-4303-a812-6cd88503d860](../outputs/results/reference-run-96b33ded-c47b-4303-a812-6cd88503d860.json) |

Los diez casos cubren formación, duración, continuidad, límites de experiencia, cronología, tecnologías/aportes, ambigüedad, premisa contradictoria, repetición y protección de instrucciones. Cada caso tiene una sesión independiente; sus pasos comparten historial. En ambos lotes del usuario las quince respuestas terminaron completas, sin incidencias técnicas.

Las respuestas originales y las notas para revisión se conservan en JSON. La inspección del asistente no observó contradicciones factuales. En la repetición ampliada, el orden de término fue Inventario Aula en noviembre de 2025, titulación en diciembre de 2025 y MesaFaro en septiembre de 2026. El candidato pidió precisar el periodo ambiguo, corrigió la premisa de clientes comerciales y mantuvo sus datos y rol. La redacción de titulación fue clara en esta ejecución; no se modificaron instrucciones para obtenerla.

La respuesta a la premisa comercial no explicitó por separado la ausencia de producción. Se conserva como detalle omitido, sin convertirlo en una afirmación contradictoria. No se exige una oración literal idéntica para considerar compatibles dos respuestas.

La [confirmación final](../outputs/results/reference-user-confirmation-96b33ded-c47b-4303-a812-6cd88503d860.json) distingue ejecución del usuario, lectura local e inspección del asistente. Se validaron las seis sesiones nuevas contra sus instantáneas y huellas; los cuatro originales y veintiuna sesiones anteriores permanecieron intactos. Los tiempos comunicados fueron 10,03; 9,18; 3,90; 12,49; 5,30; 4,59; 5,80; 4,88; 3,83 y 4,16 s. No se extrapolan a una garantía de latencia.

## Pruebas y límites

La última suite completa registrada es **736 passed in 123.96s**. Las dos comprobaciones nuevas del conjunto ampliado pasaron por separado: **2 passed in 1.88s**. Hay 738 pruebas disponibles; no se inventa una ejecución completa de 738. Este cierre es documental y de lectura de evidencia; no se repitieron llamadas a modelos ni pruebas ya verificadas.

Son referencias de desarrollo conocidas, no un conjunto independiente. No certifican consistencia universal, resistencia ante cualquier instrucción adversaria o resultados equivalentes en otros modelos. La revisión humana de contenido sigue disponible y su aprobación explícita no se deduce del estado `completed`.

Se conservan referencia del escenario **2026-10-20**, instrucciones **1.0.11**, máximo **20**, datos aprobados y dependencias. Ollama fue el único proveedor utilizado. La alternativa externa permanece implementada y desactivada para estos lotes. Clasificación, rúbrica, puntuaciones, retroalimentación educativa y Godot quedan fuera de esta fase.

## Etapa restante

**Ocho etapas completadas en su alcance técnico; queda una: integración y validación final.** Una vez indicada la transición, la Etapa 9 reunirá la suite completa, comprobación del flujo de consola, historial, cierre, guardado/lectura e integridad, y documentación final. Se hará en un bloque, manteniendo las explicaciones breves como pidió el usuario. No se inicia automáticamente en este cierre.
