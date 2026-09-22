"""statistics 模块单元测试"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib import statistics  # noqa: E402


def _rec(username, month, usage, total, tier=None):
    """构造一条测试记录。"""
    return {"username": username, "month": month, "usage": usage,
            "total": total, "current_tier": tier}


class TestStatistics(unittest.TestCase):
    """测试多维度统计函数"""

    def setUp(self):
        self.records = [
            _rec("A", 1, 120, 54.67, 1),
            _rec("A", 2, 300, 136.68, 1),
            _rec("B", 1, 500, 300.00, 2),
            _rec("B", 2, 900, 500.00, 3),
        ]

    def test_calculate_total_fee(self):
        self.assertAlmostEqual(statistics.calculate_total_fee(self.records), 991.35, places=2)

    def test_calculate_avg_fee(self):
        self.assertAlmostEqual(statistics.calculate_avg_fee(self.records), 247.84, places=2)
        self.assertEqual(statistics.calculate_avg_fee([]), 0.0)

    def test_get_usage_ranking(self):
        top = statistics.get_usage_ranking(self.records, top=2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["username"], "B")
        self.assertEqual(top[0]["usage"], 900)

    def test_group_by_user(self):
        users = statistics.group_by_user(self.records)
        self.assertEqual(len(users), 2)
        a = [u for u in users if u["username"] == "A"][0]
        self.assertEqual(a["total_usage"], 420)
        self.assertAlmostEqual(a["total_fee"], 191.35, places=2)
        self.assertAlmostEqual(a["avg_fee"], 95.68, places=2)

    def test_group_by_month(self):
        months = statistics.group_by_month(self.records)
        self.assertEqual(len(months), 2)
        m1 = [m for m in months if m["month"] == 1][0]
        self.assertEqual(m1["total_usage"], 620)

    def test_calculate_tier_ratio(self):
        ratios = statistics.calculate_tier_ratio(self.records)
        # 总用电 1820，档1=420, 档2=500, 档3=900
        total = sum(r["usage"] for r in self.records)
        d = {r["tier"]: r["ratio"] for r in ratios}
        self.assertAlmostEqual(sum(d.values()), 1.0, places=2)
        self.assertAlmostEqual(d[1], 420 / total, places=3)


if __name__ == "__main__":
    unittest.main()