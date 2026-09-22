"""档位标准管理 — 从 JSON 配置读取/保存档位规则"""

import json
import os

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "tariffs.json")


class TariffManager:
    """管理各地区阶梯电价档位标准的增删改查。"""

    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.normpath(DEFAULT_CONFIG_PATH)
        self._data = {}
        self.load()

    def load(self):
        """从 JSON 文件加载档位配置。"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}

    def save(self):
        """保存档位配置到 JSON 文件。"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_regions(self):
        """返回所有已配置的地区名称列表。"""
        return list(self._data.keys())

    def get_tiers(self, region):
        """获取指定地区的档位列表。"""
        entry = self._data.get(region)
        if entry is None:
            return []
        return entry.get("tiers", [])

    def add_region(self, region, tiers):
        """添加或覆盖一个地区的档位配置。"""
        self._data[region] = {"tiers": tiers}
        self.save()

    def update_tier(self, region, tier_index, new_values):
        """修改指定地区某一档的参数。

        Args:
            region: 地区名
            tier_index: 档位序号（从0开始）
            new_values: 需要修改的字段，如 {"price": 0.62}
        """
        tiers = self.get_tiers(region)
        if not tiers or tier_index >= len(tiers):
            raise IndexError(f"地区 '{region}' 不存在第 {tier_index + 1} 档")
        tiers[tier_index].update(new_values)
        self.save()

    def add_tier(self, region, tier):
        """在指定地区追加一档。调用方需保证边界正确。"""
        tiers = self.get_tiers(region)
        tiers.append(tier)
        self.save()

    def insert_tier(self, region, tier_index, tier):
        """在指定地区的 tier_index 位置插入一档。"""
        tiers = self.get_tiers(region)
        tiers.insert(tier_index, tier)
        self.save()

    def remove_tier(self, region, tier_index):
        """删除指定地区某一档。"""
        tiers = self.get_tiers(region)
        if not tiers or tier_index >= len(tiers):
            raise IndexError(f"地区 '{region}' 不存在第 {tier_index + 1} 档")
        del tiers[tier_index]
        self.save()

    def remove_region(self, region):
        """删除一个地区的档位配置。"""
        if region in self._data:
            del self._data[region]
            self.save()
