#!/usr/bin/env python3
"""创建白色DMG背景图片"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("需要安装Pillow库：pip install Pillow")
    exit(1)

# 创建白色背景
width, height = 600, 400
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# 添加一个浅灰色的箭头提示（可选）
# 箭头从左指向右，位于中央
arrow_color = (200, 200, 200)  # 浅灰色
arrow_y = height // 2

# 绘制简单的箭头
arrow_points = [
    (200, arrow_y),      # 箭头起点
    (380, arrow_y),      # 箭头主体终点
    (380, arrow_y - 20), # 上箭头点
    (400, arrow_y),      # 箭头尖端
    (380, arrow_y + 20), # 下箭头点
    (380, arrow_y),      # 回到主体终点
]

# 绘制箭头主体（直线）
draw.line([(200, arrow_y), (380, arrow_y)], fill=arrow_color, width=3)

# 绘制箭头头部
draw.polygon([
    (370, arrow_y - 15),
    (400, arrow_y),
    (370, arrow_y + 15)
], fill=arrow_color)

# 保存图片
import os
base_dir = '/Users/Shared/Files From d.localized/projects/protein_screening'
docs_dir = os.path.join(base_dir, 'docs')
os.makedirs(docs_dir, exist_ok=True)
output_path = os.path.join(docs_dir, 'dmg-background.png')
image.save(output_path, 'PNG')
print(f"✅ 白色背景图片已创建：{output_path}")