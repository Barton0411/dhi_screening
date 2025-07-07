#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
干奶前流行率诊断脚本
用于诊断为什么干奶前流行率无结果
"""

import pandas as pd
import logging
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_pre_dry_prevalence():
    """诊断干奶前流行率计算问题"""
    try:
        print("=== 干奶前流行率诊断开始 ===\n")
        
        # 1. 检查是否有牛群基础信息文件
        print("1. 🔍 检查牛群基础信息文件...")
        
        possible_files = [
            'test_cattle_info.xlsx',  # 测试文件
            'uploads/牛群基础信息.xlsx',
            'uploads/慧牧云系统_牛群数据管理.xlsx',
            'uploads/伊起牛系统_牛群结构查询.xlsx',
        ]
        
        cattle_info_file = None
        for file_path in possible_files:
            if os.path.exists(file_path):
                cattle_info_file = file_path
                print(f"✅ 找到牛群基础信息文件: {file_path}")
                break
        
        if not cattle_info_file:
            # 搜索所有可能的文件
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if ('牛群' in file or '结构查询' in file) and file.endswith(('.xlsx', '.xls')):
                        cattle_info_file = os.path.join(root, file)
                        print(f"✅ 找到牛群基础信息文件: {cattle_info_file}")
                        break
                if cattle_info_file:
                    break
        
        if not cattle_info_file:
            print("❌ 未找到牛群基础信息文件")
            print("请确保已上传包含在胎天数信息的牛群基础信息文件")
            return
        
        # 2. 读取并分析牛群基础信息
        print(f"\n2. 📊 分析牛群基础信息文件: {cattle_info_file}")
        
        try:
            cattle_df = pd.read_excel(cattle_info_file)
            print(f"✅ 成功读取，共 {len(cattle_df)} 行数据")
            print(f"列名: {list(cattle_df.columns)}")
            
            # 检查关键字段
            key_fields = ['耳号', '在胎天数', '怀孕天数', 'gestation_days', 'pregnancy_days']
            found_fields = []
            
            for field in key_fields:
                if field in cattle_df.columns:
                    found_fields.append(field)
                    non_null_count = cattle_df[field].count()
                    print(f"  - {field}: {non_null_count} 个非空值")
                    
                    if '天数' in field:
                        # 分析在胎天数分布
                        valid_data = cattle_df[field].dropna()
                        if len(valid_data) > 0:
                            over_180 = (valid_data > 180).sum()
                            print(f"    范围: {valid_data.min():.0f} - {valid_data.max():.0f} 天")
                            print(f"    >180天的牛只: {over_180} 头")
            
            if not any('天数' in field for field in found_fields):
                print("❌ 未找到在胎天数相关字段")
                print("需要的字段：在胎天数、怀孕天数、gestation_days 或 pregnancy_days")
                return
                
        except Exception as e:
            print(f"❌ 读取牛群基础信息失败: {e}")
            return
        
        # 3. 检查DHI数据
        print(f"\n3. 📈 检查DHI数据...")
        
        dhi_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if ('dhi' in file.lower() or 'ghi' in file.lower()) and file.endswith(('.xlsx', '.xls')):
                    dhi_files.append(os.path.join(root, file))
        
        if not dhi_files:
            print("❌ 未找到DHI数据文件")
            return
        
        print(f"✅ 找到 {len(dhi_files)} 个DHI文件:")
        for file in dhi_files[:3]:  # 只显示前3个
            print(f"  - {file}")
        
        # 读取一个DHI文件作为示例
        try:
            dhi_df = pd.read_excel(dhi_files[0])
            print(f"✅ DHI数据示例 - {len(dhi_df)} 行，列名: {list(dhi_df.columns)}")
            
            # 检查管理号字段
            management_fields = ['管理号', 'management_id', '牛号']
            dhi_management_field = None
            
            for field in management_fields:
                if field in dhi_df.columns:
                    dhi_management_field = field
                    unique_count = dhi_df[field].nunique()
                    print(f"  - 管理号字段: {field}, 唯一值: {unique_count} 个")
                    
                    # 显示几个示例管理号
                    sample_ids = dhi_df[field].dropna().head(5).tolist()
                    print(f"    示例: {sample_ids}")
                    break
            
            if not dhi_management_field:
                print("❌ DHI数据中未找到管理号字段")
                return
                
        except Exception as e:
            print(f"❌ 读取DHI数据失败: {e}")
            return
        
        # 4. 测试管理号匹配
        print(f"\n4. 🔗 测试管理号与耳号匹配...")
        
        try:
            # 标准化处理
            cattle_df_test = cattle_df.copy()
            
            # 找到耳号字段
            ear_tag_field = None
            for field in ['耳号', 'ear_tag']:
                if field in cattle_df_test.columns:
                    ear_tag_field = field
                    break
            
            if not ear_tag_field:
                print("❌ 牛群基础信息中未找到耳号字段")
                return
            
            # 标准化耳号
            cattle_df_test['ear_tag_standardized'] = cattle_df_test[ear_tag_field].astype(str).str.lstrip('0')
            
            # 标准化DHI管理号
            dhi_df_test = dhi_df.copy()
            dhi_df_test['management_id_standardized'] = dhi_df_test[dhi_management_field].astype(str).str.lstrip('0')
            
            # 尝试匹配
            matched_data = dhi_df_test.merge(
                cattle_df_test,
                left_on='management_id_standardized',
                right_on='ear_tag_standardized',
                how='inner'
            )
            
            print(f"✅ 匹配结果:")
            print(f"  - DHI数据: {len(dhi_df_test)} 头牛")
            print(f"  - 牛群基础信息: {len(cattle_df_test)} 头牛")
            print(f"  - 成功匹配: {len(matched_data)} 头牛")
            
            if len(matched_data) == 0:
                print("❌ 无法匹配任何牛只！")
                print("可能原因：")
                print("  1. 管理号与耳号编码方式不同")
                print("  2. 数据来源不是同一个牧场")
                print("  3. 时间差异导致牛只不重叠")
                
                # 显示一些示例数据用于对比
                print("\n💡 数据对比:")
                print(f"DHI管理号示例: {dhi_df_test['management_id_standardized'].head(5).tolist()}")
                print(f"牛群耳号示例: {cattle_df_test['ear_tag_standardized'].head(5).tolist()}")
                return
            
            # 5. 检查在胎天数>180的牛只
            print(f"\n5. 🐄 检查干奶前牛只（在胎天数>180天）...")
            
            # 确定在胎天数字段
            pregnancy_field = None
            for field in ['在胎天数', '怀孕天数', 'gestation_days', 'pregnancy_days']:
                if field in matched_data.columns:
                    pregnancy_field = field
                    break
            
            if not pregnancy_field:
                print("❌ 匹配数据中未找到在胎天数字段")
                return
            
            # 筛选在胎天数>180的牛只
            pre_dry_cattle = matched_data[matched_data[pregnancy_field] > 180]
            
            print(f"✅ 在胎天数字段: {pregnancy_field}")
            print(f"  - 匹配牛只中有在胎天数数据: {matched_data[pregnancy_field].count()} 头")
            print(f"  - 在胎天数>180天的牛只: {len(pre_dry_cattle)} 头")
            
            if len(pre_dry_cattle) == 0:
                print("❌ 没有在胎天数>180天的牛只！")
                pregnancy_data = matched_data[pregnancy_field].dropna()
                if len(pregnancy_data) > 0:
                    print(f"  在胎天数范围: {pregnancy_data.min():.0f} - {pregnancy_data.max():.0f} 天")
                    print(f"  平均在胎天数: {pregnancy_data.mean():.1f} 天")
                else:
                    print("  所有在胎天数都是空值")
                return
            
            # 6. 检查体细胞数据
            print(f"\n6. 🔬 检查体细胞数据...")
            
            scc_field = None
            for field in ['体细胞数(万/ml)', '体细胞数', 'somatic_cell_count']:
                if field in pre_dry_cattle.columns:
                    scc_field = field
                    break
            
            if not scc_field:
                print("❌ 未找到体细胞数字段")
                return
            
            # 检查体细胞数据
            scc_data = pre_dry_cattle[scc_field].dropna()
            if len(scc_data) == 0:
                print("❌ 干奶前牛只没有体细胞数据")
                return
            
            print(f"✅ 体细胞数字段: {scc_field}")
            print(f"  - 干奶前牛只有体细胞数据: {len(scc_data)} 头")
            print(f"  - 体细胞数范围: {scc_data.min():.1f} - {scc_data.max():.1f} 万/ml")
            
            # 计算干奶前流行率
            scc_threshold = 20.0  # 默认阈值
            high_scc_count = (scc_data > scc_threshold).sum()
            total_count = len(scc_data)
            prevalence = (high_scc_count / total_count) * 100
            
            print(f"\n🎯 干奶前流行率计算结果:")
            print(f"  - 体细胞阈值: {scc_threshold} 万/ml")
            print(f"  - 干奶前牛只总数: {total_count} 头")
            print(f"  - 体细胞>阈值的牛只: {high_scc_count} 头")
            print(f"  - 干奶前流行率: {prevalence:.1f}%")
            
        except Exception as e:
            print(f"❌ 匹配测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n=== 诊断完成 ===")
        
    except Exception as e:
        print(f"❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_pre_dry_prevalence() 