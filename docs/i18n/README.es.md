# arXiv Paper Tracker

> Encuentra artículos relevantes en arXiv, descarta resultados ya incluidos en informes y, de forma opcional, convierte los resúmenes en análisis estructurados con un LLM.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../../LICENSE)
[![arXiv API](https://img.shields.io/badge/Data-arXiv-B31B1B?logo=arxiv&logoColor=white)](https://info.arxiv.org/help/api/)

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · **Español**

arXiv Paper Tracker es una herramienta ligera en Python, controlada mediante configuración, para descubrir bibliografía de forma recurrente. Busca palabras clave en títulos y resúmenes, filtra por fecha de envío, elimina duplicados de informes recientes y produce tanto JSON procesable como informes Markdown fáciles de leer. También puede conectarse a una API compatible con OpenAI para añadir resúmenes estructurados y filtrado por área de investigación.

```text
API de arXiv → coincidencia por fecha y palabras clave → deduplicación → análisis LLM opcional → JSON + Markdown
```

![Ejemplo de un resumen diario distribuido mediante OpenClaw](../images/demo.png)

## Funcionalidades

- Busca varias palabras clave en los títulos y resúmenes de arXiv.
- Consulta una fecha de envío o un intervalo inclusivo de varios días.
- Omite los artículos presentes en informes JSON locales recientes.
- Genera resúmenes estructurados de motivación, método, resultados y conclusiones mediante una API compatible con OpenAI.
- Usa el LLM para clasificar los artículos por área y, opcionalmente, eliminar los que no pertenezcan al área configurada.
- Analiza hasta cinco artículos en paralelo.
- Exporta registros JSON completos y un informe Markdown con enlaces a arXiv y al PDF.
- Comprueba las actualizaciones de cualquier categoría de arXiv y permite distribuir informes programados mediante OpenClaw.

## Inicio rápido

### Requisitos

- Python 3.10 o posterior
- Git y acceso de red a arXiv
- Opcional: credenciales para un endpoint de Chat Completions compatible con OpenAI

### Instalación

```bash
git clone https://github.com/zk-yue/arXiv-Paper-Tracker.git
cd arXiv-Paper-Tracker

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Configuración

```bash
cp config.example.json config.json
```

Edita `config.json` antes de ejecutar el programa:

```json
{
  "keywords": ["Deep Learning", "Transformer", "Large Language Model"],
  "max_results": 100,
  "sort_by": "submittedDate",
  "save_format": "json",
  "domain_filter": {
    "enabled": false,
    "domain": "Robotics",
    "filter_out_non_domain": true
  },
  "llm": {
    "api_key": "YOUR_API_KEY",
    "api_base": "https://api.deepseek.com",
    "model": "deepseek-chat"
  }
}
```

Git ignora `config.json`. No confirmes nunca claves de API. Para usar la variable de entorno `LLM_API_KEY`, elimina el campo `api_key` del objeto `llm`; mientras exista ese campo, su valor tiene prioridad sobre la variable de entorno.

### Ejecución

Ejecuta los comandos desde la raíz del repositorio para que el programa encuentre `config.json` y `results/`.

```bash
# Buscar artículos enviados hoy sin análisis LLM
python arxiv_search.py

# Buscar el 2026-06-23 y los tres días anteriores, y analizar las coincidencias
python arxiv_search.py --date 2026-06-23 --date-range 3 --llm

# Analizar solo el primer artículo al probar la configuración del LLM
python arxiv_search.py --date 2026-06-23 --llm --test

# Comprobar los últimos siete días de la categoría Robotics
python check_arxiv_update.py --category cs.RO
```

## Referencia de configuración

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `keywords` | lista de cadenas | Términos buscados sin distinguir mayúsculas y minúsculas en títulos y resúmenes. |
| `max_results` | entero | Número máximo de resultados solicitados a arXiv antes del filtrado local. |
| `sort_by` | cadena | `submittedDate`, `relevance` o `lastUpdatedDate`. |
| `save_format` | cadena | Ajuste reservado; la implementación actual siempre escribe JSON y Markdown. |
| `domain_filter.enabled` | booleano | Pide al LLM que determine si cada artículo pertenece a `domain`. Requiere `--llm`. |
| `domain_filter.domain` | cadena | Área objetivo, por ejemplo `Robotics`, `NLP` o `Computer Vision`. |
| `domain_filter.filter_out_non_domain` | booleano | Elimina los artículos que el LLM clasifique fuera del área objetivo. |
| `llm.api_key` | cadena | Credencial de la API. Elimina el campo para recurrir a `LLM_API_KEY`. |
| `llm.api_base` | cadena | URL base de una API compatible con OpenAI, sin `/chat/completions`. |
| `llm.model` | cadena | Identificador de modelo aceptado por el endpoint configurado. |

El prompt de análisis y los encabezados de los informes generados están actualmente en chino, independientemente del idioma del README. El endpoint debe aceptar `POST {api_base}/chat/completions` con `messages` al estilo de OpenAI.

## Referencia de la línea de comandos

### Búsqueda de artículos

```text
python arxiv_search.py [-d DATE] [-l] [-t]
                       [--date-range DAYS] [--dedup-days DAYS]
```

| Opción | Significado |
| --- | --- |
| `-d, --date YYYY-MM-DD` | Fecha final del intervalo de búsqueda; por defecto es hoy. |
| `-l, --llm` | Activa el análisis LLM. Se necesita una clave de API. |
| `-t, --test` | Analiza solo el primer artículo coincidente; resulta útil junto con `--llm`. |
| `--date-range DAYS` | Incluye este número de días naturales anteriores. `3` busca cuatro fechas en total. Valor predeterminado: `0`. |
| `--dedup-days DAYS` | Días de informes JSON anteriores que se revisan para encontrar identificadores de arXiv ya incluidos. Valor predeterminado: `7`. |

La deduplicación usa el identificador de arXiv de las URL guardadas, incluido el sufijo de versión. Solo lee archivos JSON de `results/` cuyos nombres comienzan con una fecha en formato `YYYYMMDD`.

### Comprobación de actualizaciones

```text
python check_arxiv_update.py [-c CATEGORY] [-d DATE]
```

El valor predeterminado de `--category` es `cs.RO`. Sin `--date`, el comando revisa por separado cada uno de los últimos siete días naturales; con `--date`, revisa solo ese día.

## Salida

Cada ejecución escribe en `results/`:

| Patrón de ruta | Contenido |
| --- | --- |
| `results/YYYYMMDD_<keywords>.json` | Metadatos de búsqueda y registros completos para procesamiento posterior. |
| `results/YYYY-MM-DD_report.md` | Informe legible con metadatos, enlaces y análisis o fragmentos de los resúmenes. |

Si no hay coincidencias, el programa genera igualmente un resultado JSON vacío y un informe Markdown. Si el filtro de área del LLM elimina todos los artículos, la implementación actual omite el informe Markdown.

## Automatización y OpenClaw

[`install_cron.sh`](../../install_cron.sh) instala una entrada cron diaria a las 09:00. Revísalo antes de ejecutarlo: presupone un entorno Conda llamado `arxiv` dentro de `~/anaconda3` y reemplaza las líneas existentes del crontab que contengan `arxiv_search.py`. Adapta las rutas, el entorno, el horario y el indicador opcional `--llm` a tu equipo.

Para distribuir informes programados por Feishu, Discord o Telegram, consulta la [guía de integración con OpenClaw](../openclaw-integration.md). El tracker crea archivos de informe locales; OpenClaw se encarga de enviar los mensajes.

## Estructura del proyecto

```text
arXiv-Paper-Tracker/
├── arxiv_search.py              # Búsqueda, deduplicación, análisis LLM y exportación
├── check_arxiv_update.py        # Comprobador de actualizaciones por categoría
├── config.example.json          # Plantilla de configuración segura
├── install_cron.sh              # Instalador de cron preparado para Conda
├── requirements.txt             # Dependencias de Python
├── docs/
│   ├── i18n/                    # Versiones traducidas del README
│   ├── images/demo.png          # Ejemplo de informe distribuido
│   └── openclaw-integration.md  # Guía de programación y distribución con OpenClaw
└── results/                     # Generado localmente e ignorado por Git
```

## Solución de problemas

| Síntoma | Qué comprobar |
| --- | --- |
| No hay resultados | Comprueba la fecha y las palabras clave. arXiv puede no tener envíos en fines de semana o festivos, y la indexación puede retrasarse. |
| HTTP 429 | Espera y vuelve a intentarlo, reduce las consultas demasiado amplias o disminuye `max_results`. El cliente ya incorpora pausas y reintentos. |
| Se omite el análisis LLM | Incluye `--llm` y comprueba cómo se resuelve `llm.api_key` o `LLM_API_KEY`. |
| Falla la petición al LLM | Comprueba la URL base, el modelo, la compatibilidad de la API, la cuota y la red. El artículo se conserva si falla el análisis. |
| Sigue apareciendo un duplicado | Versiones como `v1` y `v2` se tratan como identificadores distintos. Comprueba también `--dedup-days` y los nombres de los JSON anteriores. |

## Contribuir

Los issues y pull requests son bienvenidos. Para proponer un cambio:

1. Haz un fork del repositorio y crea una rama con un objetivo concreto.
2. Mantén coherentes el comportamiento y las cuatro versiones del README.
3. Ejecuta `python arxiv_search.py --help` y `python check_arxiv_update.py --help`; prueba las búsquedas de forma responsable contra la API pública.
4. Abre un pull request que explique la motivación, el cambio de comportamiento y las verificaciones realizadas.

No incluyas `config.json`, informes generados, credenciales ni identificadores personales de destino.

## Licencia

Publicado bajo la [licencia MIT](../../LICENSE).

## Agradecimientos

- [arXiv](https://arxiv.org/) por el acceso abierto a publicaciones académicas y su API pública.
- [arxiv.py](https://github.com/lukasschwab/arxiv.py) por el cliente de API para Python.
- [OpenClaw](https://github.com/zk-yue/OpenClaw) por la programación y distribución multicanal opcionales.
