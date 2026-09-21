"""历史记录管理 — 使用 SQLite 存储和查询计算记录"""

import sqlite3
import json
import os
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.db")


class HistoryManager:
    """管理历史计算记录的存储与查询。"""

    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.normpath(DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构。"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT    NOT NULL,
                region      TEXT    NOT NULL,
                usage       REAL    NOT NULL,
                total       REAL    NOT NULL,
                tiers       TEXT    NOT NULL,
                current_tier INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def save(self, region, usage, total, tiers, current_tier):
        """保存一条计算记录。"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO history (created_at, region, usage, total, tiers, current_tier) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                region,
                usage,
                total,
                json.dumps(tiers, ensure_ascii=False),
                current_tier,
            ),
        )
        conn.commit()
        conn.close()

    def query(self, region=None, min_usage=None, max_usage=None, limit=100):
        """按条件查询历史记录。"""
        conn = sqlite3.connect(self.db_path)
        sql = "SELECT id, created_at, region, usage, total, tiers, current_tier FROM history WHERE 1=1"
        params = []

        if region:
            sql += " AND region = ?"
            params.append(region)
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
                "region": r[2],
                "usage": r[3],
                "total": r[4],
                "tiers": json.loads(r[5]),
                "current_tier": r[6],
            }
            for r in rows
        ]

    def clear(self):
        """清空所有历史记录。"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM history")
        conn.commit()
        conn.close()
