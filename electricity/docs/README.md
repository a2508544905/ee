# 阶梯电价可视化计算与查询系统

## 项目简介

基于 Python 桌面端的阶梯电价可视化计算与查询系统。输入用电量即可自动按档位分段计算电费，支持多地区档位切换、历史记录查询和批量导入导出。

## 目录结构

```
electricity/
├── config/              # 配置文件
│   └── tariffs.json     #   各地区阶梯电价标准
├── lib/                 # 核心业务逻辑
│   ├── electricity.py   #   阶梯电费计算核心算法
│   ├── calculator.py    #   计算器（封装计算逻辑 + 档位配置）
│   ├── tariff_manager.py#   档位标准管理（增删改查）
│   └── history.py       #   历史记录存储（SQLite）
├── data/                # 数据文件（运行时生成）
├── tests/               # 测试
│   ├── test_calculator.py
│   └── test_tariff_manager.py
├── docs/                # 文档
├── main.py              # 程序入口（tkinter 主窗口）
├── requirements.txt     # 依赖清单
└── .gitignore
```

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 核心开发语言 |
| tkinter | 桌面 GUI |
| matplotlib | 图表绘制 |
| openpyxl | Excel 读写 |
| SQLite | 历史记录存储 |

## 安装与运行

```bash
cd electricity
pip install -r requirements.txt
python main.py
```

## 运行测试

```bash
python -m pytest tests/
```
