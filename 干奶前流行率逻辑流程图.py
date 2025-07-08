#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
干奶前流行率完整逻辑流程图生成器
基于代码分析的完整逻辑链路
"""
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_flowchart():
    """创建干奶前流行率逻辑流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 24))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 30)
    ax.axis('off')
    
    # 定义颜色
    colors = {
        'start': '#e8f5e8',      # 浅绿色 - 开始
        'process': '#e3f2fd',    # 浅蓝色 - 处理过程
        'decision': '#fff3e0',   # 浅橙色 - 判断
        'error': '#ffebee',      # 浅红色 - 错误
        'success': '#f3e5f5',    # 浅紫色 - 成功
        'data': '#f0f4c3'        # 浅黄绿色 - 数据
    }
    
    def add_box(x, y, width, height, text, color, fontsize=9):
        """添加流程框"""
        box = FancyBboxPatch((x-width/2, y-height/2), width, height,
                           boxstyle="round,pad=0.1", 
                           facecolor=color, edgecolor='#333', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, 
                wrap=True, bbox=dict(boxstyle="round,pad=0.1", alpha=0))
        return (x, y-height/2)  # 返回底部中心点
    
    def add_arrow(start, end, label=''):
        """添加箭头"""
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', lw=2, color='#333'))
        if label:
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            ax.text(mid_x + 0.2, mid_y, label, fontsize=8, color='#666')
    
    # 标题
    ax.text(5, 29, '干奶前流行率计算完整逻辑流程', fontsize=18, fontweight='bold', 
            ha='center', va='center')
    ax.text(5, 28.3, '基于 _calculate_pre_dry_prevalence() 函数分析', fontsize=12, 
            ha='center', va='center', style='italic', color='#666')
    
    # 1. 开始
    start_pos = add_box(5, 27, 3, 0.8, 
                       '📊 开始计算干奶前流行率\n输入：月份(month)', 
                       colors['start'], 10)
    
    # 2. 检查牛群基础信息
    check_cattle_pos = add_box(5, 25.5, 4, 1, 
                              '🔍 检查牛群基础信息\nif self.cattle_basic_info is None:', 
                              colors['decision'])
    add_arrow(start_pos, (5, 26))
    
    # 2.1 无牛群信息错误分支
    no_cattle_pos = add_box(1.5, 24, 2.5, 1.2, 
                           '❌ 返回错误\n无法计算干奶前流行率\n未上传牛群基础信息', 
                           colors['error'])
    add_arrow((5, 25), (1.5, 24.6), '无牛群信息')
    
    # 3. 获取在胎天数字段
    get_field_pos = add_box(5, 23.5, 4, 1.2, 
                           '🎯 获取在胎天数字段\n_get_pregnancy_field(system_type)\n系统类型字段映射', 
                           colors['process'])
    add_arrow((5, 25), (5, 24.1), '有牛群信息')
    
    # 3.1 字段映射详情
    field_mapping_pos = add_box(8.5, 23.5, 2.8, 1.8, 
                               '📋 字段映射规则\n• 伊起牛：在胎天数\n• 慧牧云：怀孕天数\n• 其他：通用查找\n优先级顺序匹配', 
                               colors['data'], 8)
    add_arrow((6.5, 23.5), (7.1, 23.5))
    
    # 4. 检查在胎天数字段
    check_field_pos = add_box(5, 21.5, 4, 1, 
                             '🔍 检查在胎天数字段\nif pregnancy_field not in columns:', 
                             colors['decision'])
    add_arrow((5, 22.9), (5, 22))
    
    # 4.1 无字段错误分支
    no_field_pos = add_box(1.5, 20.5, 2.5, 1.2, 
                          '❌ 返回错误\n缺少在胎天数字段\n当前系统类型检查', 
                          colors['error'])
    add_arrow((5, 21), (1.5, 21.1), '无字段')
    
    # 5. 获取DHI数据
    get_dhi_pos = add_box(5, 19.5, 3.5, 1, 
                         '📊 获取当月DHI数据\ndhi_df = monthly_data[month]', 
                         colors['process'])
    add_arrow((5, 21), (5, 20), '有字段')
    
    # 6. 匹配管理号与耳号
    match_ids_pos = add_box(5, 17.8, 4.5, 1.4, 
                           '🔗 匹配管理号与耳号\n_match_management_id_with_ear_tag()\n标准化处理：去除前导0', 
                           colors['process'])
    add_arrow((5, 19), (5, 18.5))
    
    # 6.1 匹配详情
    match_detail_pos = add_box(8.5, 17.8, 2.8, 2, 
                              '📋 匹配逻辑\n• DHI管理号标准化\n• 耳号标准化\n• Inner Join匹配\n• 计算匹配率', 
                              colors['data'], 8)
    add_arrow((6.75, 17.8), (7.15, 17.8))
    
    # 7. 检查匹配结果
    check_match_pos = add_box(5, 15.8, 4, 1.2, 
                             '🔍 检查匹配结果\nif len(matched_data) == 0:\n计算匹配率', 
                             colors['decision'])
    add_arrow((5, 17.1), (5, 16.4))
    
    # 7.1 无匹配错误分支
    no_match_pos = add_box(1.5, 14.5, 2.5, 1.4, 
                          '❌ 返回错误\nDHI数据与牛群信息\n无法匹配\n匹配率0.0%', 
                          colors['error'])
    add_arrow((5, 15.2), (1.5, 15.2), '无匹配')
    
    # 8. 检查在胎天数数据
    check_pregnancy_pos = add_box(5, 13.5, 4.5, 1.2, 
                                 '🔍 检查匹配数据中的在胎天数\npregnancy_data_count = count()', 
                                 colors['decision'])
    add_arrow((5, 15.2), (5, 14.1), '有匹配')
    
    # 8.1 无在胎天数错误分支
    no_pregnancy_pos = add_box(1.5, 12, 2.5, 1.4, 
                              '❌ 返回错误\n匹配牛只中无\n在胎天数数据', 
                              colors['error'])
    add_arrow((5, 12.9), (1.5, 12.7), '无在胎天数')
    
    # 9. 筛选干奶前牛只
    filter_predry_pos = add_box(5, 11, 4.5, 1.4, 
                               '🎯 筛选干奶前牛只\npregnancy_condition = field > 180\npre_dry_cattle = matched_data[condition]', 
                               colors['process'])
    add_arrow((5, 12.9), (5, 11.7), '有在胎天数')
    
    # 10. 检查干奶前牛只数量
    check_predry_pos = add_box(5, 9, 4, 1.2, 
                              '🔍 检查干奶前牛只数量\nif len(pre_dry_cattle) == 0:', 
                              colors['decision'])
    add_arrow((5, 10.3), (5, 9.6))
    
    # 10.1 无干奶前牛只错误分支
    no_predry_pos = add_box(1.5, 8, 2.5, 1.4, 
                           '❌ 返回错误\n无在胎天数>180天\n的牛只', 
                           colors['error'])
    add_arrow((5, 8.4), (1.5, 8.7), '无干奶前牛只')
    
    # 11. 计算干奶前流行率
    calculate_pos = add_box(5, 6.5, 5, 1.8, 
                           '✅ 计算干奶前流行率\nhigh_scc_count = (scc > threshold).sum()\ntotal_pre_dry = len(pre_dry_cattle)\nprevalence = (high_scc / total_pre_dry) * 100', 
                           colors['success'])
    add_arrow((5, 8.4), (5, 7.4), '有干奶前牛只')
    
    # 12. 返回结果
    result_pos = add_box(5, 4.2, 5.5, 2, 
                        '📊 返回计算结果\n• 干奶前流行率值\n• 详细计算公式\n• 分子分母数值\n• 匹配统计信息\n• 诊断信息', 
                        colors['success'])
    add_arrow((5, 5.6), (5, 5.2))
    
    # 添加统计信息框
    stats_box = add_box(8.5, 6, 2.8, 3, 
                       '📈 测试数据统计\n基于实际数据分析：\n\n• DHI数据：982头\n• 牛群信息：4954头\n• 匹配成功：10头(1.0%)\n• 有在胎天数：7头\n• >180天牛只：5头\n• 可计算干奶前流行率', 
                       colors['data'], 8)
    
    # 添加关键问题标注
    ax.text(0.5, 2.5, '🔍 关键问题点分析', fontsize=14, fontweight='bold', color='#d32f2f')
    problem_text = """1. 匹配率低问题：DHI管理号与牛群耳号匹配率仅1.0%
   • 原因：数据来源时间不同、编码方式差异、牧场来源不一致
   • 影响：大量DHI数据无法用于干奶前流行率计算

2. 数据依赖性：干奶前流行率需要两套数据配合
   • DHI报告：提供体细胞数据和管理号
   • 牛群基础信息：提供在胎天数和耳号
   • 必须成功匹配才能计算

3. 系统类型识别：不同系统的字段名不同
   • 伊起牛：优先使用"在胎天数"字段
   • 慧牧云：优先使用"怀孕天数"字段
   • 其他系统：通用字段名查找"""
    
    ax.text(0.5, 1.8, problem_text, fontsize=9, va='top', color='#333',
           bbox=dict(boxstyle="round,pad=0.3", facecolor='#fff3e0', alpha=0.8))
    
    plt.title('干奶前流行率计算逻辑流程图', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('/Users/Shared/Files From d.localized/projects/protein_screening/干奶前流行率逻辑流程图.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print("✅ 干奶前流行率逻辑流程图已生成")
    print("📁 保存位置: /Users/Shared/Files From d.localized/projects/protein_screening/干奶前流行率逻辑流程图.png")
    
    return fig

if __name__ == "__main__":
    create_flowchart()