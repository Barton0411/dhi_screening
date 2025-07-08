#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试干奶前流行率计算的调试脚本
"""
import sys
import pandas as pd
sys.path.append('/Users/Shared/Files From d.localized/projects/protein_screening')

from mastitis_monitoring import MastitisMonitoringCalculator
from data_processor import DataProcessor

def test_predry_prevalence():
    """测试干奶前流行率计算"""
    print("🔍 开始测试干奶前流行率计算...")
    
    # 创建计算器
    calculator = MastitisMonitoringCalculator(scc_threshold=20.0)
    
    # 使用DataProcessor处理DHI数据
    print("\n📊 使用DataProcessor加载DHI数据...")
    processor = DataProcessor()
    dhi_file = '/Users/Shared/Files From d.localized/projects/protein_screening/files_for_test/ghi_2025年6月-04-2综合测定结果表.xlsx'
    
    try:
        success, message, dhi_df = processor.process_uploaded_file(dhi_file, 'ghi_2025年6月-04-2综合测定结果表.xlsx')
        if not success or dhi_df is None:
            print(f"❌ DHI数据处理失败: {message}")
            return
        
        print(f"✅ DHI数据处理成功: {len(dhi_df)}头牛")
        print(f"   处理后列名: {list(dhi_df.columns)}")
        
        # 加载到监测计算器
        load_result = calculator.load_dhi_data([dhi_df])
        if not load_result['success']:
            print(f"❌ DHI数据加载失败: {load_result['error']}")
            return
        print(f"✅ DHI数据加载到监测计算器成功")
        
    except Exception as e:
        print(f"❌ DHI数据处理失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 加载牛群基础信息
    print("\n🐄 加载牛群基础信息...")
    cattle_file = '/Users/Shared/Files From d.localized/projects/protein_screening/files_for_test/慧牧云系统_牛群数据管理2025-06-14.xlsx'
    try:
        cattle_df = pd.read_excel(cattle_file)
        print(f"✅ 牛群数据加载成功: {len(cattle_df)}头牛")
        
        # 加载到计算器
        cattle_result = calculator.load_cattle_basic_info(cattle_df, 'huimuyun')
        if not cattle_result['success']:
            print(f"❌ 牛群数据加载失败: {cattle_result['error']}")
            return
        print(f"✅ 牛群数据处理成功")
        
    except Exception as e:
        print(f"❌ 牛群数据读取失败: {e}")
        return
    
    # 计算干奶前流行率
    print("\n🎯 开始计算干奶前流行率...")
    print("=" * 60)
    
    try:
        # 获取第一个月份进行测试
        months = list(calculator.monthly_data.keys())
        if not months:
            print("❌ 没有可用的月份数据")
            return
            
        test_month = months[0]
        print(f"测试月份: {test_month}")
        
        # 直接调用干奶前流行率计算函数
        result = calculator._calculate_pre_dry_prevalence(test_month)
        
        print("=" * 60)
        print("\n📋 计算结果:")
        print(f"   值: {result.get('value')}")
        print(f"   分子: {result.get('numerator')}")
        print(f"   分母: {result.get('denominator')}")
        print(f"   匹配数量: {result.get('matched_count')}")
        print(f"   DHI总数: {result.get('total_dhi_count')}")
        print(f"   诊断: {result.get('diagnosis')}")
        
        if result.get('value') is not None:
            print(f"\n🎉 干奶前流行率计算成功: {result['value']:.1f}%")
        else:
            print(f"\n❌ 干奶前流行率计算失败")
            print(f"   原因: {result.get('diagnosis')}")
        
    except Exception as e:
        print(f"❌ 计算过程异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_predry_prevalence()