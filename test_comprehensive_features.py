"""
DHI蛋白筛查系统 - 综合功能测试
使用真实测试数据验证所有新功能的强壮度
"""

import sys
import os
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor import DataProcessor

class ComprehensiveFeatureTester:
    """综合功能测试类"""
    
    def __init__(self):
        self.test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "测试数据")
        self.dhi_dir = os.path.join(self.test_data_dir, "DHI报告")
        self.cattle_dir = os.path.join(self.test_data_dir, "牧场在群牛数据")
        self.processor = DataProcessor()
        
        print(f"测试数据目录: {self.test_data_dir}")
        print(f"DHI报告目录: {self.dhi_dir}")
        print(f"在群牛数据目录: {self.cattle_dir}")
    
    def test_1_file_processing_robustness(self):
        """测试1: 文件处理的强壮度"""
        print("\n" + "="*60)
        print("测试1: 文件处理强壮度 - 处理多种DHI文件格式")
        print("="*60)
        
        # 获取所有DHI文件
        dhi_files = []
        if os.path.exists(self.dhi_dir):
            for file in os.listdir(self.dhi_dir):
                if file.endswith(('.xlsx', '.xls', '.zip')):
                    file_path = os.path.join(self.dhi_dir, file)
                    dhi_files.append((file_path, file))
        
        print(f"找到{len(dhi_files)}个DHI文件:")
        for i, (_, filename) in enumerate(dhi_files, 1):
            print(f"  {i}. {filename}")
        
        # 测试每个文件的处理
        success_count = 0
        failed_count = 0
        all_results = []
        
        for file_path, filename in dhi_files:
            print(f"\n处理文件: {filename}")
            try:
                success, message, df = self.processor.process_uploaded_file(file_path, filename)
                
                if success and df is not None:
                    print(f"  ✅ 成功: {message}")
                    print(f"     数据行数: {len(df)}")
                    
                    # 检查关键字段
                    key_fields = ['farm_id', 'management_id', 'sample_date', 'protein_pct']
                    missing_fields = [field for field in key_fields if field not in df.columns]
                    if missing_fields:
                        print(f"     ⚠️  缺少字段: {missing_fields}")
                    
                    # 检查数据质量
                    if 'farm_id' in df.columns:
                        farm_ids = df['farm_id'].dropna().unique()
                        print(f"     牧场编号: {list(farm_ids)}")
                    
                    if 'management_id' in df.columns:
                        mgmt_count = df['management_id'].notna().sum()
                        print(f"     管理号数量: {mgmt_count}")
                    
                    all_results.append({
                        'filename': filename,
                        'data': df,
                        'success': True,
                        'message': message
                    })
                    success_count += 1
                else:
                    print(f"  ❌ 失败: {message}")
                    all_results.append({
                        'filename': filename,
                        'success': False,
                        'message': message
                    })
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ❌ 异常: {str(e)}")
                failed_count += 1
        
        print(f"\n文件处理汇总:")
        print(f"  成功: {success_count}/{len(dhi_files)}")
        print(f"  失败: {failed_count}/{len(dhi_files)}")
        
        return all_results
    
    def test_2_farm_id_consistency(self, data_results: List[Dict]):
        """测试2: 牧场编号一致性检查和统一"""
        print("\n" + "="*60)
        print("测试2: 牧场编号一致性检查和统一功能")
        print("="*60)
        
        # 只使用成功处理的数据
        valid_data = [item for item in data_results if item.get('success', False) and 'data' in item]
        
        if len(valid_data) < 2:
            print("⚠️  需要至少2个有效文件来测试牧场编号一致性")
            return
        
        print(f"使用{len(valid_data)}个有效文件进行测试")
        
        # 检查一致性
        is_consistent, all_farm_ids, farm_id_files_map = self.processor.check_farm_id_consistency(valid_data)
        
        print(f"\n牧场编号一致性检查结果:")
        print(f"  一致性: {'✅ 一致' if is_consistent else '❌ 不一致'}")
        print(f"  发现的牧场编号: {all_farm_ids}")
        print(f"  牧场编号分布:")
        
        for farm_id, files in farm_id_files_map.items():
            print(f"    牧场{farm_id}: {len(files)}个文件")
            for file in files:
                print(f"      - {file}")
        
        # 如果不一致，测试统一功能
        if not is_consistent and len(all_farm_ids) > 1:
            print(f"\n测试牧场编号统一功能")
            target_farm_id = all_farm_ids[0]  # 选择第一个作为目标
            print(f"  目标牧场编号: {target_farm_id}")
            
            try:
                unified_data = self.processor.unify_farm_ids(valid_data, target_farm_id)
                
                # 验证统一结果
                final_is_consistent, final_farm_ids, final_map = self.processor.check_farm_id_consistency(unified_data)
                
                print(f"  统一后结果:")
                print(f"    一致性: {'✅ 成功' if final_is_consistent else '❌ 失败'}")
                print(f"    最终牧场编号: {final_farm_ids}")
                
                return unified_data
            except Exception as e:
                print(f"  ❌ 统一过程出错: {str(e)}")
                return valid_data
        
        return valid_data
    
    def test_3_active_cattle_filter(self, data_results: List[Dict]):
        """测试3: 在群牛筛选功能"""
        print("\n" + "="*60)
        print("测试3: 在群牛筛选功能")
        print("="*60)
        
        # 查找在群牛文件
        cattle_file = None
        if os.path.exists(self.cattle_dir):
            for file in os.listdir(self.cattle_dir):
                if file.endswith(('.xlsx', '.xls')):
                    cattle_file = os.path.join(self.cattle_dir, file)
                    print(f"找到在群牛文件: {file}")
                    break
        
        if not cattle_file:
            print("❌ 未找到在群牛文件，跳过测试")
            return
        
        # 处理在群牛文件
        try:
            success, message, cattle_list = self.processor.process_active_cattle_file(cattle_file, os.path.basename(cattle_file))
            
            print(f"\n在群牛文件处理结果:")
            print(f"  成功: {'✅' if success else '❌'}")
            print(f"  消息: {message}")
            
            if success and cattle_list:
                print(f"  在群牛数量: {len(cattle_list)}")
                print(f"  在群牛号示例: {cattle_list[:10] if len(cattle_list) >= 10 else cattle_list}")
                
                # 测试筛选功能
                print(f"\n测试在群牛筛选:")
                
                valid_data = [item for item in data_results if item.get('success', False) and 'data' in item]
                
                total_before = 0
                total_after = 0
                
                for item in valid_data:
                    df = item['data']
                    if 'management_id' in df.columns:
                        before_count = len(df.groupby(['farm_id', 'management_id']) if 'farm_id' in df.columns else df.groupby('management_id'))
                        
                        filtered_df = self.processor.apply_active_cattle_filter(df)
                        
                        after_count = len(filtered_df.groupby(['farm_id', 'management_id']) if 'farm_id' in filtered_df.columns else filtered_df.groupby('management_id'))
                        
                        print(f"  {item['filename']}: {before_count}头牛 -> {after_count}头牛")
                        total_before += before_count
                        total_after += after_count
                
                print(f"\n总体筛选效果: {total_before}头牛 -> {total_after}头牛")
                print(f"保留比例: {(total_after/total_before*100):.1f}%" if total_before > 0 else "无数据")
                
        except Exception as e:
            print(f"❌ 在群牛筛选测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def test_4_multi_filter_logic(self, data_results: List[Dict]):
        """测试4: 多筛选项逻辑"""
        print("\n" + "="*60)
        print("测试4: 多筛选项逻辑 - 蛋白率、体细胞数等")
        print("="*60)
        
        valid_data = [item for item in data_results if item.get('success', False) and 'data' in item]
        
        if not valid_data:
            print("❌ 没有有效数据进行筛选测试")
            return
        
        # 合并所有数据以分析字段分布
        all_data = []
        for item in valid_data:
            all_data.append(item['data'])
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        print(f"合并数据: {len(combined_df)}行记录")
        print(f"可用字段: {list(combined_df.columns)}")
        
        # 检查关键筛选字段的数据情况
        filter_fields = {
            'protein_pct': '蛋白率(%)',
            'somatic_cell_count': '体细胞数(万/ml)',
            'fat_pct': '乳脂率(%)',
            'fat_protein_ratio': '脂蛋比'
        }
        
        print(f"\n筛选字段数据分析:")
        available_fields = {}
        
        for field, chinese_name in filter_fields.items():
            if field in combined_df.columns:
                non_null_count = combined_df[field].notna().sum()
                if non_null_count > 0:
                    min_val = combined_df[field].min()
                    max_val = combined_df[field].max()
                    avg_val = combined_df[field].mean()
                    print(f"  ✅ {chinese_name}: {non_null_count}条有效数据, 范围{min_val:.2f}-{max_val:.2f}, 平均{avg_val:.2f}")
                    available_fields[field] = {
                        'min': min_val,
                        'max': max_val,
                        'avg': avg_val,
                        'count': non_null_count
                    }
                else:
                    print(f"  ⚠️  {chinese_name}: 无有效数据")
            else:
                print(f"  ❌ {chinese_name}: 字段不存在")
        
        # 设计测试筛选条件
        if 'protein_pct' in available_fields:
            print(f"\n测试蛋白率筛选:")
            
            protein_stats = available_fields['protein_pct']
            # 设置一个合理的筛选范围
            min_threshold = protein_stats['avg'] - 0.2  # 平均值减0.2
            max_threshold = protein_stats['max']
            
            filters = {
                'protein_pct': {
                    'field': 'protein_pct',
                    'enabled': True,
                    'min': min_threshold,
                    'max': max_threshold,
                    'min_match_months': 2,
                    'treat_empty_as_match': False
                }
            }
            
            print(f"  筛选条件: {min_threshold:.2f}% <= 蛋白率 <= {max_threshold:.2f}%")
            print(f"  最少符合月数: 2个月")
            
            try:
                selected_files = [item['filename'] for item in valid_data]
                result_df = self.processor.apply_multi_filter_logic(valid_data, filters, selected_files)
                
                if not result_df.empty:
                    unique_cows = len(result_df.groupby(['farm_id', 'management_id']) if 'farm_id' in result_df.columns else result_df.groupby('management_id'))
                    print(f"  ✅ 筛选结果: {unique_cows}头牛符合条件")
                else:
                    print(f"  ⚠️  无牛符合筛选条件")
                    
            except Exception as e:
                print(f"  ❌ 蛋白率筛选失败: {str(e)}")
        
        # 测试多字段联合筛选
        if len(available_fields) >= 2:
            print(f"\n测试多字段联合筛选:")
            
            multi_filters = {}
            
            # 添加蛋白率筛选
            if 'protein_pct' in available_fields:
                protein_stats = available_fields['protein_pct']
                multi_filters['protein_pct'] = {
                    'field': 'protein_pct',
                    'enabled': True,
                    'min': protein_stats['avg'] - 0.3,
                    'max': protein_stats['max'],
                    'min_match_months': 2,
                    'treat_empty_as_match': False
                }
                print(f"  蛋白率: >= {protein_stats['avg'] - 0.3:.2f}%")
            
            # 添加体细胞数筛选
            if 'somatic_cell_count' in available_fields:
                somatic_stats = available_fields['somatic_cell_count']
                multi_filters['somatic_cell_count'] = {
                    'field': 'somatic_cell_count',
                    'enabled': True,
                    'min': somatic_stats['min'],
                    'max': somatic_stats['avg'] + 10,  # 平均值加10
                    'min_match_months': 2,
                    'treat_empty_as_match': False
                }
                print(f"  体细胞数: <= {somatic_stats['avg'] + 10:.1f}万/ml")
            
            if len(multi_filters) >= 2:
                try:
                    selected_files = [item['filename'] for item in valid_data]
                    multi_result_df = self.processor.apply_multi_filter_logic(valid_data, multi_filters, selected_files)
                    
                    if not multi_result_df.empty:
                        unique_cows = len(multi_result_df.groupby(['farm_id', 'management_id']) if 'farm_id' in multi_result_df.columns else multi_result_df.groupby('management_id'))
                        print(f"  ✅ 联合筛选结果: {unique_cows}头牛同时符合所有条件")
                    else:
                        print(f"  ⚠️  无牛同时符合所有筛选条件")
                        
                except Exception as e:
                    print(f"  ❌ 多字段筛选失败: {str(e)}")
    
    def test_5_optional_filters_config(self):
        """测试5: 可选筛选项目配置"""
        print("\n" + "="*60)
        print("测试5: 可选筛选项目配置")
        print("="*60)
        
        # 检查配置文件中的可选筛选项
        optional_filters = self.processor.rules.get("optional_filters", {})
        field_map = self.processor.rules.get("field_map", {})
        
        print(f"配置的可选筛选项目 (共{len(optional_filters)}项):")
        
        for i, (field_key, config) in enumerate(optional_filters.items(), 1):
            chinese_name = config.get('chinese_name', field_key)
            min_val = config.get('min', 0)
            max_val = config.get('max', 100)
            min_months = config.get('min_match_months', 3)
            
            print(f"  {i:2d}. {chinese_name} ({field_key})")
            print(f"      默认范围: {min_val} - {max_val}")
            print(f"      最少符合月数: {min_months}")
        
        # 检查字段映射
        print(f"\n字段映射检查:")
        new_fields_count = 0
        for chinese_name, english_name in field_map.items():
            if english_name in optional_filters:
                new_fields_count += 1
                print(f"  ✅ {chinese_name} -> {english_name}")
        
        print(f"\n配置完整性:")
        print(f"  可选筛选项: {len(optional_filters)}项")
        print(f"  已映射字段: {new_fields_count}项")
        print(f"  配置完整性: {(new_fields_count/len(optional_filters)*100):.1f}%")
    
    def test_6_error_handling(self):
        """测试6: 错误处理和边界情况"""
        print("\n" + "="*60)
        print("测试6: 错误处理和边界情况")
        print("="*60)
        
        test_cases = [
            "空文件路径",
            "不存在的文件",
            "损坏的ZIP文件",
            "空的Excel文件",
            "缺少关键列的Excel文件",
            "在群牛文件格式错误",
            "无效的筛选参数"
        ]
        
        print(f"测试错误处理场景:")
        
        # 测试1: 空文件路径
        try:
            success, message, df = self.processor.process_uploaded_file("", "")
            print(f"  1. 空文件路径: {'✅ 正确处理' if not success else '❌ 应该失败'}")
        except Exception as e:
            print(f"  1. 空文件路径: ✅ 正确抛出异常")
        
        # 测试2: 不存在的文件
        try:
            success, message, df = self.processor.process_uploaded_file("不存在的文件.xlsx", "test.xlsx")
            print(f"  2. 不存在的文件: {'✅ 正确处理' if not success else '❌ 应该失败'}")
        except Exception as e:
            print(f"  2. 不存在的文件: ✅ 正确抛出异常")
        
        # 测试3: 创建临时损坏文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file.write("这不是一个有效的Excel文件".encode('utf-8'))
            temp_path = temp_file.name
        
        try:
            success, message, df = self.processor.process_uploaded_file(temp_path, "damaged.xlsx")
            print(f"  3. 损坏的Excel文件: {'✅ 正确处理' if not success else '❌ 应该失败'}")
        except Exception as e:
            print(f"  3. 损坏的Excel文件: ✅ 正确抛出异常")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        # 测试4: 空的筛选条件
        try:
            empty_data = [{'filename': 'test.xlsx', 'data': pd.DataFrame()}]
            result = self.processor.apply_multi_filter_logic(empty_data, {}, [])
            print(f"  4. 空数据筛选: ✅ 正确处理")
        except Exception as e:
            print(f"  4. 空数据筛选: ❌ 处理异常: {str(e)}")
        
        print(f"\n错误处理测试完成")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("DHI蛋白筛查系统 - 综合功能测试")
        print("测试新增功能的强壮度和边界情况处理")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 测试1: 文件处理强壮度
            data_results = self.test_1_file_processing_robustness()
            
            # 测试2: 牧场编号一致性
            unified_data = self.test_2_farm_id_consistency(data_results)
            
            # 测试3: 在群牛筛选
            self.test_3_active_cattle_filter(unified_data)
            
            # 测试4: 多筛选项逻辑
            self.test_4_multi_filter_logic(unified_data)
            
            # 测试5: 可选筛选项配置
            self.test_5_optional_filters_config()
            
            # 测试6: 错误处理
            self.test_6_error_handling()
            
            print("\n" + "="*60)
            print("✅ 所有测试完成")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("启动DHI蛋白筛查系统综合功能测试...")
    
    tester = ComprehensiveFeatureTester()
    tester.run_all_tests()
    
    input("\n按回车键退出...") 