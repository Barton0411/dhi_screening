# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_app():
    """使用PyInstaller打包DHI蛋白筛查系统"""
    
    print("开始打包DHI蛋白筛查系统...")
    
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 清理之前的构建文件
    print("清理之前的构建文件...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   已删除: {dir_name}")
    
    # 删除之前的spec文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        os.remove(spec_file)
        print(f"   已删除: {spec_file}")
    
    # 检查必要文件是否存在
    required_files = [
        'desktop_app.py',
        'config.yaml',
        'rules.yaml',
        'models.py', 
        'data_processor.py',
        'whg3r-qi1nv-001.ico'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"错误：缺少以下必要文件:")
        for file_name in missing_files:
            print(f"   - {file_name}")
        return False
    
    # PyInstaller命令参数
    app_name = "DHI蛋白筛查系统"
    main_script = "desktop_app.py"
    
    pyinstaller_args = [
        'pyinstaller',
        '--onedir',  # 使用onedir模式
        '--windowed',  # Windows下隐藏控制台窗口
        '--noconfirm',  # 不询问覆盖
        f'--name={app_name}',
        '--clean',  # 清理临时文件
        
        # 添加图标
        '--icon=whg3r-qi1nv-001.ico',
        
        # 添加数据文件 - 包含所有必要的配置和模块文件
        '--add-data=config.yaml;.',
        '--add-data=rules.yaml;.',  # 重要！筛选规则配置
        '--add-data=models.py;.',
        '--add-data=data_processor.py;.',
        '--add-data=requirements.txt;.',
        
        # 添加图标文件到程序内部
        '--add-data=whg3r-qi1nv-001.ico;.',
        
        # 排除不需要的模块以减小体积
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=tornado',
        '--exclude-module=fastapi',
        '--exclude-module=uvicorn',
        
        # 添加隐藏导入（确保PyQt6相关模块被包含）
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtWidgets', 
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=yaml',
        '--hidden-import=openpyxl',
        '--hidden-import=pandas',
        
        # 主脚本
        main_script
    ]
    
    print("开始PyInstaller打包...")
    print(f"   命令: {' '.join(pyinstaller_args)}")
    
    try:
        # 运行PyInstaller
        result = subprocess.run(pyinstaller_args, check=True, capture_output=True, text=True, encoding='utf-8')
        print("PyInstaller打包完成!")
        
        # 检查输出目录
        dist_dir = Path('dist') / app_name
        if dist_dir.exists():
            print(f"应用程序已打包到: {dist_dir.absolute()}")
            
            # 复制额外文件到输出目录
            extra_files = [
                'README.md',
                '需求说明.md'
            ]
            
            print("复制额外文件...")
            for file_name in extra_files:
                if os.path.exists(file_name):
                    shutil.copy2(file_name, dist_dir)
                    print(f"   已复制: {file_name}")
            
            # 创建使用说明
            create_usage_guide(dist_dir)
            
            # 验证关键文件是否被正确包含
            verify_packaging(dist_dir)
            
            # 显示打包结果
            print()
            print("=== 打包完成! ===")
            print(f"输出目录: {dist_dir.absolute()}")
            print(f"主程序: {dist_dir / f'{app_name}.exe'}")
            print()
            print("使用说明:")
            print("   1. 进入输出目录")
            print(f"   2. 双击运行 {app_name}.exe")
            print("   3. 首次运行可能需要几秒钟启动时间")
            print("   4. 如需分发，可将整个文件夹打包为ZIP")
            
        else:
            print("打包失败：找不到输出目录")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller打包失败:")
        print(f"   错误代码: {e.returncode}")
        if e.stderr:
            print(f"   错误输出: {e.stderr}")
        if e.stdout:
            print(f"   标准输出: {e.stdout}")
        return False
    except Exception as e:
        print(f"打包过程中发生错误: {e}")
        return False
    
    return True

def verify_packaging(dist_dir):
    """验证打包结果是否包含必要文件"""
    print("验证打包结果...")
    
    # 检查关键文件是否存在
    critical_files = [
        'config.yaml',
        'rules.yaml',
        'models.py',
        'data_processor.py',
        'whg3r-qi1nv-001.ico'
    ]
    
    missing_critical = []
    for file_name in critical_files:
        file_path = dist_dir / file_name
        if file_path.exists():
            print(f"   ✓ {file_name}")
        else:
            missing_critical.append(file_name)
            print(f"   ✗ {file_name} (缺失)")
    
    if missing_critical:
        print(f"   警告：缺少关键文件，可能会导致运行时错误")
        return False
    else:
        print("   所有关键文件已正确包含")
        return True

def create_usage_guide(dist_dir):
    """创建使用说明文件"""
    usage_content = """DHI蛋白筛查系统 使用说明

== 快速开始 ==

1. 启动程序
   - 双击 DHI蛋白筛查系统.exe 启动程序
   - 首次启动可能需要几秒钟时间

2. 上传文件
   - 点击"选择文件"按钮
   - 选择DHI报告Excel文件或ZIP压缩包
   - 程序会自动处理和分析数据

3. 设置筛选条件
   - 调整牛场编号、胎次范围、蛋白率等筛选条件
   - 设置采样日期范围
   - 可选择是否启用未来泌乳天数筛选

4. 查看结果
   - 点击"开始筛选"进行数据筛选
   - 在"筛选结果"标签页查看筛选后的数据
   - 在"筛选分析"标签页查看统计信息

5. 导出结果
   - 点击"导出Excel"保存筛选结果
   - 可选择直接打开文件或打开文件夹

== 界面设置 ==

- 点击菜单栏"设置 -> 界面显示设置"
- 可调整字体大小、颜色、样式等
- 支持显示缩放调节
- 设置会自动保存

== 文件结构 ==

DHI蛋白筛查系统/
├── DHI蛋白筛查系统.exe    # 主程序
├── config.yaml           # 系统配置文件
├── rules.yaml            # 筛选规则配置
├── models.py             # 数据模型
├── data_processor.py     # 数据处理模块
├── whg3r-qi1nv-001.ico  # 程序图标
├── 使用说明.txt          # 本文件
└── _internal/            # 程序依赖文件（请勿删除）

== 注意事项 ==

- 请确保上传的是标准DHI报告格式
- 程序支持.xlsx和.zip格式文件
- 建议定期备份筛选结果
- 如遇问题请联系技术支持
- 分发时请保持整个文件夹完整，不要只复制exe文件

== 故障排除 ==

1. 如果程序无法启动：
   - 检查是否有杀毒软件阻止
   - 确保所有文件都在同一目录下
   - 尝试以管理员权限运行

2. 如果出现"缺少文件"错误：
   - 确保config.yaml和rules.yaml文件存在
   - 重新解压安装包
   - 检查文件夹权限

版本: 2.0
更新日期: 2024年12月
构建包含: 所有配置文件、图标、核心模块
"""
    
    usage_file = dist_dir / "使用说明.txt"
    with open(usage_file, 'w', encoding='utf-8') as f:
        f.write(usage_content)
    print(f"   已创建: 使用说明.txt")

def check_requirements():
    """检查打包所需的依赖"""
    print("检查打包环境...")
    
    required_packages = [
        'pyinstaller',
        'PyQt6',
        'pandas',
        'openpyxl',
        'PyYAML'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PyYAML':
                import yaml
            else:
                __import__(package)
            print(f"   已安装: {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   缺失: {package}")
    
    if missing_packages:
        print(f"\n缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print(f"\n请运行: pip install {' '.join(missing_packages)}")
        return False
    
    print("所有依赖检查通过!")
    return True

if __name__ == "__main__":
    print("DHI蛋白筛查系统 - PyInstaller打包工具")
    print("=" * 50)
    
    # 检查环境
    if not check_requirements():
        sys.exit(1)
    
    # 开始打包
    if build_app():
        print("\n=== 打包成功完成! ===")
        print("您现在可以分发 dist/DHI蛋白筛查系统/ 整个文件夹")
        sys.exit(0)
    else:
        print("\n=== 打包失败! ===")
        print("请检查错误信息并重试")
        sys.exit(1) 