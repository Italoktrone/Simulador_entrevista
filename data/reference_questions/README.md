# Preguntas de referencia

El conjunto adicional [consistencia_ampliada.json](consistencia_ampliada.json) reúne seis casos y diez preguntas: cronología, tecnologías/aportes, ambigüedad, contradicciones, repetición y protección de instrucciones. Utiliza el mismo esquema y ejecutor. El [bloque 8.3](../../docs/pruebas/consistencia-ampliada.md) documenta comando, criterios, ejecución real y observaciones. Entre ambos conjuntos hay diez casos y quince preguntas; la revisión humana final está pendiente.

[consistencia_basica.json](consistencia_basica.json) contiene cuatro casos de consistencia factual del candidato y cinco preguntas. Incluye fuentes de hechos, notas para revisión humana y el requisito de una sesión nueva por caso. El caso de continuidad conserva sus dos pasos en la misma sesión.

Los valores esperados se resuelven desde el perfil aprobado y sus cálculos temporales; la huella del perfil vincula el conjunto a la fuente revisada. El contrato está en [reference_suite.schema.json](../../schemas/reference_suite.schema.json). Se puede comprobar y mostrar sin consultar al modelo:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.show_reference_cases
```

Ejecutar desde la raíz del proyecto. Véase la [guía 8.1](../../docs/pruebas/referencias-consistencia.md). Los casos se ejecutaron con Ollama local en la [unidad 8.2](../../docs/pruebas/ejecucion-referencias.md); la revisión humana permanece pendiente. Son referencias de desarrollo con preguntas conocidas; no un conjunto independiente reservado para prueba.

No contiene clasificación de preguntas, etiquetas de calidad, rúbrica ni puntuaciones educativas. Esas funciones futuras de la plantilla siguen pendientes y no forman parte de esta unidad.
