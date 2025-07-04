#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DHI蛋白筛查系统 - 数据范围动态设置测试
测试改进功能：
1. 筛选范围的最大值和最小值根据上传数据动态设置
2. 符合月数的最大值根据收集到的月数上限设置
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor import DataProcessor

def test_data_ranges():
    """测试数据范围计算功能"""
    print("DHI蛋白筛查系统 - 数据范围动态设置测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "测试数据")
    dhi_dir = os.path.join(test_data_dir, "DHI报告")
    
    processor = DataProcessor()
    
    # 1. 处理测试文件
    print("1. 处理测试文件...")
    
    dhi_files = []
    if os.path.exists(dhi_dir):
        for file in os.listdir(dhi_dir):
            if file.endswith(('.xlsx', '.xls', '.zip')):
                file_path = os.path.join(dhi_dir, file)
                dhi_files.append((file_path, file))
    
    # 只处理前5个文件进行快速测试
    test_files = dhi_files[:5]
    print(f"选择{len(test_files)}个文件进行测试")
    
    all_data = []
    for file_path, filename in test_files:
        try:
            print(f"  处理: {filename}")
            success, message, df = processor.process_uploaded_file(file_path, filename)
            
            if success and df is not None and not df.empty:
                all_data.append({'filename': filename, 'data': df})
                print(f"    ✅ 成功: {len(df)}行数据")
            else:
                print(f"    ❌ 失败: {message}")
                
        except Exception as e:
            print(f"    ❌ 异常: {str(e)}")
    
    if not all_data:
        print("❌ 没有成功处理的文件，测试终止")
        return
    
    print(f"\n成功处理{len(all_data)}个文件")
    
    # 2. 测试数据范围计算
    print("\n2. 测试数据范围计算...")
    
    data_ranges = processor.get_data_ranges(all_data)
    
    print(f"计算完成，发现{len(data_ranges)}个字段的范围信息")
    
    # 显示月数范围
    if 'months' in data_ranges:
        months_info = data_ranges['months']
        print(f"\n📅 月数范围:")
        print(f"   最小: {months_info['min']}个月")
        print(f"   最大: {months_info['max']}个月")
        print(f"   描述: {months_info['description']}")
    
    # 显示关键字段的范围
    key_fields = ['protein_pct', 'fat_pct', 'somatic_cell_count', 'milk_yield', 'lactation_days']
    
    for field in key_fields:
        if field in data_ranges:
            range_info = data_ranges[field]
            print(f"\n📊 {field}:")
            print(f"   实际范围: {range_info['min']:.2f} - {range_info['max']:.2f}")
            print(f"   建议范围: {range_info['suggested_min']:.2f} - {range_info['suggested_max']:.2f}")
            print(f"   平均值: {range_info['mean']:.2f}")
            print(f"   有效数据: {range_info['count']}条")
            print(f"   描述: {range_info['description']}")
    
    # 3. 测试合理默认值计算
    print("\n3. 测试合理默认值计算...")
    
    test_fields = ['protein_pct', 'somatic_cell_count', 'fat_pct', 'milk_yield']
    
    for field in test_fields:
        if field in data_ranges:
            defaults = processor.get_reasonable_filter_defaults(field, data_ranges)
            print(f"\n🎯 {field} 筛选默认值:")
            print(f"   推荐筛选范围: {defaults['min']:.2f} - {defaults['max']:.2f}")
            print(f"   最少符合月数: {defaults['min_match_months']}")
            print(f"   空值判断: {'是' if defaults['treat_empty_as_match'] else '否'}")
            
            if 'suggested_min' in defaults and 'suggested_max' in defaults:
                print(f"   完整建议范围: {defaults['suggested_min']:.2f} - {defaults['suggested_max']:.2f}")
    
    # 4. 测试界面控件范围设置
    print("\n4. 测试界面控件范围设置...")
    
    months_info = data_ranges.get('months', {})
    max_months = months_info.get('max', 12)
    
    print(f"📋 界面控件建议设置:")
    print(f"   最少符合月数范围: 0 - {max_months}")
    print(f"   推荐默认值: {min(3, max_months // 2) if max_months > 0 else 1}")
    
    # 为蛋白率和体细胞数显示具体的控件设置建议
    if 'protein_pct' in data_ranges:
        protein_defaults = processor.get_reasonable_filter_defaults('protein_pct', data_ranges)
        print(f"\n🟡 蛋白率筛选控件设置:")
        print(f"   数值范围: 0.0 - 99.99")
        print(f"   推荐默认值: {protein_defaults['min']:.2f} - {protein_defaults['max']:.2f}")
        print(f"   最少符合月数: 0 - {max_months} (默认{protein_defaults['min_match_months']})")
    
    if 'somatic_cell_count' in data_ranges:
        somatic_defaults = processor.get_reasonable_filter_defaults('somatic_cell_count', data_ranges)
        print(f"\n🔵 体细胞数筛选控件设置:")
        print(f"   数值范围: 0.0 - 9999.99")
        print(f"   推荐默认值: {somatic_defaults['min']:.2f} - {somatic_defaults['max']:.2f}")
        print(f"   最少符合月数: 0 - {max_months} (默认{somatic_defaults['min_match_months']})")
    
    # 5. 验证范围合理性
    print("\n5. 验证范围合理性...")
    
    validation_results = []
    
    for field, range_info in data_ranges.items():
        if field == 'months' or not isinstance(range_info, dict):
            continue
        
        min_val = range_info.get('min', 0)
        max_val = range_info.get('max', 0)
        suggested_min = range_info.get('suggested_min', 0)
        suggested_max = range_info.get('suggested_max', 0)
        
        # 检查基本合理性
        checks = []
        
        # 1. 最小值应该小于等于最大值
        checks.append(("最小值≤最大值", min_val <= max_val))
        
        # 2. 建议范围应该包含实际范围
        checks.append(("建议范围包含实际", suggested_min <= min_val and suggested_max >= max_val))
        
        # 3. 特定字段的合理性检查
        if field == 'protein_pct':
            checks.append(("蛋白率在合理范围", 0.5 <= min_val <= 8.0 and 1.0 <= max_val <= 10.0))
        elif field == 'somatic_cell_count':
            checks.append(("体细胞数在合理范围", 0 <= min_val and max_val <= 5000))
        elif field == 'lactation_days':
            checks.append(("泌乳天数在合理范围", 1 <= min_val and max_val <= 500))
        elif field == 'milk_yield':
            checks.append(("产奶量在合理范围", 5 <= min_val and max_val <= 100))
        
        # 记录验证结果
        all_passed = all(result for _, result in checks)
        validation_results.append((field, all_passed, checks))
        
        print(f"\n✅ {field} 验证结果:")
        for check_name, result in checks:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {check_name}: {status}")
    
    # 6. 输出测试总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    total_fields = len([r for r in validation_results])
    passed_fields = len([r for r in validation_results if r[1]])
    
    print(f"📊 数据范围计算: 成功")
    print(f"📊 字段验证: {passed_fields}/{total_fields} 通过")
    print(f"📊 月数范围: 0-{max_months}个月")
    
    if 'protein_pct' in data_ranges and 'somatic_cell_count' in data_ranges:
        print(f"📊 核心字段: 蛋白率和体细胞数都有完整数据")
    
    # 成功率
    if total_fields > 0:
        success_rate = passed_fields / total_fields * 100
        if success_rate >= 90:
            print(f"🎉 数据范围功能测试优秀! ({success_rate:.1f}%)")
        elif success_rate >= 80:
            print(f"👍 数据范围功能测试良好! ({success_rate:.1f}%)")
        else:
            print(f"⚠️  数据范围功能需要改进 ({success_rate:.1f}%)")
    
    # 给出使用建议
    print(f"\n💡 使用建议:")
    print(f"   1. 界面控件的最少符合月数范围设为: 0-{max_months}")
    print(f"   2. 使用get_reasonable_filter_defaults()为新增筛选项设置智能默认值")
    print(f"   3. 数据上传后调用get_data_ranges()动态更新所有控件范围")

if __name__ == "__main__":
    test_data_ranges()
    input("\n按回车键退出...") 