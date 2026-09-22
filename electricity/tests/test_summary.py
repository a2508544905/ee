"""summary 模块单元测试 — 覆盖记录汇总统计"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib import summary  # noqa: E402


class TestSummarize(unittest.TestCase):
    """测试汇总统计逻辑"""

    def setUp(self):
        self.records = [
            {"username": "A", "month": 1, "region": "贵州", "usage": 100, "total": 60.0},
            {"username": "A", "month": 2, "region": "贵州", "usage": 200, "total": 130.0},
            {"username": "B", "month": 2, "region": "贵州", "usage": 300, "total": 220.0},
        ]

    def test_空记录(self):
        s = summary.summarize([])
        self.assertEqual(s["count"], 0)
        self.assertEqual(s["total_usage"], 0)
        self.assertEqual(s["total_fee"], 0)
        self.assertEqual(s["avg_fee"], 0)
        self.assertEqual(s["user_count"], 0)

    def test_聚合数值正确(self):
        s = summary.summarize(self.records)
        self.assertEqual(s["count"], 3)
        self.assertEqual(s["total_usage"], 600)
        self.assertEqual(s["total_fee"], 410)
        self.assertAlmostEqual(s["avg_fee"], 410 / 3)

    def test_用户数与月份跨度去重(self):
        s = summary.summarize(self.records)
        self.assertEqual(s["user_count"], 2)
        self.assertEqual(s["month_span"], 2)

    def test_缺失字段不报错(self):
        s = summary.summarize([{"usage": 1}, {"total": 5}])
        self.assertEqual(s["total_usage"], 1)
        self.assertEqual(s["total_fee"], 5)

    def test_格式文本(self):
        text = summary.format_summary_text(summary.summarize(self.records))
        self.assertIn("3 条记录", text)
        self.assertIn("600.0 度", text)
        self.assertIn("2 位用户", text)


if __name__ == "__main__":
    unittest.main()