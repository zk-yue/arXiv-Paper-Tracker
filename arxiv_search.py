#!/usr/bin/env python3
"""
arXiv论文检索程序
支持关键词搜索，定时执行
"""

import arxiv
import json
import os
import argparse
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
        paper = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary.replace('\n', ' ').strip(),
            "published": result.published.strftime("%Y-%m-%d"),
            "updated": result.updated.strftime("%Y-%m-%d"),
            "arxiv_url": result.entry_id,
            "pdf_url": result.pdf_url,
            "categories": result.categories,
            "primary_category": result.primary_category
        }
        papers.append(paper)

    return papers


def save_results(papers: List[Dict], keywords: List[str], search_date: str):
    """保存搜索结果"""
    # 创建结果目录
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keywords_str = "_".join(keywords[:3]).replace(" ", "_")[:50]
    json_file = os.path.join(RESULTS_DIR, f"{timestamp}_{keywords_str}.json")
    md_file = os.path.join(RESULTS_DIR, f"{search_date}_report.md")

    # 保存JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "search_time": datetime.now().isoformat(),
            "keywords": keywords,
            "total_results": len(papers),
            "papers": papers
        }, f, ensure_ascii=False, indent=2)

    # 生成Markdown报告
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# arXiv 论文检索报告\n\n")
        f.write(f"**检索日期**: {search_date}\n\n")
        f.write(f"**关键词**: {', '.join(keywords)}\n\n")
        f.write(f"**检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**结果数量**: {len(papers)} 篇\n\n")
        f.write("---\n\n")

        for i, paper in enumerate(papers, 1):
            f.write(f"## {i}. {paper['title']}\n\n")
            f.write(f"- **作者**: {', '.join(paper['authors'][:5])}{'...' if len(paper['authors']) > 5 else ''}\n")
            f.write(f"- **发布日期**: {paper['published']}\n")
            f.write(f"- **arXiv链接**: [{paper['arxiv_url']}]({paper['arxiv_url']})\n")
            f.write(f"- **PDF链接**: [下载PDF]({paper['pdf_url']})\n")
            f.write(f"- **分类**: {', '.join(paper['categories'])}\n\n")
            f.write(f"**摘要**:\n\n{paper['summary'][:500]}{'...' if len(paper['summary']) > 500 else ''}\n\n")
            f.write("---\n\n")

    print(f"JSON已保存: {json_file}")
    print(f"报告已保存: {md_file}")
    return json_file


def run(date: Optional[str] = None):
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

    # 搜索论文
    print("\n正在搜索arXiv...")
    papers = search_papers(
        keywords=config["keywords"],
        max_results=config["max_results"],
        sort_by=config["sort_by"],
        date=date
    )

    print(f"找到 {len(papers)} 篇论文\n")

    if len(papers) == 0:
        print(f"{search_date} 没有匹配的新论文。")
        return papers

    # 显示结果摘要
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper['title']}")
        print(f"   作者: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"   发布日期: {paper['published']}")
        print(f"   链接: {paper['arxiv_url']}")
        print()

    # 保存结果
    save_results(papers, config["keywords"], search_date)

    return papers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="arXiv论文检索程序")
    parser.add_argument("-d", "--date", type=str, default=None,
                        help="指定检索日期 (格式: YYYY-MM-DD)，默认为当天")
    args = parser.parse_args()

    run(date=args.date)