# lib/ 目录说明

本目录存放**核心业务逻辑模块**（纯逻辑，不依赖界面、不引入 tkinter）。

| 文件                 | 功能说明                                             |
| -------------------- | ---------------------------------------------------- |
| electricity.py       | 阶梯电费核心算法（分档累加、当前档位、到下一档距离）  |
| fee_calculator.py    | 阶梯电价计算函数 calculate_fee（兼容旧接口）          |
| calculator.py        | 计算器封装（绑定地区档位，产出完整计算结果字典）      |
| tariff_manager.py    | 档位标准管理（增删改查，读写 config/tariffs.json）    |
| history.py           | 历史记录 SQLite 存取与条件查询                       |
| user_manager.py      | 用户名单读取（config/users.json）                    |
| validator.py         | 输入校验（用电量/月份/地区，中文错误提示）           |
| data_loader.py       | CSV 批量导入（逐条算费、跳过错行、GBK/UTF-8 编码识别）、JSON 持久化 |
| importer.py          | CSV 导入（兼容旧接口）                               |
| exporter.py          | CSV/Excel 导出（兼容旧接口）                         |
| report_exporter.py   | 导出（CSV + Excel 多 Sheet、列宽自适应）             |
| statistics.py        | 多维度统计（总量/均值/排行/按用户/按月/档位占比）    |
| summary.py           | 记录汇总指标与格式化文本                             |
| anomaly.py           | 异常用电检测（负值/过高/环比暴涨暴跌/远超均值）      |
| chart_generator.py   | matplotlib 图表生成（返回 Figure，不依赖 tkinter）   |
| logger.py            | 日志系统（文件轮转 + 控制台，data/app.log）          |

## 约定

- `lib/` 不依赖 `ui/`，不引入 tkinter
- 所有核心函数带中文注释与类型提示
- 依赖方向：`ui/ → lib/ → config+data`