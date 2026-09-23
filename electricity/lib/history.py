"""历史记录管理 — 使用 SQLite 存储和查询计算记录"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.db")


class HistoryManager:
    """管理历史计算记录的存储与查询。"""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or os.path.normpath(DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表结构（含旧库迁移）。"""
        need_columns = ["username", "month"]
        existing_columns = self._get_columns()

        # 老库缺列时补列，全新库则正常建表
        if existing_columns:
            for col in need_columns:
                if col not in existing_columns:
                    self._alter_add_column(col)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at  TEXT    NOT NULL,
                    username    TEXT,
                    month       INTEGER,
                    region      TEXT    NOT NULL,
                    usage       REAL    NOT NULL,
                    total       REAL    NOT NULL,
                    tiers       TEXT    NOT NULL,
                    current_tier INTEGER
                )
            """)
            conn.commit()
            conn.close()

    def _get_columns(self) -> list[str]:
        """返回 history 表的全部列名；表不存在时返回空列表。"""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("PRAGMA table_info(history)").fetchall()
        except sqlite3.OperationalError:
            rows = []
        conn.close()
        return [r[1] for r in rows]

    def _alter_add_column(self, col: str, ddl: str = "TEXT") -> None:
        """给 history 表追加一列。"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(f"ALTER TABLE history ADD COLUMN {col} {ddl}")
        conn.commit()
        conn.close()

    def save(self, region: str, usage: float, total: float, tiers: list[dict[str, Any]],
             current_tier: Optional[int], username: Optional[str] = None,
             month: Optional[int] = None) -> None:
        """保存一条计算记录。

        Args:
            username: 用户名（纯标签，可为空）
            month: 月份（1-12，可为空）
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO history "
            "(created_at, username, month, region, usage, total, tiers, current_tier) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                username,
                month,
                region,
                usage,
                total,
                json.dumps(tiers, ensure_ascii=False),
                current_tier,
            ),
        )
        conn.commit()
        conn.close()

    def query(self, region: Optional[str] = None, min_usage: Optional[float] = None,
              max_usage: Optional[float] = None, username: Optional[str] = None,
              month: Optional[int] = None, limit: int = 100) -> list[dict[str, Any]]:
        """按条件查询历史记录。"""
        conn = sqlite3.connect(self.db_path)
        sql = ("SELECT id, created_at, username, month, region, usage, total, "
               "tiers, current_tier FROM history WHERE 1=1")
        params = []

        if region:
            sql += " AND region = ?"
            params.append(region)
        if username is not None:
            sql += " AND username = ?"
            params.append(username)
        if month is not None:
            sql += " AND month = ?"
            params.append(month)
        if min_usage is not None:
            sql += " AND usage >= ?"
            params.append(min_usage)
        if max_usage is not None:
            sql += " AND usage <= ?"
            params.append(max_usage)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "created_at": r[1],
                "username": r[2],
                "month": r[3],
                "region": r[4],
                "usage": r[5],
                "total": r[6],
                "tiers": json.loads(r[7]),
                "current_tier": r[8],
            }
            for r in rows
        ]

    def clear(self):
        """清空所有历史记录。"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM history")
        conn.commit()
        conn.close()

    def delete_by_id(self, record_id: int) -> bool:
        """按记录 id 删除一条历史记录。

        Args:
            record_id: 要删除的记录 id。

        Returns:
            bool: 是否成功删除了 1 条（不存在则返回 False）。
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted