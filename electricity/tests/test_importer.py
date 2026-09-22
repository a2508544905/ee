"""importer 模块单元测试"""

import os
import tempfile
import unittest


def _write_csv(path, text):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)


class TestImporter(unittest.TestCase):
    """测试 CSV 批量导入"""

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def _import(self, text, default_region=None):
        _write_csv(self.path, text)
        from lib.importer import read_records
        return read_records(self.path, default_region=default_region)

    def test_带表头导入(self):
        recs = self._import("用户名,月份,地区,用电量\nA,1,贵州,3000\nB,2,贵州,100\n")
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0]["username"], "A")
        self.assertEqual(recs[0]["usage"], 3000)
        self.assertEqual(recs[1]["usage"], 100)

    def test_无表头按位置(self):
        recs = self._import("C,3,贵州,200\nD,4,贵州,5000\n", default_region="贵州")
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0]["username"], "C")
        self.assertEqual(recs[0]["usage"], 200)

    def test_负值被跳过(self):
        recs = self._import("A,1,贵州,3000\nB,1,贵州,-5\n")
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["usage"], 3000)

    def test_空文件抛错(self):
        _write_csv(self.path, "")
        from lib.importer import read_records
        with self.assertRaises(ValueError):
            read_records(self.path)

    def test_default_region_兜底(self):
        # 只有用户名和用电量，用默认地区补全
        recs = self._import("A,1,,3000\n", default_region="广东")
        self.assertEqual(recs[0]["region"], "广东")


if __name__ == "__main__":
    unittest.main()