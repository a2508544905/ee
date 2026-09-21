"""验收测试：验证 calculate_fee 对 100、300、500 度的计算结果

运行方式（在 electricity/ 目录下）：
    python -m unittest tests.test_fee_calculator -v
"""

import sys
import os
import unittest

# 确保项目根目录在 sys.path 中，以便导入 lib 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.fee_calculator import calculate_fee


class TestCalculateFee(unittest.TestCase):
    """阶梯电价计算函数验收测试"""

    def test_100_degrees(self):
        """100 度：全部落在第一档（0~200 度，0.5 元/度）"""
        # 手算：100 × 0.5 = 50.00
        self.assertEqual(calculate_fee(100), 50.0)

    def test_300_degrees(self):
        """300 度：跨第一档和第二档"""
        # 手算：200 × 0.5 + 100 × 0.7 = 100 + 70 = 170.00
        self.assertEqual(calculate_fee(300), 170.0)

    def test_500_degrees(self):
        """500 度：跨三档"""
        # 手算：200 × 0.5 + 200 × 0.7 + 100 × 1.0
        #     = 100 + 140 + 100 = 340.00
        self.assertEqual(calculate_fee(500), 340.0)


if __name__ == "__main__":
    unittest.main()