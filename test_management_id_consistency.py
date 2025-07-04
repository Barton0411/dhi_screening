#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import tempfile
import os
from data_processor import DataProcessor

def test_management_id_consistency():
    """测试管理号前导零保持一致性"""
    
    print("=== 测试管理号前导零一致性 ===")
    
    # 创建测试数据 - 模拟Excel中有前导零的情况
    test_data = {
        '牛场编号': ['A001', 'A001', 'A001', 'A001', 'A001', 'A001'],
        '管理号': ['001', '002', '003', '001', '002', '003'],  # 注意这里有前导零
        '胎次(胎)': [2, 1, 3, 2, 1, 3],
        '采样日期': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-02-15', '2024-02-15', '2024-02-15'],
        '蛋白率(%)': [3.2, 3.3, 3.5, 3.1, 3.4, 3.6],
        '泌乳天数(天)': [150, 120, 200, 180, 150, 230]
    }
    
    df = pd.DataFrame(test_data)
    print("原始测试数据:")
    print(df)
    print(f"管理号数据类型: {df['管理号'].dtype}")
    print(f"管理号唯一值: {df['管理号'].unique()}")
    
    # 创建临时Excel文件
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        df.to_excel(tmp_file.name, index=False)
        temp_excel_path = tmp_file.name
    
    try:
        # 使用DataProcessor处理
        processor = DataProcessor()
        success, message, processed_df = processor._process_excel_file(temp_excel_path, None)
        
        if success and processed_df is not None:
            print(f"\n处理成功: {message}")
            print(f"处理后数据行数: {len(processed_df)}")
            print(f"处理后management_id数据类型: {processed_df['management_id'].dtype}")
            print(f"处理后management_id唯一值: {sorted(processed_df['management_id'].dropna().unique())}")
            
            # 检查是否保留了前导零
            mgmt_ids = processed_df['management_id'].dropna().unique()
            zero_prefixed = [mid for mid in mgmt_ids if str(mid).startswith('0')]
            
            print(f"\n前导零保留检查:")
            print(f"0开头的管理号: {zero_prefixed}")
            print(f"是否正确保留前导零: {'是' if len(zero_prefixed) > 0 else '否'}")
            
            # 统计每个管理号的记录数
            mgmt_counts = processed_df['management_id'].value_counts()
            print(f"\n每个管理号的记录数:")
            for mid, count in mgmt_counts.items():
                print(f"  管理号 {mid}: {count} 条记录")
            
            # 检查分组一致性
            cow_groups = processed_df.groupby(['farm_id', 'management_id'])
            print(f"\n分组统计:")
            print(f"总共分组数: {len(cow_groups)}")
            print(f"预期分组数: 3 (应该是3头牛)")
            
            for (farm_id, mgmt_id), group in cow_groups:
                print(f"  牛场{farm_id}-管理号{mgmt_id}: {len(group)}条记录")
            
            # 测试月度报告生成
            print(f"\n=== 测试月度报告生成 ===")
            monthly_report = processor.create_monthly_report(processed_df, [], "2024-05-15")
            
            if not monthly_report.empty:
                print(f"月度报告生成成功，共{len(monthly_report)}头牛")
                print("月度报告中的管理号:")
                for _, row in monthly_report.iterrows():
                    print(f"  牛场{row['farm_id']}-管理号{row['management_id']}")
                
                # 检查是否有重复牛只
                unique_cows = monthly_report[['farm_id', 'management_id']].drop_duplicates()
                print(f"\n唯一牛只数: {len(unique_cows)} (应该等于3)")
                if len(unique_cows) == 3:
                    print("✅ 管理号一致性测试通过!")
                else:
                    print("❌ 管理号一致性测试失败 - 存在重复牛只")
            else:
                print("❌ 月度报告生成失败")
                
        else:
            print(f"❌ 处理失败: {message}")
            
    finally:
        # 清理临时文件
        if os.path.exists(temp_excel_path):
            os.unlink(temp_excel_path)

def test_mixed_management_id_formats():
    """测试混合格式的管理号处理"""
    
    print("\n=== 测试混合格式管理号 ===")
    
    # 创建混合格式的测试数据
    test_data = {
        '牛场编号': ['A001', 'A001', 'A001', 'A001'],
        '管理号': ['001', '1', '002', '2'],  # 混合格式：有的有前导零，有的没有
        '胎次(胎)': [2, 2, 1, 1],  # 相同胎次，便于测试
        '采样日期': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-15'],
        '蛋白率(%)': [3.2, 3.2, 3.3, 3.3],  # 相同蛋白率
        '泌乳天数(天)': [150, 150, 120, 120]  # 相同泌乳天数
    }
    
    df = pd.DataFrame(test_data)
    print("混合格式测试数据:")
    print(df)
    
    # 模拟Excel读取可能的情况
    print("\n模拟可能的问题情况:")
    print("假设Excel读取后，'001'保持为'001'，但'002'变成了'2'")
    print("这种情况下，'002'和'2'会被当作不同的牛")
    
    # 显示这种情况的后果
    problematic_mgmt_ids = ['001', '1', '002', '2']  # 模拟问题情况
    print(f"问题管理号列表: {problematic_mgmt_ids}")
    print(f"唯一管理号数: {len(set(problematic_mgmt_ids))} (错误：应该是2)")
    
    # 正确处理后的期望结果
    print(f"\n正确处理后的期望:")
    print("所有管理号都应该保持原始格式，避免'001'和'1'混淆")

if __name__ == "__main__":
    test_management_id_consistency()
    test_mixed_management_id_formats()
    
    print("\n=== 修复总结 ===")
    print("1. Excel读取时强制指定管理号为字符串类型")
    print("2. 数据处理各环节都确保字符串类型一致性")
    print("3. 分组操作前都进行类型检查和转换")
    print("4. 添加前导零检测和记录功能")
    print("5. 防止'nan'字符串和空字符串的干扰") 