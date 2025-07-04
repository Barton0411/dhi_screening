#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_processor import DataProcessor

# 创建模拟月度报告数据
monthly_data = pd.DataFrame([
    {'farm_id': 'A001', 'management_id': 'C001', '未来泌乳天数(天)': 250},
    {'farm_id': 'A001', 'management_id': 'C002', '未来泌乳天数(天)': 150},
    {'farm_id': 'A001', 'management_id': 'C003', '未来泌乳天数(天)': 350},
    {'farm_id': 'A001', 'management_id': 'C004', '未来泌乳天数(天)': None},
])

print("原始数据:")
print(monthly_data.to_string())

# 创建筛选条件
future_filter = {
    'min': 200,
    'max': 300,
    'include_null_as_match': False
}

processor = DataProcessor()
result = processor.apply_numeric_filter(monthly_data, '未来泌乳天数(天)', future_filter)

print("\n筛选后数据:")
print(result.to_string())
print("\n预期结果：只有C001应该保留（250天在200-300范围内）") 