# UNAB IA: consumo y respuestas rechazadas

## Evidencia de la sesión del usuario

[Sesión cd0fa34f-b9a1-491f-9f9a-fa7c83ff6ecc](../../outputs/sessions/session-cd0fa34f-b9a1-491f-9f9a-fa7c83ff6ecc.json): cuatro preguntas, tres errores `invalid_response` y una respuesta completa. La institución y fecha de titulación fueron correctas; el perfil conserva su huella aprobada.

La llamada completa informó **6045 tokens de entrada y 233 de salida**. Las tres rechazadas no conservaron métricas, motivo de finalización ni forma del contenido: no puede determinarse su causa exacta retrospectivamente. El adaptador emitía el mismo error para varias causas distintas y no registraba uso de respuestas rechazadas; las pruebas iniciales no cubrían una salida vacía al agotar tokens con razonamiento.

El contexto fijo actual contiene **24 822 caracteres**, y se vuelve a enviar en cada pregunta junto al historial completo aceptado. Los intentos fallidos se conservan en el registro, pero no se añaden al contexto posterior. Cuatro entradas del orden de 6000 tokens implican unas 24 000 unidades de entrada, antes de sumar la generación. La captura muestra **25 963 créditos consumidos hoy de 50 000**, con **24 037 disponibles**. Es un consumo compatible en orden de magnitud; no se conoce la equivalencia exacta crédito/token del servicio ni si hubo otras llamadas. No se afirma que toda la cifra proceda de esta sesión.

## Hipótesis y primera corrección (histórica: 512 tokens)

El límite enviado era `max_tokens: 512`. Una respuesta compleja puede gastar su presupuesto en razonamiento y terminar sin texto final. Gemma admite modos de razonamiento según su [ficha oficial en Ollama](https://ollama.com/library/gemma4), y la [documentación de compatibilidad](https://docs.ollama.com/api/openai-compatibility) describe `reasoning_effort: none`. Eso hace plausible la hipótesis; no demuestra cómo la pasarela UNAB resolvió las tres llamadas anteriores.

En la primera corrección se solicitó `reasoning_effort: none`, manteniendo **512 tokens** y sin aumentar presupuesto ni repetir automáticamente generaciones. La pasarela puede aplicar, ignorar o rechazar el parámetro: su efecto real debe comprobarse con un único intento controlado. No se presenta como reparación confirmada en el servicio desplegado.

El cliente conserva metadatos permitidos incluso al rechazar contenido: estado HTTP, finalización conocida, límite solicitado, caracteres de contenido, presencia de razonamiento y métricas de uso disponibles. Los valores desconocidos permanecen `null`; no se estiman ni convierten a cero. Los contadores de razonamiento y caché son desgloses cuando el servidor los informa, no cargos adicionales que deban sumarse otra vez al total.

No se guardan mensajes, cabeceras, claves, cuerpo bruto ni razonamiento. Los marcadores de pensamiento conocidos se rechazan como respuesta final, sin exponer su contenido. Al cerrar la consola se escribe `outputs/results/unab-usage-<UUID>.json`, separado del registro original de la entrevista y sin alterar su esquema. Las respuestas completas muestran sus tokens informados en terminal.

## Comprobación del usuario

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview
```

Elegir **2**, usar `/iniciar`, formular **solo la primera pregunta compleja** y cerrar con `/salir`. Revisar la respuesta y el archivo indicado como **Diagnóstico de uso de API**. Si falla, conservar ese diagnóstico antes de repetir preguntas. El diagnóstico distingue salida vacía al límite de otras salidas inválidas; permite comprobar o descartar la hipótesis sin publicar la clave.

La reparación se prueba con HTTP simulado; no se utilizó la clave privada ni se consumió cuota UNAB durante esta investigación. El historial, perfil e instrucciones originales permanecen sin cambios. Este trabajo mejora observabilidad y solicita menor razonamiento; no reduce por sí solo los aproximadamente 6000 tokens de contexto inicial por petición ni cambia la contabilidad del proveedor.

Verificación: **27 passed in 3.97s** en el adaptador; suite completa **765 passed in 254.13s (0:04:14)**, 687 unitarias y 78 integraciones. Evidencia: [investigación y hechos confirmados](../../outputs/results/unab-response-investigation-737c141f23f7423ba79fa9b0d23ade18.json). No hubo llamadas reales a UNAB ni acceso a la clave privada; la sesión original conserva su huella.

## Comprobación posterior: límite confirmado y presupuesto configurable

El usuario probó una sola pregunta sobre lentitud de Flask/PostgreSQL. [Diagnóstico b84552c0-bccb-48e3-8498-bbeae51ed951](../../outputs/results/unab-usage-b84552c0-bccb-48e3-8498-bbeae51ed951.json): HTTP 200, entrada 6058, salida 512, total informado 6570, finish_reason length y contenido final de cero caracteres. Se había solicitado reasoning_effort none. No se recibió razonamiento en los campos inspeccionados y su número de tokens no fue informado; no equivale a demostrar que no hubo procesamiento interno ni que la pasarela aplicó o ignoró el parámetro.

Se confirmó el agotamiento de la salida sin respuesta, no su causa interna. La solución controlada siguiente solicita **2048 tokens de salida para UNAB**, mantiene reasoning_effort none y no repite la generación. El límite 512 de Ollama y del adaptador Responses anterior no cambia. El máximo es un techo solicitado, no garantiza que se consuma entero ni define la fórmula de créditos UNAB.

El selector muestra el presupuesto antes de abrir la entrevista. El archivo privado anterior de tres campos funciona sin editarlo ni cambiar la clave. Opcionalmente admite api_max_output_tokens como entero entre 16 y 4096; si falta, usa 2048. Nunca se aumenta el presupuesto de forma automática. La fábrica también admite UNAB_MAX_OUTPUT_TOKENS para uso programático; al iniciar con el selector prevalece el archivo privado o su valor por defecto.

Se verificaron **109 pruebas en 1,44 s** del adaptador/selector, fábrica y Responses, sin cuota API. Incluyen 17 regresiones nuevas para límites, tipos inválidos, compatibilidad local, valor predeterminado y correspondencia del presupuesto enviado con el diagnóstico. No se repitió toda la suite para este cambio aislado; el resultado completo anterior de 765 queda como evidencia histórica. Hay 782 pruebas disponibles, no una nueva ejecución completa de 782.

Repetir únicamente la misma pregunta y cerrar con /salir. El diagnóstico debe indicar requested_max_tokens 2048. Si vuelve a finalizar sin texto, detener la prueba y revisar el diagnóstico y la configuración del servicio antes de seguir aumentando límites o repitiendo llamadas. Esta modificación aún no tiene validación real del usuario.

## Confirmación real con 2048

El usuario repitió exactamente la misma pregunta sobre Flask/PostgreSQL. La [sesión 162df680-88d6-40ca-9e8f-d095fae07025](../../outputs/sessions/session-162df680-88d6-40ca-9e8f-d095fae07025.json) terminó con una respuesta completa y cero incidencias; el perfil permaneció intacto. El [diagnóstico](../../outputs/results/unab-usage-162df680-88d6-40ca-9e8f-d095fae07025.json) informó HTTP 200, presupuesto 2048, finish_reason stop, entrada 6058, salida 1255 y total 7313. El contenido final tuvo 684 caracteres. Tiempo comunicado: 12,82 s.

La respuesta distinguió cantidad de consultas por petición, duración/plan de ejecución y tiempo total del endpoint, presentándolo como propuesta hipotética. La inspección del asistente no sustituye una aprobación semántica humana. La repetición confirma funcionamiento de este caso con el presupuesto mayor; no demuestra el comportamiento interno del parámetro de razonamiento ni la compatibilidad de todas las preguntas. El proveedor no desglosó tokens de razonamiento o caché, y sigue sin conocerse su fórmula de créditos.

Se mantiene el presupuesto configurado de 2048, sin cambios adicionales ni reintentos. Se validaron los dos archivos sin modificarlos; no se hicieron nuevas llamadas o lecturas de la clave privada ni se repitieron tests para registrar esta confirmación. [Evidencia estructurada](../../outputs/results/unab-success-confirmation-162df680-88d6-40ca-9e8f-d095fae07025.json).
