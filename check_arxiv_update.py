#!/usr/bin/env python3
"""
arXiv 更新检查工具
检查过去一周每天 arXiv 的更新情况
"""

import arxiv
from datetime import datetime, timedelta
from typing import Dict, List
import time


def check_arxiv_update(date: str, category: str = "cs.RO", get_count: bool = True) -> Dict:
    """
    检查指定日期 arXiv 是否有更新
    
    Args:
        date: 日期，格式 YYYY-MM-DD
        category: 分类，默认 cs.RO
        get_count: 是否获取实际论文数量（较慢），否则只检查是否有更新
        
    Returns:
        包含更新信息的字典
    """
    date_str = date.replace('-', '')
    
    if get_count:
        # 获取实际论文数量
        query = f"cat:{category} AND submittedDate:[{date_str} TO {date_str}]"
        search = arxiv.Search(
            query=query,
            max_results=10000,  # 设置一个较大的值以获取所有结果
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
    else:
        # 只检查是否有更新
        query = f"cat:{category} AND submittedDate:[{date_str} TO {date_str}]"
        search = arxiv.Search(
            query=query,
            max_results=1,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
    
    client = arxiv.Client(
        page_size=100,
        delay_seconds=3.0,
        num_retries=3
    )
    
    try:
        papers = list(client.results(search))
        count = len(papers)
        return {
            "date": date,
            "category": category,
            "count": count,
            "has_update": count > 0,
            "status": "updated" if count > 0 else "no_update"
        }
    except Exception as e:
        return {
            "date": date,
            "category": category,
            "count": 0,
            "has_update": False,
            "status": f"error: {str(e)}"
        }


def check_past_week(category: str = "cs.RO") -> List[Dict]:
    """
    检查过去一周 arXiv 的更新情况
    
    Args:
        category: 分类，默认 cs.RO
        
    Returns:
        每天更新情况的列表
    """
    results = []
    today = datetime.now()
    
    print(f"\n检查过去一周 {category} 分类的 arXiv 更新情况")
    print("=" * 50)
    
    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        print(f"\n检查 {date}...", end=" ")
        
        result = check_arxiv_update(date, category)
        results.append(result)
        
        if result["has_update"]:
            print(f"✓ 已更新 ({result['count']} 篇)")
        else:
            print(f"✗ 未更新")
        
        # 避免请求过快
        if i < 6:
            time.sleep(3)
    
    return results


def print_summary(results: List[Dict]):
    """打印汇总信息"""
    print("\n" + "=" * 50)
    print("汇总:")
    print("=" * 50)
    
    updated_days = sum(1 for r in results if r["has_update"])
    total_papers = sum(r["count"] for r in results)
    
    print(f"已更新天数: {updated_days}/7")
    print(f"总论文数: {total_papers}")
    
    print("\n详细:")
    for r in results:
        status = "✓" if r["has_update"] else "✗"
        print(f"  {status} {r['date']}: {r['count']} 篇")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查 arXiv 更新情况")
    parser.add_argument("-c", "--category", type=str, default="cs.RO",
                        help="arXiv 分类 (默认: cs.RO)")
    parser.add_argument("-d", "--date", type=str, default=None,
                        help="检查指定日期 (格式: YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    if args.date:
        # 检查指定日期
        print(f"\n检查 {args.date} {args.category} 的更新情况...")
        result = check_arxiv_update(args.date, args.category)
        
        if result["has_update"]:
            print(f"✓ 已更新 ({result['count']} 篇)")
        else:
            print(f"✗ 未更新")
    else:
        # 检查过去一周
        results = check_past_week(args.category)
        print_summary(results)


if __name__ == "__main__":
    main()
