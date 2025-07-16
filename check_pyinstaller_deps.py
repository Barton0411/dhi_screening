#!/usr/bin/env python3
"""
PyInstaller依赖检查工具
用于诊断DHI筛查系统打包时可能缺少的文件和依赖
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

def check_python_dll():
    """检查Python DLL是否可用"""
    print("🔍 检查Python运行时...")
    
    # 获取Python版本信息
    version_info = sys.version_info
    python_version = f"python{version_info.major}{version_info.minor}"
    
    # 在Windows上查找Python DLL
    if platform.system() == "Windows":
        python_dll = f"{python_version}.dll"
        python_dir = Path(sys.executable).parent
        
        # 检查可能的DLL位置
        dll_locations = [
            python_dir / python_dll,
            python_dir / "DLLs" / python_dll,
            Path(sys.prefix) / python_dll,
            Path(sys.prefix) / "DLLs" / python_dll,
        ]
        
        found_dll = False
        for location in dll_locations:
            if location.exists():
                print(f"✅ 找到Python DLL: {location}")
                found_dll = True
                break
        
        if not found_dll:
            print(f"❌ 未找到 {python_dll}")
            print(f"   Python路径: {sys.executable}")
            print(f"   搜索位置: {[str(loc) for loc in dll_locations]}")
            return False
    
    return True

def check_required_modules():
    """检查必需的模块是否可导入"""
    print("\n🔍 检查必需模块...")
    
    required_modules = {
        # 核心库
        'PyQt6': ['PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui'],
        'pandas': ['pandas'],
        'numpy': ['numpy', 'numpy.core._multiarray_umath'],
        'openpyxl': ['openpyxl', 'openpyxl.styles', 'openpyxl.utils.dataframe'],
        'yaml': ['yaml'],
        
        # 本地模块
        'local': ['data_processor', 'models', 'mastitis_monitoring']
    }
    
    all_ok = True
    for category, modules in required_modules.items():
        print(f"\n📚 {category} 模块:")
        for module in modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except ImportError as e:
                print(f"  ❌ {module}: {e}")
                all_ok = False
            except Exception as e:
                print(f"  ⚠️ {module}: {e}")
    
    return all_ok

def check_data_files():
    """检查数据文件是否存在"""
    print("\n🔍 检查数据文件...")
    
    required_files = [
        'config.yaml',
        'rules.yaml',
        'whg3r-qi1nv-001.ico',
        'README.md',
        'desktop_app.py',
        'data_processor.py',
        'models.py',
        'mastitis_monitoring.py'
    ]
    
    all_ok = True
    for filename in required_files:
        if os.path.exists(filename):
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename}")
            all_ok = False
    
    return all_ok

def check_pyinstaller_config():
    """检查PyInstaller配置"""
    print("\n🔍 检查PyInstaller配置...")
    
    spec_file = "DHI_Screening_System_v3.3.spec"
    if not os.path.exists(spec_file):
        print(f"❌ 未找到spec文件: {spec_file}")
        return False
    
    print(f"✅ 找到spec文件: {spec_file}")
    
    # 检查spec文件内容
    with open(spec_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键配置
    checks = [
        ('exclude_binaries=True', 'OneDIR模式配置'),
        ('mastitis_monitoring', '本地模块导入'),
        ('openpyxl.styles', 'openpyxl子模块'),
        ('console=False', 'GUI应用配置'),
        ('COLLECT', 'OneDIR收集配置')
    ]
    
    for check, desc in checks:
        if check in content:
            print(f"  ✅ {desc}: {check}")
        else:
            print(f"  ❌ {desc}: 未找到 {check}")
    
    return True

def suggest_fixes():
    """提供修复建议"""
    print("\n🔧 修复建议:")
    print("1. 确保已更新到最新的spec文件配置")
    print("2. 重新运行PyInstaller构建:")
    print("   pyinstaller --clean --noconfirm DHI_Screening_System_v3.3.spec")
    print("3. 如果仍有DLL问题，尝试:")
    print("   - 在虚拟环境中重新安装Python")
    print("   - 使用 --add-binary 手动添加DLL")
    print("   - 检查PyInstaller版本兼容性")
    print("4. 确保所有依赖都已安装:")
    print("   pip install -r requirements.txt")

def main():
    """主函数"""
    print("=" * 60)
    print("DHI筛查系统 - PyInstaller依赖检查工具")
    print("=" * 60)
    
    print(f"Python版本: {sys.version}")
    print(f"平台: {platform.platform()}")
    print(f"架构: {platform.architecture()[0]}")
    print(f"可执行文件: {sys.executable}")
    
    # 执行检查
    dll_ok = check_python_dll()
    modules_ok = check_required_modules()
    files_ok = check_data_files()
    config_ok = check_pyinstaller_config()
    
    print("\n" + "=" * 60)
    print("检查结果汇总:")
    print(f"Python DLL: {'✅' if dll_ok else '❌'}")
    print(f"必需模块: {'✅' if modules_ok else '❌'}")
    print(f"数据文件: {'✅' if files_ok else '❌'}")  
    print(f"PyInstaller配置: {'✅' if config_ok else '❌'}")
    
    if all([dll_ok, modules_ok, files_ok, config_ok]):
        print("\n🎉 所有检查通过！可以尝试重新构建。")
    else:
        print("\n⚠️ 发现问题，请参考修复建议。")
        suggest_fixes()

if __name__ == "__main__":
    main() 