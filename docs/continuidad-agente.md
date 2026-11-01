# Continuidad del proyecto — 1 de noviembre de 2026

## Punto de partida

Raíz: `C:\Users\franc\Downloads\Ejemplo_de_proyecto`. Python del proyecto: `.venv/Scripts/python.exe` (3.14.3). Las nueve etapas del agente candidato están completadas en su alcance técnico. La siguiente parte del proyecto todavía debe ser definida por el usuario; no empezar automáticamente clasificación, rúbrica, puntuación, retroalimentación o Godot.

## Fuentes y decisiones que conservar

- Perfil aprobado: `data/candidates/candidato_junior.json`, Nicolás Vera Soto, `cand-001`. Fecha ficticia del escenario **2026-10-20**, independiente de la fecha real.
- Puesto: `data/jobs/desarrollador_junior.json`, Aplicaciones Nexo, Desarrollador de Software Junior.
- Configuración: `config/interviews/basica.json`. Máximo **20 preguntas enviadas**, incluyendo fallos.
- Reglas del candidato: `agent/agent.md`, versión **1.0.11**. No modificar antecedentes aprobados para acomodar respuestas.
- Historial completo guardado en sesiones JSON locales; las respuestas completas alimentan la conversación, los intentos fallidos no. Resumen extractivo opcional en local, con auditoría y registro original conservado.
- Documentación histórica: `docs/estado-etapas.md`, `docs/validacion-final.md`. Su validación de 738 pruebas y veinte preguntas corresponde a esa versión; hubo ampliaciones posteriores.

## Proveedores y último estado confirmado

- Inicio actual: `.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview`.
- Opción 1: Ollama local, selección de modelo del archivo privado; modelo utilizado **gemma4:e4b**. El adaptador local conserva máximo de salida **512**. El predeterminado del adaptador sigue siendo gemma3n:e2b si no hay selección explícita.
- Opción 2: UNAB IA, **gemma4:26b**, `https://quotas.devhub.cl/api/v1/chat/completions`. Adaptador independiente en `harness/llm/unab_client.py`; el adaptador Responses anterior se mantiene separado.
- Configuración privada: `config/llm.local.json`, ignorada por Git. No leer, imprimir, copiar ni pedir su clave para retomar el proyecto. Plantilla pública: `config/llm.local.example.json`.
- UNAB usa **2048 tokens máximos de salida por defecto**, campo opcional `api_max_output_tokens`, rango 16–4096. El selector muestra el presupuesto. No aumentar límites ni repetir generaciones automáticamente.
- Se solicita `reasoning_effort: none`, pero no se ha confirmado su aplicación interna por la pasarela. La ausencia de campos de razonamiento no demuestra ausencia de procesamiento interno.
- Con 512 se observó `finish_reason: length` y contenido vacío. Con 2048 el usuario repitió exactamente la misma pregunta de Flask/PostgreSQL: respuesta completa, **6058 tokens de entrada, 1255 de salida, 7313 totales**, 12,82 s, cero incidencias.
- Evidencia exitosa: `outputs/sessions/session-162df680-88d6-40ca-9e8f-d095fae07025.json`, `outputs/results/unab-usage-162df680-88d6-40ca-9e8f-d095fae07025.json` y `outputs/results/unab-success-confirmation-162df680-88d6-40ca-9e8f-d095fae07025.json`.
- Diagnósticos de uso sin clave, cuerpo bruto ni razonamiento: `outputs/results/unab-usage-<UUID>.json`. No equivaler créditos UNAB a tokens: su fórmula no se conoce. Se reenvían aproximadamente 6000 tokens de contexto por pregunta; no se ha optimizado ese contexto.

## Pruebas y límites de lo comprobado

Última suite completa: **765 passed in 254.13s**. Después se añadieron 17 pruebas de presupuesto y se ejecutaron **109 pruebas relevantes, todas aprobadas en 1,44 s**. Hay 782 disponibles; no afirmar que se ejecutaron juntas las 782. No repetir pruebas o llamadas de pago sin que un cambio o duda lo justifique. Las pruebas automatizadas simulan HTTP. La confirmación real de UNAB cubre una pregunta compleja, no las veinte preguntas difíciles ni consistencia universal.

## Forma de trabajo solicitada

Responder en español, breve y claro. Agrupar trabajo en bloques verificables para reducir vueltas y tokens de chat. Consultar primero archivos concretos; evitar leer registros y todo el repositorio sin necesidad. Mantener la integridad del perfil. Distinguir evidencia, hipótesis y validación técnica de revisión semántica humana. No avanzar de fase sin indicación del usuario. La siguiente tarea debe definirse antes de implementar componentes nuevos.

Esta nota resume el estado a su fecha. Antes de modificar, contrastar los archivos pertinentes y cualquier instrucción posterior del usuario; el historial del chat no reemplaza al código actual. Si hay discrepancias con documentación antigua, indicar qué versión o evidencia se está usando.
