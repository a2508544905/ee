"""validator 模块单元测试 — 覆盖输入校验与错误处理"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib import validator  # noqa: E402


class TestValidateRecord(unittest.TestCase):
    """测试整条记录的统一校验"""

    def test_合法输入(self):
        rec = validator.validate_record("A", "3", "贵州", "300")
        self.assertEqual(rec, {"username": "A", "month": 3, "region": "贵州", "usage": 300.0})

    def test_用户名和月份可为空(self):
        rec = validator.validate_record("", "", "贵州", "100")
        self.assertEqual(rec["username"], "")
        self.assertIsNone(rec["month"])

    def test_地区为空报错(self):
        with self.assertRaises(ValueError) as ctx:
            validator.validate_record("A", "1", "  ", "100")
        self.assertIn("选择地区", str(ctx.exception))

    def test_用电量为空报错(self):
        with self.assertRaises(ValueError) as ctx:
            validator.validate_record("A", "1", "贵州", "   ")
        self.assertIn("请输入用电量", str(ctx.exception))

    def test_用电量非数字报错(self):
        with self.assertRaises(ValueError) as ctx:
            validator.validate_record("A", "1", "贵州", "abc")
        self.assertIn("有效数字", str(ctx.exception))

    def test_用电量为负报错(self):
        with self.assertRaises(ValueError) as ctx:
            validator.validate_record("A", "1", "贵州", "-50")
        self.assertIn("负数", str(ctx.exception))

    def test_用电量过大报错(self):
        with self.assertRaises(ValueError) as ctx:
            validator.validate_record("A", "1", "贵州", str(validator.MAX_USAGE + 1))
        self.assertIn("过大", str(ctx.exception))

    def test_月份超范围报错(self):
        with self.assertRaises(ValueError) as ctx:
            validator.validate_record("A", "13", "贵州", "100")
        self.assertIn("1-12", str(ctx.exception))


class TestParseUsage(unittest.TestCase):
    """测试 parse_usage 独立解析"""

    def test_解析整数和浮点(self):
        self.assertEqual(validator.parse_usage("300"), 300.0)
        self.assertEqual(validator.parse_usage(150.5), 150.5)

    def test_去掉首尾空格(self):
        self.assertEqual(validator.parse_usage("  260  "), 260.0)

    def test_无穷与NaN拒绝(self):
        with self.assertRaises(ValueError):
            validator.parse_usage("nan")
        with self.assertRaises(ValueError):
            validator.parse_usage("inf")


class TestParseMonth(unittest.TestCase):
    """测试 parse_month 独立解析"""

    def test_合法月份(self):
        self.assertEqual(validator.parse_month("5"), 5)
        self.assertEqual(validator.parse_month(12), 12)

    def test_空返回None(self):
        self.assertIsNone(validator.parse_month(""))
        self.assertIsNone(validator.parse_month(None))

    def test_非法月份(self):
        with self.assertRaises(ValueError):
            validator.parse_month("0")
        with self.assertRaises(ValueError):
            validator.parse_month("13")
        with self.assertRaises(ValueError):
            validator.parse_month("abc")


if __name__ == "__main__":
    unittest.main()