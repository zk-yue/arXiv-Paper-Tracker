#!/usr/bin/env python3
"""
arXiv论文检索程序
支持关键词搜索，定时执行，LLM分析总结
"""

import arxiv
import json
import os
import argparse
import re
import requests
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

# 配置文件路径
CONFIG_FILE = "config.json"
RESULTS_DIR = "results"


def load_config() -> Dict:
    """加载配置文件"""
    default_config = {
        "keywords": ["machine learning", "deep learning"],
        "max_results": 10,
        "sort_by": "submittedDate",
        "save_format": "json"
    }

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 合并默认配置
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    else:
        # 创建默认配置文件
        save_config(default_config)
        return default_config


def save_config(config: Dict):
    """保存配置文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def find_matched_keywords(title: str, summary: str, keywords: List[str]) -> List[str]:
    """
    查找论文标题和摘要中匹配的关键词

    Args:
        title: 论文标题
        summary: 论文摘要
        keywords: 关键词列表

    Returns:
        匹配的关键词列表
    """
    matched = []
    text = (title + " " + summary).lower()

    for kw in keywords:
        if kw.lower() in text:
            matched.append(kw)

    return matched


def analyze_paper_with_llm(paper: Dict, api_key: str, api_base: str = "https://api.deepseek.com", model: str = "deepseek-chat") -> Optional[Dict]:
    """
    使用LLM分析论文摘要

    Args:
        paper: 论文信息字典
        api_key: API密钥
        api_base: API地址
        model: 模型名称

    Returns:
        分析结果字典
    """
    prompt = f"""请分析以下论文，用中文回答。按以下格式输出：

## 一句话概括
（用一句话概括论文核心内容）

## Motivation
（论文的研究动机，解决了什么问题）

## Method
（论文提出的方法，关键技术方案）

## Result
（实验结果和主要发现）

## Conclusion
（结论和贡献）

---

论文标题：{paper['title']}

摘要：
{paper['summary']}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }

    try:
        response = requests.post(
            f"{api_base}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return {
            "analysis": result["choices"][0]["message"]["content"],
            "model": model,
            "success": True
        }
    except Exception as e:
        print(f"    LLM分析失败: {str(e)}")
        return {
            "analysis": None,
            "error": str(e),
            "success": False
        }


def search_papers(keywords: List[str], max_results: int = 10, sort_by: str = "submittedDate", date: Optional[str] = None) -> List[Dict]:
    """
    搜索arXiv论文

    Args:
        keywords: 搜索关键词列表
        max_results: 最大返回结果数
        sort_by: 排序方式 (submittedDate, relevance, lastUpdatedDate)
        date: 指定日期 (格式: YYYY-MM-DD)，None表示当天

    Returns:
        论文列表
    """
    # 构建搜索查询 - 搜索标题和摘要
    query = " OR ".join([f'(ti:"{kw}" OR abs:"{kw}")' for kw in keywords])

    # 添加日期过滤
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    else:
        date = date.replace("-", "")

    query = f"({query}) AND submittedDate:[{date} TO {date}]"

    # 设置排序方式
    sort_criteria = {
        "submittedDate": arxiv.SortCriterion.SubmittedDate,
        "relevance": arxiv.SortCriterion.Relevance,
        "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate
    }.get(sort_by, arxiv.SortCriterion.SubmittedDate)

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_criteria
    )

    # 使用新的Client API
    client = arxiv.Client()
    papers = []
    for result in client.results(search):
        # 查找匹配的关键词
        matched_kw = find_matched_keywords(result.title, result.summary, keywords)

        paper = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary.replace('\n', ' ').strip(),
            "published": result.published.strftime("%Y-%m-%d"),
            "updated": result.updated.strftime("%Y-%m-%d"),
            "arxiv_url": result.entry_id,
            "pdf_url": result.pdf_url,
            "categories": result.categories,
            "primary_category": result.primary_category,
            "matched_keywords": matched_kw
        }
        papers.append(paper)

    return papers


def save_results(papers: List[Dict], keywords: List[str], search_date: str, config: Dict = None, enable_llm: bool = False):
    """保存搜索结果"""
    # 创建结果目录
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keywords_str = "_".join(keywords[:3]).replace(" ", "_")[:50]
    json_file = os.path.join(RESULTS_DIR, f"{timestamp}_{keywords_str}.json")
    md_file = os.path.join(RESULTS_DIR, f"{search_date}_report.md")

    # LLM分析配置
    llm_config = config.get("llm", {}) if config else {}
    api_key = llm_config.get("api_key", os.environ.get("DEEPSEEK_API_KEY", ""))
    api_base = llm_config.get("api_base", "https://api.deepseek.com")
    model = llm_config.get("model", "deepseek-chat")

    # 如果启用LLM分析但没有API key
    if enable_llm and not api_key:
        print("警告: 未配置DeepSeek API key，跳过LLM分析")
        enable_llm = False

    # 对每篇论文进行LLM分析
    if enable_llm:
        print("\n正在使用LLM分析论文...")
        for i, paper in enumerate(papers, 1):
            print(f"  分析 {i}/{len(papers)}: {paper['title'][:50]}...")
            analysis = analyze_paper_with_llm(paper, api_key, api_base, model)
            paper["llm_analysis"] = analysis
            # 避免请求过快
            if i < len(papers):
                time.sleep(1)

    # 保存JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "search_time": datetime.now().isoformat(),
            "keywords": keywords,
            "total_results": len(papers),
            "llm_enabled": enable_llm,
            "papers": papers
        }, f, ensure_ascii=False, indent=2)

    # 生成Markdown报告
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# arXiv 论文检索报告\n\n")
        f.write(f"**检索日期**: {search_date}\n\n")
        f.write(f"**关键词**: {', '.join(keywords)}\n\n")
        f.write(f"**检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**结果数量**: {len(papers)} 篇\n\n")
        if enable_llm:
            f.write(f"**LLM分析**: 已启用 ({model})\n\n")
        f.write("---\n\n")

        for i, paper in enumerate(papers, 1):
            f.write(f"## {i}. {paper['title']}\n\n")
            f.write(f"- **匹配关键词**: {', '.join(paper['matched_keywords'])}\n")
            f.write(f"- **作者**: {', '.join(paper['authors'][:5])}{'...' if len(paper['authors']) > 5 else ''}\n")
            f.write(f"- **发布日期**: {paper['published']}\n")
            f.write(f"- **arXiv链接**: [{paper['arxiv_url']}]({paper['arxiv_url']})\n")
            f.write(f"- **PDF链接**: [下载PDF]({paper['pdf_url']})\n")
            f.write(f"- **分类**: {', '.join(paper['categories'])}\n\n")

            # LLM分析结果
            if enable_llm and paper.get("llm_analysis", {}).get("success"):
                f.write(f"### 📝 LLM分析\n\n")
                f.write(paper["llm_analysis"]["analysis"])
                f.write("\n\n---\n\n")
            else:
                f.write(f"**摘要**:\n\n{paper['summary'][:500]}{'...' if len(paper['summary']) > 500 else ''}\n\n")
                f.write("---\n\n")

    print(f"\nJSON已保存: {json_file}")
    print(f"报告已保存: {md_file}")
    return json_file


def run(date: Optional[str] = None, enable_llm: bool = False):
    """主运行函数"""
    if date is None:
        search_date = datetime.now().strftime("%Y-%m-%d")
    else:
        search_date = date

    print(f"\n{'='*50}")
    print(f"arXiv论文检索 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    # 加载配置
    config = load_config()
    print(f"\n搜索关键词: {config['keywords']}")
    print(f"日期过滤: 仅 {search_date} 发布的论文")
    print(f"最大结果数: {config['max_results']}")
    if enable_llm:
        llm_config = config.get("llm", {})
        print(f"LLM分析: 已启用 ({llm_config.get('model', 'deepseek-chat')})")

    # 搜索论文
    print("\n正在搜索arXiv...")
    papers = search_papers(
        keywords=config["keywords"],
        max_results=config["max_results"],
        sort_by=config["sort_by"],
        date=date
    )

    print(f"找到 {len(papers)} 篇论文")

    # 过滤掉没有匹配关键词的论文
    papers = [p for p in papers if p['matched_keywords']]
    print(f"匹配关键词的论文: {len(papers)} 篇\n")

    if len(papers) == 0:
        print(f"{search_date} 没有匹配的新论文。")
        return papers

    # 显示结果摘要
    for i, paper in enumerate(papers, 1):
        matched = ', '.join(paper['matched_keywords'])
        print(f"{i}. {paper['title']}")
        print(f"   匹配关键词: {matched}")
        print(f"   作者: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"   发布日期: {paper['published']}")
        print(f"   链接: {paper['arxiv_url']}")
        print()

    # 保存结果
    save_results(papers, config["keywords"], search_date, config, enable_llm)

    return papers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="arXiv论文检索程序")
    parser.add_argument("-d", "--date", type=str, default=None,
                        help="指定检索日期 (格式: YYYY-MM-DD)，默认为当天")
    parser.add_argument("-l", "--llm", action="store_true",
                        help="启用LLM分析论文 (需要配置DeepSeek API)")
    args = parser.parse_args()

    run(date=args.date, enable_llm=args.llm)