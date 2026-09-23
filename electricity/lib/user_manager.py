"""用户名单管理 — 从 config/users.json 读取 Excel 列号进位形式的用户标识"""

import json
import os
from typing import Optional

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
_USERS_FILE = os.path.join(_CONFIG_DIR, "users.json")


class UserManager:
    """管理预置的用户名单。

    名单用 Excel 列号进位形式命名（A,B,...,Z,AA,AB,...），
    供界面下拉选择，避免用户手动输入姓名。
    """

    def __init__(self, file_path: Optional[str] = _USERS_FILE) -> None:
        """从指定文件加载名单；文件不存在或损坏时返回空名单。"""
        self._file_path = file_path
        self._users = self._load()

    def _load(self) -> list[str]:
        """读取名单文件，异常时返回空列表。"""
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            users = data.get("users", [])
            return [str(u).strip() for u in users if str(u).strip()]
        except (OSError, ValueError, json.JSONDecodeError):
            return []

    def get_users(self) -> list[str]:
        """返回全部用户名列表（保持文件顺序）。"""
        return list(self._users)

    def get_count(self) -> int:
        """返回名单人数。"""
        return len(self._users)

    def contains(self, name: str) -> bool:
        """判断某用户是否在名单中。"""
        return name in self._users