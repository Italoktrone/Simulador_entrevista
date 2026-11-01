# Protocolo de revisión de consistencia del candidato

## Alcance actual

La Etapa 8 revisa si las respuestas conservan los antecedentes ficticios y las referencias conversacionales. La unidad 8.1 prepara y valida un conjunto de desarrollo con cuatro casos y cinco preguntas; quedó confirmada por el usuario. La [unidad 8.2](ejecucion-referencias.md) añade ejecución local por lotes y conserva las respuestas para revisión. No hay veredicto semántico automático, rúbrica ni puntuación educativa.

Las instrucciones de uso y comprobación están en [referencias de consistencia](referencias-consistencia.md) y el [catálogo](casos-de-prueba.md). El estado global permanece en [estado de etapas](../estado-etapas.md).

## Preparación y procedimiento previsto

1. Validar el conjunto, su esquema y sus referencias contra el perfil aprobado. No cambiar los antecedentes para acomodar una respuesta.
2. Registrar versión y huella del conjunto y del perfil, fecha del escenario, instrucciones, configuración, proveedor/modelo solicitado y metadatos disponibles del resultado. Una versión no informada se conserva como desconocida.
3. Iniciar una sesión nueva por caso. Mantener juntos los dos pasos de continuidad; no mezclar conversaciones de casos diferentes. Conservar preguntas y respuestas originales, incluidos fallos, en el registro local.
4. Revisar manualmente hechos y referencias contra las fuentes. Distinguir contradicción, detalle omitido, dato añadido sin respaldo e imprecisión de redacción. Una paráfrasis compatible no es un fallo por diferir de una oración literal.
5. Registrar evidencia concreta de cada observación y el archivo fuente. No marcar una respuesta como revisada porque su estado técnico sea `completed`. Separar errores técnicos de la revisión de contenido.
6. Si se corrige una causa, conservar la evidencia anterior y repetir el caso con la nueva procedencia. No mezclar resultados de contextos distintos ni atribuir la repetición a una versión anterior.

La unidad 8.2 automatiza la procedencia y las sesiones de los pasos 2 y 3. La revisión del contenido de los pasos 4 a 6 permanece explícita; el ejecutor no la aprueba automáticamente. El listado offline de referencias sigue sin crear sesiones o llamar a proveedores.

## Interpretación y límites

En duración, el total es de meses calendario distintos y no representa equivalencia a jornada completa. Si falta el desglose con el total correcto, se observa la falta de detalle sin inventar una contradicción. En continuidad, una corrección explícita de una primera respuesta errónea debe diferenciarse de perder su referencia. La fuente aprobada conserva prioridad sobre lo dicho antes por el candidato.

Las preguntas son conocidas durante el desarrollo: sirven para regresión, no para estimar desempeño en preguntas independientes. El número de casos, el número de pruebas técnicas o una respuesta correcta aislada no certifican consistencia global. Las ampliaciones y su alcance se registrarán antes del cierre de la Etapa 8.

Los tiempos y tokens informados se conservarán como observaciones de cada llamada. No se convierten en garantías de latencia ni se completan datos desconocidos con cero. La evaluación educativa del entrevistador y sus métricas de clasificación quedan para una fase posterior.
