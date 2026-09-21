"""阶梯电费计算器 — 封装计算逻辑，对接档位配置"""

import json
import os

from lib.electricity import calculate_tiered_bill, get_current_tier, get_distance_to_next_tier


class Calculator:
    """电费计算器，绑定一个地区的档位规则后即可反复调用。"""

    def __init__(self, tariff_manager):
        self.tariff_manager = tariff_manager

    def calculate(self, region, usage):
        """计算指定地区、指定用电量的电费。

        Returns:
            dict: {
                "region": "广东",
                "usage": 300,
                "tiers": [...],
                "total": 180.20,
                "current_tier": 2,
                "distance_to_next": {...},
            }
        """
        tiers = self.tariff_manager.get_tiers(region)
        if not tiers:
            raise ValueError(f"未找到地区 '{region}' 的档位配置")

        tier_details, total = calculate_tiered_bill(usage, tiers)
        current = get_current_tier(usage, tiers)
        distance = get_distance_to_next_tier(usage, tiers)

        return {
            "region": region,
            "usage": usage,
            "tiers": tier_details,
            "total": total,
            "current_tier": current,
            "distance_to_next": distance,
        }
