"""chart_generator 图表生成逻辑单元测试"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib import chart_generator  # noqa: E402
from lib.chart_generator import _daily_key  # noqa: E402


def _record(day, hour, usage, total):
    """构造一条测试记录（created_at 为 '2022-09-DD HH:MM:SS'）。"""
    return {"created_at": f"2022-09-{day:02d} {hour:02d}:00:00",
            "usage": usage, "total": total}


class TestDailyKey(unittest.TestCase):
    """_daily_key：把时间戳压缩成 'MM-DD' 日期"""

    def test_压缩到日期粒度(self):
        self.assertEqual(_daily_key("2022-09-09 21:17:00"), "09-09")

    def test_保留原始值(self):
        # 非法输入直接原样返回前 10 位
        self.assertEqual(_daily_key("bad"), "bad")


class TestGenerateTrendChart(unittest.TestCase):
    """generate_trend_chart：按天汇总柱线图"""

    def test_空数据返回空图(self):
        fig = chart_generator.generate_trend_chart([])
        self.assertIsNotNone(fig)

    def test_同天多条记录聚合成一根柱(self):
        rows = [
            _record(9, 9, 100, 50),
            _record(9, 14, 200, 100),
            _record(10, 9, 300, 150),
        ]
        fig = chart_generator.generate_trend_chart(rows)
        ax1 = fig.axes[0]
        bars = [p for p in ax1.patches]
        # 只有 2 天，因此只有 2 根柱子（09-09 与 09-10）
        self.assertEqual(len(bars), 2)

    def test_极端值保留不过滤(self):
        # 35000 度的极端值必须仍然参与绘图（不屏蔽）
        rows = [_record(9, 9, 35000, 29000), _record(10, 9, 100, 50)]
        fig = chart_generator.generate_trend_chart(rows)
        ax1 = fig.axes[0]
        bars = [p for p in ax1.patches]
        self.assertEqual(len(bars), 2)
        heights = [p.get_height() for p in bars]
        self.assertIn(35000.0, heights)  # 极端值柱高完整保留


if __name__ == "__main__":
    unittest.main()