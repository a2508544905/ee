"""check_rules/ast_rules 规则逻辑单元测试"""

import ast
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from check_rules.ast_rules import (  # noqa: E402
    check_s001_eval_exec,
    check_s002_print,
    check_s003_config_import,
)


def _parse(src: str) -> ast.AST:
    """解析源码为语法树。"""
    return ast.parse(src)


class TestS001(unittest.TestCase):
    """S001：禁止 eval()/exec()"""

    def test_eval被拦截(self):
        self.assertTrue(check_s001_eval_exec(_parse("eval(x)\n"), "lib/a.py"))

    def test_exec被拦截(self):
        self.assertTrue(check_s001_eval_exec(_parse("exec(code)\n"), "lib/a.py"))

    def test普通调用放行(self):
        self.assertEqual(check_s001_eval_exec(_parse("print('ok')\n"), "lib/a.py"), [])


class TestS002(unittest.TestCase):
    """S002：lib/ui 中禁止 print"""

    def test_lib下print被拦截(self):
        self.assertTrue(check_s002_print(_parse("print(1)\n"), "/proj/lib/x.py"))

    def test_ui下print被拦截(self):
        self.assertTrue(check_s002_print(_parse("print(1)\n"), "/proj/ui/x.py"))

    def test_config下print放行(self):
        self.assertEqual(check_s002_print(_parse("print(1)\n"), "/proj/config/x.py"), [])


class TestS003(unittest.TestCase):
    """S003：config 反向 import lib 被拦截"""

    def test_config_import_lib被拦截(self):
        self.assertTrue(check_s003_config_import(_parse("from lib import a\n"), "/proj/config/x.py"))

    def test_config其他import放行(self):
        self.assertEqual(check_s003_config_import(_parse("import json\n"), "/proj/config/x.py"), [])

    def test_lib文件不受影响(self):
        self.assertEqual(check_s003_config_import(_parse("from lib import a\n"), "/proj/lib/x.py"), [])


if __name__ == "__main__":
    unittest.main()