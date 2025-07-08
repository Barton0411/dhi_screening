#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建隐形乳房炎监测界面布局示意图
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

def create_layout_mockups():
    """创建三种布局方案的示意图"""
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    fig.suptitle('隐形乳房炎监测界面 - 三种布局方案对比', fontsize=16, weight='bold')
    
    # 定义颜色
    colors = {
        'config': '#e3f2fd',      # 淡蓝色 - 配置区域
        'table': '#f3e5f5',       # 淡紫色 - 表格区域
        'chart': '#e8f5e8',       # 淡绿色 - 图表区域
        'formula': '#fff3e0',     # 淡橙色 - 公式区域
        'border': '#666'          # 边框色
    }
    
    def add_rect(ax, x, y, width, height, color, text, fontsize=10):
        """添加矩形区域"""
        rect = FancyBboxPatch((x, y), width, height,
                             boxstyle="round,pad=0.02", 
                             facecolor=color, edgecolor=colors['border'], linewidth=1)
        ax.add_patch(rect)
        ax.text(x + width/2, y + height/2, text, ha='center', va='center', 
               fontsize=fontsize, weight='bold', wrap=True)
    
    # 方案A: 上下排列
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_title('方案A: 上下排列', fontsize=14, weight='bold', pad=20)
    
    # 配置区域
    add_rect(ax1, 0.5, 8.5, 9, 1.2, colors['config'], 
             '配置区域\n体细胞阈值设置 | 图表选项 | 开始分析按钮', 9)
    
    # 结果表格
    add_rect(ax1, 0.5, 6.5, 9, 1.8, colors['table'], 
             '指标结果表格\n月份 | 当月流行率 | 新发感染率 | 慢性感染率 | 计算公式\n支持排序、筛选、导出Excel', 9)
    
    # 折线图
    add_rect(ax1, 0.5, 3.5, 9, 2.8, colors['chart'], 
             '折线图展示区域\n5条趋势线：当月流行率、新发感染率、慢性感染率\n慢性感染牛占比、头胎/经产首测流行率\n可配置Y轴范围、图例显示', 9)
    
    # 公式说明
    add_rect(ax1, 0.5, 0.5, 9, 2.8, colors['formula'], 
             '计算公式详细说明区域\n各指标的计算公式和实例\n数据来源说明\n注意事项和统计意义说明', 9)
    
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    
    # 方案B: 左右分栏
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.set_title('方案B: 左右分栏', fontsize=14, weight='bold', pad=20)
    
    # 左侧栏
    add_rect(ax2, 0.5, 5.5, 4, 4, colors['config'], 
             '左侧配置栏\n\n体细胞阈值设置\n图表选项配置\n开始分析按钮', 9)
    
    add_rect(ax2, 0.5, 0.5, 4, 4.8, colors['formula'], 
             '计算公式说明\n\n各指标计算公式\n数据来源说明\n统计意义解释\n注意事项', 9)
    
    # 右侧栏
    add_rect(ax2, 5.5, 5.5, 4, 4, colors['table'], 
             '右侧结果栏\n\n指标结果表格\n支持排序筛选\n导出Excel功能', 9)
    
    add_rect(ax2, 5.5, 0.5, 4, 4.8, colors['chart'], 
             '折线图展示\n\n5条趋势线显示\n交互式图表\n可配置显示选项', 9)
    
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    
    # 方案C: 标签页组织
    ax3 = axes[2]
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)
    ax3.set_title('方案C: 标签页组织', fontsize=14, weight='bold', pad=20)
    
    # 标签页头部
    add_rect(ax3, 0.5, 9, 2, 0.8, colors['config'], '配置', 8)
    add_rect(ax3, 2.7, 9, 2, 0.8, colors['table'], '结果', 8)
    add_rect(ax3, 4.9, 9, 2, 0.8, colors['chart'], '图表', 8)
    add_rect(ax3, 7.1, 9, 2.4, 0.8, colors['formula'], '公式说明', 8)
    
    # 当前显示的标签页内容（以配置标签为例）
    add_rect(ax3, 0.5, 1, 9, 7.8, colors['config'], 
             '当前显示：配置标签页\n\n• 体细胞数阈值设置 (默认20万/ml)\n• 图表显示选项\n  - Y轴范围配置\n  - 显示的指标选择\n  - 颜色主题选择\n• 分析参数\n• 开始分析按钮\n\n用户点击其他标签页可切换到：\n结果表格 | 折线图 | 公式说明', 10)
    
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['bottom'].set_visible(False)
    ax3.spines['left'].set_visible(False)
    
    # 添加优缺点说明
    fig.text(0.17, 0.02, '优点：一目了然，信息密度高\n缺点：需要较大屏幕空间', 
             ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7))
    
    fig.text(0.5, 0.02, '优点：布局平衡，易于操作\n缺点：配置和结果相对分离', 
             ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7))
    
    fig.text(0.83, 0.02, '优点：界面简洁，分步引导\n缺点：需要频繁切换标签页', 
             ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('/Users/Shared/Files From d.localized/projects/protein_screening/界面布局方案对比.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return fig

def create_data_integration_architecture():
    """创建数据整合架构示意图"""
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))
    fig.suptitle('数据上传整合方案对比', fontsize=16, weight='bold')
    
    # 定义颜色
    colors = {
        'data_mgmt': '#e1f5fe',     # 数据管理
        'function': '#f3e5f5',      # 功能模块
        'shared': '#e8f5e8',        # 共享状态
        'upload': '#fff3e0',        # 上传功能
        'arrow': '#666'             # 箭头
    }
    
    def add_rect_with_text(ax, x, y, width, height, color, text, fontsize=10):
        """添加带文本的矩形"""
        rect = FancyBboxPatch((x, y), width, height,
                             boxstyle="round,pad=0.05", 
                             facecolor=color, edgecolor='#333', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + width/2, y + height/2, text, ha='center', va='center', 
               fontsize=fontsize, weight='bold', wrap=True)
    
    def add_arrow(ax, x1, y1, x2, y2, text=''):
        """添加箭头"""
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', lw=2, color=colors['arrow']))
        if text:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mid_x, mid_y, text, fontsize=8, ha='center', 
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # 方案A: 统一数据管理
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_title('推荐方案：统一数据管理 + 状态共享', fontsize=14, weight='bold', pad=20)
    
    # 数据管理中心
    add_rect_with_text(ax1, 3, 8, 4, 1.5, colors['data_mgmt'], 
                      '📁 数据管理中心\n(第一个选项卡)', 11)
    
    # DHI数据和牛群信息
    add_rect_with_text(ax1, 0.5, 6, 2.5, 1.2, colors['upload'], 
                      'DHI报告\n上传管理', 9)
    add_rect_with_text(ax1, 7, 6, 2.5, 1.2, colors['upload'], 
                      '牛群基础信息\n上传管理', 9)
    
    # 功能模块
    add_rect_with_text(ax1, 0.5, 3.5, 2.8, 1.2, colors['function'], 
                      '📊 DHI基础筛选\n状态：已就绪', 9)
    add_rect_with_text(ax1, 3.6, 3.5, 2.8, 1.2, colors['function'], 
                      '🔍 慢性乳房炎筛查\n状态：已就绪', 9)
    add_rect_with_text(ax1, 6.7, 3.5, 2.8, 1.2, colors['function'], 
                      '👁️ 隐形乳房炎监测\n状态：需要多月数据', 9)
    
    # 共享状态指示器
    add_rect_with_text(ax1, 3, 1.5, 4, 1.2, colors['shared'], 
                      '📋 全局数据状态\nDHI: 6个月 | 牛群信息: 已上传\n系统类型: 伊起牛', 9)
    
    # 箭头连接
    add_arrow(ax1, 4, 8, 2, 6.8, 'DHI数据')
    add_arrow(ax1, 6, 8, 8, 6.8, '牛群信息')
    add_arrow(ax1, 5, 8, 2, 4.5, '共享')
    add_arrow(ax1, 5, 8, 5, 4.5, '共享')
    add_arrow(ax1, 5, 8, 8, 4.5, '共享')
    
    # 优点说明
    ax1.text(5, 0.5, '✅ 优点：\n• 数据管理统一清晰\n• 避免重复上传\n• 状态一目了然\n• 功能间数据共享', 
             ha='center', va='center', fontsize=10,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.7))
    
    ax1.set_xticks([])
    ax1.set_yticks([])
    for spine in ax1.spines.values():
        spine.set_visible(False)
    
    # 方案B: 分散上传
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.set_title('对比方案：分散上传 + 状态同步', fontsize=14, weight='bold', pad=20)
    
    # 各功能模块独立上传
    add_rect_with_text(ax2, 0.5, 7, 2.8, 2, colors['function'], 
                      '📊 DHI基础筛选\n\n📤 独立上传DHI\n📤 独立上传牛群信息', 9)
    add_rect_with_text(ax2, 3.6, 7, 2.8, 2, colors['function'], 
                      '🔍 慢性乳房炎筛查\n\n📤 独立上传DHI\n📤 独立上传牛群信息', 9)
    add_rect_with_text(ax2, 6.7, 7, 2.8, 2, colors['function'], 
                      '👁️ 隐形乳房炎监测\n\n📤 独立上传DHI\n📤 独立上传牛群信息', 9)
    
    # 复杂的状态同步
    add_rect_with_text(ax2, 1, 4, 8, 1.5, colors['shared'], 
                      '🔄 复杂状态同步机制\n需要实时同步各模块的上传状态，防止数据不一致', 10)
    
    # 数据存储
    add_rect_with_text(ax2, 3, 1.5, 4, 1.2, colors['data_mgmt'], 
                      '💾 共享数据存储\n但管理入口分散', 9)
    
    # 箭头连接（表示复杂的同步关系）
    add_arrow(ax2, 2, 7, 3, 5.2, '同步')
    add_arrow(ax2, 5, 7, 5, 5.2, '同步')
    add_arrow(ax2, 8, 7, 7, 5.2, '同步')
    add_arrow(ax2, 5, 4, 5, 2.5, '存储')
    
    # 缺点说明
    ax2.text(5, 0.5, '❌ 缺点：\n• 界面重复，用户困惑\n• 状态同步复杂\n• 数据管理分散\n• 开发维护成本高', 
             ha='center', va='center', fontsize=10,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcoral', alpha=0.7))
    
    ax2.set_xticks([])
    ax2.set_yticks([])
    for spine in ax2.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    plt.savefig('/Users/Shared/Files From d.localized/projects/protein_screening/数据整合架构对比.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return fig

if __name__ == "__main__":
    print("正在生成界面布局方案对比图...")
    fig1 = create_layout_mockups()
    print("✅ 布局方案对比图已生成")
    
    print("\\n正在生成数据整合架构对比图...")
    fig2 = create_data_integration_architecture()
    print("✅ 数据整合架构对比图已生成")
    
    print("\\n📁 图片保存位置:")
    print("- 界面布局方案对比.png")
    print("- 数据整合架构对比.png")