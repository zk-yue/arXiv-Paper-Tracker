#!/usr/bin/env python3
"""
arXiv论文检索程序
支持关键词搜索，定时执行，LLM分析总结
"""

import arxiv
import json
import os
import argparse
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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


def get_reported_paper_ids(before_date: str, days: int = 7) -> set:
    """
    获取指定日期之前已汇报过的论文ID集合
    
    Args:
        before_date: 日期，格式 YYYY-MM-DD，只返回此日期之前的论文
        days: 回溯天数，默认7天
        
    Returns:
        已汇报论文的ID集合
    """
    reported_ids = set()
    
    if not os.path.exists(RESULTS_DIR):
        return reported_ids
    
    # 解析before_date，计算回溯截止日期
    before_dt = datetime.strptime(before_date, "%Y-%m-%d")
    cutoff_dt = before_dt - timedelta(days=days)
    
    # 遍历results目录下的JSON文件
    for filename in os.listdir(RESULTS_DIR):
        if filename.endswith('.json'):
            # 从文件名提取日期，如 20260617_xxx.json
            try:
                file_date_str = filename[:8]
                file_dt = datetime.strptime(file_date_str, "%Y%m%d")
                # 只处理 [cutoff_dt, before_dt) 范围内的文件
                if file_dt < cutoff_dt or file_dt >= before_dt:
                    continue
            except ValueError:
                # 无法解析日期，跳过
                continue
            
            file_path = os.path.join(RESULTS_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 提取论文ID（从arxiv_url中提取）
                    for paper in data.get('papers', []):
                        arxiv_url = paper.get('arxiv_url', '')
                        if arxiv_url:
                            # 从URL中提取ID，如 http://arxiv.org/abs/2603.17189v1 -> 2603.17189v1
                            paper_id = arxiv_url.split('/')[-1]
                            reported_ids.add(paper_id)
            except Exception:
                # 忽略读取失败的文件
                pass
    
    return reported_ids


def filter_new_papers(papers: List[Dict], reported_ids: set) -> List[Dict]:
    """
    过滤掉已汇报过的论文
    
    Args:
        papers: 论文列表
        reported_ids: 已汇报论文的ID集合
        
    Returns:
        过滤后的新论文列表
    """
    new_papers = []
    filtered_count = 0
    
    for paper in papers:
        arxiv_url = paper.get('arxiv_url', '')
        if arxiv_url:
            paper_id = arxiv_url.split('/')[-1]
            if paper_id in reported_ids:
                filtered_count += 1
                continue
        new_papers.append(paper)
    
    if filtered_count > 0:
        print(f"去重: 过滤掉 {filtered_count} 篇已汇报论文")
    
    return new_papers


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


def analyze_paper_with_llm(paper: Dict, api_key: str, api_base: str = "https://api.deepseek.com", model: str = "deepseek-chat", domain_filter: Dict = None) -> Optional[Dict]:
    """
    使用LLM分析论文摘要

    Args:
        paper: 论文信息字典
        api_key: API密钥
        api_base: API地址
        model: 模型名称
        domain_filter: 领域过滤配置 {"enabled": bool, "domain": str, "filter_out_non_domain": bool}

    Returns:
        分析结果字典
    """
    # 构建领域判断相关的 prompt
    domain_config = domain_filter or {}
    domain_enabled = domain_config.get("enabled", False)
    target_domain = domain_config.get("domain", "Robotics")

    if domain_enabled:
        domain_prompt = f"""判断这篇论文的核心贡献是否属于{target_domain}领域。

判断标准：
1. 论文的核心问题或应用场景应与{target_domain}相关
2. 纯粹的其他领域问题（如纯图像分类、纯文本生成、纯图形渲染）且与{target_domain}无关联的，判断为"否"

以Robotics为例：
- 属于：机器人操作、抓取、导航、控制、规划、人机交互、机器人感知与决策、机器人相关数据集、机器人学习理论等
- 不属于：纯计算机视觉（无机器人应用）、纯图形学、纯NLP、纯机器学习算法（无机器人场景）等

如果属于{target_domain}领域，请按以下格式输出：

## 领域判断
是

## 一句话概括
（用一句话概括论文核心内容）

## Motivation
（论文的研究动机，解决了什么问题）

## Method
（论文提出的方法，包括：核心创新点、算法框架、关键技术方案）

## Result
（实验结果和主要发现）

## Conclusion
（结论和贡献）

如果不属于{target_domain}领域，只需输出：

## 领域判断
否

## 原因
（简要说明为什么不属于{target_domain}领域，指出其核心贡献属于哪个领域）

---
"""
    else:
        domain_prompt = f"""请分析以下论文，按以下格式输出：

## 一句话概括
（用一句话概括论文核心内容）

## Motivation
（论文的研究动机，解决了什么问题）

## Method
（论文提出的方法，包括：核心创新点、算法框架、关键技术方案）

## Result
（实验结果和主要发现）

## Conclusion
（结论和贡献）

---
"""

    prompt = f"""{domain_prompt}

论文标题：{paper['title']}

分类标签：{', '.join(paper.get('categories', []))}

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
            f"{api_base}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 判断是否是目标领域
        domain_enabled = domain_filter.get("enabled", False) if domain_filter else False
        if domain_enabled:
            is_target_domain = "## 领域判断\n是" in content or "## 领域判断\n 是" in content
        else:
            is_target_domain = True  # 未启用领域过滤时，默认保留所有论文

        return {
            "analysis": content,
            "is_target_domain": is_target_domain,
            "model": model,
            "success": True
        }
    except Exception as e:
        print(f"    LLM分析失败: {str(e)}")
        return {
            "analysis": None,
            "is_target_domain": True,  # 分析失败时保留论文
            "error": str(e),
            "success": False
        }


def search_papers(keywords: List[str], max_results: int = 10, sort_by: str = "submittedDate", date: Optional[str] = None, date_range: int = 0) -> List[Dict]:
    """
    搜索arXiv论文

    Args:
        keywords: 搜索关键词列表
        max_results: 最大返回结果数
        sort_by: 排序方式 (submittedDate, relevance, lastUpdatedDate)
        date: 指定日期 (格式: YYYY-MM-DD)，None表示当天
        date_range: 日期范围扩展天数，0表示仅当天，1表示往前扩展1天

    Returns:
        论文列表
    """
    # 构建搜索查询 - 搜索标题和摘要
    query = " OR ".join([f'(ti:"{kw}" OR abs:"{kw}")' for kw in keywords])

    # 添加日期过滤
    if date is None:
        base_date = datetime.now()
    else:
        base_date = datetime.strptime(date, "%Y-%m-%d")
    
    # 计算日期范围
    if date_range > 0:
        start_date = (base_date - timedelta(days=date_range)).strftime("%Y%m%d")
        end_date = base_date.strftime("%Y%m%d")
    else:
        start_date = base_date.strftime("%Y%m%d")
        end_date = start_date

    query = f"({query}) AND submittedDate:[{start_date} TO {end_date}]"

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

    # 使用新的Client API，添加限流保护
    # 增加delay_seconds以避免触发arXiv API频率限制
    client = arxiv.Client(
        page_size=100,      # 每页返回更多结果，减少请求次数
        delay_seconds=5.0,  # 增加到5秒，更保守地避免限流
        num_retries=8       # 增加到8次重试，提高容错能力
    )
    papers = []
    max_retries = 3  # 整个搜索过程的最大重试次数
    retry_count = 0
    
    while retry_count < max_retries:
        try:
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
            break
        except arxiv.HTTPError as e:
            if e.status == 429:
                retry_count += 1
                if retry_count < max_retries:
                    # 指数退避：等待时间随重试次数增加
                    wait_time = 10 * (2 ** (retry_count - 1))  # 10s, 20s, 40s
                    print(f"警告: arXiv API 请求频率过高 (HTTP 429)，等待 {wait_time} 秒后重试 ({retry_count}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"错误: arXiv API 请求频率过高 (HTTP 429)，已达到最大重试次数")
                    print(f"建议: 1. 增加delay_seconds参数 2. 减少关键词数量 3. 分批执行检索")
                    return papers
            else:
                print(f"错误: arXiv API 请求失败 (HTTP {e.status})")
                return papers
        except Exception as e:
            print(f"错误: 检索论文时发生异常: {str(e)}")
            return papers

    return papers


def save_results(papers: List[Dict], keywords: List[str], search_date: str, config: Dict = None, enable_llm: bool = False, test_mode: bool = False, total_scanned: int = 0, matched_count: int = 0):
    """保存搜索结果"""
    # 创建结果目录
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # 生成文件名（使用检索日期）
    date_str = search_date.replace("-", "")
    keywords_str = "_".join(keywords[:3]).replace(" ", "_")[:50]
    json_file = os.path.join(RESULTS_DIR, f"{date_str}_{keywords_str}.json")
    md_file = os.path.join(RESULTS_DIR, f"{search_date}_report.md")

    # LLM分析配置
    llm_config = config.get("llm", {}) if config else {}
    api_key = llm_config.get("api_key", os.environ.get("LLM_API_KEY", ""))
    api_base = llm_config.get("api_base", "https://api.deepseek.com")
    model = llm_config.get("model", "deepseek-chat")
    domain_filter = config.get("domain_filter", {}) if config else {}

    # 如果启用LLM分析但没有API key
    if enable_llm and not api_key:
        print("警告: 未配置 API key，跳过LLM分析")
        enable_llm = False

    # 领域过滤配置
    domain_enabled = domain_filter.get("enabled", False)
    target_domain = domain_filter.get("domain", "Robotics")
    filter_out = domain_filter.get("filter_out_non_domain", True)

    # 对每篇论文进行LLM分析
    if enable_llm:
        print("\n正在使用LLM分析论文...")
        if domain_enabled:
            print(f"领域过滤: 已启用 (目标领域: {target_domain})")
        # 测试模式只分析第一篇
        papers_to_analyze = papers[:1] if test_mode else papers
        
        # 并行处理LLM分析
        max_workers = min(5, len(papers_to_analyze))  # 最多5个并行 worker
        if max_workers > 1:
            print(f"  并行处理: {max_workers} 个 worker")
        
        # 使用锁保护共享资源
        lock = threading.Lock()
        analyzed_count = [0]  # 使用列表以便在闭包中修改
        
        def analyze_single(paper_idx):
            """分析单篇论文"""
            idx, paper = paper_idx
            analysis = analyze_paper_with_llm(paper, api_key, api_base, model, domain_filter)
            with lock:
                analyzed_count[0] += 1
                print(f"  分析 {analyzed_count[0]}/{len(papers_to_analyze)}: {paper['title'][:50]}...")
                # 显示领域判断结果（仅在启用领域过滤时）
                if domain_enabled and filter_out and analysis.get("success") and not analysis.get("is_target_domain", True):
                    print(f"    非目标领域，已剔除")
            return idx, analysis
        
        if max_workers > 1:
            # 并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_idx = {
                    executor.submit(analyze_single, (idx, paper)): idx
                    for idx, paper in enumerate(papers_to_analyze)
                }
                
                # 收集结果
                results = {}
                for future in as_completed(future_to_idx):
                    try:
                        idx, analysis = future.result()
                        results[idx] = analysis
                    except Exception as e:
                        idx = future_to_idx[future]
                        print(f"  分析失败: {papers_to_analyze[idx]['title'][:50]}... - {str(e)}")
                        results[idx] = {
                            "analysis": None,
                            "is_target_domain": True,
                            "error": str(e),
                            "success": False
                        }
                
                # 按顺序赋值结果
                for idx, analysis in results.items():
                    papers_to_analyze[idx]["llm_analysis"] = analysis
        else:
            # 串行处理（当只有1篇论文时）
            for idx, paper in enumerate(papers_to_analyze):
                print(f"  分析 {idx+1}/{len(papers_to_analyze)}: {paper['title'][:50]}...")
                analysis = analyze_paper_with_llm(paper, api_key, api_base, model, domain_filter)
                paper["llm_analysis"] = analysis
                # 显示领域判断结果（仅在启用领域过滤时）
                if domain_enabled and filter_out and analysis.get("success") and not analysis.get("is_target_domain", True):
                    print(f"    非目标领域，已剔除")

        if test_mode:
            print(f"\n[测试模式] 只分析了第一篇论文")

        # 过滤掉非目标领域的论文（仅在启用过滤时）
        if domain_enabled and filter_out:
            original_count = len(papers)
            papers = [p for p in papers if p.get("llm_analysis", {}).get("is_target_domain", True)]
            filtered_count = original_count - len(papers)
            if filtered_count > 0:
                print(f"\n已剔除 {filtered_count} 篇非{target_domain}领域论文，保留 {len(papers)} 篇")

        if len(papers) == 0:
            print(f"没有目标领域的论文，跳过报告生成")
            return json_file

    # 保存JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "search_time": datetime.now().isoformat(),
            "keywords": keywords,
            "total_scanned": total_scanned,
            "matched_count": matched_count,
            "final_results": len(papers),
            "llm_enabled": enable_llm,
            "papers": papers
        }, f, ensure_ascii=False, indent=2)

    # 生成Markdown报告
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# arXiv 论文检索报告\n\n")
        f.write(f"**检索日期**: {search_date}\n\n")
        f.write(f"**关键词**: {', '.join(keywords)}\n\n")
        f.write(f"**检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**扫描总数**: {total_scanned} 篇\n\n")
        f.write(f"**关键词匹配**: {matched_count} 篇\n\n")
        f.write(f"**最终结果**: {len(papers)} 篇\n\n")
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


def run(date: Optional[str] = None, enable_llm: bool = False, test_mode: bool = False, date_range: int = 0, dedup_days: int = 7):
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
    if date_range > 0:
        print(f"日期范围: {search_date} 前 {date_range} 天")
    else:
        print(f"日期过滤: 仅 {search_date} 发布的论文")
    print(f"最大结果数: {config['max_results']}")
    if enable_llm:
        llm_config = config.get("llm", {})
        print(f"LLM分析: 已启用 ({llm_config.get('model', 'deepseek-chat')})")
        domain_filter = config.get("domain_filter", {})
        if domain_filter.get("enabled", False):
            print(f"领域过滤: 已启用 (目标领域: {domain_filter.get('domain', 'Robotics')})")

    # 获取已汇报过的论文ID（只看search_date之前的）
    print(f"\n检查已汇报论文（{search_date} 之前）...")
    reported_ids = get_reported_paper_ids(search_date, dedup_days)
    print(f"已汇报论文数: {len(reported_ids)}")

    # 搜索论文
    print("\n正在搜索arXiv...")
    papers = search_papers(
        keywords=config["keywords"],
        max_results=config["max_results"],
        sort_by=config["sort_by"],
        date=date,
        date_range=date_range
    )

    print(f"找到 {len(papers)} 篇论文")

    # 记录扫描总数
    total_scanned = len(papers)

    # 过滤掉已汇报过的论文
    papers = filter_new_papers(papers, reported_ids)

    # 过滤掉没有匹配关键词的论文
    papers = [p for p in papers if p['matched_keywords']]
    matched_count = len(papers)
    print(f"匹配关键词的论文: {len(papers)} 篇\n")

    if len(papers) == 0:
        print(f"{search_date} 没有匹配的新论文。")
        # 仍然保存报告，记录扫描情况
        save_results(papers, config["keywords"], search_date, config, enable_llm, test_mode, total_scanned, matched_count)
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
    save_results(papers, config["keywords"], search_date, config, enable_llm, test_mode, total_scanned, matched_count)

    return papers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="arXiv论文检索程序")
    parser.add_argument("-d", "--date", type=str, default=None,
                        help="指定检索日期 (格式: YYYY-MM-DD)，默认为当天")
    parser.add_argument("-l", "--llm", action="store_true",
                        help="启用LLM分析论文 (需要配置API Key)")
    parser.add_argument("-t", "--test", action="store_true",
                        help="测试模式：只分析第一篇论文")
    parser.add_argument("--date-range", type=int, default=0,
                        help="日期范围扩展天数，0表示仅当天，1表示往前扩展1天 (默认: 0)")
    parser.add_argument("--dedup-days", type=int, default=7,
                        help="去重回溯天数，检查已汇报论文 (默认: 7)")
    args = parser.parse_args()

    run(date=args.date, enable_llm=args.llm, test_mode=args.test, 
        date_range=args.date_range, dedup_days=args.dedup_days)