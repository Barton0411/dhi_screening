#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试隐形乳房炎月度监测模块
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
import os
sys.path.append('/Users/Shared/Files From d.localized/projects/protein_screening')

from mastitis_monitoring import MastitisMonitoringCalculator
from data_processor import DataProcessor

def test_mastitis_monitoring():
    """测试隐形乳房炎月度监测功能"""
    
    print("=== 测试隐形乳房炎月度监测模块 ===")
    
    try:
        # 创建监测计算器
        calculator = MastitisMonitoringCalculator(scc_threshold=20.0)
        
        # 1. 首先测试加载牛群基础信息
        print("\n=== 1. 测试加载牛群基础信息 ===")
        cattle_info_file = './test_cattle_info.xlsx'
        
        if os.path.exists(cattle_info_file):
            cattle_df = pd.read_excel(cattle_info_file)
            print(f"✅ 成功读取牛群基础信息: {len(cattle_df)}头牛")
            
            # 加载到计算器
            load_result = calculator.load_cattle_basic_info(cattle_df, 'yiqiniu')
            print(f"牛群基础信息加载结果: {load_result}")
            
            if load_result['success']:
                print(f"✅ 牛群基础信息加载成功")
                print(f"  - 牛只数量: {load_result['cattle_count']}")
                print(f"  - 系统类型: {load_result['system_type']}")
                print(f"  - 在胎天数字段: {load_result['pregnancy_field']}")
            else:
                print(f"❌ 牛群基础信息加载失败: {load_result.get('error')}")
                return
        else:
            print(f"❌ 未找到牛群基础信息文件: {cattle_info_file}")
            return
        
        # 2. 测试加载DHI数据
        print("\n=== 2. 测试加载DHI数据 ===")
        
        # 使用现有的测试数据
        test_dhi_files = [
            './files_for_test/ghi_2025年6月-04-2综合测定结果表.xlsx',
            './files_for_test/dhi_2024-08-04综合测定结果表.xlsx'
        ]
        
        processor = DataProcessor()
        dhi_data_list = []
        
        for file_path in test_dhi_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                print(f"处理文件: {filename}")
                
                success, message, df = processor.process_uploaded_file(file_path, filename)
                
                if success and df is not None:
                    print(f"✅ 成功加载: {len(df)}条数据")
                    dhi_data_list.append(df)
                else:
                    print(f"❌ 加载失败: {message}")
            else:
                print(f"⚠️ 文件不存在: {file_path}")
        
        if len(dhi_data_list) == 0:
            print("❌ 没有成功加载的DHI数据")
            return
        
        # 3. 加载DHI数据到监测计算器
        print(f"\n=== 3. 加载{len(dhi_data_list)}个DHI文件到监测计算器 ===")
        load_result = calculator.load_dhi_data(dhi_data_list)
        print(f"DHI数据加载结果: {load_result}")
        
        if not load_result['success']:
            print(f"❌ DHI数据加载失败: {load_result.get('error')}")
            return
        
        # 4. 执行计算
        print(f"\n=== 4. 执行监测指标计算 ===")
        results = calculator.calculate_all_indicators()
        
        if not results['success']:
            print(f"❌ 计算失败: {results.get('error')}")
            return
        
        print(f"✅ 计算成功，共{results['month_count']}个月份的数据")
        print(f"月份: {results['months']}")
        
        # 5. 显示详细结果
        print(f"\n=== 5. 详细结果展示 ===")
        indicators = results['indicators']
        months = results['months']
        
        for month in months:
            if month not in indicators:
                continue
                
            month_indicators = indicators[month]
            print(f"\n--- {month}月指标 ---")
            
            # 当月流行率
            if 'current_prevalence' in month_indicators:
                cp = month_indicators['current_prevalence']
                if cp.get('value') is not None:
                    print(f"当月流行率: {cp['value']:.1f}% ({cp['numerator']}/{cp['denominator']})")
                else:
                    print(f"当月流行率: {cp.get('formula', '无法计算')}")
            
            # 头胎/经产首测流行率
            if 'first_test_prevalence' in month_indicators:
                ftp = month_indicators['first_test_prevalence']
                
                # 头胎
                if ftp.get('primiparous', {}).get('value') is not None:
                    primi = ftp['primiparous']
                    print(f"头胎首测流行率: {primi['value']:.1f}% ({primi['numerator']}/{primi['denominator']})")
                else:
                    print(f"头胎首测流行率: {ftp.get('primiparous', {}).get('formula', '无法计算')}")
                
                # 经产
                if ftp.get('multiparous', {}).get('value') is not None:
                    multi = ftp['multiparous']
                    print(f"经产首测流行率: {multi['value']:.1f}% ({multi['numerator']}/{multi['denominator']})")
                else:
                    print(f"经产首测流行率: {ftp.get('multiparous', {}).get('formula', '无法计算')}")
            
            # 新发感染率
            if 'new_infection_rate' in month_indicators:
                nir = month_indicators['new_infection_rate']
                if nir.get('value') is not None:
                    print(f"新发感染率: {nir['value']:.1f}% ({nir['numerator']}/{nir['denominator']}) [重叠:{nir['overlap_count']}头]")
                    if nir.get('warning'):
                        print(f"  ⚠️ {nir['warning']}")
                else:
                    print(f"新发感染率: {nir.get('formula', '无法计算')}")
            
            # 慢性感染率
            if 'chronic_infection_rate' in month_indicators:
                cir = month_indicators['chronic_infection_rate']
                if cir.get('value') is not None:
                    print(f"慢性感染率: {cir['value']:.1f}% ({cir['numerator']}/{cir['denominator']}) [重叠:{cir['overlap_count']}头]")
                    if cir.get('warning'):
                        print(f"  ⚠️ {cir['warning']}")
                else:
                    print(f"慢性感染率: {cir.get('formula', '无法计算')}")
            
            # 慢性感染牛占比
            if 'chronic_infection_proportion' in month_indicators:
                cip = month_indicators['chronic_infection_proportion']
                if cip.get('value') is not None:
                    print(f"慢性感染牛占比: {cip['value']:.1f}% ({cip['numerator']}/{cip['denominator']}) [重叠:{cip['overlap_count']}头]")
                    if cip.get('warning'):
                        print(f"  ⚠️ {cip['warning']}")
                else:
                    print(f"慢性感染牛占比: {cip.get('formula', '无法计算')}")
            
            # 干奶前流行率
            if 'pre_dry_prevalence' in month_indicators:
                pdp = month_indicators['pre_dry_prevalence']
                if pdp.get('value') is not None:
                    print(f"干奶前流行率: {pdp['value']:.1f}% ({pdp['numerator']}/{pdp['denominator']}) [匹配:{pdp['matched_count']}/{pdp['total_dhi_count']}头]")
                    print(f"  诊断: {pdp.get('diagnosis')}")
                    print(f"  匹配率: {pdp.get('match_rate', 0):.1f}%")
                    print(f"  在胎天数字段: {pdp.get('pregnancy_field')}")
                else:
                    print(f"干奶前流行率: 无法计算")
                    print(f"  诊断: {pdp.get('diagnosis', '未知')}")
                    print(f"  详细信息: {pdp.get('formula', '无详细信息')}")
        
        print(f"\n✅ 隐形乳房炎月度监测模块测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mastitis_monitoring()