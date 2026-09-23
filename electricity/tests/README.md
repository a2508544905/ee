# tests/ 目录说明

本目录存放**单元测试**，使用 unittest（兼容 pytest 运行）。

| 文件                 | 覆盖模块                                         |
| -------------------- | ------------------------------------------------ |
| test_fee_calculator.py | 阶梯电价计算（分档、边界、负数报错）              |
| test_calculator.py   | 计算器（当前档位、到下一档距离、预算反推用电量）  |
| test_tariff_manager.py | 档位标准增删改查                                 |
| test_history.py      | 历史记录保存与条件查询                           |
| test_validator.py    | 输入校验（用电量/月份/地区联合校验）              |
| test_data_loader.py  | CSV 导入、单条录入、JSON 持久化、导入错误处理、GBK 编码 |
| test_importer.py     | CSV 批量导入                                     |
| test_exporter.py     | CSV/Excel 导出                                   |
| test_anomaly.py      | 异常用电检测（各规则 + 阈值可配置）               |
| test_statistics.py   | 多维统计函数                                     |
| test_summary.py      | 记录汇总指标与格式化文本                         |

## 运行测试

```bash
python -m unittest discover -s tests -p "test_*.py"
# 或用 pytest
python -m pytest tests/ -v
```