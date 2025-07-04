#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试新功能的脚本
包括：
1. 在群牛文件处理
2. 多筛选项逻辑
3. 新的界面布局
"""

import pandas as pd
import os
import sys
import tempfile
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_processor import DataProcessor


def test_active_cattle_processing():
    """测试在群牛文件处理功能"""
    print("=== 测试在群牛文件处理功能 ===")
    
    # 创建测试在群牛文件
    test_data = {
        '耳号': ['001234', '567890', '000999', '123456', '000001'],
        '备注': ['在群', '在群', '在群', '在群', '在群']
    }
    test_df = pd.DataFrame(test_data)
    
    # 保存为临时文件
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        test_df.to_excel(tmp_file.name, index=False)
        tmp_filename = tmp_file.name
    
    try:
        # 测试处理
        processor = DataProcessor()
        success, message, cattle_list = processor.process_active_cattle_file(tmp_filename, "test_active_cattle.xlsx")
        
        print(f"处理结果: {success}")
        print(f"消息: {message}")
        if cattle_list:
            print(f"在群牛列表: {cattle_list}")
            print(f"标准化后的管理号: {cattle_list}")
        
        # 测试筛选功能
        if success:
            # 创建测试DHI数据
            dhi_data = {
                'farm_id': ['001', '001', '001', '001', '001'],
                'management_id': ['1234', '567890', '999', '123456', '2222'],
                'parity': [2, 3, 1, 4, 2],
                'protein_pct': [3.2, 3.8, 3.1, 4.2, 3.5],
                'sample_date': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-15', '2024-01-15']
            }
            dhi_df = pd.DataFrame(dhi_data)
            
            print("\n--- 应用在群牛筛选前 ---")
            print(f"DHI数据行数: {len(dhi_df)}")
            print(dhi_df[['management_id', 'protein_pct']])
            
            filtered_df = processor.apply_active_cattle_filter(dhi_df)
            
            print("\n--- 应用在群牛筛选后 ---")
            print(f"筛选后行数: {len(filtered_df)}")
            if not filtered_df.empty:
                print(filtered_df[['management_id', 'protein_pct']])
        
    finally:
        # 清理临时文件
        os.unlink(tmp_filename)
    
    print("=== 在群牛文件处理功能测试完成 ===\n")


def test_multi_filter_logic():
    """测试多筛选项逻辑"""
    print("=== 测试多筛选项逻辑 ===")
    
    # 创建测试数据
    processor = DataProcessor()
    
    # 模拟多月数据
    data_list = []
    for month in ['2024-01', '2024-02', '2024-03']:
        month_data = {
            'farm_id': ['001'] * 5,
            'management_id': ['1001', '1002', '1003', '1004', '1005'],
            'parity': [2, 3, 1, 4, 2],
            'protein_pct': [3.2, 3.8, 3.1, 4.2, 3.5],
            'somatic_cell_count': [15.5, 45.2, 12.1, 55.8, 25.3],
            'sample_date': [f'{month}-15'] * 5
        }
        df = pd.DataFrame(month_data)
        data_list.append({
            'filename': f'{month}.xlsx',
            'data': df
        })
    
    # 测试筛选条件
    filters = {
        'farm_id': {
            'field': 'farm_id',
            'enabled': True,
            'allowed': ['001']
        },
        'parity': {
            'field': 'parity',
            'enabled': True,
            'min': 1,
            'max': 4
        },
        'protein_pct': {
            'field': 'protein_pct',
            'enabled': True,
            'min': 3.0,
            'max': 4.0,
            'min_match_months': 2,
            'treat_empty_as_match': False
        },
        'somatic_cell_count': {
            'field': 'somatic_cell_count',
            'enabled': True,
            'min': 0,
            'max': 50,
            'min_match_months': 2,
            'treat_empty_as_match': False
        }
    }
    
    selected_files = [item['filename'] for item in data_list]
    
    print("筛选条件:")
    print(f"- 蛋白率: 3.0-4.0%, 最少2个月")
    print(f"- 体细胞数: 0-50万/ml, 最少2个月")
    
    # 执行筛选
    result_df = processor.apply_multi_filter_logic(data_list, filters, selected_files)
    
    print(f"\n筛选结果:")
    print(f"符合条件的数据行数: {len(result_df)}")
    if not result_df.empty:
        print("符合条件的牛只:")
        unique_cows = result_df[['farm_id', 'management_id']].drop_duplicates()
        for _, cow in unique_cows.iterrows():
            print(f"  牛场{cow['farm_id']}-管理号{cow['management_id']}")
    
    print("=== 多筛选项逻辑测试完成 ===\n")


def test_rules_config():
    """测试配置文件加载"""
    print("=== 测试配置文件加载 ===")
    
    processor = DataProcessor()
    
    print("已加载的筛选项配置:")
    filters_config = processor.rules.get("filters", {})
    for filter_name, config in filters_config.items():
        print(f"- {filter_name}: {config.get('chinese_name', filter_name)}")
    
    print("\n可选筛选项配置:")
    optional_filters = processor.rules.get("optional_filters", {})
    for filter_name, config in optional_filters.items():
        print(f"- {filter_name}: {config.get('chinese_name', filter_name)}")
    
    print("\n在群牛配置:")
    active_cattle_config = processor.rules.get("active_cattle", {})
    print(f"- 支持的列名: {active_cattle_config.get('ear_tag_columns', [])}")
    print(f"- 标准化管理号: {active_cattle_config.get('normalize_management_id', False)}")
    
    print("=== 配置文件加载测试完成 ===\n")


def main():
    """主测试函数"""
    print("开始测试新功能...")
    print(f"测试时间: {datetime.now()}")
    print("=" * 50)
    
    try:
        test_rules_config()
        test_active_cattle_processing()
        test_multi_filter_logic()
        
        print("=" * 50)
        print("所有测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 