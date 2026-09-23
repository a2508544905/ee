# run_all.py — 规则指定的检查命令入口（薄包装）
#
# 规则文件约定 `python check_rules/run_all.py` 为检查入口，
# 此处复用 check.py 的完整逻辑，保持与 `python check.py` 行为一致。

import os
import subprocess
import sys

sys.exit(subprocess.call([sys.executable, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "check.py")] + sys.argv[1:]))