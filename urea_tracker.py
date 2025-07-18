"""
尿素氮追踪分析模块
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class UreaTracker:
    """尿素氮追踪分析器"""
    
    def __init__(self):
        """初始化"""
        self.dhi_data_dict = {}  # 存储所有DHI数据 {date: DataFrame}
        self.latest_date = None  # 最新数据日期
        self.group_definitions = {
            "1-30天": (1, 30),
            "31-60天": (31, 60),
            "61-90天": (61, 90),
            "91-120天": (91, 120),
            "121-150天": (121, 150),
            "151-180天": (151, 180),
            "181-210天": (181, 210),
            "211-240天": (211, 240),
            "241-270天": (241, 270),
            "271-300天": (271, 300),
            "301-330天": (301, 330),
            "331天以上": (331, 9999)
        }
    
    def add_dhi_data(self, df: pd.DataFrame, date_str: str):
        """
        添加DHI数据
        
        Args:
            df: DHI数据DataFrame
            date_str: 日期字符串 (YYYY-MM)
        """
        try:
            # 确保必要的列存在
            required_cols = ['management_id', 'lactation_days', 'urea_nitrogen', 'milk_yield']
            
            # 列名映射（处理可能的列名差异）
            column_mapping = {
                '管理号': 'management_id',
                '泌乳天数': 'lactation_days',
                '尿素氮(mg/dl)': 'urea_nitrogen',
                '产奶量': 'milk_yield',
                '日产奶量': 'milk_yield'
            }
            
            # 重命名列
            df_copy = df.copy()
            for old_name, new_name in column_mapping.items():
                if old_name in df_copy.columns:
                    df_copy.rename(columns={old_name: new_name}, inplace=True)
            
            # 检查必要列
            missing_cols = [col for col in required_cols if col not in df_copy.columns]
            if missing_cols:
                logger.warning(f"DHI数据缺少必要列: {missing_cols}")
                return False
            
            # 转换数据类型
            df_copy['management_id'] = df_copy['management_id'].astype(str)
            df_copy['lactation_days'] = pd.to_numeric(df_copy['lactation_days'], errors='coerce')
            df_copy['urea_nitrogen'] = pd.to_numeric(df_copy['urea_nitrogen'], errors='coerce')
            df_copy['milk_yield'] = pd.to_numeric(df_copy['milk_yield'], errors='coerce')
            
            # 存储数据
            self.dhi_data_dict[date_str] = df_copy
            
            # 更新最新日期
            if not self.latest_date or date_str > self.latest_date:
                self.latest_date = date_str
            
            logger.info(f"成功添加 {date_str} 的DHI数据，共 {len(df_copy)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"添加DHI数据失败: {e}")
            return False
    
    def analyze(self, selected_groups: List[str], 
                filter_outliers: bool = False,
                min_value: float = 5.0,
                max_value: float = 30.0,
                min_sample_size: int = 5) -> Dict:
        """
        执行尿素氮追踪分析
        
        Args:
            selected_groups: 选中的泌乳天数组列表
            filter_outliers: 是否筛选异常值
            min_value: 尿素氮最小值
            max_value: 尿素氮最大值
            min_sample_size: 最小样本数
            
        Returns:
            分析结果字典
        """
        if not self.latest_date or self.latest_date not in self.dhi_data_dict:
            return {"error": "没有可用的DHI数据"}
        
        results = {}
        latest_df = self.dhi_data_dict[self.latest_date]
        
        # 基于最新数据进行分组
        for group_name in selected_groups:
            if group_name not in self.group_definitions:
                continue
            
            min_days, max_days = self.group_definitions[group_name]
            
            # 获取该组的牛只
            group_mask = (latest_df['lactation_days'] >= min_days) & \
                        (latest_df['lactation_days'] <= max_days)
            group_cows = latest_df[group_mask]['management_id'].unique()
            
            if len(group_cows) < min_sample_size:
                continue
            
            # 创建组名（包含月份）
            full_group_name = f"{self.latest_date} {group_name}"
            
            # 追踪历史数据
            history = []
            for date_str in sorted(self.dhi_data_dict.keys()):
                df = self.dhi_data_dict[date_str]
                
                # 找到这些牛在该月的数据
                cow_data = df[df['management_id'].isin(group_cows)].copy()
                
                if len(cow_data) == 0:
                    continue
                
                # 筛选异常值
                if filter_outliers:
                    cow_data = cow_data[
                        (cow_data['urea_nitrogen'] >= min_value) & 
                        (cow_data['urea_nitrogen'] <= max_value)
                    ]
                
                if len(cow_data) < min_sample_size:
                    continue
                
                # 计算统计值
                arithmetic_mean = cow_data['urea_nitrogen'].mean()
                
                # 计算加权平均
                total_milk = cow_data['milk_yield'].sum()
                if total_milk > 0:
                    weighted_mean = (cow_data['urea_nitrogen'] * cow_data['milk_yield']).sum() / total_milk
                else:
                    weighted_mean = arithmetic_mean
                
                # 计算该组在这个月的平均泌乳天数
                avg_lactation_days = cow_data['lactation_days'].mean()
                
                history.append({
                    'date': date_str,
                    'cow_count': len(cow_data),
                    'avg_lactation_days': round(avg_lactation_days, 1),
                    'arithmetic_mean': round(arithmetic_mean, 2),
                    'weighted_mean': round(weighted_mean, 2),
                    'cow_ids': cow_data['management_id'].tolist(),
                    'detail_data': cow_data[['management_id', 'lactation_days', 
                                            'milk_yield', 'urea_nitrogen']].to_dict('records')
                })
            
            if history:
                results[full_group_name] = {
                    'current_cows': group_cows.tolist(),
                    'current_count': len(group_cows),
                    'history': history
                }
        
        return results
    
    def get_summary_dataframe(self, results: Dict) -> pd.DataFrame:
        """
        将分析结果转换为汇总DataFrame
        
        Args:
            results: 分析结果字典
            
        Returns:
            汇总数据DataFrame
        """
        rows = []
        
        for group_name, group_data in results.items():
            for record in group_data['history']:
                rows.append({
                    '泌乳天数组': group_name,
                    '采样月份': record['date'],
                    '头数': record['cow_count'],
                    '平均泌乳天数': record['avg_lactation_days'],
                    '算术平均尿素氮': record['arithmetic_mean'],
                    '加权平均尿素氮': record['weighted_mean']
                })
        
        if rows:
            df = pd.DataFrame(rows)
            # 按组名和日期排序
            df.sort_values(['泌乳天数组', '采样月份'], ascending=[True, False], inplace=True)
            return df
        else:
            return pd.DataFrame()
    
    def get_detail_dataframe(self, results: Dict) -> pd.DataFrame:
        """
        获取详细牛只清单DataFrame
        
        Args:
            results: 分析结果字典
            
        Returns:
            详细数据DataFrame
        """
        rows = []
        
        for group_name, group_data in results.items():
            for record in group_data['history']:
                for cow in record['detail_data']:
                    rows.append({
                        '泌乳天数组': group_name,
                        '采样月份': record['date'],
                        '管理号': cow['management_id'],
                        '泌乳天数': cow['lactation_days'],
                        '产奶量(kg)': cow['milk_yield'],
                        '尿素氮(mg/dl)': cow['urea_nitrogen'],
                        '备注': ''
                    })
        
        if rows:
            df = pd.DataFrame(rows)
            # 按组名、日期和管理号排序
            df.sort_values(['泌乳天数组', '采样月份', '管理号'], inplace=True)
            return df
        else:
            return pd.DataFrame()
    
    def get_chart_data(self, results: Dict, value_type: str = 'both') -> Dict:
        """
        获取图表数据
        
        Args:
            results: 分析结果字典
            value_type: 'arithmetic', 'weighted', 或 'both'
            
        Returns:
            图表数据字典
        """
        chart_data = {
            'dates': [],
            'series': []
        }
        
        # 收集所有日期
        all_dates = set()
        for group_data in results.values():
            for record in group_data['history']:
                all_dates.add(record['date'])
        
        chart_data['dates'] = sorted(all_dates)
        
        # 为每个组创建数据系列
        for group_name, group_data in results.items():
            if value_type in ['arithmetic', 'both']:
                series_arithmetic = {
                    'name': f"{group_name} (算术平均)",
                    'type': 'arithmetic',
                    'data': []
                }
                
                # 创建日期到值的映射
                date_value_map = {
                    record['date']: record['arithmetic_mean']
                    for record in group_data['history']
                }
                
                # 填充数据
                for date in chart_data['dates']:
                    series_arithmetic['data'].append(date_value_map.get(date, None))
                
                chart_data['series'].append(series_arithmetic)
            
            if value_type in ['weighted', 'both']:
                series_weighted = {
                    'name': f"{group_name} (加权平均)",
                    'type': 'weighted',
                    'data': []
                }
                
                # 创建日期到值的映射
                date_value_map = {
                    record['date']: record['weighted_mean']
                    for record in group_data['history']
                }
                
                # 填充数据
                for date in chart_data['dates']:
                    series_weighted['data'].append(date_value_map.get(date, None))
                
                chart_data['series'].append(series_weighted)
        
        return chart_data