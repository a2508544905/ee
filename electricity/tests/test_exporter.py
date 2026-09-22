"""exporter 模块单元测试"""

import os
import tempfile
import unittest


class TestExporter(unittest.TestCase):
    """测试记录导出"""

    def setUp(self):
        self.records = [
            {"username": "A", "month": 1, "region": "贵州", "usage": 3000,
             "total": 1366.8, "current_tier": 2, "created_at": "2026-09-22 10:00:00"},
            {"username": "B", "month": 2, "region": "贵州", "usage": 100,
             "total": 45.56, "current_tier": 1, "created_at": "2026-09-22 10:01:00"},
        ]

    def test_export_csv(self):
        from lib.exporter import export_csv
        path = os.path.join(tempfile.gettempdir(), "exp_test.csv")
        n = export_csv(self.records, path)
        self.assertEqual(n, 2)
        with open(path, encoding="utf-8-sig") as f:
            lines = f.read().strip().splitlines()
        self.assertEqual(len(lines), 3)  # 表头 + 2 行
        self.assertIn("用电量(度)", lines[0])
        os.remove(path)

    def test_export_xlsx(self):
        from lib.exporter import export_xlsx
        path = os.path.join(tempfile.gettempdir(), "exp_test.xlsx")
        n = export_xlsx(self.records, path)
        self.assertEqual(n, 2)
        self.assertTrue(os.path.exists(path))
        os.remove(path)

    def test_export_按扩展名分发(self):
        from lib.exporter import export
        csv_path = os.path.join(tempfile.gettempdir(), "a.csv")
        xlsx_path = os.path.join(tempfile.gettempdir(), "a.xlsx")
        self.assertEqual(export(self.records, csv_path), 2)
        self.assertEqual(export(self.records, xlsx_path), 2)
        os.remove(csv_path)
        os.remove(xlsx_path)

    def test_不支持格式抛错(self):
        from lib.exporter import export
        path = os.path.join(tempfile.gettempdir(), "a.txt")
        with self.assertRaises(ValueError):
            export(self.records, path)


if __name__ == "__main__":
    unittest.main()