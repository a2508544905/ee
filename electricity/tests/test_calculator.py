"""测试阶梯电费计算引擎"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.electricity import calculate_tiered_bill, get_current_tier, get_distance_to_next_tier, estimate_usage_by_budget

TIERS = [
    {"min": 0, "max": 260, "price": 0.59},
    {"min": 260, "max": 600, "price": 0.64},
    {"min": 600, "max": None, "price": 0.89},
]


def test_normal_first_tier():
    """用电量在第一档内"""
    result, total = calculate_tiered_bill(200, TIERS)
    assert len(result) == 1
    assert result[0]["tier"] == 1
    assert result[0]["usage"] == 200
    assert total == 118.0


def test_cross_tier_boundary():
    """用电量跨档（第一档 + 第二档）"""
    result, total = calculate_tiered_bill(400, TIERS)
    assert len(result) == 2
    assert result[0]["usage"] == 260
    assert result[1]["usage"] == 140
    assert total == round(260 * 0.59 + 140 * 0.64, 2)


def test_third_tier():
    """用电量进入第三档"""
    result, total = calculate_tiered_bill(800, TIERS)
    assert len(result) == 3
    assert result[2]["usage"] == 200


def test_zero_usage():
    """零度"""
    result, total = calculate_tiered_bill(0, TIERS)
    assert result == []
    assert total == 0.0


def test_negative_usage():
    """负数用电量"""
    result, total = calculate_tiered_bill(-10, TIERS)
    assert result == []
    assert total == 0.0


def test_boundary_exact():
    """正好在档位边界"""
    result, total = calculate_tiered_bill(260, TIERS)
    assert len(result) == 1
    assert result[0]["usage"] == 260


def test_current_tier():
    current = get_current_tier(200, TIERS)
    assert current == 1
    current = get_current_tier(300, TIERS)
    assert current == 2
    current = get_current_tier(700, TIERS)
    assert current == 3


def test_distance_to_next_tier():
    dist = get_distance_to_next_tier(250, TIERS)
    assert dist["next_tier"] == 2
    assert dist["remaining"] == 10


def test_distance_at_max_tier():
    dist = get_distance_to_next_tier(700, TIERS)
    assert dist["next_tier"] is None


def test_estimate_usage_by_budget():
    usage = estimate_usage_by_budget(118.0, TIERS)
    assert abs(usage - 200.0) < 1


def test_estimate_large_budget():
    usage = estimate_usage_by_budget(1000.0, TIERS)
    assert usage > 600
