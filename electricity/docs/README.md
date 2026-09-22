# 阶梯电价可视化计算与查询系统

## 项目简介

基于 Python 桌面端的阶梯电价可视化计算与查询系统。输入用电量即可自动按档位分段计算电费，支持多地区档位切换、用户名单管理、历史记录查询与筛选、异常用电检测、批量导入导出和图形化统计。

## 目录结构

```
electricity/
├── config/                  # 配置文件
│   ├── tariffs.json         #   各地区阶梯电价标准（档位边界 + 单价）
│   └── users.json           #   预置用户名单（A,B,...,AA,AB 列号式）
├── lib/                     # 核心业务逻辑（不依赖界面）
│   ├── electricity.py       #   阶梯电费计算核心算法
│   ├── calculator.py        #   计算器（封装计算逻辑 + 档位配置）
│   ├── tariff_manager.py    #   档位标准管理（增删改查）
│   ├── history.py           #   历史记录存储与筛选查询（SQLite）
│   ├── user_manager.py      #   用户名单管理
│   ├── importer.py          #   CSV 批量导入
│   ├── exporter.py          #   导出 CSV / Excel
│   ├── anomaly.py           #   异常用电检测（负值/过高/环比暴涨）
│   └── logger.py            #   日志系统（文件 + 控制台）
├── ui/                      #   tkinter 界面层
│   ├── main_window.py       #   主窗口：组装面板、编排业务流程
│   ├── input_panel.py       #   输入区（用户/月份/地区/用电量/计算）
│   ├── result_panel.py      #   结果概览卡片
│   ├── record_table.py      #   记录表格（Treeview）
│   ├── more_panel.py        #   更多功能（CSV导入/导出/统计图表）
│   └── chart_view.py        #   图标窗口（趋势/阶梯/用户对比）
├── data/                    # 运行时数据（history.db、app.log）
├── tests/                   # 单元测试
│   ├── test_calculator.py
│   ├── test_fee_calculator.py
│   ├── test_tariff_manager.py
│   ├── test_history.py
│   ├── test_importer.py
│   ├── test_exporter.py
│   └── test_anomaly.py
├── docs/                    # 文档
├── main.py                  # 程序入口（tkinter 主窗口）
├── requirements.txt         # 依赖清单
└── .gitignore
```

## 架构图

```
                    ┌─────────────┐
                    │   main.py   │  程序入口（只负责启动）
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │     ui/（界面层）         │  tkinter
              │  main_window ─ 组装编排   │
              │  input/result/record/    │
              │  more/chart              │
              └──────┬────────────┬──────┘
                     │ 调用        │ 调用
        ┌────────────▼───┐   ┌────▼─────────────┐
        │  lib/（业务层） │   │  ui/chart_view   │ matplotlib
        │  calculator    │   │  （独立图窗）      │
        │  tariff/history│   └──────────────────┘
        │  importer/     │
        │  exporter/     │
        │  anomaly/logger│
        └──────┬────────┘
               │ 读写
     ┌─────────▼──────────┐
     │  config/  data/     │
     │  tariffs.json       │
     │  users.json  history.db  app.log
     └────────────────────┘
```

**依赖方向**：`main.py → ui/ → lib/ → config+data`，单向依赖；`lib/` 不依赖界面、不引入 tkinter。

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 核心开发语言 |
| tkinter + ttk | 桌面 GUI |
| matplotlib | 图表绘制 |
| openpyxl | Excel 读写（导出 .xlsx）|
| SQLite | 历史记录存储 |
| logging | 日志记录 |

## 功能

- 阶梯电价分档计算，价格与档位可从 `config/tariffs.json` 配置
- 多地区档位切换（默认贵州）
- 预置用户名单，下拉选择无需手输姓名
- 历史记录持久化 + 按用户/月份筛选
- CSV 批量导入、导出 CSV / Excel
- 图形化统计：用电趋势、阶梯费用、用户对比
- 异常用电检测：负值 / 过高用电 / 环比暴涨
- 日志系统：`data/app.log` 自动记录关键操作

## 安装与运行

```bash
cd electricity
pip install -r requirements.txt
python main.py
```

在 PyCharm 中直接运行 `main.py` 即可弹出 GUI 窗口。

## 运行测试

```bash
python -m unittest discover -s tests -p "test_*.py"
```