# arXiv Paper Tracker

自动检索 arXiv 论文，支持关键词搜索、日期过滤、LLM 智能分析

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-API-orange.svg)](https://arxiv.org)

> 配合 [OpenClaw](https://github.com/zk-yue/OpenClaw) 使用，实现每日论文自动推送到飞书/Discord/Telegram

## 功能特性

| 功能 | 说明 |
|------|------|
| 关键词搜索 | 在标题和摘要中搜索关键词 |
| 日期过滤 | 按提交日期过滤，支持日期范围扩展 |
| 自动去重 | 自动过滤已汇报过的论文 |
| LLM 分析 | AI 生成结构化摘要（动机/方法/结果/结论） |
| 领域过滤 | 按研究领域自动筛选（Robotics/NLP/CV 等） |
| 并行处理 | 最多 5 个 worker 并行分析 |
| 报告生成 | 自动生成 Markdown 格式报告 |

## 快速开始

### 安装

```bash
git clone https://github.com/zk-yue/arXiv-Paper-Tracker.git
cd arXiv-Paper-Tracker
pip install -r requirements.txt
```

### 配置

```bash
cp config.example.json config.json
```

编辑 `config.json`：

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

或设置环境变量：`export LLM_API_KEY="your-api-key"`

### 使用

```bash
# 检索当天论文
python arxiv_search.py

# 检索指定日期及前3天，启用LLM分析
python arxiv_search.py -d 2026-03-17 --date-range 3 -l

# 测试模式：只分析第一篇论文
python arxiv_search.py -d 2026-03-17 -l -t

# 检查arXiv更新状态
python check_arxiv_update.py -c cs.RO
```

## 命令行选项

| 选项 | 说明 |
|------|------|
| `-d, --date` | 指定日期（YYYY-MM-DD，默认当天） |
| `-l, --llm` | 启用 LLM 分析 |
| `-t, --test` | 测试模式：只分析第一篇 |
| `--date-range` | 日期范围扩展天数 |
| `--dedup-days` | 去重回溯天数（默认 7） |

## LLM 配置

支持 OpenAI 兼容 API，示例：

| 提供商 | api_base | model |
|--------|----------|-------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 阿里云百炼 | `https://coding.dashscope.aliyuncs.com/v1` | `qwen3.5-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |

## 集成 OpenClaw

本项目可与 [OpenClaw](https://github.com/zk-yue/OpenClaw) 结合，实现：

- **定时推送** - 自动将每日论文报告推送到飞书、Discord、Telegram
- **论文下载** - 自动下载匹配论文的 PDF 文件
- **智能总结** - 按计划生成并推送 AI 驱动的论文摘要

详细配置请参考 [OpenClaw 集成指南](docs/openclaw-integration.md)。

## 定时任务

```bash
./install_cron.sh  # 设置每天早上 9 点自动执行
```

## 输出

- `results/*.json` - JSON 格式结果
- `results/*_report.md` - Markdown 格式报告

## 项目结构

```
arXiv-Paper-Tracker/
├── arxiv_search.py          # 主程序
├── check_arxiv_update.py    # arXiv 更新检查工具
├── config.json              # 配置文件（需自行创建）
├── config.example.json      # 配置文件模板
├── requirements.txt         # Python 依赖
├── install_cron.sh          # 定时任务安装脚本
├── docs/                    # 文档
└── results/                 # 输出目录
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

- [arXiv](https://arxiv.org/) - 开放获取学术论文
- [arxiv.py](https://github.com/lukasschwab/arxiv.py) - arXiv API Python 封装
