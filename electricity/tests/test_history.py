"""history 模块单元测试（含筛选查询）"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.history import HistoryManager  # noqa: E402


class TestHistory(unittest.TestCase):
    """测试历史记录的保存与筛选查询"""

    def setUp(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.h = HistoryManager(db_path=path)
        self.h.clear()

    def tearDown(self):
        if os.path.exists(self.h.db_path):
            os.remove(self.h.db_path)

    def test_保存并读取(self):
        self.h.save("贵州", 300, 1366.8, [], 2, username="A", month=1)
        rows = self.h.query()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["username"], "A")
        self.assertEqual(rows[0]["month"], 1)
        self.assertEqual(rows[0]["usage"], 300)

    def test_按用户筛选(self):
        self.h.save("贵州", 100, 45.56, [], 1, username="A", month=1)
        self.h.save("贵州", 200, 91.12, [], 1, username="B", month=1)
        rows = self.h.query(username="A")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["username"], "A")

    def test_按用户加月份筛选(self):
        self.h.save("贵州", 100, 45.56, [], 1, username="A", month=1)
        self.h.save("贵州", 200, 91.12, [], 1, username="A", month=2)
        rows = self.h.query(username="A", month=2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["month"], 2)

    def test_clear清空(self):
        self.h.save("贵州", 100, 45.56, [], 1, username="A", month=1)
        self.h.clear()
        self.assertEqual(self.h.query(), [])


if __name__ == "__main__":
    unittest.main()