#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DHI精准筛查助手 - UI修复验证测试
测试所有4个UI问题的修复情况
"""

import sys
import os
# import pytest  # 暂时注释掉，避免导入错误
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QLabel, QProgressBar
from PyQt6.QtCore import Qt

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试1: 验证进度区域高度压缩
def test_progress_area_compression():
    """测试进度区域高度是否正确压缩到16px"""
    print("\n=== 测试1: 进度区域高度压缩 ===")
    
    try:
        from desktop_app import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # 检查进度容器的最大高度
        if hasattr(window, 'progress_container'):
            max_height = window.progress_container.maximumHeight()
            print(f"进度容器最大高度: {max_height}px")
            assert max_height == 16, f"进度容器高度应该是16px，实际是{max_height}px"
        
        # 检查进度条高度
        if hasattr(window, 'progress_bar'):
            bar_max_height = window.progress_bar.maximumHeight()
            bar_min_height = window.progress_bar.minimumHeight()
            print(f"进度条高度: min={bar_min_height}px, max={bar_max_height}px")
            assert bar_max_height == 12, f"进度条最大高度应该是12px，实际是{bar_max_height}px"
            assert bar_min_height == 12, f"进度条最小高度应该是12px，实际是{bar_min_height}px"
        
        # 检查progress_label是否隐藏
        if hasattr(window, 'progress_label'):
            is_visible = window.progress_label.isVisible()
            print(f"进度标签是否可见: {is_visible}")
            assert not is_visible, "进度标签应该被隐藏"
        
        print("✅ 进度区域高度压缩测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 进度区域高度压缩测试失败: {e}")
        return False

# 测试2: 验证筛选容器高度自动扩展
def test_filter_container_auto_expand():
    """测试筛选容器高度是否能自动扩展"""
    print("\n=== 测试2: 筛选容器高度自动扩展 ===")
    
    try:
        from desktop_app import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # 模拟添加筛选项
        window.added_other_filters = {
            'protein_pct': {'name': '蛋白率'},
            'fat_pct': {'name': '乳脂率'},
            'milk_yield': {'name': '产奶量'}
        }
        
        # 调用高度调整方法
        if hasattr(window, 'adjust_filters_container_height'):
            window.adjust_filters_container_height()
            
            if hasattr(window, 'filters_container'):
                max_height = window.filters_container.maximumHeight()
                min_height = window.filters_container.minimumHeight()
                print(f"筛选容器高度: min={min_height}px, max={max_height}px")
                
                # 检查最大高度是否设置为无限制
                assert max_height == 16777215, f"筛选容器最大高度应该是16777215（无限制），实际是{max_height}"
                
                # 检查最小高度是否根据筛选项数量调整
                expected_min_height = 3 * 120 + 20  # 3个筛选项 * 120px + 20px边距
                assert min_height >= expected_min_height, f"筛选容器最小高度应该≥{expected_min_height}px，实际是{min_height}px"
                
                print("✅ 筛选容器高度自动扩展测试通过")
                return True
        else:
            print("⚠️ 未找到adjust_filters_container_height方法")
            return False
        
    except Exception as e:
        print(f"❌ 筛选容器高度自动扩展测试失败: {e}")
        return False

# 测试3: 验证历史数据填充功能
def test_historical_data_filling():
    """测试历史数据填充功能是否正确工作"""
    print("\n=== 测试3: 历史数据填充功能 ===")
    
    try:
        from data_processor import DataProcessor
        
        processor = DataProcessor()
        
        # 创建测试数据，包含空值
        test_data = pd.DataFrame({
            'management_id': ['A001', 'A001', 'A001', 'B002', 'B002', 'B002'],
            'sample_date': ['2024-01-01', '2024-02-01', '2024-03-01', 
                           '2024-01-01', '2024-02-01', '2024-03-01'],
            'protein_pct': [3.5, None, 3.8, None, 3.2, 3.4]  # 有空值需要填充
        })
        
        print("原始数据:")
        print(test_data)
        print(f"空值数量: {test_data['protein_pct'].isna().sum()}")
        
        # 应用历史数据填充
        filled_df = processor._fill_empty_values_with_history(test_data, 'protein_pct')
        
        print("\n填充后数据:")
        print(filled_df)
        print(f"填充后空值数量: {filled_df['protein_pct'].isna().sum()}")
        
        # 验证填充结果
        assert filled_df['protein_pct'].isna().sum() < test_data['protein_pct'].isna().sum(), "应该减少空值数量"
        
        # 验证填充标记
        if 'protein_pct_historical_filled' in filled_df.columns:
            filled_count = filled_df['protein_pct_historical_filled'].sum()
            print(f"标记为历史填充的记录数: {filled_count}")
            assert filled_count > 0, "应该有记录被标记为历史填充"
            print("✅ 历史数据填充功能测试通过")
            return True
        else:
            print("⚠️ 未找到历史填充标记列")
            return False
        
    except Exception as e:
        print(f"❌ 历史数据填充功能测试失败: {e}")
        return False

# 测试4: 验证状态显示取消
def test_status_display_cancellation():
    """测试DHI和在群牛状态显示是否被取消"""
    print("\n=== 测试4: 状态显示取消 ===")
    
    try:
        from desktop_app import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # 测试隐性乳房炎监测状态显示取消
        if hasattr(window, 'update_monitoring_data_status'):
            window.update_monitoring_data_status()
            
            if hasattr(window, 'monitoring_data_status'):
                status_text = window.monitoring_data_status.text()
                print(f"隐性乳房炎监测状态文本: '{status_text}'")
                assert status_text == "", "隐性乳房炎监测状态应该为空"
        
        # 测试在群牛文件状态标签隐藏
        if hasattr(window, 'active_cattle_label'):
            is_visible = window.active_cattle_label.isVisible()
            print(f"在群牛文件状态标签是否可见: {is_visible}")
            assert not is_visible, "在群牛文件状态标签应该被隐藏"
        
        print("✅ 状态显示取消测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 状态显示取消测试失败: {e}")
        return False

# 测试5: 验证空值处理策略
def test_empty_value_handling_strategies():
    """测试空值处理的三种策略"""
    print("\n=== 测试5: 空值处理策略 ===")
    
    try:
        from data_processor import DataProcessor
        
        processor = DataProcessor()
        
        # 创建包含空值的测试数据
        test_data = pd.DataFrame({
            'management_id': ['A001', 'A002', 'A003', 'A004'],
            'sample_date': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01'],
            'protein_pct': [3.5, None, 3.8, None]
        })
        
        print("原始测试数据:")
        print(test_data)
        
        # 测试策略1: 视为不符合
        filter_config_reject = {
            'min': 3.0,
            'max': 4.0,
            'empty_handling': '视为不符合'
        }
        
        result_reject = processor.apply_numeric_filter(test_data.copy(), 'protein_pct', filter_config_reject)
        print(f"\n策略1(视为不符合): {len(result_reject)} 条记录通过筛选")
        assert len(result_reject) == 2, "应该只有2条非空且符合条件的记录通过"
        
        # 测试策略2: 视为符合
        filter_config_accept = {
            'min': 3.0,
            'max': 4.0,
            'empty_handling': '视为符合'
        }
        
        result_accept = processor.apply_numeric_filter(test_data.copy(), 'protein_pct', filter_config_accept)
        print(f"策略2(视为符合): {len(result_accept)} 条记录通过筛选")
        assert len(result_accept) == 4, "应该所有记录都通过筛选（包括空值）"
        
        # 测试策略3: 历史数据填充
        filter_config_fill = {
            'min': 3.0,
            'max': 4.0,
            'empty_handling': '历史数据填充'
        }
        
        result_fill = processor.apply_numeric_filter(test_data.copy(), 'protein_pct', filter_config_fill)
        print(f"策略3(历史数据填充): {len(result_fill)} 条记录通过筛选")
        
        print("✅ 空值处理策略测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 空值处理策略测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始运行UI修复验证测试...")
    
    tests = [
        test_progress_area_compression,
        test_filter_container_auto_expand,
        test_historical_data_filling,
        test_status_display_cancellation,
        test_empty_value_handling_strategies
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 运行失败: {e}")
            results.append(False)
    
    # 汇总结果
    print(f"\n=== 测试结果汇总 ===")
    print(f"总测试数: {len(tests)}")
    print(f"通过测试: {sum(results)}")
    print(f"失败测试: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 所有UI修复测试通过！")
        return True
    else:
        print("❌ 部分测试失败，请检查修复代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 