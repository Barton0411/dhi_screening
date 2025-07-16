#!/usr/bin/env python3
"""
DHI精准筛查助手 OneDrive打包脚本
为用户创建完整的项目包用于OneDrive分享
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

def create_package():
    # 目标目录
    package_dir = Path.home() / "Desktop" / "DHI_Package_for_OneDrive"
    project_name = "DHI_Screening_System_v3.3"
    target_dir = package_dir / project_name
    
    # 清理并创建目录
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 当前项目目录
    source_dir = Path.cwd()
    
    print(f"🔄 创建DHI精准筛查助手 v3.3 OneDrive包...")
    print(f"📁 源目录: {source_dir}")
    print(f"📦 目标目录: {target_dir}")
    
    # 需要包含的文件和目录
    include_files = [
        # 核心源代码
        "main.py",
        "desktop_app.py", 
        "data_processor.py",
        "mastitis_monitoring.py",
        "models.py",
        
        # 配置文件
        "config.yaml",
        "rules.yaml",
        "requirements.txt",
        
        # PyInstaller配置
        "DHI_Screening_System_v3.3.spec",
        
        # Inno Setup配置
        "DHI_Screening_System_v3.0_Setup.iss",
        
        # 资源文件
        "whg3r-qi1nv-001.ico",
        
        # 文档
        "README.md",
        "CHANGELOG.md",
        "LICENSE.txt",
        "DHI_精准筛查助手-操作说明.md",
        "需求说明.md",
        "干奶前流行率问题解决方案.md",
        
        # 流程图和设计文档
        "干奶前流行率逻辑流程图.png",
        "数据整合架构对比.png", 
        "界面布局方案对比.png",
        "阶段1-数据预处理.mmd",
        "阶段2-指标计算逻辑.mmd",
        "阶段3-结果展示逻辑.mmd",
        "阶段4-异常处理流程.mmd",
        
        # 测试文件
        "test_startup.py",
        "test_mastitis_monitoring.py",
        
        # 静态资源目录
        "static",
        
        # 测试数据
        "files_for_test"
    ]
    
    # 复制文件
    copied_files = []
    for item in include_files:
        source_path = source_dir / item
        if source_path.exists():
            target_path = target_dir / item
            
            if source_path.is_file():
                # 复制文件
                shutil.copy2(source_path, target_path)
                copied_files.append(item)
                print(f"✅ 文件: {item}")
            elif source_path.is_dir():
                # 复制目录
                shutil.copytree(source_path, target_path)
                copied_files.append(item)
                print(f"📁 目录: {item}")
        else:
            print(f"⚠️  未找到: {item}")
    
    # 创建使用说明
    readme_content = f"""# DHI精准筛查助手 v3.3 - 完整项目包

## 📦 包内容

此包包含DHI精准筛查助手的完整源代码和资源文件，适用于：
- 本地开发和修改
- 创建自定义安装包 
- 代码学习和研究

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装Python 3.11
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境 (Windows)
venv\\Scripts\\activate
# 安装依赖
pip install -r requirements.txt
```

### 2. 运行程序
```bash
python main.py
```

### 3. 创建安装包

#### 使用PyInstaller创建EXE
```bash
pyinstaller --clean --noconfirm DHI_Screening_System_v3.3.spec
```

#### 使用Inno Setup创建安装包
1. 安装Inno Setup 6.x
2. 打开 `DHI_Screening_System_v3.0_Setup.iss`
3. 修改架构设置确保兼容性：
   ```
   ArchitecturesAllowed=x86 x64
   ; 注释掉或删除下面这行以支持32位系统
   ; ArchitecturesInstallIn64BitMode=x64
   ```
4. 编译生成安装包

## 📚 文档说明

- `README.md` - 项目总体说明
- `CHANGELOG.md` - 版本更新历史  
- `DHI_精准筛查助手-操作说明.md` - 用户操作指南
- `需求说明.md` - 功能需求文档
- `干奶前流行率问题解决方案.md` - 技术解决方案

## 🔧 核心文件

- `main.py` - 程序入口
- `desktop_app.py` - 桌面GUI应用
- `data_processor.py` - 数据处理核心
- `mastitis_monitoring.py` - 乳房炎监测模块
- `config.yaml` / `rules.yaml` - 配置文件

## 📊 测试数据

`files_for_test/` 目录包含测试用的DHI数据文件，可用于功能验证。

## 🎯 架构兼容性注意事项

**重要**：创建Windows安装包时，确保Inno Setup配置正确支持32位和64位系统：

```ini
[Setup]
ArchitecturesAllowed=x86 x64
; 不要设置 ArchitecturesInstallIn64BitMode=x64
```

## 📞 技术支持

- 版本：v3.3
- 更新日期：{datetime.now().strftime('%Y-%m-%d')}
- 开发单位：伊利液奶奶科院

## 📄 许可证

详见 LICENSE.txt 文件
"""
    
    with open(target_dir / "项目说明.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"📝 创建项目说明文档")
    
    # 创建压缩包
    zip_file = package_dir / f"{project_name}_{datetime.now().strftime('%Y%m%d')}.zip"
    
    print(f"\n🗜️  创建压缩包: {zip_file.name}")
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                file_path = Path(root) / file
                arc_name = file_path.relative_to(target_dir)
                zf.write(file_path, arc_name)
                
    # 获取压缩包大小
    size_mb = zip_file.stat().st_size / (1024 * 1024)
    
    print(f"\n✅ 打包完成！")
    print(f"📦 压缩包: {zip_file}")
    print(f"📏 文件大小: {size_mb:.1f} MB")
    print(f"📁 文件数量: {len(copied_files)} 项")
    
    print(f"\n🌐 OneDrive上传指南:")
    print(f"1. 打开OneDrive网页版或桌面应用")
    print(f"2. 上传文件: {zip_file}")
    print(f"3. 创建分享链接")
    print(f"4. 设置权限（可查看/可编辑）")
    
    return zip_file

if __name__ == "__main__":
    create_package()
