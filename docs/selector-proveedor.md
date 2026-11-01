# Elegir Ollama o UNAB IA desde la terminal

Ante consumo con respuestas rechazadas, consultar el [diagnóstico de salidas vacías y uso](pruebas/unab-consumo-y-salidas-vacias.md). El adaptador solicita ahora `reasoning_effort: none`, solicita un máximo configurable de 2048 tokens de salida y guarda métricas permitidas de las llamadas en un archivo separado al cerrar; su aplicación por UNAB requiere verificación real.

La ampliación añade un menú inicial. Reutiliza el candidato, historial y guardado existentes. El proveedor UNAB usa el protocolo Chat Completions; el adaptador Responses anterior conserva su funcionamiento independiente.

## Clave privada

El archivo local `config/llm.local.json` ya está creado con estos campos:

```json
{
  "local_model": "gemma4:e4b",
  "api_model": "gemma4:26b",
  "api_max_output_tokens": 2048,
  "api_key": ""
}
```

Escribir la clave entre las comillas de `api_key` y guardar. No pegarla en el chat. El archivo no se incorpora a Git; `config/llm.local.example.json` es la plantilla sin credenciales. La exclusión de Git no cifra el archivo: al compartir una copia o ZIP del proyecto hay que excluir `config/llm.local.json`.

Para abrirlo desde la raíz del proyecto:

```powershell
notepad .\config\llm.local.json
```

## Inicio

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview
```

El menú ofrece:

1. Modelo local — Ollama. Enter también selecciona esta opción. Funciona con la clave vacía, desactiva la API y activa la política normal de memoria extractiva.
2. API — UNAB IA. Esta selección autoriza el envío del escenario interno y la conversación al servicio externo para esa ejecución. Requiere la clave y usa `gemma4:26b`.

Después se conserva el menú `/cv`, `/puesto`, `/iniciar`, `/sesion`, `/salir`. No hace falta definir variables de entorno manualmente. La selección se aplica al proceso de entrevista, sin cambiar permanentemente el entorno de PowerShell. No se cambia de proveedor automáticamente si hay un error.

La URL está fijada en `https://quotas.devhub.cl/api/v1/`, con solicitud a `chat/completions`. La clave viaja en la cabecera Bearer, no en argumentos de terminal, configuración pública del cliente ni sesiones. Se usan TLS, redirecciones desactivadas y errores sin copiar cuerpos del servidor. No se instalan dependencias nuevas.

La API recibe el historial completo. No se supone una capacidad de contexto del servicio remoto ni se activa automáticamente el resumen con una capacidad inventada. El inicio anterior `scripts.run_interview` sigue disponible con sus opciones existentes.

## Estado de verificación

Las 21 pruebas nuevas usan respuestas HTTP simuladas: formato del endpoint, autenticación, salidas inválidas, límite de salida, errores y timeout sin repetir generación; selector, configuración inválida y guardado sin claves. No se ha utilizado una clave real ni se ha certificado la compatibilidad del servidor desplegado. La configuración facilitada por el usuario indica compatibilidad OpenAI; la consulta pública al endpoint no permitió obtener documentación. Si el servicio devuelve un error de endpoint o modelo, conservar su código y revisar el protocolo sin publicar la clave.

Verificación final: **759 passed in 59.65s**, incluidas las 21 comprobaciones nuevas. Perfil, puesto, configuración de entrevista e instrucciones mantienen sus huellas aprobadas. La llamada real a UNAB IA queda pendiente de que el usuario configure su clave y seleccione la opción 2.

El campo api_max_output_tokens es opcional: el archivo previo funciona con 2048 por defecto, sin modificar la clave. Solo afecta a UNAB; se muestra al elegir la opción 2. Rango admitido 16–4096. El usuario confirmó una pregunta compleja con presupuesto 2048: respuesta completa, 1255 tokens de salida y cero incidencias. Véase el diagnóstico enlazado al inicio; no se extrapola a todas las preguntas.
