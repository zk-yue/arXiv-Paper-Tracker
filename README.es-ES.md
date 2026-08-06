

# arXiv Paper Tracker

Búsqueda automática de artículos de arXiv, con soporte para búsqueda por palabras clave, filtrado por fecha y análisis inteligente mediante LLM.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-API-orange.svg)](https://arxiv.org)

> Utilícelo junto con [OpenClaw](https://github.com/zk-yue/OpenClaw) para enviar automáticamente los informes de artículos diarios a Feishu, Discord y Telegram.

## Funcionalidades

| Funcionalidad | Descripción |
|------|------|
| Búsqueda por palabras clave | Busca palabras clave en el título y el resumen |
| Filtrado por fecha | Filtra por fecha de envío, admite expansión de rango de fechas |
| Duplicación automática | Filtra automáticamente artículos ya reportados |
| Análisis LLM | Generación de resúmenes estructurados mediante IA (Motivación/Método/Resultados/Conclusiones) |
| Filtrado por área | Filtrado automático por área de investigación (Robotics/NLP/CV, etc.) |
| Procesamiento paralelo | Análisis paralelo con hasta 5 trabajadores |
| Generación de informes | Generación automática de informes en formato Markdown |

## Inicio Rápido

### Instalación

```bash
git clone https://github.com/zk-yue/arXiv-Paper-Tracker.git
cd arXiv-Paper-Tracker
pip install -r requirements.txt
```

### Configuración

```bash
cp config.example.json config.json
```

Edita `config.json`:

```json
{
  "keywords": ["Deep Learning", "Transformer", "Large Language Model"],
  "max_results": 100,
  "sort_by": "submittedDate",
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

O establece la variable de entorno: `export LLM_API_KEY="your-api-key"`

### Uso

```bash
# Buscar artículos del día actual
python arxiv_search.py

# Buscar artículos de una fecha específica y los 3 días anteriores, con análisis LLM
python arxiv_search.py -d 2026-03-17 --date-range 3 -l

# Modo prueba: solo analiza el primer artículo
python arxiv_search.py -d 2026-03-17 -l -t

# Verificar el estado de actualización de arXiv
python check_arxiv_update.py -c cs.RO
```

## Opciones de Línea de Comandos

| Opción | Descripción |
|------|------|
| `-d, --date` | Especifica la fecha (YYYY-MM-DD, por defecto el día actual) |
| `-l, --llm` | Habilita el análisis LLM |
| `-t, --test` | Modo prueba: solo analiza el primer artículo |
| `--date-range` | Días para expandir el rango de fechas |
| `--dedup-days` | Días de retroceso para la deduplicación (por defecto 7) |

## Configuración de LLM

Compatible con APIs compatibles con OpenAI, ejemplos:

| Proveedor | `api_base` | `model` |
|----------|------------|---------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Alibaba Cloud DashScope | `https://coding.dashscope.aliyuncs.com/v1` | `qwen3.5-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |

## Integración con OpenClaw

Este proyecto se puede combinar con [OpenClaw](https://github.com/zk-yue/OpenClaw) para lograr实现:

- **Envío programado** - Envía automáticamente los informes diarios de artículos a Feishu, Discord y Telegram.
- **Descarga de artículos** - Descarga automáticamente los archivos PDF de los artículos coincidentes.
- **Resumen inteligente** - Genera y envía automáticamente resúmenes de artículos impulsados por IA según un horario.

Para una configuración detallada, consulta la [Guía de integración de OpenClaw](docs/openclaw-integration.md).

## Tareas programadas

```bash
./install_cron.sh  # Programa la ejecución automática todos los días a las 9:00
```

## Salida

- `results/*.json` - Resultados en formato JSON
- `results/*_report.md` - Informes en formato Markdown

## Estructura del proyecto

```
arXiv-Paper-Tracker/
├── arxiv_search.py          # Programa principal
├── check_arxiv_update.py    # Herramienta de verificación de actualizaciones de arXiv
├── config.json              # Archivo de configuración (debe crearse manualmente)
├── config.example.json      # Plantilla de archivo de configuración
├── requirements.txt         # Dependencias de Python
├── install_cron.sh          # Script de instalación de tareas programadas
├── docs/                    # Documentación
└── results/                 # Directorio de salida
```

## Licencia

Licencia MIT - Consulta [LICENSE](LICENSE) para más detalles.

## Agradecimientos

- [arXiv](https://arxiv.org/) - Acceso abierto a artículos académicos
- [arxiv.py](https://github.com/lukasschwab/arxiv.py) - Envoltorio Python para la API de arXiv
