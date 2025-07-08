#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试范围框最大值限制修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QDoubleSpinBox, QSpinBox
from desktop_app import MainWindow
import pandas as pd

def test_range_limits():
    """测试范围框的最大值限制"""
    print("🔍 测试范围框最大值限制...")
    
    app = QApplication([])
    window = MainWindow()
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'farm_id': ['001'] * 100,
        'management_id': [f'C{i:03d}' for i in range(100)],
        'protein_pct': [i/10 + 3.0 for i in range(100)],  # 3.0 - 12.9%
        'somatic_cell_count': [i*100 + 500 for i in range(100)],  # 500 - 10400万/ml
        'fat_pct': [i/20 + 4.0 for i in range(100)],  # 4.0 - 8.95%
        'milk_yield': [i + 20 for i in range(100)],  # 20 - 119 kg
        'sample_date': ['2023-01-01'] * 100,
        'parity': [1] * 100
    })
    
    # 模拟上传数据的过程
    window.data_list = [{
        'filename': 'test_data.xlsx',
        'data': test_data
    }]
    
    # 调用更新范围的方法
    window.update_filter_ranges(test_data)
    
    # 测试蛋白率筛选控件的范围
    if hasattr(window, 'protein_min') and hasattr(window, 'protein_max'):
        protein_min_max = window.protein_min.maximum()
        protein_max_max = window.protein_max.maximum()
        print(f"✅ 蛋白率范围控件最大值: {protein_min_max} / {protein_max_max}")
        
        if protein_min_max >= 999999.99 and protein_max_max >= 999999.99:
            print("✅ 蛋白率范围控件最大值限制已修复")
        else:
            print("❌ 蛋白率范围控件最大值限制仍有问题")
    
    # 测试体细胞数筛选控件的范围
    if hasattr(window, 'somatic_min') and hasattr(window, 'somatic_max'):
        somatic_min_max = window.somatic_min.maximum()
        somatic_max_max = window.somatic_max.maximum()
        print(f"✅ 体细胞数范围控件最大值: {somatic_min_max} / {somatic_max_max}")
        
        if somatic_min_max >= 999999.99 and somatic_max_max >= 999999.99:
            print("✅ 体细胞数范围控件最大值限制已修复")
        else:
            print("❌ 体细胞数范围控件最大值限制仍有问题")
    
    # 测试其他筛选项的创建
    print("🔧 测试其他筛选项的范围限制...")
    
    # 添加一个乳脂率筛选项来测试，使用窗口的处理器获取配置
    fat_filter_config = window.processor.rules.get("optional_filters", {}).get("fat_pct", {})
    
    if fat_filter_config:
        fat_widget = window.create_other_filter_widget('fat_pct', fat_filter_config)
        fat_min_max = fat_widget.range_min.maximum()
        fat_max_max = fat_widget.range_max.maximum()
        print(f"✅ 乳脂率筛选项最大值: {fat_min_max} / {fat_max_max}")
        
        if fat_min_max >= 999999.99 and fat_max_max >= 999999.99:
            print("✅ 其他筛选项范围控件最大值限制已修复")
        else:
            print("❌ 其他筛选项范围控件最大值限制仍有问题")
    else:
        print("❌ 乳脂率筛选项配置未找到")
    
    # 验证实际数据值的设置
    print("\n📊 验证实际数据范围的设置:")
    print(f"蛋白率实际范围: {test_data['protein_pct'].min():.2f} - {test_data['protein_pct'].max():.2f}%")
    print(f"体细胞数实际范围: {test_data['somatic_cell_count'].min():.0f} - {test_data['somatic_cell_count'].max():.0f}万/ml")
    print(f"乳脂率实际范围: {test_data['fat_pct'].min():.2f} - {test_data['fat_pct'].max():.2f}%")
    print(f"产奶量实际范围: {test_data['milk_yield'].min():.0f} - {test_data['milk_yield'].max():.0f}kg")
    
    # 检查筛选控件是否设置为实际范围
    if hasattr(window, 'protein_min') and hasattr(window, 'protein_max'):
        protein_min_val = window.protein_min.value()
        protein_max_val = window.protein_max.value()
        expected_min = test_data['protein_pct'].min()
        expected_max = test_data['protein_pct'].max()
        
        if abs(protein_min_val - expected_min) < 0.01 and abs(protein_max_val - expected_max) < 0.01:
            print(f"✅ 蛋白率筛选范围已设置为实际数据范围: {protein_min_val:.2f} - {protein_max_val:.2f}%")
        else:
            print(f"❌ 蛋白率筛选范围设置有误: {protein_min_val:.2f} - {protein_max_val:.2f}% (期望: {expected_min:.2f} - {expected_max:.2f}%)")
    
    if hasattr(window, 'somatic_min') and hasattr(window, 'somatic_max'):
        somatic_min_val = window.somatic_min.value()
        somatic_max_val = window.somatic_max.value()
        expected_min = test_data['somatic_cell_count'].min()
        expected_max = test_data['somatic_cell_count'].max()
        
        if abs(somatic_min_val - expected_min) < 1 and abs(somatic_max_val - expected_max) < 1:
            print(f"✅ 体细胞数筛选范围已设置为实际数据范围: {somatic_min_val:.0f} - {somatic_max_val:.0f}万/ml")
        else:
            print(f"❌ 体细胞数筛选范围设置有误: {somatic_min_val:.0f} - {somatic_max_val:.0f}万/ml (期望: {expected_min:.0f} - {expected_max:.0f}万/ml)")
    
    app.quit()
    print("\n🎉 范围框最大值限制测试完成！")

if __name__ == "__main__":
    test_range_limits() 