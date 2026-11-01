# Etapa 8.1: preparar referencias para revisar la consistencia

Esta unidad define preguntas y hechos esperados antes de ejecutar pruebas del candidato. Permite detectar casos mal construidos, referencias inexistentes y discrepancias con el escenario aprobado. No consulta a Ollama ni a la API externa, no genera respuestas y no emite un veredicto automático sobre ellas.

## Archivos y responsabilidades

| Archivo | Función |
| --- | --- |
| [consistencia_basica.json](../../data/reference_questions/consistencia_basica.json) | Cuatro casos, cinco preguntas, referencias a hechos y notas de revisión humana. |
| [reference_suite.schema.json](../../schemas/reference_suite.schema.json) | Contrato de estructura y tipos, con versión 1.0.0. |
| [reference_cases.py](../../harness/reference_cases.py) | Carga estricta, correspondencia con el escenario, resolución de referencias y copias independientes. |
| [show_reference_cases.py](../../scripts/show_reference_cases.py) | Comando de lectura que presenta preguntas y hechos resueltos. |
| [Pruebas unitarias](../../tests/unit/test_reference_cases.py) y [de integración](../../tests/integration/test_reference_suite_flow.py) | Verifican contratos, fuentes, errores y conservación de archivos. |

Se usan las dependencias existentes: biblioteca estándar de Python, `jsonschema` y `pytest` para comprobar. No hay instalaciones nuevas.

## Fuente de los hechos

El conjunto identifica candidato, puesto y fecha de referencia **2026-10-20**. Fija la huella SHA-256 de los bytes del perfil revisado, para que una modificación posterior exija revisar también los casos. No conserva una segunda copia manual de los antecedentes esperados.

Cada hecho indica `candidate_profile` o `temporal_facts` y una lista explícita de claves e índices. El cargador obtiene los valores del perfil protegido o de los cálculos de `build_temporal_facts`. No interpreta esas listas como rutas de archivos, código o instrucciones. La huella del conjunto se calcula sobre los mismos bytes utilizados para leerlo.

Se comprueba la estructura, los identificadores y la fecha del escenario, la huella del perfil, unicidad de casos/hechos, numeración consecutiva, referencias utilizadas y límite de preguntas por caso. Los casos se devuelven como copias independientes. La detección de errores no repara ni sobrescribe las fuentes.

## Casos preparados

| Caso | Preguntas | Hechos que se revisarán |
| --- | --- | --- |
| Formación | ¿Dónde estudiaste y qué título obtuviste? | Instituto Profesional Horizonte Digital; Ingeniería en Informática. |
| Duración | ¿Cuántos meses trabajaste en total, incluyendo la práctica? | 21 meses calendario distintos: 3 de práctica y 18 posteriores. |
| Continuidad | Menciona tu proyecto académico. → ¿Cómo se llamaba el proyecto de tu primera respuesta? | Inventario Aula, académico; referencia conservada en la repregunta. |
| Límite de experiencia | ¿Has utilizado Kubernetes en un proyecto profesional? | Reconocer ausencia de experiencia práctica con Kubernetes. |

`required_content` identifica contenido esperado y `consistency_constraint` un límite de lo que puede afirmarse. El valor `null` de equivalencia laboral a jornada completa significa que no puede calcularse con los datos disponibles; no exige que el candidato pronuncie «null». Los 21 meses no deben presentarse como 21 meses a jornada completa.

Se permiten paráfrasis compatibles; las denominaciones y cantidades conservan sus hechos. Si falta el desglose de práctica/junior pero el total es correcto, se registra una omisión de detalle, sin declararla automáticamente contradicción. En continuidad, si la primera respuesta fue incorrecta, una corrección explícita debe distinguirse de un cambio injustificado de referencia. No hay comparación automática de subcadenas, puntuación educativa o juez LLM.

El contrato establece una **sesión nueva por caso** y pasos compartidos dentro del caso. En esta unidad esa regla está declarada y validada; todavía no hay un ejecutor que la aplique a llamadas reales. Son referencias de desarrollo que reutilizan preguntas conocidas, no una prueba independiente del ajuste previo.

## Comprobación en PowerShell

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.show_reference_cases
```

El segundo comando debe indicar **Casos: 4. Entradas de pregunta: 5.**, mostrar los valores de la tabla y terminar con «Casos preparados. Ejecuciones y revisión de respuestas pendientes». No requiere iniciar Ollama ni configurar un proveedor.

Si aparece `No module named scripts`, comprobar la carpeta actual y utilizar el Python de `.venv`. Ante una discrepancia de huella o referencia, conservar la salida y revisar el archivo y el escenario; no editar el perfil aprobado para forzar que la prueba pase. Un cambio de formato también altera una huella, aunque no cambien los hechos.

Las 40 pruebas nuevas pasaron con **40 passed in 3.69s**. La suite completa terminó con **730 passed in 45.44s**: 687 unitarias y 43 integraciones. La [evidencia de preparación](../../outputs/results/reference-suite-da11e781799f4ef6ba7331f1964e0e39.json) conserva el listado y los hashes antes/después de los cuatro originales y siete sesiones existentes, sin cambios. Son comprobaciones técnicas de preparación; la ejecución y revisión de respuestas reales se realizarán después de la confirmación del usuario. La Etapa 8 permanece en curso.
