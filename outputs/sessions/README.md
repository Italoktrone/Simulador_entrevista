# Registros de sesiones

Desde la unidad 7.3, la consola guarda un archivo UTF-8 `session-<UUID>.json` por ejecución cerrada, incluso sin preguntas. Conserva configuración, preguntas, respuestas, métricas e incidencias técnicas. Los archivos existentes no se sobrescriben. `harness.session_log.load_session` permite leer y validar los datos sin reanudar una entrevista.

Las pruebas automatizadas guardan en carpetas temporales. Los archivos de esta carpeta corresponden a ejecuciones locales de la aplicación; su contenido no certifica la corrección semántica del modelo. Para una entrega académica, copiar únicamente evidencia seleccionada y revisada a `docs/entregas/`. Véase la [guía de persistencia](../../docs/contexto-y-sesiones.md#persistencia-sesiones).

Con `--extractive-context`, el formato 1.1.0 incluye política y eventos de preparación, sin convertir las selecciones en preguntas. Los registros anteriores 1.0.0 se conservan y siguen siendo legibles. Las fixtures preparadas para pruebas se guardan en temporales o evidencia identificada, separadas de entrevistas naturales.
