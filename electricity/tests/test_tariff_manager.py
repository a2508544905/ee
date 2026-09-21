"""测试档位标准管理"""

import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.tariff_manager import TariffManager


def _make_manager(tiers_data):
    """用临时文件创建 TariffManager。"""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tiers_data, f, ensure_ascii=False)
    return TariffManager(path)


def test_get_regions():
    mgr = _make_manager({
        "广东": {"tiers": [{"min": 0, "max": 260, "price": 0.59}]},
        "北京": {"tiers": [{"min": 0, "max": 240, "price": 0.49}]},
    })
    regions = mgr.get_regions()
    assert "广东" in regions
    assert "北京" in regions


def test_get_tiers():
    mgr = _make_manager({
        "广东": {"tiers": [
            {"min": 0, "max": 260, "price": 0.59},
            {"min": 260, "max": 600, "price": 0.64},
        ]},
    })
    tiers = mgr.get_tiers("广东")
    assert len(tiers) == 2
    assert tiers[0]["price"] == 0.59


def test_get_tiers_nonexistent():
    mgr = _make_manager({})
    assert mgr.get_tiers("不存在") == []


def test_add_region():
    mgr = _make_manager({})
    mgr.add_region("深圳", [{"min": 0, "max": 200, "price": 0.60}])
    assert "深圳" in mgr.get_regions()
    assert mgr.get_tiers("深圳")[0]["price"] == 0.60


def test_update_tier():
    mgr = _make_manager({
        "广东": {"tiers": [{"min": 0, "max": 260, "price": 0.59}]},
    })
    mgr.update_tier("广东", 0, {"price": 0.62})
    assert mgr.get_tiers("广东")[0]["price"] == 0.62


def test_remove_region():
    mgr = _make_manager({
        "广东": {"tiers": [{"min": 0, "max": 260, "price": 0.59}]},
    })
    mgr.remove_region("广东")
    assert "广东" not in mgr.get_regions()
