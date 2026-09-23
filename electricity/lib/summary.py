"""记录汇总统计 — 对历史记录做聚合计算，供界面与导出使用"""

from typing import Any, Union

Record = dict[str, Any]


def summarize(records: list[Record]) -> dict[str, Union[int, float]]:
    """汇总一条记录列表，返回统计指标。

    Args:
        records: history.query() 返回的记录列表（含 username/month/usage/total）。

    Returns:
        dict: {
            "count": 记录条数,
            "total_usage": 总用电量(度),
            "total_fee": 总电费(元),
            "avg_fee": 平均单次电费(元),
            "user_count": 涉及用户数,
            "month_span": 覆盖月份跨度(个),
        }
    """
    count = len(records)
    total_usage = sum(r.get("usage") or 0 for r in records)
    total_fee = sum(r.get("total") or 0 for r in records)
    users = {r.get("username") for r in records if r.get("username")}
    months = {r.get("month") for r in records if r.get("month")}

    return {
        "count": count,
        "total_usage": total_usage,
        "total_fee": total_fee,
        "avg_fee": total_fee / count if count else 0.0,
        "user_count": len(users),
        "month_span": len(months),
    }


def format_summary_text(summary: dict[str, Union[int, float]]) -> str:
    """把汇总结果格式化为单行中文提示文本。"""
    return (
        f"共 {summary['count']} 条记录 | 总用电 {summary['total_usage']:.1f} 度 "
        f"| 总电费 ¥{summary['total_fee']:.2f} | 平均 ¥{summary['avg_fee']:.2f}/次 "
        f"| 涉及 {summary['user_count']} 位用户"
    )