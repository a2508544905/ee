# API 索引

本文档索引 `lib/` 目录下核心业务函数，帮助开发者快速定位功能实现与调用方式。

约定：`(self, ...)` 表示类方法，`(...)` 表示模块级函数。

---

## 计算模块

### electricity.py — 阶梯算法

| 函数 | 说明 |
| --- | --- |
| `calculate_tiered_bill(usage, tiers)` | 按给定档位规则计算用电量对应的总电费（元）。 |
| `get_current_tier(usage, tiers)` | 返回当前用电量命中的档位序号与名称。 |
| `get_distance_to_next_tier(usage, tiers)` | 计算距离下一档位还需用电多少度；若已是最高档返回 0。 |
| `estimate_usage_by_budget(budget, tiers)` | 给定预算金额，估算可用的用电量（度）。 |

### fee_calculator.py — 统一入口

| 函数 | 说明 |
| --- | --- |
| `calculate_fee(usage, config_path, region)` | 从配置文件读取指定地区档位后计算电费，返回金额。 |

### calculator.py — 计算服务（UI 使用）

| 方法 | 说明 |
| --- | --- |
| `Calculator.calculate(self, region, usage)` | 计算指定地区用电量的完整结果（总额、档位明细、当前档位）。 |

---

## 数据加载 / 持久化

### data_loader.py — CSV 导入、单条录入、JSON 持久化

| 方法 | 说明 |
| --- | --- |
| `DataLoader.load_csv(self, path, default_region)` | 批量导入 CSV，逐条计算并做错误跳过、重复去重，返回记录列表。 |
| `DataLoader.add_record(self, username, month, region, usage)` | 单条录入并自动计算电费，返回记录。 |
| `DataLoader.save_records(self, records)` | 把记录列表写入 JSON 文件。 |
| `DataLoader.load_records(self)` | 从 JSON 文件读回记录；文件缺失或损坏返回空列表。 |

### importer.py — 简易导入

| 函数 | 说明 |
| --- | --- |
| `read_records(path, default_region)` | 从 CSV 读取并返回规范化的记录列表。 |

### history.py — SQLite 历史记录

| 方法 | 说明 |
| --- | --- |
| `HistoryManager.save(self, region, usage, total, tiers, current_tier, username, month)` | 保存一条计算记录到历史库。 |
| `HistoryManager.query(self, region, min_usage, max_usage, username, month, limit)` | 按条件查询历史记录，支持地区/用量区间/用户/月份过滤。 |
| `HistoryManager.clear(self)` | 清空全部历史记录。 |

---

## 统计 / 汇总

### statistics.py — 多维统计

| 函数 | 说明 |
| --- | --- |
| `calculate_total_fee(records)` | 计算总电费（元）。 |
| `calculate_avg_fee(records)` | 计算平均电费（元/条）。 |
| `get_usage_ranking(records, top)` | 按用电量降序排行，默认 Top 10。 |
| `group_by_user(records)` | 按用户汇总（总用电、总电费、平均月电费）。 |
| `group_by_month(records)` | 按月度汇总（每月总用电、总电费）。 |
| `calculate_tier_ratio(records)` | 计算各档位用电量占比（0~1）。 |

### summary.py — 汇总文本

| 函数 | 说明 |
| --- | --- |
| `summarize(records)` | 聚合统计记录，返回条数/总用电/总电费/平均电费/用户数/月份跨度。 |
| `format_summary_text(summary)` | 将汇总结果格式化为一行中文提示文本。 |

---

## 异常检测

### anomaly.py

| 函数 | 说明 |
| --- | --- |
| `detect(records, excessive, surge, plunge, mean_factor)` | 对记录做异常检测，返回异常条目列表（负值/过高/环比暴涨暴跌/远超历史均值）。 |

---

## 导出

### exporter.py — 简易 CSV/XLSX 导出

| 函数 | 说明 |
| --- | --- |
| `export_csv(records, file_path)` | 导出记录为 CSV。 |
| `export_xlsx(records, file_path)` | 导出记录为 XLSX（需 openpyxl）。 |
| `export_alerts(alerts, file_path)` | 导出异常告警列表。 |
| `export(records, file_path)` | 按扩展名自动选择导出格式。 |

### report_exporter.py — 报表导出（多 Sheet）

| 函数 | 说明 |
| --- | --- |
| `export_csv(records, file_path)` | 导出原始数据为 CSV。 |
| `export_excel(records, file_path)` | 导出多 Sheet 报表（原始数据 + 用户汇总）。 |
| `export(records, file_path)` | 按扩展名自动选择导出格式。 |

---

## 图表生成（业务层，不依赖 tkinter）

### chart_generator.py

| 函数 | 说明 |
| --- | --- |
| `generate_trend_chart(records)` | 用电趋势图（横轴时间，左轴电量右轴电费的双轴图）。 |
| `generate_tier_chart(result)` | 阶梯费用面积图（按档位划分收费构成）。 |
| `generate_user_chart(records)` | 用户对比柱状图。 |
| `generate_tier_distribution_chart(records)` | 各档位用电量分布图。 |
| `generate_fee_composition_chart(result)` | 电费构成占比图。 |

---

## 配置管理

### tariff_manager.py — 档位规则

| 方法 | 说明 |
| --- | --- |
| `load(self)` / `save(self)` | 从/向配置文件读/写档位数据。 |
| `get_regions(self)` | 返回全部地区。 |
| `get_tiers(self, region)` | 返回指定地区的档位列表。 |
| `add_region(self, region, tiers)` / `remove_region(self, region)` | 新增/删除地区。 |
| `update_tier(self, region, tier_index, new_values)` | 更新某个档位的价格/上限。 |
| `add_tier` / `insert_tier` / `remove_tier` | 新增、插入、删除档位。 |

### user_manager.py — 用户名单

| 方法 | 说明 |
| --- | --- |
| `get_users(self)` | 返回全部用户标识列表。 |
| `get_count(self)` | 返回用户总数。 |
| `contains(self, name)` | 判断名单中是否包含指定用户。 |

---

## 校验 / 日志

### validator.py — 输入校验（业务层）

| 函数 | 说明 |
| --- | --- |
| `parse_usage(value_text)` | 解析用电量文本，非法返回 None。 |
| `parse_month(value_text)` | 解析月份文本，非法返回 None。 |
| `validate_record(text_username, text_month, region, text_usage)` | 校验一条记录，返回 (record, errors)；非法时给出中文错误。 |

### logger.py — 日志系统

| 函数 | 说明 |
| --- | --- |
| `get_logger(name)` | 获取（或创建）一个 logger 实例。 |
| `setup_logger(name, level)` | 初始化文件 + 控制台双端日志输出。 |