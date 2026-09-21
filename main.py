"""程序入口（根目录版）— 启动阶梯电价计算与查询系统

PyCharm 打开本目录（D:\\作业）后直接运行本文件即可弹出 GUI。
实际应用位于子目录 electricity/，此处仅做转发。
"""

import os
import sys

# 确保可导入 electricity/ 下的模块
HERE = os.path.dirname(os.path.abspath(__file__))
ELECTRICITY_DIR = os.path.join(HERE, "electricity")
sys.path.insert(0, ELECTRICITY_DIR)

# 复用 electricity/main.py 的入口
from main import main

if __name__ == "__main__":
    main()