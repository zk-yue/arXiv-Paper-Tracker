# OpenClaw 集成指南

本项目可与 [OpenClaw](https://github.com/zk-yue/OpenClaw) 集成，实现 arXiv 论文的自动化检索、分析与推送。

## 当前配置

| 项目 | 配置 |
|------|------|
| 任务名称 | `daily-arxiv-brief` |
| 执行时间 | 每天中午 12:00 (Asia/Shanghai) |
| 项目路径 | `/home/yzk/my_arxiv` |
| Conda 环境 | `arxiv` (Python 3.10) |
| 推送渠道 | 飞书群聊 |
| 推送目标 | `chat:oc_1ce4ebc2660e82240760457ffa690736` |
| 超时时间 | 1800 秒（30 分钟） |

## 快速配置

### 1. 环境准备

```bash
# 克隆项目
cd /home/yzk
git clone https://github.com/zk-yue/arXiv-Paper-Tracker.git my_arxiv
cd my_arxiv

# 创建环境
conda create -n arxiv python=3.10 -y
conda activate arxiv
pip install -r requirements.txt

# 配置 API Key
cp config.example.json config.json
# 编辑 config.json 填入你的 API Key
```

### 2. 测试运行

```bash
# 激活环境
source ~/anaconda3/etc/profile.d/conda.sh
conda activate arxiv

# 测试模式（只分析 1 篇）
python arxiv_search.py -d $(date -d "yesterday" +"%Y-%m-%d") -l -t

# 正式运行
python arxiv_search.py -d $(date -d "yesterday" +"%Y-%m-%d") -l
```

### 3. 定时任务配置

编辑 `~/.openclaw/cron/jobs.json`，添加以下任务：

```json
{
  "id": "0be2f12a-3274-4986-9649-c8de88aa07e9",
  "name": "daily-arxiv-brief",
  "description": "每天中午 12 点执行本地 arXiv 检索脚本并发送简报（检索前一天的论文）",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 12 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "执行 arXiv 论文检索任务：\n\n1. 获取昨日日期：`YESTERDAY=$(date -d \"yesterday\" +\"%Y-%m-%d\")`\n2. 激活环境：`source ~/anaconda3/etc/profile.d/conda.sh && conda activate arxiv`\n3. 执行检索：`cd /home/yzk/my_arxiv && python arxiv_search.py -d $YESTERDAY -l`\n4. 读取报告：`cat results/${YESTERDAY}_report.md`\n5. 提取每篇论文的标题、作者、关键词、一句话概括、链接\n6. 按格式发送简报，询问用户是否需要详细讲解",
    "thinking": "medium",
    "timeoutSeconds": 1800
  },
  "delivery": {
    "mode": "announce",
    "channel": "feishu",
    "to": "chat:oc_1ce4ebc2660e82240760457ffa690736"
  }
}
```

### 4. 推送目标配置

修改 `delivery.to` 字段：

| 渠道 | 格式 | 示例 |
|------|------|------|
| 飞书群聊 | `chat:oc_xxxxxxxxx` | `chat:oc_1ce4ebc2660e82240760457ffa690736` |
| 飞书私聊 | `user:ou_xxxxxxxxx` | `user:ou_xxxxxxxxx` |
| Discord | `channel:1234567890123456789` | - |
| Telegram | `chat:-1001234567890` | - |

## 配置说明

### config.json

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

| 字段 | 说明 |
|------|------|
| `keywords` | 搜索关键词列表 |
| `max_results` | 最大返回数（默认 500） |
| `domain_filter.enabled` | 启用领域过滤 |
| `domain_filter.domain` | 目标领域（Robotics/NLP/CV 等） |
| `llm.api_key` | LLM API 密钥 |
| `llm.api_base` | API 端点 |
| `llm.model` | 模型名称 |

### LLM 提供商

| 提供商 | api_base | model |
|--------|----------|-------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 阿里云百炼 | `https://coding.dashscope.aliyuncs.com/v1` | `qwen3.5-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |

## 输出格式

### 简报示例

```
📄 TeleDex: Accessible Dexterous Teleoperation
🏷️ 关键词：Manipulation
👤 作者：Omar Rayyan, Maximilian Gilles, Yuchen Cui...
📅 日期：2026-03-17
📂 分类：cs.RO
🔗 arXiv: http://arxiv.org/abs/2603.17065v2
📎 PDF: https://arxiv.org/pdf/2603.17065v2

💡 一句话概括：利用智能手机实现低成本灵巧遥操作，无需外部追踪设备。
```

### 输出文件

| 文件 | 说明 |
|------|------|
| `results/*.json` | 原始数据（JSON） |
| `results/*_report.md` | 可读报告（Markdown） |

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| Conda 环境找不到 | 检查路径：`ls ~/anaconda3/etc/profile.d/conda.sh` |
| API Key 无效 | 检查 `config.json` 中的 `api_key` 字段 |
| HTTP 429 错误 | 等待 30 秒后重试，或减少关键词数量 |
| 无匹配论文 | 检查日期和关键词，arXiv 更新可能有延迟 |
| 任务超时 | 增加 `timeoutSeconds` 或减少论文数量 |

## 相关链接

- 项目仓库：https://github.com/zk-yue/arXiv-Paper-Tracker
- OpenClaw 文档：https://docs.openclaw.ai
