#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_mastitis_monitoring_flowchart():
    """创建隐形乳房炎月度监测逻辑流程图"""
    
    # 创建图形
    fig, ax = plt.subplots(1, 1, figsize=(20, 24))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 120)
    ax.axis('off')
    
    # 定义颜色
    colors = {
        'start': '#4CAF50',      # 绿色 - 开始
        'process': '#2196F3',    # 蓝色 - 处理
        'decision': '#FF9800',   # 橙色 - 判断
        'data': '#9C27B0',      # 紫色 - 数据
        'result': '#F44336',     # 红色 - 结果
        'config': '#607D8B'      # 灰蓝色 - 配置
    }
    
    def add_box(x, y, width, height, text, color, fontsize=9):
        """添加文本框"""
        box = FancyBboxPatch((x-width/2, y-height/2), width, height,
                           boxstyle="round,pad=0.3", 
                           facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, 
               weight='bold', color='white', wrap=True)
    
    def add_diamond(x, y, width, height, text, color, fontsize=8):
        """添加菱形判断框"""
        diamond = patches.RegularPolygon((x, y), 4, radius=width/1.4, 
                                       orientation=np.pi/4, 
                                       facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(diamond)
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, 
               weight='bold', color='white', wrap=True)
    
    def add_arrow(x1, y1, x2, y2, text=''):
        """添加箭头"""
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))
        if text:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mid_x + 2, mid_y, text, fontsize=8, color='red', weight='bold')
    
    # 标题
    ax.text(50, 115, '隐形乳房炎月度监测 - 完整逻辑流程图', 
           ha='center', va='center', fontsize=18, weight='bold', color='#333')
    
    # 第一层：系统入口和数据准备
    add_box(50, 108, 24, 4, '用户进入隐形乳房炎月度监测功能', colors['start'])
    
    add_diamond(50, 101, 20, 6, '检查慢性乳房炎\n筛查中的牛群\n基础信息', colors['decision'])
    
    add_box(20, 95, 16, 4, '提示用户先在慢性乳房炎\n筛查中上传牛群基础信息', colors['result'])
    add_box(80, 95, 16, 4, '获取已保存的系统类型\n伊起牛/慧牧云/其他', colors['process'])
    
    # 箭头
    add_arrow(50, 106, 50, 103)
    add_arrow(42, 98, 28, 95, '无牛群信息')
    add_arrow(58, 98, 72, 95, '有牛群信息')
    add_arrow(20, 93, 15, 88)
    add_arrow(15, 88, 15, 110)
    add_arrow(15, 110, 42, 108)
    
    # 第二层：数据处理
    add_box(50, 88, 20, 4, 'DHI报告文件上传和处理', colors['data'])
    add_box(20, 81, 18, 4, '表头检测和字段映射\n标准化管理号(去前导0)', colors['process'])
    add_box(50, 81, 18, 4, '按采样日期分组月度数据\n同月多次测定取最后一次', colors['process'])
    add_box(80, 81, 18, 4, '牛群基础信息处理\n标准化耳号(去前导0)', colors['process'])
    
    add_arrow(50, 86, 50, 83)
    add_arrow(42, 83, 30, 83)
    add_arrow(58, 83, 70, 83)
    add_arrow(80, 93, 80, 83)
    
    # 第三层：月度连续性检查
    add_diamond(50, 74, 18, 6, '月度数据\n连续性检查', colors['decision'])
    
    add_box(15, 67, 14, 4, '只有1个月数据\n显示数值，不绘图', colors['result'])
    add_box(50, 67, 14, 4, '≥2个月且连续\n计算所有指标', colors['result'])
    add_box(85, 67, 14, 4, '≥2个月但不连续\n提示缺失月份', colors['decision'])
    
    add_arrow(50, 79, 50, 76)
    add_arrow(44, 71, 22, 69, '1个月')
    add_arrow(50, 71, 50, 69, '连续')
    add_arrow(56, 71, 78, 69, '不连续')
    
    # 第四层：指标计算区域
    ax.text(50, 60, '5个核心指标计算逻辑', ha='center', va='center', 
           fontsize=14, weight='bold', color='#333', 
           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.7))
    
    # 指标1：当月流行率
    add_box(10, 55, 18, 6, '指标1: 当月流行率\n\n公式：体细胞数>阈值的牛头数 / 当月参测牛头数\n示例：SCC>20万的168头 / 总982头 = 17.1%\n\n数据源：DHI报告当月数据', colors['data'], 8)
    
    # 指标2：新发感染率
    add_box(30, 55, 18, 6, '指标2: 新发感染率\n\n公式：(当月SCC>阈值 且 上月SCC≤阈值) / 上月SCC≤阈值\n示例：(06月>20 且 05月≤20)45头 / 05月≤20的758头 = 5.9%\n\n数据源：连续两月重叠牛只', colors['data'], 8)
    
    # 指标3：慢性感染率
    add_box(50, 55, 18, 6, '指标3: 慢性感染率\n\n公式：(当月SCC>阈值 且 上月SCC>阈值) / 上月SCC>阈值\n示例：(06月>20 且 05月>20)123头 / 05月>20的214头 = 57.5%\n\n数据源：连续两月重叠牛只', colors['data'], 8)
    
    # 指标4：慢性感染牛占比
    add_box(70, 55, 18, 6, '指标4: 慢性感染牛占比\n\n公式：(当月SCC>阈值 且 上月SCC>阈值) / 当月参测牛头数\n示例：(06月>20 且 05月>20)123头 / 06月参测972头 = 12.7%\n\n数据源：连续两月重叠牛只', colors['data'], 8)
    
    # 指标5：头胎/经产首测流行率
    add_box(90, 55, 18, 6, '指标5: 头胎/经产首测流行率\n\n筛选：泌乳天数5-35天\n头胎公式：头胎SCC>阈值 / 头胎参测牛数\n经产公式：经产SCC>阈值 / 经产参测牛数\n\n数据源：DHI报告当月数据', colors['data'], 8)
    
    # 连接线到指标计算
    add_arrow(15, 65, 15, 58)
    add_arrow(50, 65, 50, 58)
    add_arrow(85, 65, 85, 58)
    
    # 第五层：干奶前流行率（特殊处理）
    add_box(50, 45, 35, 6, '指标6: 干奶前流行率（需要牛群基础信息匹配）\n\n1. 管理号与耳号匹配（标准化后对比）\n2. 筛选条件：在胎天数>180天（伊起牛系统）或 怀孕天数>180天（慧牧云系统）\n3. 公式：筛选牛只中SCC>阈值的牛头数 / 筛选牛只参测总数（成功匹配的）\n4. 示例：在胎天数>180天且SCC>20的34头 / 在胎天数>180天参测127头 = 26.8%', colors['process'], 9)
    
    # 第六层：配置和异常处理
    add_box(15, 35, 16, 5, '配置选项\n\n• 体细胞阈值：用户可调整\n• Y轴范围：动态调整+手动设置\n• 时间显示：按自然月\n• 系统类型：自动识别', colors['config'], 8)
    
    add_box(50, 35, 16, 5, '异常处理\n\n• 数据缺失：显示具体原因\n• 匹配失败：显示成功/失败数量\n• 月份不连续：提示用户确认\n• 字段缺失：具体错误信息', colors['result'], 8)
    
    add_box(85, 35, 16, 5, '结果展示\n\n单月：数值+公式详情\n多月：数据表格+折线图\n趋势：4个指标绘制趋势\n干奶前：单独显示最新值', colors['result'], 8)
    
    # 第七层：详细计算示例
    ax.text(50, 25, '计算公式详细示例', ha='center', va='center', 
           fontsize=12, weight='bold', color='#333')
    
    example_text = """
当月流行率计算示例：
体细胞数(万/ml)>20的牛头数(168) ÷ 采样日期为2025-06的总牛头数(982) = 17.1%

新发感染率计算示例：
(2025-06月SCC>20 且 2025-05月SCC≤20的牛头数(45)) ÷ (2025-05月SCC≤20的牛头数(758)) = 5.9%

头胎首测流行率计算示例：
(胎次=1 且 泌乳天数5-35天 且 SCC>20的牛头数(23)) ÷ (胎次=1 且 泌乳天数5-35天的参测牛头数(89)) = 25.8%

干奶前流行率计算示例：
(在胎天数>180天 且 SCC>20的牛头数(34)) ÷ (在胎天数>180天的参测牛头数(127，已成功匹配)) = 26.8%
注：127头为管理号与耳号成功匹配的牛只数，其余牛只因匹配失败而排除
"""
    
    ax.text(50, 15, example_text, ha='center', va='center', fontsize=9, 
           bbox=dict(boxstyle="round,pad=0.8", facecolor='lightyellow', alpha=0.8))
    
    # 第八层：关键技术点
    tech_points = """
关键技术要点：
1. 管理号与耳号标准化：统一去除前导0后进行匹配
2. 同月多次测定处理：按采样日期排序，取当月最后一次记录
3. 系统字段映射：伊起牛用'在胎天数'，慧牧云用'怀孕天数'，其他系统用户自定义
4. 月份连续性：非连续月份提示用户确认是否继续计算
5. 公式透明化：每个指标都显示详细计算过程和数据来源
"""
    
    ax.text(50, 5, tech_points, ha='center', va='center', fontsize=9, 
           bbox=dict(boxstyle="round,pad=0.8", facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('/Users/Shared/Files From d.localized/projects/protein_screening/隐形乳房炎月度监测逻辑流程图.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig

if __name__ == "__main__":
    fig = create_mastitis_monitoring_flowchart()
    print("✅ 隐形乳房炎月度监测逻辑流程图已生成")
    print("📁 保存位置: /Users/Shared/Files From d.localized/projects/protein_screening/隐形乳房炎月度监测逻辑流程图.png")