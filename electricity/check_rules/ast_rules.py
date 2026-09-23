# AST 语法规则检查 — 对指定目录源码做静态扫描
#
# 规则列表（每条规则是独立函数）：
#   S001  禁止使用 eval() / exec()（危险动态执行）
#   S002  禁止在 lib/ / ui/ 业务模块中使用 print() 输出到控制台做调试
#   S003  禁止 config/ 下的文件 import lib/ 的模块（破坏分层单向依赖）
#
# 每条规则函数签名统一为：
#   def 规则名(tree: ast.AST, file_path: str) -> list[str]
#   返回：问题描述列表，空表示通过。

import ast

# 规则说明元数据，供 doc 输出使用
RULES = {
    "S001": "禁止使用 eval()/exec() 动态执行",
    "S002": "禁止在 lib/ ui/ 模块中用 print() 调试",
    "S003": "禁止 config/ 反向 import lib/ 模块",
}


def _eval_calls(tree: ast.AST):
    """生成源码中所有以 eval/exec 说明符命名的调用。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec"}:
                    yield node


def check_s001_eval_exec(tree: ast.AST, file_path: str) -> list[str]:
    """S001：扫描 eval() 与 exec() 动态执行调用。"""
    return [
        "S001 %s:%s 禁止使用 %s() 动态执行代码" % (file_path, node.lineno, node.func.id)
        for node in _eval_calls(tree)
    ]


def check_s002_print(tree: ast.AST, file_path: str) -> list[str]:
    """S002：业务模块（lib/ ui/）中禁用 print() 调试输出，改用 logger。"""
    normalized = file_path.replace("\\", "/")
    if not any(seg in normalized for seg in ("/lib/", "/ui/")):
        return []
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "print":
                issues.append("S002 %s:%s lib/ui 中禁止 print() 调试，请改用 logger"
                              % (file_path, node.lineno))
    return issues


def check_s003_config_import(tree: ast.AST, file_path: str) -> list[str]:
    """S003：config/ 下代码不得 import lib/ 模块，保持单向依赖。"""
    normalized = file_path.replace("\\", "/")
    if "/config/" not in normalized:
        return []
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] == "lib":
                issues.append("S003 %s:%s config/ 中禁止 import lib/ 模块" % (file_path, node.lineno))
        if isinstance(node, ast.Import):
            for alias in node.names:
                if (alias.name or "").split(".")[0] == "lib":
                    issues.append("S003 %s:%s config/ 中禁止 import lib/ 模块" % (file_path, node.lineno))
    return issues


# 全部规则执行器，默认启用所有规则
ALL_RULES = [
    check_s001_eval_exec,
    check_s002_print,
    check_s003_config_import,
]