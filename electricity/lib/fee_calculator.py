"""阶梯电价计算模块

从配置文件读取阶梯档位规则，按分段计算电费。
"""

import json
import os

# 配置文件默认路径
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "tariffs.json")


def _load_tiers(config_path=None, region="默认"):
    """从配置文件加载指定地区的阶梯档位规则。

    Args:
        config_path: 配置文件路径，默认使用 CONFIG_PATH
        region: 地区名称，默认"默认"

    Returns:
        list: 档位列表，如 [{"min": 0, "max": 200, "price": 0.5}, ...]
    """
    path = config_path or os.path.normpath(CONFIG_PATH)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if region not in data:
        raise ValueError(f"配置文件中未找到地区 '{region}'")

    return data[region]["tiers"]


def calculate_fee(usage, config_path=None, region="默认"):
    """阶梯电价计算函数。

    根据配置文件中的阶梯档位规则，分段计算电费：
      - 第一档：0~200 度，0.5 元/度
      - 第二档：200~400 度，0.7 元/度
      - 第三档：400 度以上，0.7 元/度
    （以上为"默认"地区的档位，实际从配置文件读取）

    Args:
        usage: 用电量（度），必须为非负数
        config_path: 配置文件路径，默认使用 CONFIG_PATH
        region: 地区名称，默认"默认"

    Returns:
        float: 总电费，保留两位小数

    Raises:
        ValueError: 当用电量为负数时抛出
    """
    # 输入校验：负数用电量不合法
    if usage < 0:
        raise ValueError("用电量不能为负数")

    # 从配置文件加载阶梯档位规则
    tiers = _load_tiers(config_path, region)

    # 分段计算电费
    total_fee = 0.0

    for tier in tiers:
        tier_min = tier["min"]       # 该档下限
        tier_max = tier["max"]        # 该档上限（None 表示无上限）
        tier_price = tier["price"]    # 该档单价

        # 用电量未进入该档，跳过
        if usage <= tier_min:
            break

        # 计算该档实际用电量
        if tier_max is None or usage < tier_max:
            # 用电量在本档范围内，取差额
            tier_usage = usage - tier_min
        else:
            # 用电量超过本档上限，取整档容量
            tier_usage = tier_max - tier_min

        # 累加该档电费
        total_fee += tier_usage * tier_price

    # 保留两位小数
    return round(total_fee, 2)
