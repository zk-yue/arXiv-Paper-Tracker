# arXiv Paper Tracker

> Find relevant arXiv papers, remove previously reported results, and optionally turn abstracts into structured LLM summaries.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![arXiv API](https://img.shields.io/badge/Data-arXiv-B31B1B?logo=arxiv&logoColor=white)](https://info.arxiv.org/help/api/)

**English** · [简体中文](docs/i18n/README.zh-CN.md) · [日本語](docs/i18n/README.ja.md) · [Español](docs/i18n/README.es.md)

arXiv Paper Tracker is a lightweight, configuration-driven Python tool for recurring literature discovery. It searches titles and abstracts by keyword, filters papers by submission date, deduplicates recent reports, and writes both machine-readable JSON and readable Markdown. An optional OpenAI-compatible API can add structured summaries and research-domain filtering.

```text
arXiv API → date and keyword matching → lookback deduplication → optional LLM analysis → JSON + Markdown
```

![Example daily paper digest delivered through OpenClaw](docs/images/demo.png)

## Features

- Search multiple keywords in arXiv titles and abstracts.
- Query one submission date or an inclusive multi-day window.
- Skip papers already present in recent local JSON reports.
- Generate structured motivation, method, result, and conclusion summaries with an OpenAI-compatible API.
- Use the LLM to classify and optionally remove papers outside a configured research domain.
- Analyze up to five papers concurrently.
- Export complete JSON records and a Markdown digest with arXiv and PDF links.
- Inspect updates for any arXiv category and connect reports to scheduled delivery through OpenClaw.

## Quick start

### Requirements

- Python 3.10 or later
- Git and network access to arXiv
- Optional: credentials for an OpenAI-compatible chat completions endpoint

### Install

```bash
git clone https://github.com/zk-yue/arXiv-Paper-Tracker.git
cd arXiv-Paper-Tracker

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Configure

```bash
cp config.example.json config.json
```

Edit `config.json` before running the tracker:

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

`config.json` is ignored by Git. Never commit API keys. To use the `LLM_API_KEY` environment variable instead, remove the `api_key` field from the `llm` object; when that field exists, its value takes precedence over the environment variable.

### Run

Run commands from the repository root so the program can find `config.json` and `results/`.

```bash
# Search papers submitted today without LLM analysis
python arxiv_search.py

# Search 2026-06-23 and the three preceding days, then analyze matches
python arxiv_search.py --date 2026-06-23 --date-range 3 --llm

# Analyze only the first matched paper while testing LLM configuration
python arxiv_search.py --date 2026-06-23 --llm --test

# Check the last seven days of updates in the Robotics category
python check_arxiv_update.py --category cs.RO
```

## Configuration reference

| Field | Type | Description |
| --- | --- | --- |
| `keywords` | string array | Terms matched case-insensitively in paper titles and abstracts. |
| `max_results` | integer | Maximum number of results requested from arXiv before local filtering. |
| `sort_by` | string | `submittedDate`, `relevance`, or `lastUpdatedDate`. |
| `save_format` | string | Reserved setting; the current implementation always writes JSON and Markdown. |
| `domain_filter.enabled` | boolean | Ask the LLM whether each paper belongs to `domain`. Requires `--llm`. |
| `domain_filter.domain` | string | Target field, such as `Robotics`, `NLP`, or `Computer Vision`. |
| `domain_filter.filter_out_non_domain` | boolean | Remove papers that the LLM classifies outside the target field. |
| `llm.api_key` | string | API credential. Remove this field to fall back to `LLM_API_KEY`. |
| `llm.api_base` | string | Base URL of an OpenAI-compatible API, without `/chat/completions`. |
| `llm.model` | string | Model identifier accepted by the configured endpoint. |

The current analysis prompt and generated report headings are in Chinese, regardless of the README language. The endpoint must accept `POST {api_base}/chat/completions` with OpenAI-style `messages`.

## Command-line reference

### Paper search

```text
python arxiv_search.py [-d DATE] [-l] [-t]
                       [--date-range DAYS] [--dedup-days DAYS]
```

| Option | Meaning |
| --- | --- |
| `-d, --date YYYY-MM-DD` | End date of the search window; defaults to today. |
| `-l, --llm` | Enable LLM analysis. An API key is required. |
| `-t, --test` | Analyze only the first matched paper; meaningful with `--llm`. |
| `--date-range DAYS` | Include this many preceding calendar days. `3` searches four dates in total. Default: `0`. |
| `--dedup-days DAYS` | Look back through this many days of JSON reports for already reported arXiv IDs. Default: `7`. |

Deduplication uses the arXiv ID from stored URLs, including its version suffix. It only reads JSON files in `results/` whose filenames start with a date in `YYYYMMDD` format.

### Update checker

```text
python check_arxiv_update.py [-c CATEGORY] [-d DATE]
```

`--category` defaults to `cs.RO`. Without `--date`, the command checks each of the last seven calendar days; with `--date`, it checks only that day.

## Output

Each run writes to `results/`:

| Path pattern | Contents |
| --- | --- |
| `results/YYYYMMDD_<keywords>.json` | Search metadata and complete paper records for downstream processing. |
| `results/YYYY-MM-DD_report.md` | Human-readable digest with metadata, links, and summaries or abstract excerpts. |

If no paper matches, the tracker still writes an empty JSON result and Markdown report. When domain filtering removes every paper after LLM analysis, the current implementation skips the Markdown report.

## Automation and OpenClaw

[`install_cron.sh`](install_cron.sh) installs a daily 09:00 cron entry. Review it before running: it assumes a Conda environment named `arxiv` under `~/anaconda3`, and it replaces existing crontab lines containing `arxiv_search.py`. Adjust the paths, environment, schedule, and optional `--llm` flag for your machine.

For scheduled digests delivered to Feishu, Discord, or Telegram, see the [OpenClaw integration guide](docs/openclaw-integration.md). The tracker itself creates local report files; message delivery is handled by OpenClaw.

## Project layout

```text
arXiv-Paper-Tracker/
├── arxiv_search.py              # Search, deduplication, LLM analysis, and export
├── check_arxiv_update.py        # Category update checker
├── config.example.json          # Safe configuration template
├── install_cron.sh              # Opinionated cron installer for Conda
├── requirements.txt             # Python dependencies
├── docs/
│   ├── i18n/                    # Translated README files
│   ├── images/demo.png          # Example delivered digest
│   └── openclaw-integration.md  # OpenClaw scheduling and delivery guide
└── results/                     # Generated locally; ignored by Git
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| No results | Confirm the date and keywords. arXiv may have no submissions on weekends or holidays, and indexing can be delayed. |
| HTTP 429 | Wait and retry, reduce broad keyword queries, or lower `max_results`. The client already uses delays and retries. |
| LLM analysis is skipped | Pass `--llm` and verify how `llm.api_key` or `LLM_API_KEY` is resolved. |
| LLM request fails | Confirm the base URL, model identifier, API compatibility, quota, and network access. Failed analysis keeps the paper. |
| Duplicate paper remains | Versioned IDs such as `v1` and `v2` are treated as different IDs. Also check `--dedup-days` and prior JSON filenames. |

## Contributing

Issues and pull requests are welcome. For a change:

1. Fork the repository and create a focused branch.
2. Keep behavior and all four README versions consistent.
3. Run `python arxiv_search.py --help` and `python check_arxiv_update.py --help`; test searches responsibly against the public API.
4. Open a pull request that explains the motivation, behavior change, and verification performed.

Please avoid committing `config.json`, generated reports, credentials, or personal delivery identifiers.

## License

Released under the [MIT License](LICENSE).

## Acknowledgements

- [arXiv](https://arxiv.org/) for open access to scholarly papers and its public API.
- [arxiv.py](https://github.com/lukasschwab/arxiv.py) for the Python API client.
- [OpenClaw](https://github.com/zk-yue/OpenClaw) for optional scheduling and multi-channel delivery.
