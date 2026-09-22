"""anomaly 模块单元测试"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib import anomaly  # noqa: E402


class TestAnomaly(unittest.TestCase):
    """测试异常用电检测"""

    def test_负值检测(self):
        recs = [{"username": "A", "region": "贵州", "month": 1, "usage": -50}]
        alerts = anomaly.detect(recs)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["level"], "error")

    def test_过高用电检测(self):
        recs = [{"username": "B", "region": "贵州", "month": 1, "usage": 9999}]
        alerts = anomaly.detect(recs)
        levels = [a["level"] for a in alerts]
        self.assertIn("warn", levels)

    def test_环比暴涨检测(self):
        recs = [
            {"username": "C", "region": "贵州", "month": 1, "usage": 100},
            {"username": "C", "region": "贵州", "month": 2, "usage": 900},  # 9倍
        ]
        alerts = anomaly.detect(recs)
        self.assertTrue(any("暴涨" in a["message"] for a in alerts))

    def test_正常增长不误报(self):
        recs = [
            {"username": "D", "region": "贵州", "month": 1, "usage": 100},
            {"username": "D", "region": "贵州", "month": 2, "usage": 110},  # +10%
        ]
        self.assertEqual(anomaly.detect(recs), [])

    def test_无异常返回空(self):
        recs = [{"username": "E", "region": "贵州", "month": 1, "usage": 200}]
        self.assertEqual(anomaly.detect(recs), [])

    def test_环比暴跌检测(self):
        recs = [
            {"username": "F", "region": "贵州", "month": 1, "usage": 800},
            {"username": "F", "region": "贵州", "month": 2, "usage": 80},  # 剩 10%
        ]
        alerts = anomaly.detect(recs)
        self.assertTrue(any("骤降" in a["message"] for a in alerts))

    def test_远超历史均值检测(self):
        recs = [
            {"username": "G", "region": "贵州", "month": 1, "usage": 100},
            {"username": "G", "region": "贵州", "month": 2, "usage": 120},  # 均值 110
            {"username": "G", "region": "贵州", "month": 3, "usage": 2000},  # 超均值 ~18 倍
        ]
        alerts = anomaly.detect(recs)
        self.assertTrue(any("历史均值" in a["message"] for a in alerts))

    def test_阈值可配置(self):
        # 默认 5000 不报警，调低后报警
        recs = [{"username": "H", "region": "贵州", "month": 1, "usage": 3000}]
        self.assertEqual(anomaly.detect(recs), [])
        alerts = anomaly.detect(recs, excessive=2000)
        self.assertTrue(any("过高" in a["message"] for a in alerts))


if __name__ == "__main__":
    unittest.main()