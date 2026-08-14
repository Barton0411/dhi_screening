#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐性乳房炎月度监测模块
功能：计算月度流行率、新发感染率、慢性感染率等6个关键指标
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MastitisMonitoringCalculator:
    """隐性乳房炎月度监测计算器"""
    
    def __init__(self, scc_threshold: float = 20.0):
        """
        初始化监测计算器
        
        Args:
            scc_threshold: 体细胞数阈值，默认20万/ml
        """
        self.scc_threshold = scc_threshold
        self.monthly_data = {}  # 存储按月份分组的DHI数据
        self.cattle_basic_info = None  # 牛群基础信息
        self.cattle_system_type = None  # 牛群信息系统类型
        self.results = {}  # 存储计算结果
    
    def set_scc_threshold(self, threshold: float):
        """设置体细胞数阈值"""
        self.scc_threshold = threshold
        logger.info(f"体细胞数阈值已设置为: {threshold}万/ml")
    
    def load_dhi_data(self, dhi_data_list: List[pd.DataFrame]) -> Dict[str, Any]:
        """
        加载DHI数据并按月份分组
        
        Args:
            dhi_data_list: DHI数据DataFrame列表
            
        Returns:
            处理结果字典
        """
        try:
            self.monthly_data = {}
            total_files = len(dhi_data_list)
            processed_files = 0
            skipped_files = 0
            
            logger.info(f"开始加载DHI数据，共{total_files}个数据文件")
            
            for i, df in enumerate(dhi_data_list):
                if df.empty:
                    logger.warning(f"数据文件{i+1}为空，跳过")
                    skipped_files += 1
                    continue
                
                logger.info(f"处理数据文件{i+1}/{total_files}，包含{len(df)}行数据")
                logger.info(f"数据文件{i+1}的字段: {list(df.columns)}")
                
                # 检查必要字段存在 - 更详细的诊断
                required_fields = ['sample_date', 'management_id', 'somatic_cell_count']
                missing_fields = []
                available_similar_fields = {}
                
                for field in required_fields:
                    if field not in df.columns:
                        missing_fields.append(field)
                        # 查找相似字段用于诊断
                        if field == 'sample_date':
                            similar = [c for c in df.columns if any(word in str(c).lower() for word in ['date', '日期', '采样', 'sample'])]
                        elif field == 'management_id':
                            similar = [c for c in df.columns if any(word in str(c).lower() for word in ['id', '号', '管理', 'management', '牛号'])]
                        elif field == 'somatic_cell_count':
                            similar = [c for c in df.columns if any(word in str(c).lower() for word in ['cell', '细胞', '体细胞', 'somatic'])]
                        else:
                            similar = []
                        available_similar_fields[field] = similar
                
                if missing_fields:
                    logger.warning(f"数据文件{i+1}缺少必要字段: {missing_fields}")
                    for missing_field in missing_fields:
                        similar_fields = available_similar_fields.get(missing_field, [])
                        if similar_fields:
                            logger.info(f"  - {missing_field} 可能的相似字段: {similar_fields}")
                        else:
                            logger.info(f"  - {missing_field} 未找到相似字段")
                    skipped_files += 1
                    continue
                
                logger.info(f"数据文件{i+1}字段检查通过，开始按月份分组")
                
                # 按月份分组
                df['sample_date'] = pd.to_datetime(df['sample_date'], errors='coerce')
                invalid_dates = df['sample_date'].isna().sum()
                if invalid_dates > 0:
                    logger.warning(f"数据文件{i+1}有{invalid_dates}行无效日期，将被忽略")
                
                df = df.dropna(subset=['sample_date'])
                
                if df.empty:
                    logger.warning(f"数据文件{i+1}过滤无效日期后为空，跳过")
                    skipped_files += 1
                    continue
                
                months_in_file = 0
                for month, group_df in df.groupby(df['sample_date'].dt.to_period('M')):
                    month_str = str(month)  # 格式: 2025-01
                    months_in_file += 1
                    
                    # 处理同月多次测定：按采样日期排序，取最后一次
                    processed_df = self._process_monthly_duplicates(group_df)
                    
                    # 标准化管理号
                    processed_df = self._standardize_management_ids(processed_df)
                    
                    # 如果已存在该月份数据，合并
                    if month_str in self.monthly_data:
                        existing_df = self.monthly_data[month_str]
                        combined_df = pd.concat([existing_df, processed_df], ignore_index=True)
                        # 再次处理重复数据
                        self.monthly_data[month_str] = self._process_monthly_duplicates(combined_df)
                        logger.info(f"月份{month_str}：合并数据，共{len(self.monthly_data[month_str])}头牛")
                    else:
                        self.monthly_data[month_str] = processed_df
                        logger.info(f"月份{month_str}：新增数据，{len(processed_df)}头牛")
                
                logger.info(f"数据文件{i+1}处理完成，包含{months_in_file}个月份的数据")
                processed_files += 1
            
            if processed_files == 0:
                error_msg = f"所有{total_files}个数据文件都无法处理"
                if skipped_files > 0:
                    error_msg += f"，跳过了{skipped_files}个文件"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'total_files': total_files,
                    'processed_files': processed_files,
                    'skipped_files': skipped_files
                }
            
            final_months = sorted(self.monthly_data.keys())
            total_records = sum(len(df) for df in self.monthly_data.values())
            
            logger.info(f"DHI数据加载完成:")
            logger.info(f"  - 处理文件: {processed_files}/{total_files} (跳过{skipped_files}个)")
            logger.info(f"  - 有效月份: {len(final_months)}个 ({', '.join(final_months)})")
            logger.info(f"  - 总记录数: {total_records}")
            
            return {
                'success': True,
                'months': final_months,
                'total_months': len(final_months),
                'total_files': total_files,
                'processed_files': processed_files,
                'skipped_files': skipped_files,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"加载DHI数据失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def load_cattle_basic_info(self, cattle_df: pd.DataFrame, system_type: str) -> Dict[str, Any]:
        """
        加载牛群基础信息
        
        Args:
            cattle_df: 牛群基础信息DataFrame
            system_type: 系统类型 ('yiqiniu', 'huimuyun', 'other')
            
        Returns:
            处理结果字典
        """
        try:
            self.cattle_basic_info = cattle_df.copy()
            self.cattle_system_type = system_type
            
            # 标准化耳号
            # 支持多种耳号字段名
            ear_tag_field = None
            possible_ear_fields = ['耳号', 'ear_tag', '牛号', 'cow_id', 'tag_id']
            
            for field in possible_ear_fields:
                if field in cattle_df.columns:
                    ear_tag_field = field
                    break
            
            if ear_tag_field:
                self.cattle_basic_info['ear_tag_standardized'] = self.cattle_basic_info[ear_tag_field].astype(str).str.lstrip('0')
                logger.info(f"使用耳号字段: {ear_tag_field}")
            else:
                logger.warning(f"未找到耳号字段，可用字段: {list(cattle_df.columns)}")
            
            # 根据系统类型确定在胎天数字段
            pregnancy_field = self._get_pregnancy_field(system_type)
            
            logger.info(f"成功加载牛群基础信息: {len(cattle_df)}头牛, 系统类型: {system_type}, 在胎天数字段: {pregnancy_field}")
            
            return {
                'success': True,
                'cattle_count': len(cattle_df),
                'system_type': system_type,
                'pregnancy_field': pregnancy_field
            }
            
        except Exception as e:
            logger.error(f"加载牛群基础信息失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_all_indicators(self) -> Dict[str, Any]:
        """
        计算所有指标
        
        Returns:
            包含所有指标计算结果的字典
        """
        try:
            if not self.monthly_data:
                return {
                    'success': False,
                    'error': '没有可用的DHI数据'
                }
            
            months = sorted(self.monthly_data.keys())
            month_count = len(months)
            
            logger.info(f"开始计算隐性乳房炎月度监测指标，共{month_count}个月: {months}")
            
            # 检查月份连续性
            continuity_check = self._check_month_continuity(months)
            
            results = {
                'success': True,
                'months': months,
                'month_count': month_count,
                'continuity_check': continuity_check,
                'scc_threshold': self.scc_threshold,
                'indicators': {}
            }
            
            # 计算各个指标
            for month in months:
                month_results = {}
                
                # 指标1: 当月流行率
                month_results['current_prevalence'] = self._calculate_current_prevalence(month)
                
                # 指标5: 头胎/经产首测流行率
                month_results['first_test_prevalence'] = self._calculate_first_test_prevalence(month)
                
                results['indicators'][month] = month_results
            
            # 计算需要两个月数据的指标
            if month_count >= 2:
                for i in range(1, len(months)):
                    current_month = months[i]
                    previous_month = months[i-1]
                    
                    # 指标2: 新发感染率
                    results['indicators'][current_month]['new_infection_rate'] = self._calculate_new_infection_rate(
                        previous_month, current_month)
                    
                    # 指标3: 慢性感染率
                    results['indicators'][current_month]['chronic_infection_rate'] = self._calculate_chronic_infection_rate(
                        previous_month, current_month)
                    
                    # 指标4: 慢性感染牛占比
                    results['indicators'][current_month]['chronic_infection_proportion'] = self._calculate_chronic_infection_proportion(
                        previous_month, current_month)
            
            # 计算干奶前流行率（只计算最新月份）
            latest_month = months[-1]
            print(f"\n🔍 准备计算干奶前流行率 - 最新月份: {latest_month}")
            print(f"   牛群基础信息状态: {self.cattle_basic_info is not None}")
            print(f"   牛群信息数量: {len(self.cattle_basic_info) if self.cattle_basic_info is not None else 0}")
            
            if self.cattle_basic_info is not None:
                print(f"   ✅ 开始计算干奶前流行率...")
                results['indicators'][latest_month]['pre_dry_prevalence'] = self._calculate_pre_dry_prevalence(latest_month)
            else:
                print(f"   ❌ 跳过干奶前流行率计算：未加载牛群基础信息")
                # 为了调试，我们仍然添加一个空的结果
                results['indicators'][latest_month]['pre_dry_prevalence'] = {
                    'value': None,
                    'formula': '📋 无法计算干奶前流行率 - 未加载牛群基础信息',
                    'diagnosis': '未加载牛群基础信息'
                }
            
            self.results = results
            return results
            
        except Exception as e:
            logger.error(f"计算指标失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_monthly_duplicates(self, month_df: pd.DataFrame) -> pd.DataFrame:
        """处理同月多次测定：取最后一次记录"""
        # 按管理号分组，每组按采样日期排序取最后一条
        result_rows = []
        
        for management_id, group in month_df.groupby('management_id'):
            # 按采样日期排序，取最后一条记录
            sorted_group = group.sort_values('sample_date')
            last_record = sorted_group.iloc[-1]
            result_rows.append(last_record)
        
        return pd.DataFrame(result_rows).reset_index(drop=True)
    
    def _standardize_management_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化管理号：去除前导0"""
        df = df.copy()
        df['management_id_standardized'] = df['management_id'].astype(str).str.lstrip('0')
        return df
    
    def _get_pregnancy_field(self, system_type: str) -> Optional[str]:
        """根据系统类型获取在胎天数字段名"""
        if self.cattle_basic_info is None:
            return None
        
        # 获取实际可用的字段
        available_fields = list(self.cattle_basic_info.columns)
        
        if system_type == 'yiqiniu':
            # 伊起牛系统：数据处理后已标准化为gestation_days，优先查找标准字段
            possible_fields = ['gestation_days', '在胎天数', '怀孕天数', 'pregnancy_days']
        elif system_type == 'huimuyun':
            # 慧牧云系统：优先查找对应字段
            possible_fields = ['gestation_days', 'pregnancy_days', '怀孕天数', '在胎天数']
        else:
            # 其他系统查找所有可能的字段名
            possible_fields = ['gestation_days', 'pregnancy_days', '在胎天数', '怀孕天数']
        
        # 查找匹配的字段
        for field in possible_fields:
            if field in available_fields:
                return field
        
        # 如果没有完全匹配，尝试模糊匹配
        pregnancy_related_fields = [f for f in available_fields if '天数' in f or 'days' in f.lower()]
        gestation_related_fields = [f for f in pregnancy_related_fields if '胎' in f or 'gest' in f.lower() or 'preg' in f.lower()]
        
        if gestation_related_fields:
            return gestation_related_fields[0]
        
        return None
    
    def _check_month_continuity(self, months: List[str]) -> Dict[str, Any]:
        """检查月份连续性"""
        if len(months) <= 1:
            return {'is_continuous': True, 'missing_months': []}
        
        # 转换为日期进行比较
        try:
            month_dates = [pd.Period(month) for month in months]
            missing_months = []
            
            for i in range(len(month_dates) - 1):
                current = month_dates[i]
                next_month = month_dates[i + 1]
                
                # 检查是否连续
                expected_next = current + 1
                if next_month != expected_next:
                    # 找出缺失的月份
                    temp_month = expected_next
                    while temp_month < next_month:
                        missing_months.append(str(temp_month))
                        temp_month += 1
            
            return {
                'is_continuous': len(missing_months) == 0,
                'missing_months': missing_months
            }
        except Exception:
            # 如果日期处理出错，返回简单的结果
            return {'is_continuous': True, 'missing_months': []}
    
    def _calculate_current_prevalence(self, month: str) -> Dict[str, Any]:
        """计算当月流行率"""
        try:
            df = self.monthly_data[month]
            
            # 过滤有效的体细胞数据
            valid_scc = df['somatic_cell_count'].dropna()
            
            if len(valid_scc) == 0:
                return {
                    'value': None,
                    'formula': f'无法计算 - {month}月DHI数据中无有效体细胞数据',
                    'numerator': 0,
                    'denominator': 0
                }
            
            high_scc_count = (valid_scc > self.scc_threshold).sum()
            total_count = len(valid_scc)
            prevalence = (high_scc_count / total_count) * 100
            
            formula = f'体细胞数(万/ml)>{self.scc_threshold}的牛头数({high_scc_count}) ÷ {month}月参测牛头数({total_count}) = {prevalence:.1f}%'
            
            return {
                'value': prevalence,
                'formula': formula,
                'numerator': high_scc_count,
                'denominator': total_count
            }
            
        except Exception as e:
            logger.error(f"计算{month}月当月流行率失败: {e}")
            return {
                'value': None,
                'formula': f'计算错误: {str(e)}',
                'numerator': 0,
                'denominator': 0
            }
    
    def _calculate_first_test_prevalence(self, month: str) -> Dict[str, Any]:
        """计算头胎/经产首测流行率"""
        try:
            df = self.monthly_data[month]
            
            # 筛选DIM 5-35天的牛只
            if 'lactation_days' not in df.columns:
                return {
                    'primiparous': {
                        'value': None,
                        'formula': f'无法计算 - {month}月DHI数据缺少泌乳天数字段',
                        'numerator': 0,
                        'denominator': 0
                    },
                    'multiparous': {
                        'value': None,
                        'formula': f'无法计算 - {month}月DHI数据缺少泌乳天数字段',
                        'numerator': 0,
                        'denominator': 0
                    }
                }
            
            # 筛选泌乳天数5-35天
            dim_filtered = df[(df['lactation_days'] >= 5) & (df['lactation_days'] <= 35)].copy()
            
            if len(dim_filtered) == 0:
                return {
                    'primiparous': {
                        'value': None,
                        'formula': f'无法计算 - {month}月无泌乳天数5-35天的牛只',
                        'numerator': 0,
                        'denominator': 0
                    },
                    'multiparous': {
                        'value': None,
                        'formula': f'无法计算 - {month}月无泌乳天数5-35天的牛只',
                        'numerator': 0,
                        'denominator': 0
                    }
                }
            
            # 头胎牛 (胎次=1)
            primiparous = dim_filtered[dim_filtered['parity'] == 1]
            if len(primiparous) > 0:
                primi_high_scc = (primiparous['somatic_cell_count'] > self.scc_threshold).sum()
                primi_total = len(primiparous)
                primi_prevalence = (primi_high_scc / primi_total) * 100
                primi_formula = f'(胎次=1 且 DIM5-35天 且 SCC>{self.scc_threshold}的牛头数({primi_high_scc})) ÷ (胎次=1 且 DIM5-35天的参测牛头数({primi_total})) = {primi_prevalence:.1f}%'
            else:
                primi_prevalence = None
                primi_formula = f'无法计算 - {month}月无头胎且DIM5-35天的牛只'
                primi_high_scc = 0
                primi_total = 0
            
            # 经产牛 (胎次>1)
            multiparous = dim_filtered[dim_filtered['parity'] > 1]
            if len(multiparous) > 0:
                multi_high_scc = (multiparous['somatic_cell_count'] > self.scc_threshold).sum()
                multi_total = len(multiparous)
                multi_prevalence = (multi_high_scc / multi_total) * 100
                multi_formula = f'(胎次>1 且 DIM5-35天 且 SCC>{self.scc_threshold}的牛头数({multi_high_scc})) ÷ (胎次>1 且 DIM5-35天的参测牛头数({multi_total})) = {multi_prevalence:.1f}%'
            else:
                multi_prevalence = None
                multi_formula = f'无法计算 - {month}月无经产且DIM5-35天的牛只'
                multi_high_scc = 0
                multi_total = 0
            
            return {
                'primiparous': {
                    'value': primi_prevalence,
                    'formula': primi_formula,
                    'numerator': primi_high_scc,
                    'denominator': primi_total
                },
                'multiparous': {
                    'value': multi_prevalence,
                    'formula': multi_formula,
                    'numerator': multi_high_scc,
                    'denominator': multi_total
                }
            }
            
        except Exception as e:
            logger.error(f"计算{month}月首测流行率失败: {e}")
            return {
                'primiparous': {
                    'value': None,
                    'formula': f'计算错误: {str(e)}',
                    'numerator': 0,
                    'denominator': 0
                },
                'multiparous': {
                    'value': None,
                    'formula': f'计算错误: {str(e)}',
                    'numerator': 0,
                    'denominator': 0
                }
            }
    
    def _get_overlapping_cattle(self, month1: str, month2: str) -> Tuple[pd.DataFrame, int, List[str]]:
        """获取两个月重叠的牛只数据"""
        df1 = self.monthly_data[month1]
        df2 = self.monthly_data[month2]
        
        # 获取重叠的管理号
        ids1 = set(df1['management_id_standardized'])
        ids2 = set(df2['management_id_standardized'])
        overlapping_ids = ids1.intersection(ids2)
        
        if len(overlapping_ids) == 0:
            return pd.DataFrame(), 0, []
        
        # 获取重叠牛只的数据
        overlap_df1 = df1[df1['management_id_standardized'].isin(overlapping_ids)].copy()
        overlap_df2 = df2[df2['management_id_standardized'].isin(overlapping_ids)].copy()
        
        # 合并数据
        merged_df = overlap_df1.merge(
            overlap_df2, 
            on='management_id_standardized', 
            suffixes=('_prev', '_curr')
        )
        
        return merged_df, len(overlapping_ids), list(overlapping_ids)
    
    def _calculate_new_infection_rate(self, prev_month: str, curr_month: str) -> Dict[str, Any]:
        """计算新发感染率"""
        try:
            merged_df, overlap_count, _ = self._get_overlapping_cattle(prev_month, curr_month)
            
            if overlap_count == 0:
                return {
                    'value': None,
                    'formula': f'无法计算 - {prev_month}月与{curr_month}月无重叠牛只',
                    'numerator': 0,
                    'denominator': 0,
                    'overlap_count': 0,
                    'warning': None
                }
            
            # 筛选条件：上月SCC≤阈值的牛只
            prev_low_scc = merged_df['somatic_cell_count_prev'] <= self.scc_threshold
            eligible_cattle = merged_df[prev_low_scc]
            
            if len(eligible_cattle) == 0:
                return {
                    'value': None,
                    'formula': f'无法计算 - {prev_month}月所有重叠牛只SCC均>{self.scc_threshold}万/ml',
                    'numerator': 0,
                    'denominator': 0,
                    'overlap_count': overlap_count,
                    'warning': None
                }
            
            # 计算新发感染：当月SCC>阈值 且 上月SCC≤阈值
            new_infections = (eligible_cattle['somatic_cell_count_curr'] > self.scc_threshold).sum()
            total_eligible = len(eligible_cattle)
            
            if total_eligible > 0:
                new_infection_rate = (new_infections / total_eligible) * 100
            else:
                new_infection_rate = 0
            
            formula = f'({curr_month}月SCC>{self.scc_threshold} 且 {prev_month}月SCC≤{self.scc_threshold}的牛头数({new_infections})) ÷ ({prev_month}月SCC≤{self.scc_threshold}的牛头数({total_eligible})) = {new_infection_rate:.1f}%'
            
            # 检查重叠牛只数量是否太少
            warning = None
            if overlap_count < 20:
                warning = f'重叠牛只数量较少({overlap_count}头)，统计结果可能不具代表性'
            
            return {
                'value': new_infection_rate,
                'formula': formula,
                'numerator': new_infections,
                'denominator': total_eligible,
                'overlap_count': overlap_count,
                'warning': warning
            }
            
        except Exception as e:
            logger.error(f"计算{prev_month}到{curr_month}新发感染率失败: {e}")
            return {
                'value': None,
                'formula': f'计算错误: {str(e)}',
                'numerator': 0,
                'denominator': 0,
                'overlap_count': 0,
                'warning': None
            }
    
    def _calculate_chronic_infection_rate(self, prev_month: str, curr_month: str) -> Dict[str, Any]:
        """计算慢性感染率"""
        try:
            merged_df, overlap_count, _ = self._get_overlapping_cattle(prev_month, curr_month)
            
            if overlap_count == 0:
                return {
                    'value': None,
                    'formula': f'无法计算 - {prev_month}月与{curr_month}月无重叠牛只',
                    'numerator': 0,
                    'denominator': 0,
                    'overlap_count': 0,
                    'warning': None
                }
            
            # 筛选条件：上月SCC>阈值的牛只
            prev_high_scc = merged_df['somatic_cell_count_prev'] > self.scc_threshold
            eligible_cattle = merged_df[prev_high_scc]
            
            if len(eligible_cattle) == 0:
                return {
                    'value': None,
                    'formula': f'无法计算 - {prev_month}月无SCC>{self.scc_threshold}万/ml的重叠牛只',
                    'numerator': 0,
                    'denominator': 0,
                    'overlap_count': overlap_count,
                    'warning': None
                }
            
            # 计算慢性感染：当月SCC>阈值 且 上月SCC>阈值
            chronic_infections = (eligible_cattle['somatic_cell_count_curr'] > self.scc_threshold).sum()
            total_eligible = len(eligible_cattle)
            
            chronic_infection_rate = (chronic_infections / total_eligible) * 100
            
            formula = f'({curr_month}月SCC>{self.scc_threshold} 且 {prev_month}月SCC>{self.scc_threshold}的牛头数({chronic_infections})) ÷ ({prev_month}月SCC>{self.scc_threshold}的牛头数({total_eligible})) = {chronic_infection_rate:.1f}%'
            
            # 检查重叠牛只数量是否太少
            warning = None
            if overlap_count < 20:
                warning = f'重叠牛只数量较少({overlap_count}头)，统计结果可能不具代表性'
            
            return {
                'value': chronic_infection_rate,
                'formula': formula,
                'numerator': chronic_infections,
                'denominator': total_eligible,
                'overlap_count': overlap_count,
                'warning': warning
            }
            
        except Exception as e:
            logger.error(f"计算{prev_month}到{curr_month}慢性感染率失败: {e}")
            return {
                'value': None,
                'formula': f'计算错误: {str(e)}',
                'numerator': 0,
                'denominator': 0,
                'overlap_count': 0,
                'warning': None
            }
    
    def _calculate_chronic_infection_proportion(self, prev_month: str, curr_month: str) -> Dict[str, Any]:
        """计算慢性感染牛占比"""
        try:
            merged_df, overlap_count, _ = self._get_overlapping_cattle(prev_month, curr_month)
            
            if overlap_count == 0:
                return {
                    'value': None,
                    'formula': f'无法计算 - {prev_month}月与{curr_month}月无重叠牛只',
                    'numerator': 0,
                    'denominator': 0,
                    'overlap_count': 0,
                    'warning': None
                }
            
            # 计算慢性感染牛：当月SCC>阈值 且 上月SCC>阈值
            chronic_condition = (
                (merged_df['somatic_cell_count_curr'] > self.scc_threshold) &
                (merged_df['somatic_cell_count_prev'] > self.scc_threshold)
            )
            chronic_count = chronic_condition.sum()
            
            # 分母是当月全部有效DHI参测牛头数。
            # 两个月的重叠牛只仅用于识别分子中的慢性感染牛，不能用于缩小分母。
            current_df = self.monthly_data[curr_month]
            total_current = current_df['somatic_cell_count'].notna().sum()

            if total_current == 0:
                return {
                    'value': None,
                    'formula': f'无法计算 - {curr_month}月DHI数据中无有效体细胞数据',
                    'numerator': chronic_count,
                    'denominator': 0,
                    'overlap_count': overlap_count,
                    'warning': None
                }
            
            chronic_proportion = (chronic_count / total_current) * 100
            
            formula = f'({curr_month}月SCC>{self.scc_threshold} 且 {prev_month}月SCC>{self.scc_threshold}的牛头数({chronic_count})) ÷ ({curr_month}月参测牛头数({total_current})) = {chronic_proportion:.1f}%'
            
            # 检查重叠牛只数量是否太少
            warning = None
            if overlap_count < 20:
                warning = f'重叠牛只数量较少({overlap_count}头)，统计结果可能不具代表性'
            
            return {
                'value': chronic_proportion,
                'formula': formula,
                'numerator': chronic_count,
                'denominator': total_current,
                'overlap_count': overlap_count,
                'warning': warning
            }
            
        except Exception as e:
            logger.error(f"计算{prev_month}到{curr_month}慢性感染牛占比失败: {e}")
            return {
                'value': None,
                'formula': f'计算错误: {str(e)}',
                'numerator': 0,
                'denominator': 0,
                'overlap_count': 0,
                'warning': None
            }
    
    def _calculate_pre_dry_prevalence(self, month: str) -> Dict[str, Any]:
        """计算干奶前流行率"""
        try:
            debug_msg = f"\n🔍 开始计算干奶前流行率 - 月份: {month}"
            debug_msg += f"\n体细胞阈值: {self.scc_threshold}万/ml"
            print(debug_msg)
            
            # 写入调试文件（跨平台兼容）
            try:
                import os
                import tempfile
                debug_file = os.path.join(tempfile.gettempdir(), 'predry_debug.log')
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write(debug_msg + '\n')
            except Exception:
                # 如果无法写入调试文件，忽略错误继续执行
                pass
            
            # 检查基础数据
            if self.cattle_basic_info is None:
                print("❌ 检查失败: 未上传牛群基础信息")
                return {
                    'value': None,
                    'formula': '📋 无法计算干奶前流行率 - 未上传牛群基础信息<br/>💡 解决方案：请在"慢性乳房炎筛查"功能中上传包含在胎天数信息的牛群基础信息文件',
                    'numerator': 0,
                    'denominator': 0,
                    'matched_count': 0,
                    'total_dhi_count': 0,
                    'diagnosis': '缺少牛群基础信息'
                }
            
            # Windows环境调试：输出更多系统信息
            try:
                import platform
                import sys
                print(f"🔍 系统环境调试:")
                print(f"   操作系统: {platform.system()} {platform.release()}")
                print(f"   Python版本: {sys.version}")
                print(f"   是否打包环境: {getattr(sys, 'frozen', False)}")
                print(f"   执行路径: {sys.executable}")
            except Exception as debug_e:
                print(f"   系统信息获取失败: {debug_e}")
            
            print(f"✅ 牛群基础信息已加载: {len(self.cattle_basic_info)}头牛")
            
            # 获取在胎天数字段 - 增强调试
            available_fields = list(self.cattle_basic_info.columns)
            pregnancy_field = self._get_pregnancy_field(self.cattle_system_type or 'other')
            
            print(f"🔍 详细字段调试:")
            print(f"   系统类型: {self.cattle_system_type}")
            print(f"   牛群信息总字段数: {len(available_fields)}")
            print(f"   所有字段: {available_fields}")
            print(f"   包含'天数'的字段: {[f for f in available_fields if '天数' in f]}")
            print(f"   包含'days'的字段: {[f for f in available_fields if 'days' in f.lower()]}")
            print(f"   获取到的在胎天数字段: {pregnancy_field}")
            
            # 检查数据类型和数据样本
            if pregnancy_field and pregnancy_field in self.cattle_basic_info.columns:
                preg_data = self.cattle_basic_info[pregnancy_field]
                print(f"   在胎天数字段数据类型: {preg_data.dtype}")
                print(f"   在胎天数非空值数量: {preg_data.count()}")
                print(f"   在胎天数样本值: {preg_data.dropna().head().tolist()}")
            else:
                print(f"   ❌ 在胎天数字段不存在或为空")
            
            if not pregnancy_field or pregnancy_field not in self.cattle_basic_info.columns:
                pregnancy_related = [f for f in available_fields if '天数' in f or 'days' in f.lower()]
                field_info = f"可用字段：{pregnancy_related}" if pregnancy_related else "未找到相关字段"
                print(f"❌ 在胎天数字段检查失败: {field_info}")
                
                return {
                    'value': None,
                    'formula': f'📋 无法计算干奶前流行率 - 牛群基础信息缺少在胎天数字段<br/>🔍 当前系统类型：{self.cattle_system_type}<br/>📊 需要字段：在胎天数/怀孕天数<br/>📋 {field_info}',
                    'numerator': 0,
                    'denominator': 0,
                    'matched_count': 0,
                    'total_dhi_count': 0,
                    'diagnosis': '缺少在胎天数字段'
                }
            
            print(f"✅ 在胎天数字段验证通过: {pregnancy_field}")
            
            # 获取当月DHI数据
            dhi_df = self.monthly_data[month]
            print(f"\n📊 DHI数据信息:")
            print(f"   当月({month})DHI数据: {len(dhi_df)}头牛")
            if len(dhi_df) > 0:
                print(f"   管理号示例: {dhi_df['management_id'].head().tolist()}")
                print(f"   体细胞数示例: {dhi_df['somatic_cell_count'].head().tolist()}")
            
            # 匹配管理号与耳号
            print(f"\n🔗 开始匹配管理号与耳号...")
            matched_data = self._match_management_id_with_ear_tag(dhi_df)
            match_rate = (len(matched_data) / len(dhi_df)) * 100 if len(dhi_df) > 0 else 0
            print(f"   匹配结果: {len(matched_data)}头 / {len(dhi_df)}头 = {match_rate:.1f}%")
            
            # 详细的匹配诊断
            if len(matched_data) == 0:
                print(f"❌ 匹配失败: 无法匹配任何牛只")
                print(f"   DHI管理号标准化示例: {dhi_df['management_id_standardized'].head().tolist()}")
                if hasattr(self.cattle_basic_info, 'ear_tag_standardized'):
                    print(f"   牛群耳号标准化示例: {self.cattle_basic_info['ear_tag_standardized'].head().tolist()}")
                return {
                    'value': None,
                    'formula': f'📋 无法计算干奶前流行率 - DHI数据与牛群基础信息无法匹配<br/>📊 DHI数据：{len(dhi_df)}头牛<br/>🐄 牛群基础信息：{len(self.cattle_basic_info)}头牛<br/>🔗 匹配成功：0头 (0.0%)<br/>💡 可能原因：<br/>　• DHI数据与牛群信息来自不同时间点<br/>　• 管理号与耳号编码方式不同<br/>　• 数据来源不是同一个牧场',
                    'numerator': 0,
                    'denominator': 0,
                    'matched_count': 0,
                    'total_dhi_count': len(dhi_df),
                    'diagnosis': '数据无法匹配'
                }
            
            print(f"✅ 匹配成功: {len(matched_data)}头牛")
            
            # 低匹配率警告
            low_match_warning = ""
            if match_rate < 50:
                low_match_warning = f"<br/>⚠️ 注意：数据匹配率较低 ({match_rate:.1f}%)，结果可能不完整"
            
            # 检查匹配数据中的在胎天数
            print(f"\n🤰 检查在胎天数数据...")
            pregnancy_data_count = matched_data[pregnancy_field].count()
            pregnancy_valid_data = matched_data[pregnancy_field].dropna()
            print(f"   匹配牛只中有在胎天数数据的: {pregnancy_data_count}头")
            
            if pregnancy_data_count == 0:
                print(f"❌ 在胎天数检查失败: 匹配成功的牛只中无在胎天数数据")
                print(f"   匹配数据列名: {list(matched_data.columns)}")
                return {
                    'value': None,
                    'formula': f'📋 无法计算干奶前流行率 - 匹配成功的牛只中无在胎天数数据<br/>📊 DHI数据：{len(dhi_df)}头牛<br/>🔗 匹配成功：{len(matched_data)}头 ({match_rate:.1f}%)<br/>📉 有在胎天数数据：0头<br/>💡 可能原因：<br/>　• 牛群基础信息导出时间与DHI测试时间不同步<br/>　• 匹配成功的牛只当时处于空怀状态{low_match_warning}',
                    'numerator': 0,
                    'denominator': 0,
                    'matched_count': len(matched_data),
                    'total_dhi_count': len(dhi_df),
                    'diagnosis': '匹配牛只无在胎天数数据'
                }
            
            print(f"✅ 在胎天数数据检查通过: {pregnancy_data_count}头牛有数据")
            
            # 筛选在胎天数>180天的牛只
            print(f"\n🎯 筛选干奶前牛只(在胎天数>180天)...")
            print(f"   在胎天数有效数据范围: {pregnancy_valid_data.min():.0f}-{pregnancy_valid_data.max():.0f}天")
            print(f"   平均在胎天数: {pregnancy_valid_data.mean():.1f}天")
            
            pregnancy_condition = matched_data[pregnancy_field] > 180
            pre_dry_cattle = matched_data[pregnancy_condition]
            over_180_count = (pregnancy_valid_data > 180).sum()
            print(f"   在胎天数>180天的牛只: {over_180_count}头")
            print(f"   筛选出的干奶前牛只: {len(pre_dry_cattle)}头")
            
            # 提供在胎天数的统计信息
            if len(pregnancy_valid_data) > 0:
                preg_stats = f"在胎天数范围：{pregnancy_valid_data.min():.0f}-{pregnancy_valid_data.max():.0f}天，平均{pregnancy_valid_data.mean():.0f}天"
                preg_stats += f"，>180天：{over_180_count}头"
            else:
                preg_stats = "无有效在胎天数数据"
            
            if len(pre_dry_cattle) == 0:
                print(f"❌ 干奶前牛只筛选失败: 无在胎天数>180天的牛只")
                print(f"   统计信息: {preg_stats}")
                return {
                    'value': None,
                    'formula': f'📋 无法计算干奶前流行率 - 无在胎天数>180天的牛只<br/>📊 DHI数据：{len(dhi_df)}头牛<br/>🔗 匹配成功：{len(matched_data)}头 ({match_rate:.1f}%)<br/>📊 有在胎天数数据：{pregnancy_data_count}头<br/>📈 {preg_stats}<br/>🎯 符合干奶前条件（>180天）：0头{low_match_warning}',
                    'numerator': 0,
                    'denominator': 0,
                    'matched_count': len(matched_data),
                    'total_dhi_count': len(dhi_df),
                    'pregnancy_stats': preg_stats,
                    'diagnosis': '无符合干奶前条件的牛只'
                }
            
            print(f"✅ 干奶前牛只筛选成功: {len(pre_dry_cattle)}头")
            
            # 成功计算干奶前流行率
            print(f"\n📈 计算干奶前流行率...")
            high_scc_count = (pre_dry_cattle['somatic_cell_count'] > self.scc_threshold).sum()
            total_pre_dry = len(pre_dry_cattle)
            
            print(f"   干奶前牛只总数: {total_pre_dry}头")
            print(f"   体细胞>{self.scc_threshold}万/ml的牛只: {high_scc_count}头")
            print(f"   干奶前牛只体细胞数详情: {pre_dry_cattle['somatic_cell_count'].tolist()}")
            
            pre_dry_prevalence = (high_scc_count / total_pre_dry) * 100
            print(f"   计算公式: ({high_scc_count} ÷ {total_pre_dry}) × 100% = {pre_dry_prevalence:.1f}%")
            print(f"✅ 干奶前流行率计算成功: {pre_dry_prevalence:.1f}%")
            
            formula = f'🎯 干奶前流行率计算成功<br/>📊 DHI数据：{len(dhi_df)}头牛<br/>🔗 匹配成功：{len(matched_data)}头 ({match_rate:.1f}%)<br/>📊 有在胎天数数据：{pregnancy_data_count}头<br/>🐄 干奶前牛只（>180天）：{total_pre_dry}头<br/>🔬 体细胞>{self.scc_threshold}万/ml：{high_scc_count}头<br/>📈 干奶前流行率：{pre_dry_prevalence:.1f}%{low_match_warning}'
            
            # 添加详细计算过程
            formula += f'<br/><br/>💡 计算公式：({high_scc_count} ÷ {total_pre_dry}) × 100% = {pre_dry_prevalence:.1f}%'
            
            return {
                'value': pre_dry_prevalence,
                'formula': formula,
                'numerator': high_scc_count,
                'denominator': total_pre_dry,
                'matched_count': len(matched_data),
                'total_dhi_count': len(dhi_df),
                'pregnancy_stats': preg_stats,
                'match_rate': match_rate,
                'latest_month': month,
                'pregnancy_field': pregnancy_field,
                'diagnosis': '计算成功'
            }
            
        except Exception as e:
            logger.error(f"计算{month}月干奶前流行率失败: {e}")
            return {
                'value': None,
                'formula': f'📋 计算错误：{str(e)}<br/>💡 请检查数据格式和完整性',
                'numerator': 0,
                'denominator': 0,
                'matched_count': 0,
                'total_dhi_count': 0,
                'diagnosis': '计算异常'
            }
    
    def _match_management_id_with_ear_tag(self, dhi_df: pd.DataFrame) -> pd.DataFrame:
        """匹配DHI报告的管理号与牛群基础信息的耳号"""
        try:
            # 将牛群基础信息的耳号标准化
            if self.cattle_basic_info is None:
                print("   ❌ 牛群基础信息为空")
                return pd.DataFrame()
            
            cattle_info = self.cattle_basic_info.copy()
            print(f"   🔍 开始匹配: DHI数据{len(dhi_df)}头，牛群信息{len(cattle_info)}头")
            
            # 检查标准化字段是否存在
            if 'ear_tag_standardized' not in cattle_info.columns:
                print("   ❌ 牛群信息缺少ear_tag_standardized字段")
                return pd.DataFrame()
                
            if 'management_id_standardized' not in dhi_df.columns:
                print("   ❌ DHI数据缺少management_id_standardized字段")
                return pd.DataFrame()
            
            print(f"   📋 DHI管理号标准化示例: {dhi_df['management_id_standardized'].head().tolist()}")
            print(f"   📋 牛群耳号标准化示例: {cattle_info['ear_tag_standardized'].head().tolist()}")
            
            # 基于标准化后的ID进行匹配
            matched_data = dhi_df.merge(
                cattle_info,
                left_on='management_id_standardized',
                right_on='ear_tag_standardized',
                how='inner'
            )
            
            print(f"   🔗 匹配结果: {len(matched_data)}头牛匹配成功")
            if len(matched_data) > 0:
                print(f"   📋 匹配成功的ID示例: {matched_data['management_id_standardized'].head().tolist()}")
            
            logger.info(f"管理号匹配结果: DHI数据{len(dhi_df)}头，成功匹配{len(matched_data)}头")
            
            return matched_data
            
        except Exception as e:
            print(f"   ❌ 匹配过程异常: {e}")
            logger.error(f"管理号与耳号匹配失败: {e}")
            return pd.DataFrame()
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """获取汇总统计信息"""
        if not self.results:
            return {}
        
        try:
            months = self.results['months']
            indicators = self.results['indicators']
            
            summary = {
                'total_months': len(months),
                'date_range': {
                    'start': months[0] if months else None,
                    'end': months[-1] if months else None
                },
                'scc_threshold': self.scc_threshold,
                'latest_indicators': {}
            }
            
            # 获取最新月份的指标
            if months:
                latest_month = months[-1]
                latest_data = indicators.get(latest_month, {})
                
                for indicator_name, indicator_data in latest_data.items():
                    if isinstance(indicator_data, dict) and 'value' in indicator_data:
                        summary['latest_indicators'][indicator_name] = {
                            'value': indicator_data['value'],
                            'month': latest_month
                        }
            
            return summary
            
        except Exception as e:
            logger.error(f"生成汇总统计失败: {e}")
            return {}
