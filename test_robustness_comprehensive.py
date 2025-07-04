#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DHI蛋白筛查系统 - 全面强壮度测试
测试数据格式一致性、重复数据检测、胎次功能、取数逻辑、算法正确性等
"""

import sys
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor import DataProcessor

def run_comprehensive_tests():
    """运行全面的强壮度测试"""
    print("DHI蛋白筛查系统 - 全面强壮度测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "测试数据")
    dhi_dir = os.path.join(test_data_dir, "DHI报告")
    
    processor = DataProcessor()
    
    # 1. 文件处理强壮度测试
    print("\n" + "="*70)
    print("1. 文件处理强壮度测试")
    print("="*70)
    
    dhi_files = []
    if os.path.exists(dhi_dir):
        for file in os.listdir(dhi_dir):
            if file.endswith(('.xlsx', '.xls', '.zip')):
                file_path = os.path.join(dhi_dir, file)
                dhi_files.append((file_path, file))
    
    print(f"找到{len(dhi_files)}个DHI文件")
    
    all_data = []
    success_count = 0
    failed_count = 0
    
    for file_path, filename in dhi_files:
        try:
            print(f"  处理: {filename}")
            success, message, df = processor.process_uploaded_file(file_path, filename)
            
            if success and df is not None and not df.empty:
                all_data.append({'filename': filename, 'data': df})
                success_count += 1
                print(f"    ✅ 成功: {len(df)}行数据")
            else:
                failed_count += 1
                print(f"    ❌ 失败: {message}")
                
        except Exception as e:
            failed_count += 1
            print(f"    ❌ 异常: {str(e)}")
    
    print(f"\n文件处理结果: 成功{success_count}个, 失败{failed_count}个")
    
    # 2. 重复数据检测测试
    print("\n" + "="*70)
    print("2. 重复数据检测测试")
    print("="*70)
    
    if len(all_data) >= 2:
        duplicate_result = processor.detect_duplicate_data(all_data)
        print(f"重复检测结果:")
        print(f"  总文件数: {duplicate_result['total_files']}")
        print(f"  重复组数: {len(duplicate_result['duplicate_groups'])}")
        print(f"  涉及文件: {duplicate_result['duplicate_files_count']}")
        
        if duplicate_result['has_duplicates']:
            for i, group in enumerate(duplicate_result['duplicate_groups'], 1):
                print(f"  重复组{i}:")
                for item in group:
                    filename = item['filename']
                    score = item.get('similarity_score', 'N/A')
                    print(f"    - {filename} (相似度: {score})")
    else:
        print("文件数量不足，跳过重复检测测试")
    
    # 3. 胎次功能测试
    print("\n" + "="*70)
    print("3. 胎次功能测试")
    print("="*70)
    
    # 3.1 胎次筛选测试
    print("\n  3.1 胎次筛选测试:")
    test_data = pd.DataFrame([
        {'farm_id': '12345', 'management_id': '001', 'parity': 1, 'sample_date': '2023-01-15', 'protein_pct': 3.2},
        {'farm_id': '12345', 'management_id': '001', 'parity': 2, 'sample_date': '2023-08-15', 'protein_pct': 3.5},
        {'farm_id': '12345', 'management_id': '001', 'parity': 3, 'sample_date': '2024-05-15', 'protein_pct': 3.7},
        {'farm_id': '12345', 'management_id': '002', 'parity': 2, 'sample_date': '2023-06-15', 'protein_pct': 3.4},
        {'farm_id': '12345', 'management_id': '003', 'parity': 1, 'sample_date': '2024-01-15', 'protein_pct': 3.3},
    ])
    
    parity_filter = {'field': 'parity', 'enabled': True, 'min': 2, 'max': 3}
    filtered_data = processor._apply_parity_filter(test_data, parity_filter)
    
    expected_records = 3  # 牛001的2、3胎 + 牛002的2胎
    actual_records = len(filtered_data)
    
    print(f"    原始数据: {len(test_data)}条记录")
    print(f"    筛选条件: 2-3胎")
    print(f"    期望结果: {expected_records}条记录")
    print(f"    实际结果: {actual_records}条记录")
    print(f"    测试结果: {'✅ 通过' if actual_records == expected_records else '❌ 失败'}")
    
    # 3.2 最后一次采样胎次测试
    print("\n  3.2 最后一次采样胎次测试:")
    test_data_parity = pd.DataFrame([
        {'farm_id': '12345', 'management_id': '001', 'parity': 1, 'sample_date': '2023-01-15', 'protein_pct': 3.2, 'milk_yield': 25},
        {'farm_id': '12345', 'management_id': '001', 'parity': 3, 'sample_date': '2024-05-15', 'protein_pct': 3.7, 'milk_yield': 35},
    ])
    
    try:
        monthly_report = processor.create_monthly_report(test_data_parity, ['farm_id', 'management_id', 'parity'])
        
        if monthly_report is not None and not monthly_report.empty and 'parity' in monthly_report.columns:
            actual_parity = monthly_report.iloc[0]['parity']
            expected_parity = 3  # 最后一次采样是3胎
            print(f"    期望胎次: {expected_parity}")
            print(f"    实际胎次: {actual_parity}")
            print(f"    测试结果: {'✅ 通过' if actual_parity == expected_parity else '❌ 失败'}")
        elif monthly_report is None:
            print(f"    ❌ 月度报告生成失败: 返回None")
        elif monthly_report.empty:
            print(f"    ❌ 月度报告生成失败: 返回空DataFrame")
        else:
            print(f"    ❌ 月度报告缺少胎次列: 列名={monthly_report.columns.tolist()}")
    except Exception as e:
        print(f"    ❌ 月度报告生成异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 3.3 在群牛胎次列测试
    print("\n  3.3 在群牛胎次列测试:")
    
    try:
        # 启用在群牛筛选
        processor.active_cattle_enabled = True
        monthly_report_active = processor.create_monthly_report(test_data_parity, ['farm_id', 'management_id', 'parity'])
        has_active_column = monthly_report_active is not None and '在群牛胎次' in monthly_report_active.columns
        
        # 不启用在群牛筛选
        processor.active_cattle_enabled = False
        monthly_report_inactive = processor.create_monthly_report(test_data_parity, ['farm_id', 'management_id', 'parity'])
        no_active_column = monthly_report_inactive is not None and '在群牛胎次' not in monthly_report_inactive.columns
        
        print(f"    启用在群牛筛选时添加在群牛胎次列: {'✅ 通过' if has_active_column else '❌ 失败'}")
        print(f"    不启用时不添加在群牛胎次列: {'✅ 通过' if no_active_column else '❌ 失败'}")
    except Exception as e:
        print(f"    ❌ 在群牛胎次列测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 4. 数据格式一致性测试
    print("\n" + "="*70)
    print("4. 数据格式一致性测试")
    print("="*70)
    
    if len(all_data) >= 2:
        print("检查关键字段的格式一致性:")
        
        # 检查牧场编号一致性
        farm_ids = set()
        for item in all_data:
            df = item['data']
            if 'farm_id' in df.columns:
                file_farm_ids = df['farm_id'].dropna().unique()
                farm_ids.update(file_farm_ids.astype(str))
        
        print(f"  牧场编号: {sorted(farm_ids)}")
        if len(farm_ids) == 1:
            print(f"    ✅ 所有文件来自同一牧场")
        else:
            print(f"    ⚠️  发现多个牧场编号，将触发统一功能")
        
        # 检查数据类型一致性
        field_types = {}
        for item in all_data[:3]:  # 检查前3个文件
            df = item['data']
            filename = item['filename']
            
            for field in ['protein_pct', 'parity', 'management_id']:
                if field in df.columns:
                    if field not in field_types:
                        field_types[field] = {}
                    field_types[field][filename] = str(df[field].dtype)
        
        for field, file_types in field_types.items():
            types = set(file_types.values())
            if len(types) == 1:
                print(f"  {field}: ✅ 类型一致 ({types.pop()})")
            else:
                print(f"  {field}: ⚠️  类型不一致 ({types})")
    
    # 5. 算法准确性测试
    print("\n" + "="*70)
    print("5. 算法准确性测试")
    print("="*70)
    
    if all_data:
        print("测试多筛选项逻辑:")
        
        test_files = all_data[:2]  # 使用前2个文件
        filters = {
            'protein_pct': {
                'field': 'protein_pct',
                'enabled': True,
                'min': 3.0,
                'max': 4.0,
                'min_match_months': 1,
                'treat_empty_as_match': False
            }
        }
        
        selected_files = [item['filename'] for item in test_files]
        
        try:
            result = processor.apply_multi_filter_logic(test_files, filters, selected_files)
            print(f"  筛选条件: 蛋白率3.0-4.0%")
            print(f"  筛选结果: {len(result)}条记录")
            
            if not result.empty and 'protein_pct' in result.columns:
                protein_values = result['protein_pct'].dropna()
                if len(protein_values) > 0:
                    min_protein = protein_values.min()
                    max_protein = protein_values.max()
                    print(f"  结果范围: {min_protein:.2f}% - {max_protein:.2f}%")
                    
                    in_range = (min_protein >= 3.0) and (max_protein <= 4.0)
                    print(f"  范围检查: {'✅ 通过' if in_range else '❌ 失败'}")
                else:
                    print(f"  ❌ 结果中无有效蛋白率数据")
            
            print(f"  筛选执行: ✅ 成功")
            
        except Exception as e:
            print(f"  筛选执行: ❌ 失败 - {str(e)}")
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)

if __name__ == "__main__":
    run_comprehensive_tests()
    input("\n按回车键退出...") 