# arXiv 论文检索程序

自动检索 arXiv 论文，支持关键词搜索、日期过滤、LLM 分析总结。

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/zk-yue/my_arxiv.git
cd my_arxiv
```

### 2. 创建环境并安装依赖
```bash
conda create -n arxiv python=3.10 -y
conda activate arxiv
pip install -r requirements.txt
```

### 3. 配置 API Key

复制配置文件模板：
```bash
cp config.example.json config.json
```

编辑 `config.json`，填入你的阿里云百炼 API Key：
```json
{
  "keywords": ["Tactile", "Imitation Learning", "VLA", "Manipulation"],
  "max_results": 100,
  "sort_by": "submittedDate",
  "llm": {
    "api_key": "YOUR_BAILIAN_API_KEY",
    "api_base": "https://coding.dashscope.aliyuncs.com/v1",
    "model": "qwen3.5-plus"
  }
}
```

或者设置环境变量：
```bash
export BAILIAN_API_KEY="your-api-key"
```

### 4. 运行

```bash
# 检索当天论文
python arxiv_search.py

# 检索指定日期
python arxiv_search.py -d 2026-03-17

# 启用 LLM 分析（需要 API Key）
python arxiv_search.py -d 2026-03-17 -l
```

## 功能

- **关键词搜索**：在标题和摘要中搜索关键词
- **日期过滤**：默认检索当天，可指定日期
- **关键词匹配**：自动标注每篇论文匹配的关键词
- **LLM 分析**：自动判断是否为机器人领域，并生成摘要
  - 一句话概括
  - Motivation（研究动机）
  - Method（方法）
  - Result（结果）
  - Conclusion（结论）
- **报告生成**：自动生成 Markdown 报告

## 配置说明

| 字段 | 说明 |
|------|------|
| keywords | 搜索关键词列表 |
| max_results | 最大返回结果数 |
| sort_by | 排序方式：submittedDate / relevance / lastUpdatedDate |
| llm.api_key | API Key |
| llm.api_base | API 地址 |
| llm.model | 模型名称 |

## 切换 LLM API

### 阿里云百炼（默认）
```json
{
  "llm": {
    "api_key": "YOUR_BAILIAN_API_KEY",
    "api_base": "https://coding.dashscope.aliyuncs.com/v1",
    "model": "qwen3.5-plus"
  }
}
```

### DeepSeek
```json
{
  "llm": {
    "api_key": "YOUR_DEEPSEEK_API_KEY",
    "api_base": "https://api.deepseek.com",
    "model": "deepseek-chat"
  }
}
```

## 定时任务

运行以下脚本设置每天早上 9 点自动执行：
```bash
./install_cron.sh
```

## 输出

- `results/*.json` - JSON 格式结果
- `results/*_report.md` - Markdown 报告