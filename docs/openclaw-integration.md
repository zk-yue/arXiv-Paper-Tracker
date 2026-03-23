# arXiv 每日论文简报任务 - 配置指南

**适用场景：** 为研究者自动检索、分析、推送每日 arXiv 论文

**最后更新：** 2026-03-23
**配置人：** 照坤 (Cedric_Y)

---

## 任务概述

| 项目 | 配置 |
|------|------|
| **任务名称** | daily-arxiv-brief |
| **执行时间** | 每天早上 8:00 (Asia/Shanghai) |
| **Cron 表达式** | `0 8 * * *` |
| **推送渠道** | 飞书群聊 / Discord / 其他 |
| **关键词** | Deep Learning, Transformer, Diffusion Model, Large Language Model |
| **LLM 分析** | DeepSeek-chat / 阿里云百炼 |
| **领域过滤** | 可选，支持自定义领域 |

---

## 前置准备

### 1. 克隆论文检索项目

```bash
cd /home/yzk/
git clone https://github.com/zk-yue/arXiv-Paper-Tracker.git
cd arXiv-Paper-Tracker
```

### 2. 创建 Conda 环境

```bash
conda create -n arxiv python=3.10 -y
conda activate arxiv
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "keywords": ["Deep Learning", "Transformer", "Diffusion Model", "Large Language Model"],
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

**领域过滤配置说明：**

| 字段 | 说明 |
|------|------|
| `domain_filter.enabled` | 是否启用领域过滤（默认 `false`） |
| `domain_filter.domain` | 目标领域，如 `Robotics`、`NLP`、`Computer Vision` |
| `domain_filter.filter_out_non_domain` | 是否过滤掉非目标领域论文 |

**支持的 LLM API：**

| 服务商 | API Base | 模型 |
|--------|----------|------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 阿里云百炼 | `https://coding.dashscope.aliyuncs.com/v1` | `qwen3.5-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |

### 4. 测试运行

```bash
# 测试模式（只分析第 1 篇）
conda activate arxiv
python arxiv_search.py -d 2026-03-17 -l -t

# 正式运行（分析所有论文）
python arxiv_search.py -d 2026-03-17 -l
```

---

## OpenClaw 定时任务配置

### 1. 编辑任务配置文件

文件位置：`~/.openclaw/cron/jobs.json`

```json
{
  "version": 1,
  "jobs": [
    {
      "id": "0be2f12a-3274-4986-9649-c8de88aa07e9",
      "name": "daily-arxiv-brief",
      "description": "每天早上 8 点执行本地 arXiv 检索脚本并发送简报",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "0 8 * * *",
        "tz": "Asia/Shanghai"
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "## arXiv 每日论文简报任务\n\n**步骤 1：获取当前日期**\n```bash\ncd /home/yzk/arXiv-Paper-Tracker\nTODAY=$(date +\"%Y-%m-%d\")\necho \"检索日期：$TODAY\"\n```\n\n**步骤 2：运行检索脚本（带 LLM 分析）**\n```bash\n# 激活 conda 环境\nsource /home/yzk/anaconda3/etc/profile.d/conda.sh\nconda activate arxiv\n\n# 正式执行：分析所有论文\npython arxiv_search.py -d $TODAY -l\n```\n\n**步骤 3：读取生成的报告文件**\n```bash\n# 找到最新的 report.md 文件\nREPORT_FILE=$(ls -t results/*_report.md | head -1)\necho \"报告文件：$REPORT_FILE\"\n```\n\n**步骤 4：解析 Markdown 报告，提取每篇论文的基本信息 + 一句话概括**\n\n从 report.md 中提取以下字段：\n- 论文标题\n- 匹配关键词\n- 作者\n- 发布日期\n- arXiv 链接\n- PDF 链接\n- 分类\n- **一句话概括**（来自 LLM 分析部分）\n\n**步骤 5：发送简报**\n简报格式要求：\n- 每篇论文只发送：基本信息 + 一句话概括\n- 不要发送完整的 LLM 分析（Motivation/Method/Result/Conclusion）\n- 如果用户回复\"详细讲\"或\"详情\"，再发送完整的 LLM 总结\n\n**简报模板：**\n```\n📄 [论文标题]\n🏷️ 关键词：[匹配的关键词]\n👤 作者：[作者列表]\n📅 日期：[发布日期]\n📂 分类：[分类]\n🔗 arXiv: [链接]\n📎 PDF: [下载链接]\n\n💡 一句话概括：[LLM 生成的一句话概括]\n```\n\n**步骤 6：询问用户**\n发送完所有论文简报后，询问：\n\"需要我详细讲解哪篇论文吗？回复论文编号或标题即可～\"\n\n**注意：**\n- 如果 report.md 不存在或为空，发送通知：\"今日暂无匹配的 arXiv 论文\"\n- 如果用户要求详细讲解，从原报告中提取完整的 LLM 分析部分发送",
        "thinking": "medium"
      },
      "delivery": {
        "mode": "announce",
        "channel": "feishu",
        "to": "chat:YOUR_CHAT_ID"
      }
    }
  ]
}
```

### 2. 修改推送目标

根据你的需求修改 `delivery.to` 字段：

| 渠道 | 配置示例 |
|------|----------|
| **飞书群聊** | `"chat:oc_xxxxxxxxxxxxxxxxx"` |
| **飞书私聊** | `"user:ou_xxxxxxxxxxxxxxxxx"` |
| **Discord** | `"channel:1234567890123456789"` |
| **Telegram** | `"chat:-1001234567890"` |

### 3. 修改项目路径

根据实际情况修改 `message` 中的路径：

```bash
# 项目路径
cd /home/yzk/arXiv-Paper-Tracker

# Conda 路径（查找你的 conda.sh 位置）
find ~ -name "conda.sh" 2>/dev/null

# 常见位置：
# ~/anaconda3/etc/profile.d/conda.sh
# ~/miniconda3/etc/profile.d/conda.sh
# ~/.conda/etc/profile.d/conda.sh
```

---

## 输出示例

### 简报格式

```
📄 Influence of Gripper Design on Human Demonstration Quality for Robot Learning

🏷️ 关键词：Manipulation
👤 作者：Gina L. Georgadarellis, Natalija Beslic, Seonhun Lee...
📅 日期：2026-03-17
📂 分类：cs.RO
🔗 arXiv: http://arxiv.org/abs/2603.17189v1
📎 PDF: https://arxiv.org/pdf/2603.17189v1

💡 一句话概括：本文通过对比实验，研究了不同手持夹爪工具（分散负载与集中负载）对人类演示质量的影响，旨在为机器人学习（尤其是医疗场景下的操作技能）提供更高效、更符合人体工程学的数据采集工具设计指导。
```

### 详细讲解（用户请求后）

```
## 完整分析

### Motivation
在医疗机器人领域，让机器人学习如打开无菌医疗包装等精细操作技能至关重要...

### Method
1. 任务选择：选择"打开绷带包装"作为代表性医疗操作任务
2. 实验设计：比较三种演示条件（分散负载夹爪、集中负载夹爪、徒手操作）
3. 评估指标：任务成功率、完成时间、NASA-TLX 问卷...

### Result
1. 集中负载夹爪在性能上优于分散负载夹爪
2. 但仍显著低于徒手操作
3. 使用夹爪工具带来更高的感知工作负担

### Conclusion
手持夹爪工具的设计对人类演示质量有显著影响...
```

---

## 自定义配置

### 修改关键词

编辑 `config.json`：

```json
{
  "keywords": [
    "Deep Learning",
    "Transformer",
    "你的关键词",
    "更多关键词"
  ]
}
```

### 启用领域过滤

如果只想看特定领域的论文，启用领域过滤：

```json
{
  "domain_filter": {
    "enabled": true,
    "domain": "NLP",
    "filter_out_non_domain": true
  }
}
```

支持领域：`Robotics`、`NLP`、`Computer Vision`、`Reinforcement Learning` 等。

---

## 测试命令

```bash
# 测试模式（只分析第 1 篇，快速验证）
cd /home/yzk/arXiv-Paper-Tracker
source ~/anaconda3/etc/profile.d/conda.sh
conda activate arxiv
python arxiv_search.py -d 2026-03-17 -l -t

# 正式运行（分析所有论文）
python arxiv_search.py -d 2026-03-17 -l

# 检索指定日期
python arxiv_search.py -d 2026-03-17 -l

# 不使用 LLM 分析（仅检索）
python arxiv_search.py -d 2026-03-17
```

---

## 输出文件

| 文件 | 位置 | 说明 |
|------|------|------|
| JSON 结果 | `results/*.json` | 原始数据 |
| Markdown 报告 | `results/*_report.md` | 人类可读报告 |

---

## 注意事项

1. **API 成本**：每篇论文的 LLM 分析会消耗 Token，30+ 篇约需 10-20 分钟
2. **领域过滤**：可选功能，启用后 LLM 会自动剔除非目标领域论文
3. **推送频率**：每天早上 8 点，即使没有论文也会发送通知
4. **时区设置**：确保 `tz` 配置正确，避免推送时间错误

---

## 故障排查

### 问题 1：Conda 环境找不到

```bash
# 检查 conda 路径
which conda
ls ~/anaconda3/etc/profile.d/conda.sh

# 更新 jobs.json 中的路径
```

### 问题 2：API Key 无效

```bash
# 检查 config.json
cat config.json | grep api_key

# 测试 API 连通性
curl -X POST "https://api.deepseek.com/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

### 问题 3：没有匹配的论文

- 检查日期是否正确（arXiv 论文发布时间可能有时差）
- 检查关键词是否过于严格
- 查看 `results/` 目录下的 JSON 文件确认检索结果

---

## 支持

- 项目仓库：https://github.com/zk-yue/arXiv-Paper-Tracker
- OpenClaw 文档：https://docs.openclaw.ai

---

**配置完成！**

复制此文档给其他 OpenClaw 用户，按步骤配置即可拥有相同的每日论文简报功能。