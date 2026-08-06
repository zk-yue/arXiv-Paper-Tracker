# arXiv Paper Tracker

> 自动发现相关 arXiv 论文、过滤近期已汇报结果，并可选择将摘要转换为结构化 LLM 分析。

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../../LICENSE)
[![arXiv API](https://img.shields.io/badge/Data-arXiv-B31B1B?logo=arxiv&logoColor=white)](https://info.arxiv.org/help/api/)

[English](../../README.md) · **简体中文** · [日本語](README.ja.md) · [Español](README.es.md)

arXiv Paper Tracker 是一个轻量、配置驱动的 Python 文献追踪工具。它可以按关键词搜索论文标题和摘要，按提交日期筛选，排除近期报告中已经出现的论文，并同时生成机器可读的 JSON 与适合阅读的 Markdown 报告。还可以接入兼容 OpenAI 格式的 API，生成结构化论文总结并执行研究领域过滤。

```text
arXiv API → 日期与关键词匹配 → 历史报告去重 → 可选 LLM 分析 → JSON + Markdown
```

![通过 OpenClaw 推送的每日论文简报示例](../images/demo.png)

## 功能特性

- 在 arXiv 论文标题和摘要中搜索多个关键词。
- 检索单个提交日期或包含起止日期的多日窗口。
- 根据近期本地 JSON 报告过滤已经汇报过的论文。
- 通过兼容 OpenAI 格式的 API，生成动机、方法、结果和结论等结构化总结。
- 使用 LLM 判断论文所属研究领域，并可移除目标领域之外的论文。
- 最多并行分析 5 篇论文。
- 导出完整 JSON 数据，以及包含 arXiv、PDF 链接的 Markdown 简报。
- 查询任意 arXiv 分类的更新情况，并通过 OpenClaw 定时推送报告。

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- Git，以及访问 arXiv 的网络环境
- 可选：兼容 OpenAI Chat Completions 接口的 API 凭证

### 安装

```bash
git clone https://github.com/zk-yue/arXiv-Paper-Tracker.git
cd arXiv-Paper-Tracker

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 配置

```bash
cp config.example.json config.json
```

运行前编辑 `config.json`：

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

`config.json` 已被 Git 忽略，请勿提交 API 密钥。如果希望改用环境变量 `LLM_API_KEY`，需要从 `llm` 对象中删除 `api_key` 字段；只要该字段存在，它的值就会优先于环境变量。

### 运行

请在仓库根目录执行命令，以便程序正确找到 `config.json` 和 `results/`。

```bash
# 检索今天提交的论文，不启用 LLM 分析
python arxiv_search.py

# 检索 2026-06-23 及其之前 3 天，并分析匹配论文
python arxiv_search.py --date 2026-06-23 --date-range 3 --llm

# 测试 LLM 配置时只分析第一篇匹配论文
python arxiv_search.py --date 2026-06-23 --llm --test

# 检查 Robotics 分类过去 7 天的更新情况
python check_arxiv_update.py --category cs.RO
```

## 配置参考

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `keywords` | 字符串数组 | 在标题和摘要中进行不区分大小写匹配的关键词。 |
| `max_results` | 整数 | 本地过滤之前，向 arXiv 请求的最大结果数。 |
| `sort_by` | 字符串 | 可选值：`submittedDate`、`relevance`、`lastUpdatedDate`。 |
| `save_format` | 字符串 | 预留字段；当前实现始终生成 JSON 和 Markdown。 |
| `domain_filter.enabled` | 布尔值 | 让 LLM 判断论文是否属于 `domain`；需要同时使用 `--llm`。 |
| `domain_filter.domain` | 字符串 | 目标领域，例如 `Robotics`、`NLP` 或 `Computer Vision`。 |
| `domain_filter.filter_out_non_domain` | 布尔值 | 移除被 LLM 判断为不属于目标领域的论文。 |
| `llm.api_key` | 字符串 | API 凭证。删除该字段后才会回退到 `LLM_API_KEY`。 |
| `llm.api_base` | 字符串 | 兼容 OpenAI 格式的 API 根地址，不包含 `/chat/completions`。 |
| `llm.model` | 字符串 | 配置的接口所接受的模型标识。 |

当前分析提示词和生成报告的标题均为中文，与 README 所选语言无关。接口必须支持通过 `POST {api_base}/chat/completions` 接收 OpenAI 风格的 `messages`。

## 命令行参考

### 论文检索

```text
python arxiv_search.py [-d DATE] [-l] [-t]
                       [--date-range DAYS] [--dedup-days DAYS]
```

| 选项 | 含义 |
| --- | --- |
| `-d, --date YYYY-MM-DD` | 检索窗口的结束日期，默认为当天。 |
| `-l, --llm` | 启用 LLM 分析，需要配置 API 密钥。 |
| `-t, --test` | 只分析第一篇匹配论文；与 `--llm` 一起使用才有意义。 |
| `--date-range DAYS` | 向前包含的日历天数。设置为 `3` 时实际检索 4 个日期。默认：`0`。 |
| `--dedup-days DAYS` | 在此前多少天的 JSON 报告中查找已汇报 arXiv ID。默认：`7`。 |

去重使用已保存 URL 中包含版本后缀的 arXiv ID。程序只读取 `results/` 中以 `YYYYMMDD` 日期开头的 JSON 文件。

### 更新检查

```text
python check_arxiv_update.py [-c CATEGORY] [-d DATE]
```

`--category` 默认为 `cs.RO`。不指定 `--date` 时会逐日检查最近 7 个日历日；指定后只检查对应日期。

## 输出

每次执行都会在 `results/` 下生成：

| 路径格式 | 内容 |
| --- | --- |
| `results/YYYYMMDD_<keywords>.json` | 检索元数据和完整论文记录，适合后续程序处理。 |
| `results/YYYY-MM-DD_report.md` | 包含元数据、链接、结构化分析或摘要节选的可读简报。 |

没有匹配论文时，程序仍会生成空的 JSON 结果和 Markdown 报告。如果启用领域过滤后所有论文都被 LLM 移除，当前实现会跳过 Markdown 报告。

## 自动化与 OpenClaw

[`install_cron.sh`](../../install_cron.sh) 会安装一个每天 09:00 执行的 cron 任务。运行前请先检查脚本：它默认使用 `~/anaconda3` 下名为 `arxiv` 的 Conda 环境，并会替换 crontab 中已有的、包含 `arxiv_search.py` 的行。请根据本机情况修改路径、环境、执行时间，以及是否添加 `--llm`。

如需将定时简报推送到飞书、Discord 或 Telegram，请阅读 [OpenClaw 集成指南](../openclaw-integration.md)。本项目只生成本地报告文件，消息推送由 OpenClaw 完成。

## 项目结构

```text
arXiv-Paper-Tracker/
├── arxiv_search.py              # 检索、去重、LLM 分析与导出
├── check_arxiv_update.py        # 分类更新检查工具
├── config.example.json          # 不含隐私信息的配置模板
├── install_cron.sh              # 面向 Conda 环境的 cron 安装脚本
├── requirements.txt             # Python 依赖
├── docs/
│   ├── i18n/                    # 多语言 README
│   ├── images/demo.png          # 推送简报示例
│   └── openclaw-integration.md  # OpenClaw 定时与推送指南
└── results/                     # 本地生成，已被 Git 忽略
```

## 故障排查

| 现象 | 排查建议 |
| --- | --- |
| 没有检索结果 | 检查日期和关键词。arXiv 在周末或节假日可能没有新提交，索引也可能延迟。 |
| HTTP 429 | 等待后重试、缩小关键词范围或降低 `max_results`；客户端已经内置延迟和重试。 |
| 跳过 LLM 分析 | 确认使用了 `--llm`，并检查 `llm.api_key` 或 `LLM_API_KEY` 的实际取值方式。 |
| LLM 请求失败 | 检查根地址、模型标识、接口兼容性、额度和网络。分析失败时论文仍会保留。 |
| 仍然出现重复论文 | `v1` 与 `v2` 等版本会被视为不同 ID；同时检查 `--dedup-days` 和历史 JSON 文件名。 |

## 参与贡献

欢迎提交 Issue 和 Pull Request。建议流程如下：

1. Fork 仓库并创建目标明确的分支。
2. 保持程序行为与四种语言 README 内容一致。
3. 执行 `python arxiv_search.py --help` 和 `python check_arxiv_update.py --help`；测试检索时请合理使用公共 API。
4. 在 Pull Request 中说明修改动机、行为变化和验证方式。

请勿提交 `config.json`、生成的报告、API 凭证或个人推送目标标识。

## 许可证

本项目基于 [MIT License](../../LICENSE) 发布。

## 致谢

- [arXiv](https://arxiv.org/)：提供开放获取的学术论文与公共 API。
- [arxiv.py](https://github.com/lukasschwab/arxiv.py)：提供 Python API 客户端。
- [OpenClaw](https://github.com/zk-yue/OpenClaw)：提供可选的定时任务与多渠道推送能力。
