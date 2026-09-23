# check.py — 静态语法规则检查命令
#
# 用法：
#   python check.py              # 扫描 lib/ ui/ config/ check_rules/
#   python check.py lib ui       # 只扫描指定目录
#   python check.py ./           # 扫描整个项目（跳过无关目录）
#
# 退出码：0 通过；1 存在违规；2 参数错误。
# 与 pytest 结合纳入项目质量门禁：先跑规则，再跑单元测试。

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_rules import ast_rules  # noqa: E402

# 默认扫描目录（相对项目根）
DEFAULT_DIRS = ["lib", "ui", "config", "check_rules"]
# 跳过无需检查的目录（即使被显式指定也不检查）
SKIP_DIRS = {"__pycache__", ".git", "tests", "data", ".pytest_cache"}
SKIP_FILES = {"__init__.py"}


def collect_py_files(dirs: list[str]) -> list[str]:
    """收集指定目录下所有待检查的 .py 文件。"""
    root = os.path.dirname(os.path.abspath(__file__))
    files = []
    for d in dirs:
        base = d if os.path.isabs(d) else os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
            for fn in filenames:
                if fn.endswith(".py") and fn not in SKIP_FILES:
                    files.append(os.path.join(dirpath, fn))
    return files


def run_checks(files: list[str]) -> list[str]:
    """对每个文件执行全部规则，汇总所有违规问题。"""
    all_issues = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=path)
            except SyntaxError as exc:
                all_issues.append("SYNTAX %s 语法错误: %s" % (path, exc))
                continue
        for rule in ast_rules.ALL_RULES:
            all_issues.extend(rule(tree, path))
    return all_issues


def main() -> int:
    """命令入口：解析参数、执行检查、输出结果并返回退出码。"""
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2

    dirs = sys.argv[1:] or DEFAULT_DIRS
    files = collect_py_files(dirs)
    if not files:
        print("警告：未找到任何待检查的 .py 文件")
        return 2

    print("检查 %d 个文件 ...\n" % len(files))
    for code, desc in ast_rules.RULES.items():
        print("  %s  %s" % (code, desc))
    print("-" * 55)

    issues = run_checks(files)
    if not issues:
        print("\nOK：通过全部 %d 条规则，未发现违规。" % len(ast_rules.ALL_RULES))
        return 0

    print("\n发现 %d 处违规：" % len(issues))
    grouped = {}
    for it in issues:
        grouped.setdefault(it.split()[0], []).append(it)
    for code, items in grouped.items():
        print("\n[%s] %s" % (code, ast_rules.RULES.get(code, "")))
        for item in items:
            print("  " + item)
    print("\n检查未通过，请修复后重试。")
    return 1


if __name__ == "__main__":
    sys.exit(main())