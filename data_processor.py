import pandas as pd
import zipfile
import os
import re
import yaml
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

from models import FilterConfig

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理核心类"""
    
    def __init__(self, rules_file: str = "rules.yaml", config_file: str = "config.yaml", temp_dir: Optional[str] = None):
        # 确保始终从项目根目录加载配置文件
        base_dir = os.path.dirname(os.path.abspath(__file__))
        rules_path = rules_file if os.path.isabs(rules_file) else os.path.join(base_dir, rules_file)
        config_path = config_file if os.path.isabs(config_file) else os.path.join(base_dir, config_file)

        self.rules = self._load_yaml(rules_path)
        self.config = self._load_yaml(config_path)
        
        # 优先使用传入的temp_dir，否则使用配置文件，最后使用默认值
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            self.temp_dir = str(self.config.get("upload", {}).get("temp_dir", "./temp"))
        
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 在群牛数据存储
        self.active_cattle_list = None
        self.active_cattle_enabled = False
    
    def _load_yaml(self, file_path: str) -> Dict:
        """加载YAML配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
    
    def process_active_cattle_file(self, file_path: str, filename: str) -> Tuple[bool, str, Optional[List[str]]]:
        """处理在群牛文件
        
        Returns:
            (success, message, cattle_list)
        """
        try:
            # 获取在群牛配置
            active_cattle_config = self.rules.get("active_cattle", {})
            ear_tag_columns = active_cattle_config.get("ear_tag_columns", ["耳号", "牛号", "管理号", "奶牛号", "牛编号"])
            normalize_id = active_cattle_config.get("normalize_management_id", True)
            
            logger.info(f"开始处理在群牛文件: {filename}")
            logger.info(f"支持的耳号列名: {ear_tag_columns}")
            
            # 读取Excel文件
            if filename.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif filename.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                return False, f"不支持的在群牛文件格式: {filename}", None
            
            logger.info(f"在群牛文件列名: {list(df.columns)}")
            
            # 查找耳号列
            ear_tag_column = None
            for col_name in ear_tag_columns:
                if col_name in df.columns:
                    ear_tag_column = col_name
                    logger.info(f"找到耳号列: {col_name}")
                    break
            
            if not ear_tag_column:
                available_columns = list(df.columns)
                error_msg = f"在群牛文件中未找到耳号列，支持的列名: {ear_tag_columns}，实际列名: {available_columns}"
                logger.error(error_msg)
                return False, error_msg, None
            
            # 提取耳号数据
            ear_tags = df[ear_tag_column].dropna()
            if len(ear_tags) == 0:
                return False, f"在群牛文件的{ear_tag_column}列为空", None
            
            # 标准化管理号（去除前导零）
            cattle_list = []
            for ear_tag in ear_tags:
                ear_tag_str = str(ear_tag).strip()
                if ear_tag_str and ear_tag_str != 'nan':
                    if normalize_id:
                        # 去除前导零，但保留单个"0"
                        normalized_id = ear_tag_str.lstrip('0') or '0'
                        cattle_list.append(normalized_id)
                    else:
                        cattle_list.append(ear_tag_str)
            
            # 去重并排序
            cattle_list = sorted(list(set(cattle_list)))
            
            logger.info(f"成功提取在群牛数据: {len(cattle_list)}头牛")
            logger.info(f"在群牛号示例: {cattle_list[:10] if len(cattle_list) >= 10 else cattle_list}")
            
            # 存储在群牛数据
            self.active_cattle_list = cattle_list
            self.active_cattle_enabled = True
            
            success_msg = f"成功加载在群牛文件，共{len(cattle_list)}头牛"
            return True, success_msg, cattle_list
            
        except Exception as e:
            error_msg = f"处理在群牛文件失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def apply_active_cattle_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用在群牛筛选
        
        Args:
            df: 待筛选的DataFrame
            
        Returns:
            筛选后的DataFrame
        """
        if not self.active_cattle_enabled or not self.active_cattle_list:
            logger.info("在群牛筛选未启用或无数据，跳过筛选")
            return df
        
        if df.empty or 'management_id' not in df.columns:
            logger.warning("DataFrame为空或缺少management_id列")
            return df
        
        original_count = len(df)
        
        # 标准化management_id用于比较
        df_copy = df.copy()
        
        # 确保management_id为字符串并去除前导零
        df_copy['management_id'] = df_copy['management_id'].astype(str)
        df_copy['normalized_mgmt_id'] = df_copy['management_id'].apply(
            lambda x: x.lstrip('0') or '0' if x and x != 'nan' else x
        )
        
        # 筛选在群牛
        in_active_condition = df_copy['normalized_mgmt_id'].isin(self.active_cattle_list)
        filtered_df = df[in_active_condition].copy()
        
        filtered_count = len(filtered_df)
        
        logger.info(f"在群牛筛选: 原始{original_count}头牛 -> 筛选后{filtered_count}头牛")
        logger.info(f"在群牛列表包含{len(self.active_cattle_list)}头牛")
        
        return filtered_df
    
    def clear_active_cattle_data(self):
        """清除在群牛数据"""
        self.active_cattle_list = None
        self.active_cattle_enabled = False
        logger.info("已清除在群牛数据")
    
    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """从文件名提取年月信息（保留用于兼容性）"""
        pattern = self.rules.get("file_ingest", {}).get("name_regex", r"^\\d+\\((\\d{4}-\\d{2})\\).+\\.zip$")
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
        return None
    
    def extract_date_range_from_data(self, df: pd.DataFrame) -> Optional[Dict[str, str]]:
        """从数据中提取日期范围"""
        if df is None or 'sample_date' not in df.columns:
            logger.warning("DataFrame为空或不包含sample_date列")
            return None
        
        try:
            # 创建副本以避免修改原始数据
            temp_df = df.copy()
            
            # 确保日期列是datetime类型
            temp_df['sample_date'] = pd.to_datetime(temp_df['sample_date'], errors='coerce')
            
            # 过滤掉无效日期
            valid_dates = temp_df['sample_date'].dropna()
            logger.info(f"有效日期数量: {len(valid_dates)}")
            
            if len(valid_dates) == 0:
                logger.warning("没有找到有效的采样日期")
                return None
            
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            
            logger.info(f"日期范围: {min_date} - {max_date}")
            
            date_range = {
                'start_date': min_date.strftime('%Y-%m-%d'),
                'end_date': max_date.strftime('%Y-%m-%d'),
                'year_month_range': f"{min_date.strftime('%Y年%m月')} - {max_date.strftime('%Y年%m月')}"
            }
            
            logger.info(f"提取的日期范围: {date_range}")
            return date_range
            
        except Exception as e:
            logger.error(f"Error extracting date range: {e}")
            return None
    
    def process_uploaded_file(self, file_path: str, filename: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理上传的文件"""
        try:
            detected_date = self.extract_date_from_filename(filename)
            
            if filename.endswith('.zip'):
                return self._process_zip_file(file_path, detected_date)
            elif filename.endswith(('.xlsx', '.xls')):
                return self._process_excel_file(file_path, detected_date)
            else:
                return False, "不支持的文件格式", None
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return False, f"处理文件时出错: {str(e)}", None
    
    def _process_zip_file(self, zip_path: str, detected_date: Optional[str]) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理ZIP压缩包 - 支持递归搜索和多种文件名"""
        target_files = self.rules.get("file_ingest", {}).get("internal_targets", [
            "04-2综合测定结果表.xlsx",
            "04-2综合测定结果表.xls", 
            "04综合测定结果表.xlsx",
            "04综合测定结果表.xls",
            "综合测定结果表.xlsx",
            "综合测定结果表.xls"
        ])
        
        # 获取需要排除的文件名列表
        excluded_files = self.rules.get("file_ingest", {}).get("excluded_files", [])
        
        logger.info(f"开始处理ZIP文件: {zip_path}")
        logger.info(f"目标文件列表: {target_files}")
        logger.info(f"排除文件列表: {excluded_files}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # 显示ZIP包中的所有文件
                    file_list = zip_ref.namelist()
                    logger.info(f"ZIP包中的文件: {file_list}")
                    
                    zip_ref.extractall(temp_dir)
                    logger.info(f"ZIP文件解压到: {temp_dir}")
                
                # 递归查找目标Excel文件
                excel_path = None
                found_files = []
                target_filename = None
                
                for root, dirs, files in os.walk(temp_dir):
                    logger.info(f"扫描目录: {root}, 文件: {files}")
                    for file in files:
                        found_files.append(file)
                        
                        # 检查文件是否在排除列表中
                        if file in excluded_files:
                            logger.info(f"跳过排除的文件: {file}")
                            continue
                        
                        # 按优先级顺序查找目标文件
                        for target_file in target_files:
                            if file == target_file:
                                excel_path = os.path.join(root, file)
                                target_filename = target_file
                                logger.info(f"找到目标文件: {excel_path}")
                                break
                        if excel_path:
                            break
                    if excel_path:
                        break
                
                if not excel_path:
                    logger.error(f"未找到任何目标文件")
                    logger.info(f"实际找到的文件: {found_files}")
                    # 尝试查找任何Excel文件（排除掉excluded_files中的文件）
                    excel_files = [f for f in found_files 
                                 if f.endswith(('.xlsx', '.xls')) 
                                 and not f.startswith('~') 
                                 and f not in excluded_files]
                    if excel_files:
                        logger.info(f"找到其他Excel文件: {excel_files}")
                        # 尝试使用第一个Excel文件
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                if file in excel_files:
                                    excel_path = os.path.join(root, file)
                                    target_filename = file
                                    logger.info(f"尝试使用文件: {excel_path}")
                                    break
                            if excel_path:
                                break
                
                if not excel_path:
                    excluded_msg = f"，已排除文件: {excluded_files}" if excluded_files else ""
                    return False, f"未找到目标文件，支持的文件名: {target_files}，实际文件: {found_files}{excluded_msg}", None
                
                return self._process_excel_file(excel_path, detected_date, target_filename)
                
            except zipfile.BadZipFile as e:
                logger.error(f"ZIP文件格式错误: {e}")
                return False, "无效的ZIP文件", None
            except Exception as e:
                logger.error(f"处理ZIP文件时出错: {e}")
                return False, f"处理ZIP文件失败: {str(e)}", None
    
    def _process_excel_file(self, excel_path: str, detected_date: Optional[str], target_filename: Optional[str] = None) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理Excel文件 - 支持老版本DHI报告"""
        try:
            # 获取老版本支持配置
            legacy_config = self.rules.get("file_ingest", {}).get("legacy_support", {})
            max_header_rows = legacy_config.get("max_header_search_rows", 15)
            summary_keywords = legacy_config.get("summary_row_keywords", ["小计", "平均与总计", "合计", "总计", "平均"])
            
            # 检测表头位置
            header_row = self._detect_header_row(excel_path, max_header_rows)
            logger.info(f"检测到表头位置: 第{header_row + 1}行")
            
            # 设置数据类型，确保管理号/牛号作为字符串读取
            dtype_dict = {}
            
            # 使用检测到的表头位置读取文件
            df = pd.read_excel(excel_path, header=header_row, dtype=dtype_dict)
            logger.info(f"读取Excel文件成功，原始列名: {list(df.columns)}")
            logger.info(f"数据行数: {len(df)}")
            
            # 过滤汇总行（老版本兼容）
            df = self._filter_summary_rows(df, summary_keywords)
            logger.info(f"过滤汇总行后数据行数: {len(df)}")
            
            # 检查是否缺少牛场编号（老版本处理）
            has_farm_id = self._check_farm_id_column(df)
            missing_farm_id_info = None
            
            if not has_farm_id:
                missing_farm_id_info = {
                    'filename': target_filename or excel_path.split('/')[-1],
                    'needs_farm_id': True
                }
                logger.warning(f"文件 {target_filename} 缺少牛场编号列，需要用户输入")
            
            # 验证表头
            field_map = self.rules.get("field_map", {})
            missing_columns = []
            
            # 检查必要的列 - 移除强制的蛋白率要求，改为可选
            # 同时移除对牧场编号的强制要求
            required_columns = ['管理号', '胎次(胎)', '采样日期']
            # 推荐列，不强制要求
            recommended_columns = ['蛋白率(%)', '产奶量(Kg)', '泌乳天数(天)', '牛场编号']
            
            # 兼容老版本字段名
            if not any(col in df.columns for col in required_columns):
                # 尝试老版本字段名
                alt_required = ['牛号', '胎次', '采样日期']
                alt_recommended = ['蛋白率', '产奶量', '泌乳天数', '牛场编号']
                
                # 检查是否存在老版本字段
                if any(col in df.columns for col in alt_required):
                    required_columns = alt_required
                    recommended_columns = alt_recommended
                else:
                    # 如果都不存在，尝试更灵活的匹配
                    flexible_required = []
                    for col in df.columns:
                        if any(keyword in col for keyword in ['牛号', '管理号', '编号']) and '牧场' not in col and '牛场' not in col:
                            if '管理号' in required_columns:
                                required_columns = [col if c == '管理号' else c for c in required_columns]
                            elif '牛号' in required_columns:
                                required_columns = [col if c == '牛号' else c for c in required_columns]
                            break
            
            for chinese_col in required_columns:
                if chinese_col not in df.columns:
                    missing_columns.append(chinese_col)
            
            # 如果缺少必要列，先检查是否是老版本兼容性问题
            if missing_columns:
                # 尝试更宽松的列名匹配
                alternative_matches = {
                    '牛号': ['牛号', '管理号', '奶牛号', '牛编号'],
                    '管理号': ['管理号', '牛号', '奶牛号', '牛编号'],
                    '胎次': ['胎次', '胎次(胎)', '胎数', '产犊胎次'],
                    '胎次(胎)': ['胎次(胎)', '胎次', '胎数', '产犊胎次'],
                    '采样日期': ['采样日期', '样品日期', '测定日期', '检测日期'],
                    '蛋白率': ['蛋白率', '蛋白率(%)', '蛋白质率', '蛋白含量'],
                    '蛋白率(%)': ['蛋白率(%)', '蛋白率', '蛋白质率', '蛋白含量']
                }
                
                # 尝试找到替代列名
                found_alternatives = []
                still_missing = []
                
                for missing_col in missing_columns:
                    found = False
                    if missing_col in alternative_matches:
                        for alt_name in alternative_matches[missing_col]:
                            if alt_name in df.columns:
                                found_alternatives.append((missing_col, alt_name))
                                found = True
                                break
                    if not found:
                        still_missing.append(missing_col)
                
                # 如果找到了替代列，更新missing_columns
                if found_alternatives:
                    logger.info(f"找到替代列名: {found_alternatives}")
                    missing_columns = still_missing
            
            # 简化的缺失列检查 - 只要有基本字段就允许处理
            if missing_columns:
                # 检查是否至少有管理号/牛号和采样日期
                essential_found = 0
                id_found = False
                date_found = False
                
                for col in df.columns:
                    if any(keyword in col for keyword in ['牛号', '管理号', '编号']) and '牧场' not in col and '牛场' not in col:
                        id_found = True
                        essential_found += 1
                    elif any(keyword in col for keyword in ['日期', '时间']):
                        date_found = True
                        essential_found += 1
                
                # 只要有ID字段和日期字段就允许处理
                if id_found and date_found:
                    logger.warning(f"文件缺少部分列但包含基本字段，继续处理: {missing_columns}")
                    missing_columns = []  # 清空，允许继续处理
                elif essential_found >= 1:
                    # 至少有一个关键字段，也允许处理
                    logger.warning(f"文件缺少部分列但包含关键字段，继续处理: {missing_columns}")
                    missing_columns = []
                
                if missing_columns:
                    logger.error(f"缺失必要列: {missing_columns}")
                    logger.info(f"文件中实际包含的列: {list(df.columns)}")
                    
                    error_msg = f"缺失必要列: {', '.join(missing_columns)}"
                    if missing_farm_id_info:
                        # 创建一个包含错误信息但保留missing_farm_id_info的特殊返回
                        temp_df = pd.DataFrame()
                        temp_df.attrs['missing_farm_id_info'] = missing_farm_id_info
                        temp_df.attrs['processing_error'] = error_msg
                        return False, error_msg, temp_df
                    else:
                        return False, error_msg, None
            
            # 重命名列 - 只重命名存在的列
            rename_dict = {}
            for chinese_col, english_col in field_map.items():
                if chinese_col in df.columns:
                    rename_dict[chinese_col] = english_col
            
            df = df.rename(columns=rename_dict)
            logger.info(f"重命名后的列名: {list(df.columns)}")
            
            # 数据类型转换
            df = self._convert_data_types(df)
            
            # 如果缺少牛场编号，添加到结果中以便后续处理
            if missing_farm_id_info:
                df.attrs['missing_farm_id_info'] = missing_farm_id_info
            
            # 检查关键字段
            if 'farm_id' in df.columns:
                farm_ids = df['farm_id'].dropna().unique()
                logger.info(f"提取到牛场编号: {list(farm_ids)}")
            elif 'management_id' in df.columns:
                logger.info(f"管理号/牛号数量: {df['management_id'].notna().sum()}")
            
            if 'sample_date' in df.columns:
                sample_dates = df['sample_date'].dropna()
                if len(sample_dates) > 0:
                    logger.info(f"采样日期范围: {sample_dates.min()} - {sample_dates.max()}")
                else:
                    logger.warning("采样日期列为空")
            
            message = f"成功处理文件，共 {len(df)} 行数据"
            if detected_date:
                message += f"，检测到日期: {detected_date}"
            if missing_farm_id_info:
                message += f"，缺少牛场编号需要用户输入"
            
            return True, message, df
            
        except Exception as e:
            logger.error(f"处理Excel文件时出错: {str(e)}")
            return False, f"读取Excel文件失败: {str(e)}", None
    
    def _detect_header_row(self, excel_path: str, max_rows: int = 15) -> int:
        """检测表头所在行数 - 智能识别新老版本"""
        try:
            # 获取检测配置
            legacy_config = self.rules.get("file_ingest", {}).get("legacy_support", {})
            new_version_indicators = legacy_config.get("new_version_indicators", ["管理号", "胎次", "采样日期", "蛋白率"])
            old_version_indicators = legacy_config.get("old_version_indicators", ["牛号", "胎次", "采样日期", "蛋白率"])
            core_indicators = legacy_config.get("core_indicators", ["胎次", "采样日期", "蛋白率"])
            
            # 读取前几行来检测表头位置
            for row_num in range(max_rows):
                try:
                    # 尝试以当前行作为表头读取
                    sample_df = pd.read_excel(excel_path, header=row_num, nrows=1)
                    columns = [str(col).strip() for col in sample_df.columns]
                    
                    # 检查新版本指示字段匹配度
                    new_version_matches = sum(1 for indicator in new_version_indicators 
                                            if any(indicator in col for col in columns))
                    
                    # 检查老版本指示字段匹配度
                    old_version_matches = sum(1 for indicator in old_version_indicators 
                                            if any(indicator in col for col in columns))
                    
                    # 检查核心字段匹配度
                    core_matches = sum(1 for indicator in core_indicators 
                                     if any(indicator in col for col in columns))
                    
                    # 判断是否找到有效表头
                    # 新版本：至少匹配3个新版本字段
                    # 老版本：至少匹配3个老版本字段
                    # 或者：至少匹配所有核心字段
                    is_valid_header = (
                        new_version_matches >= 3 or 
                        old_version_matches >= 3 or 
                        core_matches >= len(core_indicators)
                    )
                    
                    if is_valid_header:
                        # 判断版本类型
                        if new_version_matches >= 3:
                            version_type = "新版本"
                            match_count = new_version_matches
                        elif old_version_matches >= 3:
                            version_type = "老版本"
                            match_count = old_version_matches
                        else:
                            version_type = "通用"
                            match_count = core_matches
                        
                        logger.info(f"在第{row_num + 1}行找到{version_type}表头，匹配{match_count}个字段: {columns}")
                        return row_num
                        
                except Exception as e:
                    logger.debug(f"尝试第{row_num + 1}行作为表头失败: {e}")
                    continue
            
            # 如果没有找到，默认使用第一行
            logger.warning("未能自动检测表头位置，使用第1行")
            return 0
            
        except Exception as e:
            logger.error(f"表头检测出错: {e}")
            return 0
    
    def _filter_summary_rows(self, df: pd.DataFrame, summary_keywords: List[str]) -> pd.DataFrame:
        """过滤汇总行数据"""
        if df.empty:
            return df
        
        # 检查管理号/牛号列
        id_column = None
        if 'management_id' in df.columns:
            id_column = 'management_id'
        elif '管理号' in df.columns:
            id_column = '管理号'
        elif '牛号' in df.columns:
            id_column = '牛号'
        
        if not id_column:
            logger.warning("未找到管理号/牛号列，跳过汇总行过滤")
            return df
        
        # 过滤包含汇总关键字的行
        original_count = len(df)
        
        # 转换为字符串进行比较
        id_values = df[id_column].astype(str)
        
        # 创建过滤条件
        filter_condition = pd.Series([True] * len(df))
        
        for keyword in summary_keywords:
            # 过滤掉包含汇总关键字的行
            keyword_condition = ~id_values.str.contains(keyword, na=False, case=False)
            filter_condition = filter_condition & keyword_condition
        
        filtered_df = df[filter_condition].copy()
        filtered_count = len(filtered_df)
        
        logger.info(f"过滤汇总行: 原始{original_count}行 -> 过滤后{filtered_count}行，移除了{original_count - filtered_count}行汇总数据")
        
        return filtered_df
    
    def _check_farm_id_column(self, df: pd.DataFrame) -> bool:
        """检查是否存在牛场编号列"""
        farm_id_columns = ['牛场编号', 'farm_id']
        return any(col in df.columns for col in farm_id_columns)
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据类型转换 - 简化版本，只处理必要字段"""
        try:
            # 数值型字段 - 只保留必要的
            numeric_fields = ['parity', 'protein_pct', 'milk_yield']
            for field in numeric_fields:
                if field in df.columns:
                    logger.info(f"转换字段 {field} 为数值型")
                    df[field] = pd.to_numeric(df[field], errors='coerce')
                    non_null_count = df[field].notna().sum()
                    logger.info(f"字段 {field}: {non_null_count} 个有效数值")
            
            # 整数型字段（如泌乳天数）
            integer_fields = ['lactation_days']
            for field in integer_fields:
                if field in df.columns:
                    logger.info(f"转换字段 {field} 为整数型")
                    df[field] = pd.to_numeric(df[field], errors='coerce')
                    # 转换为整数，保留NaN值
                    df[field] = df[field].astype('Int64')  # 使用可空整数类型
                    non_null_count = df[field].notna().sum()
                    logger.info(f"字段 {field}: {non_null_count} 个有效整数")
            
            # 日期字段 - 只保留采样日期
            date_fields = ['sample_date']
            for field in date_fields:
                if field in df.columns:
                    logger.info(f"转换字段 {field} 为日期型")
                    # 先显示原始日期数据的样例
                    sample_values = df[field].dropna().head(3).tolist()
                    logger.info(f"字段 {field} 样例值: {sample_values}")
                    
                    df[field] = pd.to_datetime(df[field], errors='coerce')
                    non_null_count = df[field].notna().sum()
                    logger.info(f"字段 {field}: {non_null_count} 个有效日期")
            
            # 字符串字段确保为字符串类型，保留前导零
            string_fields = ['farm_id', 'management_id']
            for field in string_fields:
                if field in df.columns:
                    # 先转换为字符串，保留前导零
                    df[field] = df[field].astype(str)
                    # 移除'nan'字符串，但保留"0"开头的有效字符串
                    df.loc[df[field] == 'nan', field] = None
                    # 确保空字符串被转换为None
                    df.loc[df[field] == '', field] = None
                    
                    # 检查并记录管理号的格式
                    if field == 'management_id':
                        unique_values = df[field].dropna().unique()
                        zero_prefixed = [v for v in unique_values if v.startswith('0')]
                        if zero_prefixed:
                            logger.info(f"字段 {field}: 发现{len(zero_prefixed)}个0开头的管理号，已保留前导零")
                    
                    logger.info(f"字段 {field}: {df[field].notna().sum()} 个有效值")
            
            return df
        except Exception as e:
            logger.error(f"Data type conversion error: {e}")
            return df
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """应用筛选条件"""
        filtered_df = df.copy()
        
        for filter_name, filter_value in filters.items():
            if not filter_value.get('enabled', False):
                continue
                
            field = filter_value.get('field')
            if field not in filtered_df.columns:
                continue
            
            try:
                if filter_name == 'date_range':
                    filtered_df = self._apply_date_filter(filtered_df, field, filter_value)
                elif filter_name == 'farm_id':
                    filtered_df = self._apply_list_filter(filtered_df, field, filter_value)
                elif filter_name == 'parity':
                    # 胎次特殊处理：只保留指定胎次范围内的数据
                    filtered_df = self._apply_parity_filter(filtered_df, filter_value)
                elif filter_name == 'future_lactation_days':
                    # 对未来泌乳天数进行数值筛选（将在月度报告生成后单独处理）
                    filtered_df = self.apply_numeric_filter(filtered_df, field, filter_value)
                else:
                    filtered_df = self.apply_numeric_filter(filtered_df, field, filter_value)
            except Exception as e:
                logger.warning(f"Filter {filter_name} failed: {e}")
                continue
        
        return filtered_df
    
    def _apply_date_filter(self, df: pd.DataFrame, field: str, filter_config: Dict) -> pd.DataFrame:
        """应用日期筛选"""
        start_date = filter_config.get('start_date')
        end_date = filter_config.get('end_date')
        
        if start_date:
            df = df[df[field] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[field] <= pd.to_datetime(end_date)]
        
        return df
    
    def _apply_list_filter(self, df: pd.DataFrame, field: str, filter_config: Dict) -> pd.DataFrame:
        """应用列表筛选"""
        allowed_values = filter_config.get('allowed', [])
        if allowed_values:
            df = df[df[field].isin(allowed_values)]
        return df
    
    def apply_numeric_filter(self, df: pd.DataFrame, field: str, filter_config: Dict) -> pd.DataFrame:
        """应用数值筛选"""
        min_val = filter_config.get('min')
        max_val = filter_config.get('max')
        empty_handling = filter_config.get('empty_handling', '视为不符合')
        
        # 如果字段不存在，直接返回
        if field not in df.columns:
            return df
        
        # 处理空值填充
        if empty_handling == '历史数据填充':
            df = self._fill_empty_values_with_history(df, field)
        
        # 创建筛选条件
        condition = pd.Series([True] * len(df), index=df.index)
        
        if min_val is not None:
            if empty_handling == '视为符合':
                # 空值被视为符合条件，或者数值大于等于最小值
                condition = condition & ((df[field] >= min_val) | df[field].isna())
            elif empty_handling == '视为不符合':
                # 只有数值大于等于最小值才符合条件（空值不符合）
                condition = condition & (df[field] >= min_val)
            else:  # 历史数据填充
                # 已经填充过了，直接应用数值条件
                condition = condition & (df[field] >= min_val)
        
        if max_val is not None:
            if empty_handling == '视为符合':
                # 空值被视为符合条件，或者数值小于等于最大值
                condition = condition & ((df[field] <= max_val) | df[field].isna())
            elif empty_handling == '视为不符合':
                # 只有数值小于等于最大值才符合条件（空值不符合）
                condition = condition & (df[field] <= max_val)
            else:  # 历史数据填充
                # 已经填充过了，直接应用数值条件
                condition = condition & (df[field] <= max_val)
        
        return df[condition]
    
    def _fill_empty_values_with_history(self, df: pd.DataFrame, field: str) -> pd.DataFrame:
        """使用历史数据填充空值，并标记填充的值"""
        if 'management_id' not in df.columns or 'sample_date' not in df.columns:
            logger.warning(f"缺少management_id或sample_date列，无法进行历史数据填充")
            return df
        
        df_copy = df.copy()
        
        # 确保sample_date是datetime类型
        df_copy['sample_date'] = pd.to_datetime(df_copy['sample_date'], errors='coerce')
        
        # 记录原始空值位置
        original_null_mask = df_copy[field].isna()
        
        # 按牛只分组进行填充
        def fill_cow_data(group):
            # 按日期排序
            group = group.sort_values('sample_date')
            # 记录填充前的空值位置
            null_before = group[field].isna()
            # 前向填充，然后后向填充
            group[field] = group[field].ffill().bfill()
            # 记录填充后的空值位置
            null_after = group[field].isna()
            # 标记被填充的值（原来是空的，现在不是空的）
            filled_mask = null_before & ~null_after
            
            # 为历史填充的值添加标记
            if f'{field}_historical_filled' not in group.columns:
                group[f'{field}_historical_filled'] = False
            group.loc[filled_mask, f'{field}_historical_filled'] = True
            
            return group
        
        try:
            filled_df = df_copy.groupby('management_id', group_keys=False).apply(fill_cow_data)
            
            # 统计填充数量
            if f'{field}_historical_filled' in filled_df.columns:
                filled_count = filled_df[f'{field}_historical_filled'].sum()
                logger.info(f"已对字段{field}进行历史数据填充，共填充{filled_count}个空值")
            
            return filled_df
        except Exception as e:
            logger.error(f"历史数据填充失败: {e}")
            return df
    
    def _apply_parity_filter(self, df: pd.DataFrame, filter_config: Dict) -> pd.DataFrame:
        """应用胎次筛选 - 特殊逻辑：只保留指定胎次范围内的数据"""
        if df.empty or 'parity' not in df.columns:
            return df
        
        min_parity = filter_config.get('min', 1)
        max_parity = filter_config.get('max', 10)
        
        logger.info(f"应用胎次筛选: {min_parity}-{max_parity}胎")
        
        original_count = len(df)
        original_cow_count = 0
        
        # 统计原始牛头数
        if 'management_id' in df.columns:
            if 'farm_id' in df.columns:
                original_cow_count = len(df.groupby(['farm_id', 'management_id']))
            else:
                mgmt_series = df['management_id']
                original_cow_count = len(mgmt_series.dropna().unique())
        
        # 只保留胎次在指定范围内的记录
        parity_mask = (df['parity'] >= min_parity) & (df['parity'] <= max_parity)
        filtered_df = df[parity_mask].copy()
        
        filtered_count = len(filtered_df)
        filtered_cow_count = 0
        
        # 统计筛选后牛头数
        if not filtered_df.empty and 'management_id' in filtered_df.columns:
            if 'farm_id' in filtered_df.columns:
                filtered_cow_count = len(filtered_df.groupby(['farm_id', 'management_id']))
            else:
                mgmt_ids = filtered_df['management_id'].dropna().unique()
                filtered_cow_count = len(mgmt_ids)
        
        logger.info(f"胎次筛选结果: {original_count}条记录 -> {filtered_count}条记录")
        logger.info(f"胎次筛选结果: {original_cow_count}头牛 -> {filtered_cow_count}头牛")
        
        if not filtered_df.empty:
            # 统计每头牛的胎次分布
            if 'farm_id' in filtered_df.columns and 'management_id' in filtered_df.columns:
                cow_parity_stats = filtered_df.groupby(['farm_id', 'management_id'])['parity'].agg(['min', 'max', 'nunique']).reset_index()
                logger.info(f"筛选后牛只胎次分布: 最小{cow_parity_stats['min'].min()}胎, 最大{cow_parity_stats['max'].max()}胎")
                
                # 统计有多胎次数据的牛只
                multi_parity_cows = cow_parity_stats[cow_parity_stats['nunique'] > 1]
                if len(multi_parity_cows) > 0:
                    logger.info(f"有多个胎次数据的牛只: {len(multi_parity_cows)}头")
        
        return filtered_df
    
    def _apply_future_lactation_filter(self, df: pd.DataFrame, filter_config: Dict) -> pd.DataFrame:
        """应用未来泌乳天数筛选"""
        min_days = filter_config.get('min')
        max_days = filter_config.get('max')
        plan_date = filter_config.get('plan_date')
        
        if not plan_date:
            logger.warning("未来泌乳天数筛选：缺少计划调群日期")
            return df
        
        # 转换计划调群日期
        try:
            plan_date = pd.to_datetime(plan_date)
        except Exception as e:
            logger.error(f"计划调群日期格式错误: {e}")
            return df
        
        if df.empty:
            return df
        
        # 检查必要字段 - 泌乳天数不是必须的，可以为空
        required_fields = ['farm_id', 'management_id', 'sample_date']
        for field in required_fields:
            if field not in df.columns:
                logger.warning(f"未来泌乳天数筛选：缺少字段 {field}")
                return df
        
        # 检查泌乳天数字段是否存在（可选）
        if 'lactation_days' not in df.columns:
            logger.warning("未来泌乳天数筛选：缺少泌乳天数字段，将设置为空值")
            df = df.copy()
            df['lactation_days'] = None
        
        # 计算每头牛的未来泌乳天数
        future_lactation_df = self._calculate_future_lactation_days(df, plan_date)
        
        if future_lactation_df.empty:
            return pd.DataFrame()
        
        # 应用筛选条件 - 对于未来泌乳天数为空的记录，不进行数值筛选
        condition = pd.Series([True] * len(future_lactation_df), index=future_lactation_df.index)
        
        # 只对有数值的未来泌乳天数进行筛选
        has_future_days = future_lactation_df['future_lactation_days'].notna()
        
        if min_days is not None:
            # 只对有数值的记录应用最小值筛选，空值记录保持True
            condition = condition & ((~has_future_days) | (future_lactation_df['future_lactation_days'] >= min_days))
        
        if max_days is not None:
            # 只对有数值的记录应用最大值筛选，空值记录保持True
            condition = condition & ((~has_future_days) | (future_lactation_df['future_lactation_days'] <= max_days))
        
        logger.info(f"未来泌乳天数筛选：计划日期 {plan_date.strftime('%Y-%m-%d')}，"
                   f"范围 {min_days}-{max_days} 天，符合条件记录数：{condition.sum()}")
        
        return future_lactation_df[condition]
    
    def _calculate_future_lactation_days(self, df: pd.DataFrame, plan_date: pd.Timestamp) -> pd.DataFrame:
        """计算每头牛的未来泌乳天数"""
        
        # 确保关键字段为字符串类型，保持数据一致性
        df = df.copy()
        for field in ['farm_id', 'management_id']:
            if field in df.columns:
                df[field] = df[field].astype(str)
                # 移除'nan'字符串，转换为None
                df.loc[df[field] == 'nan', field] = None
        
        # 按牛分组，找到每头牛最后一次采样的数据
        cow_groups = df.groupby(['farm_id', 'management_id'])
        result_rows = []
        
        for (farm_id, mgmt_id), group in cow_groups:
            try:
                # 确保sample_date是datetime类型
                group = group.copy()
                group['sample_date'] = pd.to_datetime(group['sample_date'], errors='coerce')
                
                # 过滤掉无效日期的记录
                valid_dates = group.dropna(subset=['sample_date'])
                
                if valid_dates.empty:
                    continue
                
                # 找到最后一次采样记录
                latest_record = valid_dates.loc[valid_dates['sample_date'].idxmax()]
                
                # 获取最后一次的泌乳天数
                last_lactation_days = latest_record['lactation_days']
                last_sample_date = latest_record['sample_date']
                
                # 检查采样日期有效性（必须有）
                if pd.isna(last_sample_date):
                    continue
                
                # 检查泌乳天数有效性（可以为空，但如果有值必须是数值）
                if pd.isna(last_lactation_days):
                    # 泌乳天数为空时，跳过未来泌乳天数计算，但保留原始记录
                    new_record = latest_record.copy()
                    new_record['future_lactation_days'] = None  # 无法计算
                    new_record['plan_date'] = plan_date
                    new_record['days_from_last_sample'] = None
                    result_rows.append(new_record)
                    logger.debug(f"牛场{farm_id}-管理号{mgmt_id}: 泌乳天数为空，保留记录但未来泌乳天数为空")
                    continue
                
                # 确保泌乳天数是数值类型
                try:
                    last_lactation_days = float(last_lactation_days)
                except (ValueError, TypeError):
                    # 泌乳天数无法转换为数值时，也保留记录但不计算未来泌乳天数
                    new_record = latest_record.copy()
                    new_record['future_lactation_days'] = None
                    new_record['plan_date'] = plan_date
                    new_record['days_from_last_sample'] = None
                    result_rows.append(new_record)
                    logger.debug(f"牛场{farm_id}-管理号{mgmt_id}: 泌乳天数格式错误，保留记录但未来泌乳天数为空")
                    continue
                
                # 计算日期差异（天数）
                days_diff = (plan_date - last_sample_date).days
                
                # 计算未来泌乳天数：(计划调群日 - 最后一次采样日的天数) + 最后一个月泌乳天数
                future_lactation_days = int(days_diff + last_lactation_days)
                
                # 确保未来泌乳天数为正数
                if future_lactation_days > 0:
                    # 创建记录，包含原始数据和计算结果
                    new_record = latest_record.copy()
                    new_record['future_lactation_days'] = future_lactation_days
                    new_record['plan_date'] = plan_date
                    new_record['days_from_last_sample'] = days_diff
                    
                    result_rows.append(new_record)
                    
                    logger.debug(f"牛场{farm_id}-管理号{mgmt_id}: "
                               f"最后采样日{last_sample_date.strftime('%Y-%m-%d')}, "
                               f"泌乳天数{last_lactation_days}, "
                               f"间隔{days_diff}天, "
                               f"未来泌乳天数{future_lactation_days}")
            
            except Exception as e:
                logger.warning(f"计算牛场{farm_id}-管理号{mgmt_id}的未来泌乳天数时出错: {e}")
                continue
        
        if result_rows:
            result_df = pd.DataFrame(result_rows)
            logger.info(f"成功计算{len(result_df)}头牛的未来泌乳天数")
            return result_df
        else:
            logger.warning("没有计算出任何未来泌乳天数")
            return pd.DataFrame()
    
    def export_results(self, df: pd.DataFrame, output_path: str) -> bool:
        """导出筛选结果"""
        try:
            export_config = self.rules.get("export", {})
            columns = export_config.get("columns", [])
            
            # 准备导出数据
            export_df = self._prepare_export_data(df, columns)
            
            # 导出到Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                export_df.to_excel(writer, index=False, sheet_name='筛选结果')
            
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def _prepare_export_data(self, df: pd.DataFrame, columns: List) -> pd.DataFrame:
        """准备导出数据"""
        export_columns = []
        
        for col in columns:
            if isinstance(col, str) and col in df.columns:
                export_columns.append(col)
            elif isinstance(col, dict) and 'monthly_details' in col:
                # 处理月度明细（简化版本，实际可能需要更复杂的逻辑）
                detail_cols = col['monthly_details']
                for detail_col in detail_cols:
                    if detail_col in df.columns:
                        export_columns.append(detail_col)
        
        return df[export_columns] if export_columns else df
    
    def get_available_filters(self) -> Dict[str, FilterConfig]:
        """获取可用的筛选条件"""
        filters_config = self.rules.get("filters", {})
        field_map = self.rules.get("field_map", {})
        
        available_filters = {}
        
        # 添加配置的筛选条件
        for filter_name, config in filters_config.items():
            available_filters[filter_name] = config
        
        # 为field_map中的其他字段生成默认筛选条件
        for chinese_name, english_name in field_map.items():
            if english_name not in [config.get('field') for config in filters_config.values()]:
                available_filters[english_name] = {
                    'field': english_name,
                    'enabled': False,
                    'required': False,
                    'chinese_name': chinese_name
                }
        
        return available_filters
    
    def save_temp_data(self, df: pd.DataFrame, file_id: str) -> str:
        """保存临时数据"""
        temp_file = os.path.join(self.temp_dir, f"{file_id}.pkl")
        df.to_pickle(temp_file)
        return temp_file
    
    def load_temp_data(self, file_id: str) -> Optional[pd.DataFrame]:
        """加载临时数据"""
        temp_file = os.path.join(self.temp_dir, f"{file_id}.pkl")
        if os.path.exists(temp_file):
            return pd.read_pickle(temp_file)
        return None
    
    def process_multiple_files_with_progress(self, file_paths: List[str], filenames: List[str]) -> Dict[str, Any]:
        """批量处理多个文件（带进度更新）"""
        # 导入进度变量
        from main import processing_progress
        
        results = {
            'success_files': [],
            'failed_files': [],
            'data_summaries': [],
            'date_ranges': [],
            'farm_ids': set(),
            'all_data': []
        }
        
        total_files = len(file_paths)
        
        for i, (file_path, filename) in enumerate(zip(file_paths, filenames)):
            # 更新进度
            processing_progress.update({
                "current_file": filename,
                "current_step": f"处理文件 ({i+1}/{total_files})",
                "progress_percentage": 30 + int((i / total_files) * 60)  # 处理占60%
            })
            
            logger.info(f"处理文件 {i+1}/{total_files}: {filename}")
            success, message, df = self.process_uploaded_file(file_path, filename)
            
            if success and df is not None:
                # 从数据中提取日期范围
                date_range = self.extract_date_range_from_data(df)
                
                results['success_files'].append({
                    'filename': filename,
                    'message': message,
                    'row_count': len(df),
                    'date_range': date_range
                })
                
                results['all_data'].append({
                    'filename': filename,
                    'data': df,
                    'date_range': date_range
                })
                
                if date_range:
                    results['date_ranges'].append(date_range)
                
                # 收集牛场编号
                if 'farm_id' in df.columns:
                    farm_ids = df['farm_id'].dropna().unique()
                    results['farm_ids'].update(farm_ids)
                    logger.info(f"文件 {filename} 提取到牛场编号: {list(farm_ids)}")
                else:
                    logger.warning(f"文件 {filename} 没有找到farm_id列")
                    
            else:
                results['failed_files'].append({
                    'filename': filename,
                    'error': message
                })
                logger.error(f"文件 {filename} 处理失败: {message}")
        
        # 完成处理
        processing_progress.update({
            "current_step": "处理完成",
            "progress_percentage": 100,
            "completed_files": len(results['success_files']),
            "is_processing": False
        })
        
        results['farm_ids'] = sorted(list(results['farm_ids']))
        logger.info(f"批量处理完成，成功: {len(results['success_files'])}, 失败: {len(results['failed_files'])}")
        logger.info(f"所有牛场编号: {results['farm_ids']}")
        return results

    def process_multiple_files(self, file_paths: List[str], filenames: List[str]) -> Dict[str, Any]:
        """批量处理多个文件"""
        results = {
            'success_files': [],
            'failed_files': [],
            'data_summaries': [],
            'date_ranges': [],
            'farm_ids': set(),
            'all_data': []
        }
        
        for file_path, filename in zip(file_paths, filenames):
            success, message, df = self.process_uploaded_file(file_path, filename)
            
            if success and df is not None:
                # 从数据中提取日期范围
                date_range = self.extract_date_range_from_data(df)
                
                results['success_files'].append({
                    'filename': filename,
                    'message': message,
                    'row_count': len(df),
                    'date_range': date_range
                })
                
                results['all_data'].append({
                    'filename': filename,
                    'data': df,
                    'date_range': date_range
                })
                
                if date_range:
                    results['date_ranges'].append(date_range)
                
                # 收集牛场编号
                if 'farm_id' in df.columns:
                    farm_ids = df['farm_id'].dropna().unique()
                    results['farm_ids'].update(farm_ids)
                    
            else:
                # 检查失败的文件是否包含missing_farm_id_info
                if df is not None and hasattr(df, 'attrs'):
                    if 'missing_farm_id_info' in df.attrs:
                        # 这是一个包含missing_farm_id_info的特殊失败情况
                        # 将其添加到特殊处理列表而不是failed_files
                        logger.info(f"文件 {filename} 处理失败但包含缺少牛场编号信息: {message}")
                        
                        # 创建一个特殊的成功文件记录，但标记为需要补充牛场编号
                        results['success_files'].append({
                            'filename': filename,
                            'message': f"{message} (需要补充牛场编号)",
                            'row_count': 0,
                            'date_range': None,
                            'requires_farm_id': True
                        })
                        
                        # 添加到all_data以便后续处理
                        results['all_data'].append({
                            'filename': filename,
                            'data': df,
                            'date_range': None
                        })
                        continue
                
                # 普通的失败情况
                results['failed_files'].append({
                    'filename': filename,
                    'error': message
                })
        
        results['farm_ids'] = sorted(list(results['farm_ids']))
        return results
    
    def get_overall_date_range(self, date_ranges: List[Dict]) -> Optional[Dict]:
        """获取所有文件的总体日期范围"""
        if not date_ranges:
            return None
        
        try:
            all_start_dates = []
            all_end_dates = []
            
            for date_range in date_ranges:
                if date_range and 'start_date' in date_range and 'end_date' in date_range:
                    all_start_dates.append(pd.to_datetime(date_range['start_date']))
                    all_end_dates.append(pd.to_datetime(date_range['end_date']))
            
            if all_start_dates and all_end_dates:
                min_date = min(all_start_dates)
                max_date = max(all_end_dates)
                
                return {
                    'start_date': min_date.strftime('%Y-%m-%d'),
                    'end_date': max_date.strftime('%Y-%m-%d'),
                    'year_month_range': f"{min_date.strftime('%Y年%m月')} - {max_date.strftime('%Y年%m月')}"
                }
        except Exception as e:
            logger.error(f"Error getting overall date range: {e}")
        
        return None
    
    def apply_cross_month_filters(self, data_list: List[Dict], filters: Dict[str, Any], selected_files: List[str]) -> pd.DataFrame:
        """应用跨月筛选逻辑：同一牛场同一头牛在所有月份都必须符合条件"""
        
        # 筛选选中的文件
        selected_data = [item for item in data_list if item['filename'] in selected_files]
        
        if not selected_data:
            return pd.DataFrame()
        
        # 合并所有数据
        all_dfs = []
        for item in selected_data:
            df = item['data'].copy()
            df['source_file'] = item['filename']
            
            # 添加年月列
            if 'sample_date' in df.columns:
                df['year_month'] = pd.to_datetime(df['sample_date']).dt.strftime('%Y-%m')
            
            all_dfs.append(df)
        
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # 应用基础筛选条件
        filtered_df = self.apply_filters(combined_df, filters)
        
        if filtered_df.empty:
            return pd.DataFrame()
        
        # 应用跨月逻辑：找出在所有月份都符合条件的牛
        if 'management_id' not in filtered_df.columns:
            return filtered_df
        
        # 动态确定分组键
        if 'farm_id' in filtered_df.columns:
            group_keys = ['farm_id', 'management_id']
        else:
            group_keys = ['management_id']
        
        # 按分组键分组
        cow_groups = filtered_df.groupby(group_keys)
        
        # 获取选中文件对应的月份
        selected_months = set()
        for item in selected_data:
            date_range = item.get('date_range')
            if date_range:
                # 简化处理：从文件名或日期范围推断月份
                sample_data = item['data']
                if 'sample_date' in sample_data.columns:
                    months = pd.to_datetime(sample_data['sample_date']).dt.strftime('%Y-%m').unique()
                    selected_months.update(months)
        
        # 筛选在所有选定月份都有数据的牛
        valid_cows = []
        for group_key, group in cow_groups:
            cow_months = set(group['year_month'].unique())
            
            # 检查是否在所有选定月份都符合条件
            if selected_months.issubset(cow_months):
                # 保持与其他函数一致的处理方式
                if 'farm_id' in df.columns:
                    farm_id, mgmt_id = group_key
                    valid_cows.append((farm_id, mgmt_id))
                else:
                    mgmt_id = group_key if not isinstance(group_key, tuple) else group_key[0]
                    valid_cows.append(mgmt_id)
        
        # 返回符合条件的牛的所有数据
        if valid_cows:
            if 'farm_id' in filtered_df.columns:
                cow_filter = filtered_df.apply(
                    lambda row: (row['farm_id'], row['management_id']) in valid_cows, 
                    axis=1
                )
            else:
                cow_filter = filtered_df.apply(
                    lambda row: row['management_id'] in valid_cows, 
                    axis=1
                )
            return filtered_df[cow_filter]
        
        return pd.DataFrame()
    
    def apply_partial_month_filters(self, data_list: List[Dict], filters: Dict[str, Any], selected_files: List[str], min_match_months: int = 3, treat_empty_as_match: bool = False) -> pd.DataFrame:
        """应用部分月份筛选逻辑：同一牛场同一头牛在X个月中符合条件即可"""
        
        # 筛选选中的文件
        selected_data = [item for item in data_list if item['filename'] in selected_files]
        
        if not selected_data:
            return pd.DataFrame()
        
        logger.info(f"开始部分月份筛选，最少需要{min_match_months}个月符合条件")
        
        # 更新进度
        try:
            from main import processing_progress
            processing_progress.update({
                "current_step": "合并数据分析",
                "progress_percentage": 40
            })
        except Exception as e:
            logger.warning(f"更新进度失败: {e}")
        
        # 合并所有数据
        all_dfs = []
        all_months = set()
        
        for item in selected_data:
            df = item['data'].copy()
            df['source_file'] = item['filename']
            
            # 确保关键字段为字符串类型，保持数据一致性
            for field in ['farm_id', 'management_id']:
                if field in df.columns:
                    df[field] = df[field].astype(str)
                    # 移除'nan'字符串，转换为None
                    df.loc[df[field] == 'nan', field] = None
            
            # 添加年月列
            if 'sample_date' in df.columns:
                df['year_month'] = pd.to_datetime(df['sample_date']).dt.strftime('%Y-%m')
                # 收集所有月份
                months = df['year_month'].dropna().unique()
                all_months.update(months)
            
            all_dfs.append(df)
        
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # 合并后再次确保字符串字段类型一致性
        for field in ['farm_id', 'management_id']:
            if field in combined_df.columns:
                combined_df[field] = combined_df[field].astype(str)
                combined_df.loc[combined_df[field] == 'nan', field] = None
        
        logger.info(f"合并数据：共{len(combined_df)}行，覆盖月份：{sorted(all_months)}")
        
        # 使用传入的空值处理参数
        include_null_as_match = treat_empty_as_match
        logger.info(f"空值判定为符合：{include_null_as_match}")
        
        # 应用基础筛选条件（只保留简单筛选，移除所有需要月份逻辑的筛选项）
        base_filters = {}
        monthly_filters = {}  # 需要月份逻辑处理的筛选项
        
        for filter_name, filter_config in filters.items():
            if filter_name in ['parity', 'date_range']:
                # 基础筛选：胎次、日期范围
                if filter_config.get('enabled', False):
                    base_filters[filter_name] = filter_config
            elif filter_name not in ['future_lactation_days'] and isinstance(filter_config, dict) and filter_config.get('enabled', False):
                # 月份逻辑筛选：蛋白率、乳脂率等所有启用的数值筛选项
                monthly_filters[filter_name] = filter_config
        
        # 只应用不需要月份逻辑的基础筛选条件
        base_filtered_df = self.apply_filters(combined_df, base_filters)
        logger.info(f"基础筛选后：共{len(base_filtered_df)}行，启用的月份逻辑筛选项：{list(monthly_filters.keys())}")
        
        if base_filtered_df.empty:
            return pd.DataFrame()
        
        # 检查必要字段
        if 'management_id' not in base_filtered_df.columns:
            return base_filtered_df
        
        # 获取所有牛只
        if 'farm_id' in base_filtered_df.columns:
            all_cows = base_filtered_df[['farm_id', 'management_id']].drop_duplicates()
        else:
            all_cows = base_filtered_df[['management_id']].drop_duplicates()
        logger.info(f"筛选范围内共有{len(all_cows)}头牛")
        
        # 对每头牛检查每个月份的符合情况
        valid_cows = []
        
        # 更新进度
        try:
            from main import processing_progress
            processing_progress.update({
                "current_step": "逐头牛分析符合情况",
                "progress_percentage": 60
            })
        except Exception as e:
            logger.warning(f"更新进度失败: {e}")
        
        for _, cow_row in all_cows.iterrows():
            if 'farm_id' in cow_row.index:
                farm_id = cow_row['farm_id']
                mgmt_id = cow_row['management_id']
                
                # 获取这头牛的所有数据
                cow_data = base_filtered_df[
                    (base_filtered_df['farm_id'] == farm_id) & 
                    (base_filtered_df['management_id'] == mgmt_id)
                ]
            else:
                farm_id = None
                mgmt_id = cow_row['management_id']
                
                # 获取这头牛的所有数据
                cow_data = base_filtered_df[
                    base_filtered_df['management_id'] == mgmt_id
                ]
            
            # 检查每个月份的符合情况
            matched_months = 0
            
            for month in all_months:
                # 检查这头牛在这个月份的数据
                month_data = cow_data[cow_data['year_month'] == month]
                
                if len(month_data) == 0:
                    # 这个月份没有数据
                    if include_null_as_match:
                        matched_months += 1
                        logger.debug(f"牛场{farm_id}-管理号{mgmt_id} {month}月：无数据，空值判定为符合")
                    else:
                        logger.debug(f"牛场{farm_id}-管理号{mgmt_id} {month}月：无数据，不符合")
                else:
                    # 这个月份有数据，检查所有启用的月份逻辑筛选项
                    month_satisfies_all = True
                    filter_details = []
                    
                    if not monthly_filters:
                        # 没有月份逻辑筛选项，有数据就算符合
                        matched_months += 1
                        logger.debug(f"牛场{farm_id}-管理号{mgmt_id} {month}月：无月份筛选项，有数据符合")
                    else:
                        # 检查每个月份逻辑筛选项
                        for filter_name, filter_config in monthly_filters.items():
                            field = filter_config.get('field')
                            
                            if not field or field not in month_data.columns:
                                filter_details.append(f"{filter_name}:字段不存在")
                                continue
                            
                            # 获取该字段的值
                            field_values = month_data[field].dropna()
                            
                            if len(field_values) == 0:
                                # 该字段为空
                                if include_null_as_match:
                                    filter_details.append(f"{filter_name}:空值符合")
                                else:
                                    month_satisfies_all = False
                                    filter_details.append(f"{filter_name}:空值不符合")
                                    break
                            else:
                                # 该字段有值，检查是否符合条件
                                # 创建临时筛选配置，包含空值处理参数
                                temp_filter_config = filter_config.copy()
                                temp_filter_config['include_null_as_match'] = include_null_as_match
                                
                                month_filtered = self.apply_numeric_filter(month_data, field, temp_filter_config)
                                if len(month_filtered) > 0:
                                    filter_details.append(f"{filter_name}:数值符合")
                                else:
                                    month_satisfies_all = False
                                    filter_details.append(f"{filter_name}:数值不符合")
                                    break
                        
                        # 所有筛选项都符合才算这个月符合
                        if month_satisfies_all:
                            matched_months += 1
                            logger.debug(f"牛场{farm_id}-管理号{mgmt_id} {month}月：所有条件符合 ({', '.join(filter_details)})")
                        else:
                            logger.debug(f"牛场{farm_id}-管理号{mgmt_id} {month}月：条件不符合 ({', '.join(filter_details)})")
            
            if matched_months >= min_match_months:
                if farm_id is not None:
                    valid_cows.append((farm_id, mgmt_id))
                    logger.debug(f"牛场{farm_id}-管理号{mgmt_id}: {matched_months}个月符合条件，保留")
                else:
                    valid_cows.append(mgmt_id)
                    logger.debug(f"管理号{mgmt_id}: {matched_months}个月符合条件，保留")
            else:
                if farm_id is not None:
                    logger.debug(f"牛场{farm_id}-管理号{mgmt_id}: {matched_months}个月符合条件，不足{min_match_months}个月，淘汰")
                else:
                    logger.debug(f"管理号{mgmt_id}: {matched_months}个月符合条件，不足{min_match_months}个月，淘汰")
        
        logger.info(f"符合{min_match_months}个月条件的牛：{len(valid_cows)}头")
        
        # 返回符合条件的牛的所有数据 - 从base_filtered_df中返回，保持基础筛选条件
        if valid_cows:
            if 'farm_id' in base_filtered_df.columns:
                all_cow_data = base_filtered_df[
                    base_filtered_df.apply(
                        lambda row: (row['farm_id'], row['management_id']) in valid_cows, 
                        axis=1
                    )
                ]
            else:
                all_cow_data = base_filtered_df[
                    base_filtered_df.apply(
                        lambda row: row['management_id'] in valid_cows, 
                        axis=1
                    )
                ]
            return all_cow_data
        
        return pd.DataFrame()
    
    def create_monthly_report(self, df: pd.DataFrame, display_fields: List[str], plan_date: str = None) -> pd.DataFrame:
        """创建按月展开的报告"""
        if df.empty:
            return pd.DataFrame()
        
        # 确保关键字段为字符串类型，保持数据一致性
        df = df.copy()
        for field in ['farm_id', 'management_id']:
            if field in df.columns:
                df[field] = df[field].astype(str)
                # 移除'nan'字符串，转换为None
                df.loc[df[field] == 'nan', field] = None
        
        # 使用传入的display_fields参数，支持动态字段配置
        logger.info(f"生成月度报告，使用字段: {display_fields}")
        
        # 动态确定基础列和分组键
        if 'farm_id' in df.columns:
            base_columns = ['farm_id', 'management_id', 'parity']
            group_keys = ['farm_id', 'management_id']
        else:
            base_columns = ['management_id', 'parity']
            group_keys = ['management_id']
        
        # 按牛分组
        cow_groups = df.groupby(group_keys)
        
        result_rows = []
        all_protein_milk_pairs = []  # 收集所有(蛋白率, 产奶量)对用于计算加权总平均值
        all_fat_milk_pairs = []  # 收集所有(乳脂率, 产奶量)对用于计算加权总平均值  
        all_lactose_milk_pairs = []  # 收集所有(乳糖率, 产奶量)对用于计算加权总平均值
        all_total_milk = 0  # 总产奶量
        
        # 收集所有月份信息
        all_months_data = {}
        for group_key, group in cow_groups:
            for _, record in group.iterrows():
                if pd.notna(record['sample_date']):
                    sample_date = pd.to_datetime(record['sample_date'])
                    year_month = sample_date.strftime('%Y年%m月')
                    if year_month not in all_months_data:
                        all_months_data[year_month] = sample_date
        
        # 按时间顺序排序所有月份
        sorted_all_months = sorted(all_months_data.items(), key=lambda x: x[1])
        sorted_month_names = [month for month, _ in sorted_all_months]
        
        for group_key, group in cow_groups:
            # 解析分组键
            if 'farm_id' in df.columns:
                farm_id, mgmt_id = group_key
            else:
                farm_id = None
                # 确保mgmt_id是标量值，不是元组
                mgmt_id = group_key if not isinstance(group_key, tuple) else group_key[0]
            # 获取胎次（取最后一次采样时的胎次）
            parity = None
            latest_sample_date = None
            for _, record in group.iterrows():
                if pd.notna(record['sample_date']):
                    sample_date = pd.to_datetime(record['sample_date'])
                    if latest_sample_date is None or sample_date > latest_sample_date:
                        latest_sample_date = sample_date
                        if pd.notna(record['parity']):
                            parity = record['parity']
            
            # 基础信息 - 按固定顺序
            row_data = {}
            
            # 按月份整理数据，按日期排序
            monthly_data = {}
            for _, record in group.iterrows():
                if pd.notna(record['sample_date']):
                    sample_date = pd.to_datetime(record['sample_date'])
                    year_month = sample_date.strftime('%Y年%m月')
                    monthly_data[year_month] = {
                        'record': record,
                        'date': sample_date
                    }
            
            # 计算这头牛的加权平均值（蛋白率、乳脂率、乳糖率）
            cow_protein_values = []  # 存储(蛋白率, 产奶量)对
            cow_fat_values = []  # 存储(乳脂率, 产奶量)对
            cow_lactose_values = []  # 存储(乳糖率, 产奶量)对
            cow_total_milk = 0  # 总产奶量
            last_lactation_days = None
            
            # 按固定顺序组织列
            # 1. 基础列
            if farm_id is not None:
                row_data['farm_id'] = farm_id
            row_data['management_id'] = mgmt_id
            row_data['parity'] = parity
            
            # 2. 按月份顺序添加启用的筛选项的月度明细
            # 定义字段的中文名称映射
            field_chinese_map = {
                'protein_pct': '蛋白率(%)',
                'fat_pct': '乳脂率(%)',
                'fat_protein_ratio': '脂蛋比',
                'somatic_cell_count': '体细胞数(万/ml)',
                'somatic_cell_score': '体细胞分',
                'urea_nitrogen': '尿素氮(mg/dl)',
                'lactose_pct': '乳糖率',
                'milk_loss': '奶损失(Kg)',
                'milk_payment_diff': '奶款差',
                'economic_loss': '经济损失',
                'corrected_milk': '校正奶(Kg)',
                'persistency': '持续力',
                'whi': 'WHI',
                'fore_milk_yield': '前奶量(Kg)',
                'fore_somatic_cell_count': '前体细胞(万/ml)',
                'fore_somatic_cell_score': '前体细胞分',
                'fore_milk_loss': '前奶损失(Kg)',
                'peak_milk_yield': '高峰奶(Kg)',
                'peak_days': '高峰日(天)',
                'milk_305': '305奶量(Kg)',
                'total_milk_yield': '总奶量(Kg)',
                'total_fat_pct': '总乳脂(%)',
                'total_protein_pct': '总蛋白(%)',
                'mature_equivalent': '成年当量(Kg)',
                'milk_yield': '产奶量(Kg)',
                'lactation_days': '泌乳天数(天)'
            }
            
            for year_month in sorted_month_names:
                if year_month in monthly_data:
                    record = monthly_data[year_month]['record']
                    
                    # 为每个启用的字段添加月度明细列
                    for field in display_fields:
                        if field in ['farm_id', 'management_id', 'parity']:
                            continue  # 跳过基础字段
                        
                        if field in field_chinese_map:
                            chinese_name = field_chinese_map[field]
                            column_name = f"{year_month}{chinese_name}"
                            
                            # 获取字段值
                            field_value = None
                            if field in record and pd.notna(record[field]):
                                field_value = record[field]
                                
                                # 特殊处理：泌乳天数转为整数
                                if field == 'lactation_days':
                                    try:
                                        field_value = int(float(field_value))
                                        if field_value is not None:
                                            last_lactation_days = field_value  # 更新为最新的
                                    except (ValueError, TypeError):
                                        field_value = None
                                
                                row_data[column_name] = field_value
                            else:
                                row_data[column_name] = None
                            
                            # 收集蛋白率、乳脂率、乳糖率和产奶量用于加权平均计算
                            if field in ['protein_pct', 'fat_pct', 'lactose_pct'] and field_value is not None:
                                # 需要对应的产奶量
                                milk_value = None
                                if 'milk_yield' in record and pd.notna(record['milk_yield']):
                                    milk_value = record['milk_yield']
                                    
                                if milk_value is not None:
                                    # 收集各个指标的加权平均数据
                                    if field == 'protein_pct':
                                        cow_protein_values.append((float(field_value), float(milk_value)))
                                        all_protein_milk_pairs.append((float(field_value), float(milk_value)))
                                    elif field == 'fat_pct':
                                        cow_fat_values.append((float(field_value), float(milk_value)))
                                        all_fat_milk_pairs.append((float(field_value), float(milk_value)))
                                    elif field == 'lactose_pct':
                                        cow_lactose_values.append((float(field_value), float(milk_value)))
                                        all_lactose_milk_pairs.append((float(field_value), float(milk_value)))
                                    
                                    cow_total_milk += float(milk_value)
                                    all_total_milk += float(milk_value)
                else:
                    # 该月份没有数据，为所有启用的字段添加空值
                    for field in display_fields:
                        if field in ['farm_id', 'management_id', 'parity']:
                            continue  # 跳过基础字段
                        
                        if field in field_chinese_map:
                            chinese_name = field_chinese_map[field]
                            column_name = f"{year_month}{chinese_name}"
                            row_data[column_name] = None
            
            # 3. 添加加权平均值（蛋白率、乳脂率、乳糖率）
            # 加权平均蛋白率
            if 'protein_pct' in display_fields:
                if cow_protein_values and cow_total_milk > 0:
                    weighted_protein_sum = sum(protein * milk for protein, milk in cow_protein_values)
                    cow_avg = weighted_protein_sum / cow_total_milk
                    row_data['平均蛋白率(%)'] = round(cow_avg, 2)
                else:
                    row_data['平均蛋白率(%)'] = None
            
            # 加权平均乳脂率
            if 'fat_pct' in display_fields:
                if cow_fat_values and cow_total_milk > 0:
                    weighted_fat_sum = sum(fat * milk for fat, milk in cow_fat_values)
                    cow_avg = weighted_fat_sum / cow_total_milk
                    row_data['平均乳脂率(%)'] = round(cow_avg, 2)
                else:
                    row_data['平均乳脂率(%)'] = None
            
            # 加权平均乳糖率
            if 'lactose_pct' in display_fields:
                if cow_lactose_values and cow_total_milk > 0:
                    weighted_lactose_sum = sum(lactose * milk for lactose, milk in cow_lactose_values)
                    cow_avg = weighted_lactose_sum / cow_total_milk
                    row_data['平均乳糖率(%)'] = round(cow_avg, 2)
                else:
                    row_data['平均乳糖率(%)'] = None
            
            # 4. 添加最后一个月的泌乳天数
            if last_lactation_days is not None:
                try:
                    last_lactation_days = int(float(last_lactation_days))
                except (ValueError, TypeError):
                    last_lactation_days = None
            row_data['最后一个月泌乳天数(天)'] = last_lactation_days
            
            # 5. 添加最后一次采样日
            last_sample_date = None
            if monthly_data:
                # 找到最后一次采样的日期
                sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[1]['date'])
                if sorted_monthly:
                    last_sample_date = sorted_monthly[-1][1]['date'].strftime('%Y-%m-%d')
            row_data['最后一次采样日'] = last_sample_date
            
            # 6. 添加未来泌乳天数
            future_lactation_days = None
            
            # 首先尝试从已有记录中获取
            for _, record in group.iterrows():
                if 'future_lactation_days' in record and pd.notna(record['future_lactation_days']):
                    future_lactation_days = int(record['future_lactation_days'])
                    break
            
            # 如果没有现成的未来泌乳天数，且有计划调群日，则计算
            if future_lactation_days is None and plan_date and last_sample_date and last_lactation_days is not None:
                try:
                    plan_datetime = pd.to_datetime(plan_date)
                    last_sample_datetime = pd.to_datetime(last_sample_date)
                    days_diff = (plan_datetime - last_sample_datetime).days
                    calculated_days = int(days_diff + last_lactation_days)
                    if calculated_days > 0:
                        future_lactation_days = calculated_days
                        logger.debug(f"计算未来泌乳天数: 牛场{farm_id}-管理号{mgmt_id}, 计划日{plan_date}, 最后采样{last_sample_date}, 差{days_diff}天, 最后泌乳{last_lactation_days}天, 未来{future_lactation_days}天")
                except Exception as e:
                    logger.warning(f"计算未来泌乳天数失败: {e}")
            
            row_data['未来泌乳天数(天)'] = future_lactation_days
            
            result_rows.append(row_data)
        
        result_df = pd.DataFrame(result_rows)
        
        # 重新排序列以确保正确的顺序
        if not result_df.empty:
            # 构建正确的列顺序
            ordered_columns = ['farm_id', 'management_id', 'parity']
            
            # 定义字段的中文名称映射（与上面保持一致）
            field_chinese_map = {
                'protein_pct': '蛋白率(%)',
                'fat_pct': '乳脂率(%)',
                'fat_protein_ratio': '脂蛋比',
                'somatic_cell_count': '体细胞数(万/ml)',
                'somatic_cell_score': '体细胞分',
                'urea_nitrogen': '尿素氮(mg/dl)',
                'lactose_pct': '乳糖率',
                'milk_loss': '奶损失(Kg)',
                'milk_payment_diff': '奶款差',
                'economic_loss': '经济损失',
                'corrected_milk': '校正奶(Kg)',
                'persistency': '持续力',
                'whi': 'WHI',
                'fore_milk_yield': '前奶量(Kg)',
                'fore_somatic_cell_count': '前体细胞(万/ml)',
                'fore_somatic_cell_score': '前体细胞分',
                'fore_milk_loss': '前奶损失(Kg)',
                'peak_milk_yield': '高峰奶(Kg)',
                'peak_days': '高峰日(天)',
                'milk_305': '305奶量(Kg)',
                'total_milk_yield': '总奶量(Kg)',
                'total_fat_pct': '总乳脂(%)',
                'total_protein_pct': '总蛋白(%)',
                'mature_equivalent': '成年当量(Kg)',
                'milk_yield': '产奶量(Kg)',
                'lactation_days': '泌乳天数(天)'
            }
            
            # 添加月度列（按时间顺序，按display_fields中的字段顺序）
            for year_month in sorted_month_names:
                for field in display_fields:
                    if field in ['farm_id', 'management_id', 'parity']:
                        continue  # 跳过基础字段
                    
                    if field in field_chinese_map:
                        chinese_name = field_chinese_map[field]
                        column_name = f"{year_month}{chinese_name}"
                        ordered_columns.append(column_name)
            
            # 添加最后的汇总列（动态添加）
            summary_columns = []
            if 'protein_pct' in display_fields:
                summary_columns.append('平均蛋白率(%)')
            if 'fat_pct' in display_fields:
                summary_columns.append('平均乳脂率(%)')
            if 'lactose_pct' in display_fields:
                summary_columns.append('平均乳糖率(%)')
            if 'lactation_days' in display_fields:
                summary_columns.append('最后一个月泌乳天数(天)')
            summary_columns.append('最后一次采样日')
            summary_columns.append('未来泌乳天数(天)')
            
            # 只添加实际存在的汇总列
            for col in summary_columns:
                if col in result_df.columns:
                    ordered_columns.append(col)
            
            # 重新排序DataFrame的列
            available_columns = [col for col in ordered_columns if col in result_df.columns]
            result_df = result_df[available_columns]
        
        # 计算所有月份的加权总平均值，存储为DataFrame属性
        # 蛋白率总平均值
        if all_protein_milk_pairs and all_total_milk > 0:
            weighted_overall_sum = sum(protein * milk for protein, milk in all_protein_milk_pairs)
            overall_avg = weighted_overall_sum / all_total_milk
            result_df.attrs['overall_protein_avg'] = round(overall_avg, 2)
        else:
            result_df.attrs['overall_protein_avg'] = None
        
        # 乳脂率总平均值
        if all_fat_milk_pairs and all_total_milk > 0:
            weighted_overall_sum = sum(fat * milk for fat, milk in all_fat_milk_pairs)
            overall_avg = weighted_overall_sum / all_total_milk
            result_df.attrs['overall_fat_avg'] = round(overall_avg, 2)
        else:
            result_df.attrs['overall_fat_avg'] = None
        
        # 乳糖率总平均值
        if all_lactose_milk_pairs and all_total_milk > 0:
            weighted_overall_sum = sum(lactose * milk for lactose, milk in all_lactose_milk_pairs)
            overall_avg = weighted_overall_sum / all_total_milk
            result_df.attrs['overall_lactose_avg'] = round(overall_avg, 2)
        else:
            result_df.attrs['overall_lactose_avg'] = None
        
        # 计算胎次平均值
        if not result_df.empty and 'parity' in result_df.columns:
            parity_data = result_df['parity'].dropna()
            if not parity_data.empty:
                result_df.attrs['parity_avg'] = round(parity_data.mean(), 1)
            else:
                result_df.attrs['parity_avg'] = None
        else:
            result_df.attrs['parity_avg'] = None
        
        # 计算各月份所有启用字段的平均值
        monthly_averages = {}
        if not result_df.empty:
            # 重新定义字段的中文名称映射
            field_chinese_map = {
                'protein_pct': '蛋白率(%)',
                'somatic_cell_count': '体细胞数(万/ml)',
                'fat_pct': '乳脂率(%)',
                'lactose_pct': '乳糖率(%)',
                'milk_yield': '产奶量(Kg)',
                'lactation_days': '泌乳天数(天)',
                'solids_pct': '固形物(%)',
                'fat_protein_ratio': '脂蛋比',
                'urea_nitrogen': '尿素氮(mg/dl)',
                'total_fat_pct': '总乳脂(%)',
                'total_protein_pct': '总蛋白(%)',
                'mature_equivalent': '成年当量(Kg)'
            }
            
            for year_month in sorted_month_names:
                for field in display_fields:
                    if field in ['farm_id', 'management_id', 'parity']:
                        continue  # 跳过基础字段
                    
                    if field in field_chinese_map:
                        chinese_name = field_chinese_map[field]
                        column_name = f"{year_month}{chinese_name}"
                        
                        if column_name in result_df.columns:
                            month_data = result_df[column_name].dropna()
                            
                            if not month_data.empty:
                                # 特殊处理：蛋白率使用加权平均（如果有产奶量数据）
                                if field == 'protein_pct':
                                    milk_col = f"{year_month}产奶量(Kg)"
                                    if milk_col in result_df.columns:
                                        # 使用产奶量加权平均
                                        try:
                                            combined_data = result_df[[column_name, milk_col]].dropna()
                                            if not combined_data.empty:
                                                weighted_sum = (combined_data[column_name] * combined_data[milk_col]).sum()
                                                total_milk = combined_data[milk_col].sum()
                                                if total_milk > 0:
                                                    monthly_averages[column_name] = round(weighted_sum / total_milk, 2)
                                                else:
                                                    monthly_averages[column_name] = None
                                            else:
                                                monthly_averages[column_name] = None
                                        except Exception as e:
                                            logger.warning(f"计算{column_name}加权平均失败: {e}")
                                            monthly_averages[column_name] = round(month_data.mean(), 2)
                                    else:
                                        # 没有产奶量数据，使用简单平均
                                        monthly_averages[column_name] = round(month_data.mean(), 2)
                                
                                # 其他字段使用简单平均
                                else:
                                    if field in ['milk_yield', 'mature_equivalent']:
                                        # 产奶量等保留1位小数
                                        monthly_averages[column_name] = round(month_data.mean(), 1)
                                    elif field in ['lactation_days']:
                                        # 泌乳天数保留1位小数
                                        monthly_averages[column_name] = round(month_data.mean(), 1)
                                    elif field in ['somatic_cell_count', 'urea_nitrogen']:
                                        # 体细胞数、尿素氮保留1位小数
                                        monthly_averages[column_name] = round(month_data.mean(), 1)
                                    else:
                                        # 其他比例类数据保留2位小数
                                        monthly_averages[column_name] = round(month_data.mean(), 2)
                            else:
                                monthly_averages[column_name] = None
        
        result_df.attrs['monthly_averages'] = monthly_averages
        
        # 如果启用了在群牛筛选，添加在群牛胎次列
        if self.active_cattle_enabled and not result_df.empty:
            logger.info("添加在群牛胎次信息")
            
            # 为每头牛添加在群牛胎次（最后一次采样时的胎次）
            result_df['在群牛胎次'] = result_df['parity']
            
            # 重新排序列，将在群牛胎次放在胎次后面
            if 'parity' in result_df.columns:
                columns = list(result_df.columns)
                # 找到parity的位置
                parity_index = columns.index('parity')
                # 移除在群牛胎次，然后插入到parity后面
                columns.remove('在群牛胎次')
                columns.insert(parity_index + 1, '在群牛胎次')
                result_df = result_df[columns]
                
                logger.info(f"已添加在群牛胎次列，共{len(result_df)}头在群牛")
        
        return result_df
    
    def detect_duplicate_data(self, data_list: List[Dict]) -> Dict[str, Any]:
        """检测重复数据：文件名不同但内容相同或高度相似
        
        Returns:
            检测结果字典，包含重复组信息
        """
        logger.info("开始检测重复数据")
        
        duplicate_groups = []
        processed_indices = set()
        
        for i, item1 in enumerate(data_list):
            if i in processed_indices:
                continue
                
            df1 = item1['data']
            filename1 = item1['filename']
            
            # 跳过空数据
            if df1.empty:
                continue
            
            current_group = [{'index': i, 'filename': filename1, 'data': df1}]
            
            for j, item2 in enumerate(data_list):
                if j <= i or j in processed_indices:
                    continue
                    
                df2 = item2['data']
                filename2 = item2['filename']
                
                # 跳过空数据
                if df2.empty:
                    continue
                
                # 检测数据相似度
                similarity = self._calculate_data_similarity(df1, df2)
                
                if similarity['is_duplicate']:
                    current_group.append({
                        'index': j, 
                        'filename': filename2, 
                        'data': df2,
                        'similarity_score': similarity['score'],
                        'details': similarity['details']
                    })
                    processed_indices.add(j)
            
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
                processed_indices.add(i)
        
        result = {
            'has_duplicates': len(duplicate_groups) > 0,
            'duplicate_groups': duplicate_groups,
            'total_files': len(data_list),
            'duplicate_files_count': sum(len(group) for group in duplicate_groups)
        }
        
        logger.info(f"重复数据检测完成: 发现{len(duplicate_groups)}组重复，涉及{result['duplicate_files_count']}个文件")
        
        return result
    
    def _calculate_data_similarity(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
        """计算两个DataFrame的相似度"""
        
        # 基础检查
        if df1.empty or df2.empty:
            return {'is_duplicate': False, 'score': 0.0, 'details': 'Empty dataframe'}
        
        details = {}
        similarity_scores = []
        
        # 1. 检查数据行数相似度
        row_count_diff = abs(len(df1) - len(df2))
        max_rows = max(len(df1), len(df2))
        row_similarity = 1.0 - (row_count_diff / max_rows) if max_rows > 0 else 0.0
        details['row_count'] = {
            'df1_rows': len(df1),
            'df2_rows': len(df2),
            'similarity': row_similarity
        }
        similarity_scores.append(row_similarity * 0.2)  # 20% 权重
        
        # 2. 检查关键字段的数据重叠度
        key_fields = ['farm_id', 'management_id', 'sample_date', 'protein_pct']
        field_similarities = {}
        
        for field in key_fields:
            if field in df1.columns and field in df2.columns:
                # 对于关键标识字段，检查唯一值重叠度
                if field in ['farm_id', 'management_id']:
                    values1 = set(df1[field].dropna().astype(str))
                    values2 = set(df2[field].dropna().astype(str))
                    
                    if values1 and values2:
                        overlap = len(values1 & values2)
                        union = len(values1 | values2)
                        field_sim = overlap / union if union > 0 else 0.0
                    else:
                        field_sim = 0.0
                
                # 对于日期字段，检查日期范围重叠
                elif field == 'sample_date':
                    try:
                        dates1 = pd.to_datetime(df1[field], errors='coerce').dropna()
                        dates2 = pd.to_datetime(df2[field], errors='coerce').dropna()
                        
                        if len(dates1) > 0 and len(dates2) > 0:
                            range1 = (dates1.min(), dates1.max())
                            range2 = (dates2.min(), dates2.max())
                            
                            # 计算日期范围重叠度
                            overlap_start = max(range1[0], range2[0])
                            overlap_end = min(range1[1], range2[1])
                            
                            if overlap_start <= overlap_end:
                                overlap_days = (overlap_end - overlap_start).days + 1
                                total_days = max((range1[1] - range1[0]).days + 1, (range2[1] - range2[0]).days + 1)
                                field_sim = overlap_days / total_days if total_days > 0 else 0.0
                            else:
                                field_sim = 0.0
                        else:
                            field_sim = 0.0
                    except:
                        field_sim = 0.0
                
                # 对于数值字段，检查分布相似度
                else:
                    try:
                        values1 = df1[field].dropna()
                        values2 = df2[field].dropna()
                        
                        if len(values1) > 0 and len(values2) > 0:
                            # 使用统计特征比较
                            stats1 = (values1.mean(), values1.std(), values1.min(), values1.max())
                            stats2 = (values2.mean(), values2.std(), values2.min(), values2.max())
                            
                            # 计算统计特征的相似度
                            stat_similarities = []
                            for s1, s2 in zip(stats1, stats2):
                                if pd.notna(s1) and pd.notna(s2) and max(abs(s1), abs(s2)) > 0:
                                    diff = abs(s1 - s2) / max(abs(s1), abs(s2))
                                    stat_similarities.append(1.0 - min(diff, 1.0))
                                else:
                                    stat_similarities.append(1.0 if pd.isna(s1) and pd.isna(s2) else 0.0)
                            
                            field_sim = sum(stat_similarities) / len(stat_similarities) if stat_similarities else 0.0
                        else:
                            field_sim = 1.0 if len(values1) == 0 and len(values2) == 0 else 0.0
                    except:
                        field_sim = 0.0
                
                field_similarities[field] = field_sim
        
        details['field_similarities'] = field_similarities
        
        # 3. 计算加权平均相似度
        if field_similarities:
            # 不同字段的权重
            field_weights = {
                'farm_id': 0.15,
                'management_id': 0.25,
                'sample_date': 0.25,
                'protein_pct': 0.15
            }
            
            weighted_sum = 0.0
            total_weight = 0.0
            
            for field, similarity in field_similarities.items():
                weight = field_weights.get(field, 0.1)
                weighted_sum += similarity * weight
                total_weight += weight
            
            field_similarity_score = weighted_sum / total_weight if total_weight > 0 else 0.0
            similarity_scores.append(field_similarity_score * 0.8)  # 80% 权重
        
        # 4. 计算最终相似度分数
        final_score = sum(similarity_scores)
        
        # 5. 判断是否为重复数据
        # 阈值：相似度超过85%认为是重复数据
        is_duplicate = final_score > 0.85
        
        details['final_score'] = final_score
        details['threshold'] = 0.85
        
        return {
            'is_duplicate': is_duplicate,
            'score': final_score,
            'details': details
        }

    def _get_field_chinese_name(self, field: str) -> str:
        """获取字段的中文名称"""
        # 直接映射常用字段
        field_chinese_map = {
            'protein_pct': '蛋白率(%)',
            'fat_pct': '乳脂率(%)',
            'lactose_pct': '乳糖率(%)',
            'solids_pct': '固形物(%)',
            'milk_yield': '产奶量',
            'lactation_days': '泌乳天数(天)',
            'farm_id': '牛场编号',
            'management_id': '管理号',
            'parity': '胎次',
            'sample_date': '采样日期',
            'last_sample_date': '最后一次采样日'
        }
        
        if field in field_chinese_map:
            return field_chinese_map[field]
        
        # 从rules.yaml获取映射
        field_map = self.rules.get("field_map", {})
        for chinese_name, english_name in field_map.items():
            if english_name == field:
                return chinese_name
        
        return field
    
    def debug_zip_processing(self, zip_path: str, filename: str) -> Dict:
        """调试ZIP文件处理过程"""
        debug_info = {"processing_steps": []}
        target_files = self.rules.get("file_ingest", {}).get("internal_targets", [
            "04-2综合测定结果表.xlsx",
            "04-2综合测定结果表.xls", 
            "04综合测定结果表.xlsx",
            "04综合测定结果表.xls",
            "综合测定结果表.xlsx",
            "综合测定结果表.xls"
        ])
        
        # 获取需要排除的文件名列表
        excluded_files = self.rules.get("file_ingest", {}).get("excluded_files", [])
        
        try:
            # 步骤2：解析ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                debug_info["processing_steps"].append({
                    "step": "2. 解析ZIP文件",
                    "success": True,
                    "zip_files": [str(f) for f in file_list],
                    "target_files": [str(f) for f in target_files],
                    "excluded_files": [str(f) for f in excluded_files],
                    "target_found": any(f in target_files and f not in excluded_files for f in file_list)
                })
                
                # 步骤3：提取文件
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # 查找Excel文件（排除excluded_files）
                    excel_files = []
                    target_path = None
                    
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith(('.xlsx', '.xls')):
                                if file not in excluded_files:
                                    excel_files.append(file)
                                    if file in target_files:
                                        target_path = os.path.join(root, file)
                    
                    debug_info["processing_steps"].append({
                        "step": "3. 查找Excel文件",
                        "excel_files_found": [str(f) for f in excel_files],
                        "target_file_path": str(target_path) if target_path else None,
                        "temp_dir": str(temp_dir)
                    })
                    
                    # 步骤4：处理Excel文件
                    if target_path:
                        excel_debug = self.debug_excel_processing(target_path, target_path.split('/')[-1])
                        debug_info["processing_steps"].extend(excel_debug["processing_steps"])
                    elif excel_files:
                        # 尝试第一个Excel文件
                        first_excel = excel_files[0]
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                if file == first_excel:
                                    excel_debug = self.debug_excel_processing(os.path.join(root, file), first_excel)
                                    debug_info["processing_steps"].extend(excel_debug["processing_steps"])
                                    break
                            break
                    else:
                        debug_info["processing_steps"].append({
                            "step": "4. 处理Excel文件",
                            "success": False,
                            "error": "未找到任何Excel文件"
                        })
        
        except Exception as e:
            debug_info["processing_steps"].append({
                "step": "ZIP处理错误",
                "success": False,
                "error": str(e)
            })
        
        return debug_info
    
    def debug_excel_processing(self, excel_path: str, filename: str) -> Dict:
        """调试Excel文件处理过程"""
        debug_info = {"processing_steps": []}
        
        try:
            # 步骤4：读取Excel文件
            df = pd.read_excel(excel_path)
            
            # 清理数据以避免JSON序列化问题
            df_clean = df.copy()
            
            # 替换NaN和无穷大值
            df_clean = df_clean.replace([float('inf'), float('-inf')], None)
            df_clean = df_clean.where(pd.notna(df_clean), None)
            
            # 获取前几行数据，确保可以JSON序列化
            sample_rows = []
            if len(df_clean) > 0:
                for _, row in df_clean.head(3).iterrows():
                    clean_row = {}
                    for col, val in row.items():
                        if pd.isna(val) or val in [float('inf'), float('-inf')]:
                            clean_row[str(col)] = None
                        elif isinstance(val, (int, float)) and (val != val):  # 检查NaN
                            clean_row[str(col)] = None
                        else:
                            clean_row[str(col)] = str(val) if not isinstance(val, (int, float, bool, type(None))) else val
                    sample_rows.append(clean_row)
            
            debug_info["processing_steps"].append({
                "step": "4. 读取Excel文件",
                "success": True,
                "shape": df.shape,
                "columns": [str(col) for col in df.columns],
                "first_few_rows": sample_rows
            })
            
            # 步骤5：检查表头映射
            field_map = self.rules.get("field_map", {})
            required_columns = ['管理号', '胎次(胎)', '采样日期']  # 移除牛场编号的强制要求
            
            # 确保field_map可以JSON序列化
            clean_field_map = {}
            for k, v in field_map.items():
                clean_field_map[str(k)] = str(v)
            
            mapping_info = {
                "step": "5. 检查表头映射",
                "field_map": clean_field_map,
                "required_columns": [str(col) for col in required_columns],
                "missing_columns": [],
                "available_mappings": {}
            }
            
            for req_col in required_columns:
                if req_col in df.columns:
                    if req_col in field_map:
                        mapping_info["available_mappings"][str(req_col)] = str(field_map[req_col])
                else:
                    mapping_info["missing_columns"].append(str(req_col))
            
            debug_info["processing_steps"].append(mapping_info)
            
            # 步骤6：数据重命名和转换
            if not mapping_info["missing_columns"]:
                rename_dict = {}
                for chinese_col, english_col in field_map.items():
                    if chinese_col in df.columns:
                        rename_dict[chinese_col] = english_col
                
                df_renamed = df.rename(columns=rename_dict)
                
                # 确保重命名字典可以JSON序列化
                clean_rename_dict = {}
                for k, v in rename_dict.items():
                    clean_rename_dict[str(k)] = str(v)
                
                debug_info["processing_steps"].append({
                    "step": "6. 重命名列",
                    "success": True,
                    "rename_dict": clean_rename_dict,
                    "new_columns": [str(col) for col in df_renamed.columns]
                })
                
                # 步骤7：数据类型转换
                conversion_info = {
                    "step": "7. 数据类型转换",
                    "conversions": {}
                }
                
                # 检查关键字段
                if 'farm_id' in df_renamed.columns:
                    farm_ids = df_renamed['farm_id'].dropna().unique()
                    # 确保farm_ids可以JSON序列化
                    clean_farm_ids = []
                    for fid in farm_ids:
                        if pd.notna(fid):
                            clean_farm_ids.append(str(fid))
                    
                    conversion_info["conversions"]["farm_id"] = {
                        "unique_values": clean_farm_ids,
                        "count": len(clean_farm_ids),
                        "sample_values": clean_farm_ids[:5]
                    }
                
                if 'sample_date' in df_renamed.columns:
                    sample_dates = df_renamed['sample_date'].dropna()
                    if len(sample_dates) > 0:
                        date_converted = pd.to_datetime(sample_dates, errors='coerce').dropna()
                        if len(date_converted) > 0:
                            date_range_str = f"{date_converted.min()} - {date_converted.max()}"
                        else:
                            date_range_str = "无有效日期"
                        
                        conversion_info["conversions"]["sample_date"] = {
                            "original_count": len(sample_dates),
                            "converted_count": len(date_converted),
                            "date_range": date_range_str
                        }
                
                debug_info["processing_steps"].append(conversion_info)
                
            else:
                debug_info["processing_steps"].append({
                    "step": "6-7. 跳过后续处理",
                    "reason": f"缺失必要列: {mapping_info['missing_columns']}"
                })
        
        except Exception as e:
            debug_info["processing_steps"].append({
                "step": "Excel处理错误",
                "success": False,
                "error": str(e)
            })
        
        return debug_info 
    
    def apply_multi_filter_logic(self, data_list: List[Dict], filters: Dict[str, Any], selected_files: List[str], progress_callback=None, should_stop=None) -> pd.DataFrame:
        """应用新的多筛选项逻辑：每个筛选项独立计算，所有启用的筛选项都必须符合（优化版本）
        
        Args:
            data_list: 数据列表
            filters: 筛选条件字典
            selected_files: 选中的文件列表
            progress_callback: 进度回调函数
            should_stop: 停止检查函数
            
        Returns:
            筛选后的DataFrame
        """
        # 筛选选中的文件
        selected_data = [item for item in data_list if item['filename'] in selected_files]
        
        if not selected_data:
            return pd.DataFrame()
        
        logger.info(f"开始多筛选项逻辑处理（优化版本），已选择{len(selected_data)}个文件")
        
        # 检查是否应该停止
        if should_stop and should_stop():
            logger.info("筛选被用户取消")
            return pd.DataFrame()
        
        if progress_callback:
            progress_callback("🚀 合并数据文件（优化版本）...", 26)
        
        # 合并所有数据
        all_dfs = []
        all_months = set()
        
        for i, item in enumerate(selected_data):
            if should_stop and should_stop():
                logger.info("筛选被用户取消")
                return pd.DataFrame()
                
            df = item['data'].copy()
            df['source_file'] = item['filename']
            
            # 确保关键字段为字符串类型，保持数据一致性
            for field in ['farm_id', 'management_id']:
                if field in df.columns:
                    df[field] = df[field].astype(str)
                    # 移除'nan'字符串，转换为None
                    df.loc[df[field] == 'nan', field] = None
            
            # 添加年月列
            if 'sample_date' in df.columns:
                df['year_month'] = pd.to_datetime(df['sample_date']).dt.strftime('%Y-%m')
                # 收集所有月份
                months = df['year_month'].dropna().unique()
                all_months.update(months)
            
            all_dfs.append(df)
            
            # 更新进度
            if progress_callback:
                file_progress = 26 + int((i + 1) / len(selected_data) * 5)  # 26-31%
                progress_callback(f"🚀 处理文件 {i+1}/{len(selected_data)}: {item['filename']}", file_progress)
        
        if progress_callback:
            progress_callback("🚀 合并数据...", 32)
        
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # 合并后再次确保字符串字段类型一致性
        for field in ['farm_id', 'management_id']:
            if field in combined_df.columns:
                combined_df[field] = combined_df[field].astype(str)
                combined_df.loc[combined_df[field] == 'nan', field] = None
        
        logger.info(f"合并数据：共{len(combined_df)}行，覆盖月份：{sorted(all_months)}")
        
        if progress_callback:
            progress_callback("🚀 应用基础筛选条件...", 33)
        
        # 检查是否应该停止
        if should_stop and should_stop():
            logger.info("筛选被用户取消")
            return pd.DataFrame()
        
        # 应用基础筛选条件（牛场、胎次、日期等）
        base_filters = {}
        for filter_name, filter_config in filters.items():
            if filter_name in ['farm_id', 'parity', 'date_range']:
                if filter_config.get('enabled', False):
                    # 检查farm_id字段是否存在
                    if filter_name == 'farm_id':
                        field = filter_config.get('field', 'farm_id')
                        if field not in combined_df.columns:
                            logger.warning(f"跳过{filter_name}筛选：字段{field}不存在")
                            continue
                    base_filters[filter_name] = filter_config
        
        # 应用基础筛选
        base_filtered_df = self.apply_filters(combined_df, base_filters)
        logger.info(f"基础筛选后：共{len(base_filtered_df)}行")
        
        if base_filtered_df.empty:
            return pd.DataFrame()
        
        # 检查必要字段 - 只需要management_id，farm_id是可选的
        if 'management_id' not in base_filtered_df.columns:
            return base_filtered_df
        
        # 收集启用的特殊筛选项（蛋白率、体细胞数等）
        special_filters = {}
        for filter_name, filter_config in filters.items():
            if (filter_name not in ['farm_id', 'parity', 'date_range', 'future_lactation_days'] and 
                isinstance(filter_config, dict) and 
                filter_config.get('enabled', False)):
                special_filters[filter_name] = filter_config
        
        if not special_filters:
            logger.info("没有启用的特殊筛选项，返回基础筛选结果")
            return base_filtered_df
        
        logger.info(f"启用的特殊筛选项: {list(special_filters.keys())}")
        
        # 使用向量化方法进行高速筛选
        return self._apply_vectorized_multi_filters(
            base_filtered_df, special_filters, list(all_months), 
            progress_callback, should_stop
        )
    
    def _apply_vectorized_multi_filters(self, df: pd.DataFrame, special_filters: Dict, all_months: List[str], progress_callback=None, should_stop=None) -> pd.DataFrame:
        """使用向量化操作应用多筛选项逻辑（高性能版本）
        
        Args:
            df: 基础筛选后的DataFrame
            special_filters: 特殊筛选项配置
            all_months: 所有月份列表
            progress_callback: 进度回调函数
            should_stop: 停止检查函数
            
        Returns:
            筛选后的DataFrame
        """
        if progress_callback:
            progress_callback("🚀 开始向量化筛选（高速模式）...", 35)
        
        # 获取所有牛只
        if 'farm_id' in df.columns:
            all_cows = df[['farm_id', 'management_id']].drop_duplicates()
            # 为每头牛创建唯一标识
            df['cow_id'] = df['farm_id'].astype(str) + '_' + df['management_id'].astype(str)
        else:
            all_cows = df[['management_id']].drop_duplicates()
            # 为每头牛创建唯一标识
            df['cow_id'] = df['management_id'].astype(str)
        logger.info(f"筛选范围内共有{len(all_cows)}头牛，将使用向量化处理")
        all_cow_ids = set(df['cow_id'].unique())
        
        if progress_callback:
            progress_callback("🚀 预处理数据结构...", 40)
        
        # 预处理：为每个筛选项创建符合条件的掩码
        filter_masks = {}
        
        for i, (filter_name, filter_config) in enumerate(special_filters.items()):
            if should_stop and should_stop():
                logger.info("筛选被用户取消")
                return pd.DataFrame()
            
            field = filter_config.get('field')
            min_val = filter_config.get('min', 0)
            max_val = filter_config.get('max', 100)
            min_match_months = filter_config.get('min_match_months', 3)
            treat_empty_as_match = filter_config.get('treat_empty_as_match', False)
            
            if not field or field not in df.columns:
                logger.warning(f"跳过筛选项{filter_name}：字段{field}不存在")
                continue
            
            if progress_callback:
                filter_progress = 40 + int((i / len(special_filters)) * 30)  # 40-70%
                progress_callback(f"🚀 处理筛选项: {filter_name}", filter_progress)
            
            # 创建数值范围掩码（向量化操作）
            numeric_values = pd.to_numeric(df[field], errors='coerce')
            value_mask = (numeric_values >= min_val) & (numeric_values <= max_val)
            
            # 处理空值逻辑
            if treat_empty_as_match:
                # 空值被视为符合条件
                empty_mask = df[field].isna() | (df[field] == '')
                condition_mask = value_mask | empty_mask
            else:
                # 空值不符合条件
                condition_mask = value_mask & df[field].notna()
            
            # 为符合条件的记录添加标记
            df[f'{filter_name}_match'] = condition_mask
            
            # 计算每头牛每个月的符合情况（使用groupby向量化操作）
            if progress_callback:
                progress_callback(f"🚀 统计月度符合情况: {filter_name}", filter_progress + 3)
            
            # 按牛只和月份分组，计算每月是否有符合条件的记录
            monthly_matches = df.groupby(['cow_id', 'year_month'])[f'{filter_name}_match'].any().reset_index()
            
            # 计算每头牛的符合月数
            cow_match_counts = monthly_matches.groupby('cow_id')[f'{filter_name}_match'].sum().reset_index()
            cow_match_counts.columns = ['cow_id', f'{filter_name}_count']
            
            # 处理没有数据的月份（如果treat_empty_as_match为True）
            if treat_empty_as_match:
                # 为每头牛添加所有月份，缺失的月份视为符合
                all_cow_month_combinations = pd.MultiIndex.from_product(
                    [all_cow_ids, all_months], 
                    names=['cow_id', 'year_month']
                ).to_frame(index=False)
                
                # 左连接，缺失的会被填充为False
                complete_monthly = all_cow_month_combinations.merge(
                    monthly_matches, on=['cow_id', 'year_month'], how='left'
                )
                complete_monthly[f'{filter_name}_match'] = complete_monthly[f'{filter_name}_match'].fillna(True)
                
                # 重新计算符合月数
                cow_match_counts = complete_monthly.groupby('cow_id')[f'{filter_name}_match'].sum().reset_index()
                cow_match_counts.columns = ['cow_id', f'{filter_name}_count']
            
            # 创建通过此筛选项的牛只掩码
            passing_cows = cow_match_counts[cow_match_counts[f'{filter_name}_count'] >= min_match_months]['cow_id']
            filter_masks[filter_name] = set(passing_cows)
            
            logger.info(f"筛选项{filter_name}: {len(passing_cows)}头牛通过（需要{min_match_months}个月，treat_empty_as_match={treat_empty_as_match}）")
        
        if progress_callback:
            progress_callback("🚀 合并筛选结果...", 70)
        
        # 检查是否应该停止
        if should_stop and should_stop():
            logger.info("筛选被用户取消")
            return pd.DataFrame()
        
        # 找出通过所有筛选项的牛只（集合交集操作）
        if filter_masks:
            valid_cow_ids = set.intersection(*filter_masks.values())
            logger.info(f"通过所有{len(special_filters)}个筛选项的牛：{len(valid_cow_ids)}头")
        else:
            valid_cow_ids = all_cow_ids
            logger.info("没有有效的筛选项，返回所有牛")
        
        if progress_callback:
            progress_callback("🚀 提取最终结果...", 85)
        
        # 返回符合条件的牛的所有数据（向量化筛选）
        if valid_cow_ids:
            result_df = df[df['cow_id'].isin(valid_cow_ids)].copy()
            
            # 清理临时列
            cols_to_drop = ['cow_id'] + [col for col in result_df.columns if col.endswith('_match')]
            result_df = result_df.drop(columns=cols_to_drop, errors='ignore')
            
            if progress_callback:
                progress_callback("🚀 向量化筛选完成", 90)
                
            logger.info(f"最终结果：{len(result_df)}行数据，来自{len(valid_cow_ids)}头牛")
            return result_df
        
        if progress_callback:
            progress_callback("🚀 向量化筛选完成（无符合条件的牛）", 90)
            
        return pd.DataFrame()
    
    def check_farm_id_consistency(self, data_list: List[Dict]) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """检查所有文件的牧场编号一致性
        
        Args:
            data_list: 包含数据的文件列表
            
        Returns:
            (is_consistent, all_farm_ids, farm_id_files_map)
            - is_consistent: 是否一致
            - all_farm_ids: 所有发现的牧场编号列表
            - farm_id_files_map: 牧场编号到文件列表的映射
        """
        farm_id_files_map = {}
        all_farm_ids = set()
        
        for item in data_list:
            filename = item['filename']
            df = item['data']
            
            if 'farm_id' in df.columns:
                # 获取该文件的所有牧场编号
                file_farm_ids = df['farm_id'].dropna().astype(str).unique()
                file_farm_ids = [fid for fid in file_farm_ids if fid and fid != 'nan']
                
                for farm_id in file_farm_ids:
                    all_farm_ids.add(farm_id)
                    if farm_id not in farm_id_files_map:
                        farm_id_files_map[farm_id] = []
                    farm_id_files_map[farm_id].append(filename)
        
        all_farm_ids_list = sorted(list(all_farm_ids))
        is_consistent = len(all_farm_ids_list) <= 1
        
        logger.info(f"牧场编号一致性检查: 发现{len(all_farm_ids_list)}个不同的牧场编号")
        for farm_id, files in farm_id_files_map.items():
            logger.info(f"  牧场{farm_id}: {len(files)}个文件 - {files[:3]}{'...' if len(files) > 3 else ''}")
        
        return is_consistent, all_farm_ids_list, farm_id_files_map
    
    def unify_farm_ids(self, data_list: List[Dict], target_farm_id: str) -> List[Dict]:
        """统一所有数据的牧场编号
        
        Args:
            data_list: 数据列表
            target_farm_id: 目标牧场编号
            
        Returns:
            更新后的数据列表
        """
        updated_data_list = []
        total_updated_records = 0
        
        for item in data_list:
            df = item['data'].copy()
            filename = item['filename']
            
            if 'farm_id' in df.columns:
                # 统计更新前的记录数
                original_records = len(df[df['farm_id'].notna()])
                
                # 将所有非空的牧场编号更新为目标牧场编号
                df.loc[df['farm_id'].notna(), 'farm_id'] = target_farm_id
                
                # 统计更新后的记录数
                updated_records = len(df[df['farm_id'] == target_farm_id])
                total_updated_records += updated_records
                
                logger.info(f"文件{filename}: 更新了{original_records}条记录的牧场编号为{target_farm_id}")
            
            # 创建新的数据项
            updated_item = item.copy()
            updated_item['data'] = df
            updated_data_list.append(updated_item)
        
        logger.info(f"牧场编号统一完成: 总共更新了{total_updated_records}条记录为牧场{target_farm_id}")
        return updated_data_list
    
    def get_data_ranges(self, data_list: List[Dict]) -> Dict[str, Dict]:
        """计算上传数据中各个性状的数值范围和月数范围
        
        Args:
            data_list: 数据列表
            
        Returns:
            包含各字段范围信息的字典
        """
        if not data_list:
            return {}
        
        # 合并所有数据
        all_dfs = []
        all_months = set()
        
        for item in data_list:
            df = item['data'].copy()
            
            # 收集所有月份
            if 'sample_date' in df.columns:
                df['year_month'] = pd.to_datetime(df['sample_date'], errors='coerce').dt.strftime('%Y-%m')
                months = df['year_month'].dropna().unique()
                all_months.update(months)
            
            all_dfs.append(df)
        
        combined_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        
        ranges = {}
        
        # 计算月数范围
        ranges['months'] = {
            'min': 0,
            'max': len(all_months),
            'description': f'数据跨越{len(all_months)}个月'
        }
        
        # 定义需要计算范围的数值字段
        numeric_fields = [
            'protein_pct', 'fat_pct', 'lactose_pct', 'solids_pct', 
            'milk_yield', 'lactation_days', 'somatic_cell_count',
            'fat_protein_ratio', 'somatic_cell_score', 'urea_nitrogen',
            'freezing_point', 'total_bacterial_count', 'dry_matter_intake',
            'net_energy_lactation', 'metabolizable_protein', 'crude_protein',
            'neutral_detergent_fiber', 'acid_detergent_fiber', 'starch',
            'ether_extract', 'ash', 'calcium', 'phosphorus', 'magnesium',
            'sodium', 'potassium', 'sulfur'
        ]
        
        for field in numeric_fields:
            if field in combined_df.columns:
                try:
                    # 尝试转换为数值类型
                    numeric_data = pd.to_numeric(combined_df[field], errors='coerce').dropna()
                    
                    if len(numeric_data) > 0:
                        min_val = float(numeric_data.min())
                        max_val = float(numeric_data.max())
                        mean_val = float(numeric_data.mean())
                        count = len(numeric_data)
                        
                        # 对于某些字段，设置更合理的默认范围
                        if field == 'protein_pct':
                            # 蛋白率：在实际范围基础上适当扩展
                            range_margin = (max_val - min_val) * 0.1  # 10%的边距
                            suggested_min = max(0, min_val - range_margin)
                            suggested_max = min(10, max_val + range_margin)
                        elif field == 'fat_pct':
                            # 乳脂率：类似处理
                            range_margin = (max_val - min_val) * 0.1
                            suggested_min = max(0, min_val - range_margin)
                            suggested_max = min(15, max_val + range_margin)
                        elif field == 'somatic_cell_count':
                            # 体细胞数：通常比较大的数值
                            suggested_min = 0
                            suggested_max = max_val * 1.2
                        elif field == 'lactation_days':
                            # 泌乳天数：合理范围
                            suggested_min = 0
                            suggested_max = min(500, max_val * 1.1)
                        elif field == 'milk_yield':
                            # 产奶量：合理范围
                            suggested_min = 0
                            suggested_max = max_val * 1.2
                        else:
                            # 其他字段：基于实际数据范围
                            range_margin = (max_val - min_val) * 0.1 if max_val > min_val else abs(max_val) * 0.1
                            suggested_min = min_val - range_margin
                            suggested_max = max_val + range_margin
                        
                        ranges[field] = {
                            'min': min_val,
                            'max': max_val,
                            'mean': round(mean_val, 2),
                            'count': count,
                            'suggested_min': round(suggested_min, 2),
                            'suggested_max': round(suggested_max, 2),
                            'description': f'范围: {min_val:.2f}-{max_val:.2f}, 平均: {mean_val:.2f}, {count}个有效值'
                        }
                        
                        logger.debug(f"字段 {field} 范围: {min_val:.2f}-{max_val:.2f}")
                        
                except Exception as e:
                    logger.warning(f"计算字段 {field} 范围时出错: {e}")
                    continue
        
        logger.info(f"数据范围计算完成: {len(ranges)}个字段，跨越{len(all_months)}个月")
        
        return ranges
    
    def get_reasonable_filter_defaults(self, field: str, data_ranges: Dict) -> Dict:
        """根据数据范围获取合理的筛选默认值
        
        Args:
            field: 字段名
            data_ranges: 数据范围字典
            
        Returns:
            包含默认筛选参数的字典
        """
        if field not in data_ranges:
            # 如果没有数据范围，返回通用默认值
            return {
                'min': 0.0,
                'max': 100.0,
                'min_match_months': 1,
                'treat_empty_as_match': False
            }
        
        field_range = data_ranges[field]
        
        # 根据字段特性设置默认的筛选范围
        if field == 'protein_pct':
            # 蛋白率：选择中等偏上的范围
            mean_val = field_range['mean']
            default_min = max(field_range['suggested_min'], mean_val - 0.5)
            default_max = min(field_range['suggested_max'], mean_val + 0.5)
        elif field == 'fat_pct':
            # 乳脂率：类似处理
            mean_val = field_range['mean']
            default_min = max(field_range['suggested_min'], mean_val - 0.5)
            default_max = min(field_range['suggested_max'], mean_val + 0.5)
        elif field == 'somatic_cell_count':
            # 体细胞数：选择较低的范围（健康牛）
            default_min = field_range['suggested_min']
            default_max = min(field_range['suggested_max'], field_range['mean'] * 1.5)
        elif field == 'milk_yield':
            # 产奶量：选择中等偏上的范围
            mean_val = field_range['mean']
            default_min = max(field_range['suggested_min'], mean_val * 0.8)
            default_max = field_range['suggested_max']
        else:
            # 其他字段：使用建议范围
            default_min = field_range['suggested_min']
            default_max = field_range['suggested_max']
        
        return {
            'min': round(default_min, 2),
            'max': round(default_max, 2),
            'suggested_min': field_range['suggested_min'],
            'suggested_max': field_range['suggested_max'],
            'min_match_months': 1,
            'treat_empty_as_match': False
        }

    # ==================== 慢性乳房炎筛查相关方法 ====================
    
    def process_mastitis_system_files(self, system_type: str, file_paths: Dict[str, str], field_mappings: Dict[str, Dict[str, str]] = None) -> Tuple[bool, str, Dict[str, pd.DataFrame]]:
        """处理不同系统的慢性乳房炎筛查相关文件
        
        Args:
            system_type: 系统类型 ('yiqiniu', 'huimuyun', 'custom')
            file_paths: 文件路径字典，键为文件类型，值为文件路径
            field_mappings: 字段映射字典，仅用于自定义系统
            
        Returns:
            (success, message, processed_data)
            processed_data包含: {
                'cattle_info': 牛群基础信息DataFrame,
                'milk_yield': 奶牛产奶日汇总DataFrame (仅伊起牛),
                'disease': 发病查询导出DataFrame
            }
        """
        try:
            processed_data = {}
            
            if system_type == 'yiqiniu':
                # 伊起牛系统：需要3个表
                required_files = ['cattle_info', 'milk_yield', 'disease']
                for file_type in required_files:
                    if file_type not in file_paths:
                        return False, f"伊起牛系统缺少{file_type}文件", {}
                
                # 处理牛群基础信息表
                success, msg, cattle_df = self._process_yiqiniu_cattle_info(file_paths['cattle_info'])
                if not success:
                    return False, f"处理牛群基础信息表失败: {msg}", {}
                processed_data['cattle_info'] = cattle_df
                
                # 处理奶牛产奶日汇总表（多个sheet）
                success, msg, milk_df = self._process_yiqiniu_milk_yield(file_paths['milk_yield'])
                if not success:
                    return False, f"处理奶牛产奶日汇总表失败: {msg}", {}
                processed_data['milk_yield'] = milk_df
                
                # 处理发病查询导出表
                success, msg, disease_df = self._process_yiqiniu_disease(file_paths['disease'])
                if not success:
                    return False, f"处理发病查询导出表失败: {msg}", {}
                processed_data['disease'] = disease_df
                
            elif system_type == 'huimuyun':
                # 慧牧云系统：需要2个表
                required_files = ['cattle_info', 'disease']
                for file_type in required_files:
                    if file_type not in file_paths:
                        return False, f"慧牧云系统缺少{file_type}文件", {}
                
                # 处理牛群数据管理表
                success, msg, cattle_df = self._process_huimuyun_cattle_info(file_paths['cattle_info'])
                if not success:
                    return False, f"处理牛群数据管理表失败: {msg}", {}
                processed_data['cattle_info'] = cattle_df
                
                # 处理发病事件管理表
                success, msg, disease_df = self._process_huimuyun_disease(file_paths['disease'])
                if not success:
                    return False, f"处理发病事件管理表失败: {msg}", {}
                processed_data['disease'] = disease_df
                
            elif system_type == 'custom':
                # 自定义系统：用户自定义字段映射
                if not field_mappings:
                    return False, "自定义系统需要字段映射配置", {}
                
                required_files = ['cattle_info', 'disease']
                for file_type in required_files:
                    if file_type not in file_paths:
                        return False, f"自定义系统缺少{file_type}文件", {}
                
                # 处理牛群基础信息表
                success, msg, cattle_df = self._process_custom_cattle_info(file_paths['cattle_info'], field_mappings.get('cattle_info', {}))
                if not success:
                    return False, f"处理牛群基础信息表失败: {msg}", {}
                processed_data['cattle_info'] = cattle_df
                
                # 处理发病查询导出表
                success, msg, disease_df = self._process_custom_disease(file_paths['disease'], field_mappings.get('disease', {}))
                if not success:
                    return False, f"处理发病查询导出表失败: {msg}", {}
                processed_data['disease'] = disease_df
            
            return True, f"成功处理{system_type}系统文件", processed_data
            
        except Exception as e:
            logger.error(f"处理{system_type}系统文件时出错: {e}")
            return False, f"处理文件时出错: {str(e)}", {}
    
    def _process_yiqiniu_cattle_info(self, file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理伊起牛系统的牛群基础信息表"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"伊起牛牛群基础信息表原始列名: {list(df.columns)}")
            
            # 检查必要列
            required_columns = ['耳号', '胎次', '泌乳天数', '繁育状态', '在胎天数', '最近产犊日期']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"缺少必要列: {missing_columns}", None
            
            # 标准化数据
            result_df = pd.DataFrame()
            result_df['ear_tag'] = df['耳号'].astype(str).str.lstrip('0').replace('', '0')  # 去前导零
            result_df['parity'] = pd.to_numeric(df['胎次'], errors='coerce')
            result_df['lactation_days'] = pd.to_numeric(df['泌乳天数'], errors='coerce')
            result_df['breeding_status'] = df['繁育状态'].astype(str)
            result_df['gestation_days'] = pd.to_numeric(df['在胎天数'], errors='coerce')
            result_df['last_calving_date'] = pd.to_datetime(df['最近产犊日期'], errors='coerce')
            
            # 清理数据
            result_df = result_df.dropna(subset=['ear_tag'])
            result_df = result_df[result_df['ear_tag'] != 'nan']
            
            logger.info(f"伊起牛牛群基础信息表处理完成: {len(result_df)}条记录")
            return True, f"成功处理{len(result_df)}条牛群基础信息", result_df
            
        except Exception as e:
            logger.error(f"处理伊起牛牛群基础信息表出错: {e}")
            return False, str(e), None
    
    def _process_yiqiniu_milk_yield(self, file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理伊起牛系统的奶牛产奶日汇总表（合并所有sheet）"""
        try:
            # 读取所有sheet
            all_sheets_data = []
            with pd.ExcelFile(file_path) as xls:
                sheet_names = xls.sheet_names
                logger.info(f"发现{len(sheet_names)}个sheet: {sheet_names}")
                
                for sheet_name in sheet_names:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        if len(df) > 0:
                            df['source_sheet'] = sheet_name
                            all_sheets_data.append(df)
                            logger.info(f"Sheet {sheet_name}: {len(df)}条记录")
                    except Exception as e:
                        logger.warning(f"读取sheet {sheet_name}出错: {e}")
                        continue
            
            if not all_sheets_data:
                return False, "所有sheet都无法读取或为空", None
            
            # 合并所有sheet
            combined_df = pd.concat(all_sheets_data, ignore_index=True)
            logger.info(f"合并后总记录数: {len(combined_df)}")
            
            # 检查必要列
            required_columns = ['耳号', '挤奶日期', '日产量(kg)']
            missing_columns = [col for col in required_columns if col not in combined_df.columns]
            
            if missing_columns:
                return False, f"缺少必要列: {missing_columns}", None
            
            # 标准化数据
            result_df = pd.DataFrame()
            result_df['ear_tag'] = combined_df['耳号'].astype(str).str.lstrip('0').replace('', '0')
            result_df['milk_date'] = pd.to_datetime(combined_df['挤奶日期'], errors='coerce')
            result_df['daily_yield'] = pd.to_numeric(combined_df['日产量(kg)'], errors='coerce')
            
            # 清理数据
            result_df = result_df.dropna(subset=['ear_tag', 'milk_date', 'daily_yield'])
            result_df = result_df[result_df['ear_tag'] != 'nan']
            result_df = result_df[result_df['daily_yield'] > 0]
            
            logger.info(f"奶牛产奶日汇总表处理完成: {len(result_df)}条有效记录")
            return True, f"成功处理{len(result_df)}条产奶记录", result_df
            
        except Exception as e:
            logger.error(f"处理奶牛产奶日汇总表出错: {e}")
            return False, str(e), None
    
    def _process_yiqiniu_disease(self, file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理伊起牛系统的发病查询导出表"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"伊起牛发病查询导出表原始列名: {list(df.columns)}")
            
            # 检查必要列
            required_columns = ['耳号', '发病日期', '疾病种类']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"缺少必要列: {missing_columns}", None
            
            # 标准化数据
            result_df = pd.DataFrame()
            result_df['ear_tag'] = df['耳号'].astype(str).str.lstrip('0').replace('', '0')
            result_df['disease_date'] = pd.to_datetime(df['发病日期'], errors='coerce')
            result_df['disease_type'] = df['疾病种类'].astype(str)
            
            # 筛选乳房炎相关疾病
            mastitis_keywords = ['乳房疾病', '乳房炎', '乳房感染']
            mastitis_condition = result_df['disease_type'].str.contains('|'.join(mastitis_keywords), na=False)
            result_df = result_df[mastitis_condition]
            
            # 清理数据
            result_df = result_df.dropna(subset=['ear_tag', 'disease_date'])
            result_df = result_df[result_df['ear_tag'] != 'nan']
            
            logger.info(f"伊起牛发病查询导出表处理完成: {len(result_df)}条乳房炎记录")
            return True, f"成功处理{len(result_df)}条乳房炎发病记录", result_df
            
        except Exception as e:
            logger.error(f"处理伊起牛发病查询导出表出错: {e}")
            return False, str(e), None
    
    def _process_huimuyun_cattle_info(self, file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理慧牧云系统的牛群数据管理表"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"慧牧云牛群数据管理表原始列名: {list(df.columns)}")
            
            # 检查必要列
            required_columns = ['耳号', '胎次', '泌乳天数', '繁育状态', '怀孕天数', '产犊日期']
            # 慧牧云特有的列
            if '最近七天奶厅平均奶量' in df.columns:
                required_columns.append('最近七天奶厅平均奶量')
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"缺少必要列: {missing_columns}", None
            
            # 标准化数据
            result_df = pd.DataFrame()
            result_df['ear_tag'] = df['耳号'].astype(str).str.lstrip('0').replace('', '0')
            result_df['parity'] = pd.to_numeric(df['胎次'], errors='coerce')
            result_df['lactation_days'] = pd.to_numeric(df['泌乳天数'], errors='coerce')
            result_df['breeding_status'] = df['繁育状态'].astype(str)
            result_df['gestation_days'] = pd.to_numeric(df['怀孕天数'], errors='coerce')
            result_df['last_calving_date'] = pd.to_datetime(df['产犊日期'], errors='coerce')
            
            # 慧牧云系统包含现成的最近七天平均奶量
            if '最近七天奶厅平均奶量' in df.columns:
                result_df['recent_7day_avg_yield'] = pd.to_numeric(df['最近七天奶厅平均奶量'], errors='coerce')
            
            # 清理数据
            result_df = result_df.dropna(subset=['ear_tag'])
            result_df = result_df[result_df['ear_tag'] != 'nan']
            
            logger.info(f"慧牧云牛群数据管理表处理完成: {len(result_df)}条记录")
            return True, f"成功处理{len(result_df)}条牛群数据", result_df
            
        except Exception as e:
            logger.error(f"处理慧牧云牛群数据管理表出错: {e}")
            return False, str(e), None
    
    def _process_huimuyun_disease(self, file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理慧牧云系统的发病事件管理表"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"慧牧云发病事件管理表原始列名: {list(df.columns)}")
            
            # 检查必要列
            required_columns = ['耳号', '事件日期', '事件类型']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"缺少必要列: {missing_columns}", None
            
            # 标准化数据
            result_df = pd.DataFrame()
            result_df['ear_tag'] = df['耳号'].astype(str).str.lstrip('0').replace('', '0')
            result_df['disease_date'] = pd.to_datetime(df['事件日期'], errors='coerce')
            result_df['disease_type'] = df['事件类型'].astype(str)
            
            # 筛选乳房炎相关事件
            mastitis_keywords = ['乳房炎', '乳房感染']
            mastitis_condition = result_df['disease_type'].str.contains('|'.join(mastitis_keywords), na=False)
            result_df = result_df[mastitis_condition]
            
            # 清理数据
            result_df = result_df.dropna(subset=['ear_tag', 'disease_date'])
            result_df = result_df[result_df['ear_tag'] != 'nan']
            
            logger.info(f"慧牧云发病事件管理表处理完成: {len(result_df)}条乳房炎记录")
            return True, f"成功处理{len(result_df)}条乳房炎事件记录", result_df
            
        except Exception as e:
            logger.error(f"处理慧牧云发病事件管理表出错: {e}")
            return False, str(e), None
    
    def calculate_recent_7day_avg_yield(self, milk_data: pd.DataFrame) -> pd.DataFrame:
        """计算每头牛最近七天奶厅平均奶量（仅用于伊起牛系统）
        
        Args:
            milk_data: 奶牛产奶日汇总数据，包含columns: ['ear_tag', 'milk_date', 'daily_yield']
            
        Returns:
            包含最近七天平均奶量的DataFrame，columns: ['ear_tag', 'recent_7day_avg_yield']
        """
        try:
            if milk_data.empty:
                return pd.DataFrame(columns=['ear_tag', 'recent_7day_avg_yield'])
            
            results = []
            
            # 按耳号分组处理
            for ear_tag, group in milk_data.groupby('ear_tag'):
                try:
                    # 按日期排序
                    group_sorted = group.sort_values('milk_date')
                    
                    # 找到最近的挤奶日期
                    latest_date = group_sorted['milk_date'].max()
                    
                    # 计算7天前的日期
                    seven_days_ago = latest_date - pd.Timedelta(days=6)  # 包含当天，所以是6天前
                    
                    # 筛选最近7天的数据
                    recent_data = group_sorted[
                        (group_sorted['milk_date'] >= seven_days_ago) & 
                        (group_sorted['milk_date'] <= latest_date)
                    ]
                    
                    if len(recent_data) > 0:
                        # 计算平均值（忽略缺失的天数）
                        avg_yield = recent_data['daily_yield'].mean()
                        results.append({
                            'ear_tag': ear_tag,
                            'recent_7day_avg_yield': round(avg_yield, 2),
                            'days_count': len(recent_data),
                            'latest_date': latest_date
                        })
                        
                        logger.debug(f"牛{ear_tag}: 最近{len(recent_data)}天平均奶量 {avg_yield:.2f}kg")
                    
                except Exception as e:
                    logger.warning(f"计算牛{ear_tag}最近7天平均奶量时出错: {e}")
                    continue
            
            result_df = pd.DataFrame(results)
            logger.info(f"成功计算{len(result_df)}头牛的最近7天平均奶量")
            
            return result_df[['ear_tag', 'recent_7day_avg_yield']]
            
        except Exception as e:
            logger.error(f"计算最近7天平均奶量时出错: {e}")
            return pd.DataFrame(columns=['ear_tag', 'recent_7day_avg_yield'])
    
    def calculate_mastitis_count_per_lactation(self, cattle_info: pd.DataFrame, disease_data: pd.DataFrame) -> pd.DataFrame:
        """计算每头牛本泌乳期的乳房炎发病次数
        
        Args:
            cattle_info: 牛群基础信息，包含columns: ['ear_tag', 'last_calving_date']
            disease_data: 发病数据，包含columns: ['ear_tag', 'disease_date', 'disease_type']
            
        Returns:
            包含乳房炎发病统计的DataFrame，columns: ['ear_tag', 'mastitis_count', 'mastitis_dates']
        """
        try:
            if cattle_info.empty or disease_data.empty:
                return pd.DataFrame(columns=['ear_tag', 'mastitis_count', 'mastitis_dates'])
            
            results = []
            
            # 为每头牛计算乳房炎发病次数
            for _, cow in cattle_info.iterrows():
                ear_tag = cow['ear_tag']
                calving_date = cow['last_calving_date']
                
                if pd.isna(calving_date):
                    # 如果没有产犊日期，跳过
                    results.append({
                        'ear_tag': ear_tag,
                        'mastitis_count': 0,
                        'mastitis_dates': ''
                    })
                    continue
                
                # 找到该牛的所有发病记录
                cow_diseases = disease_data[disease_data['ear_tag'] == ear_tag]
                
                if cow_diseases.empty:
                    results.append({
                        'ear_tag': ear_tag,
                        'mastitis_count': 0,
                        'mastitis_dates': ''
                    })
                    continue
                
                # 筛选本泌乳期（产犊日期之后）的乳房炎发病记录
                lactation_diseases = cow_diseases[
                    cow_diseases['disease_date'] >= calving_date
                ]
                
                mastitis_dates = lactation_diseases['disease_date'].dt.strftime('%Y-%m-%d').tolist()
                mastitis_count = len(mastitis_dates)
                
                results.append({
                    'ear_tag': ear_tag,
                    'mastitis_count': mastitis_count,
                    'mastitis_dates': ','.join(mastitis_dates)
                })
                
                if mastitis_count > 0:
                    logger.debug(f"牛{ear_tag}: 本泌乳期乳房炎{mastitis_count}次，日期: {mastitis_dates}")
            
            result_df = pd.DataFrame(results)
            total_cases = result_df['mastitis_count'].sum()
            affected_cows = len(result_df[result_df['mastitis_count'] > 0])
            
            logger.info(f"乳房炎发病统计完成: {affected_cows}头牛发病，总计{total_cases}次")
            
            return result_df
            
        except Exception as e:
            logger.error(f"计算乳房炎发病次数时出错: {e}")
            return pd.DataFrame(columns=['ear_tag', 'mastitis_count', 'mastitis_dates'])
    
    def identify_chronic_mastitis_cows(self, dhi_data_list: List[Dict], selected_months: List[str], scc_threshold: float = 20.0, scc_operator: str = ">=") -> pd.DataFrame:
        """识别慢性乳房炎感染牛
        
        Args:
            dhi_data_list: DHI数据列表
            selected_months: 选择的月份列表（格式：YYYY年MM月）
            scc_threshold: 体细胞数阈值（万/ml）
            scc_operator: 体细胞数比较操作符 ('<', '<=', '=', '>=', '>')
            
        Returns:
            慢性感染牛DataFrame，columns: ['management_id', 'chronic_mastitis'] 或 ['ear_tag', 'chronic_mastitis']
        """
        try:
            if not dhi_data_list:
                return pd.DataFrame(columns=['management_id', 'chronic_mastitis'])
            
            if not selected_months:
                logger.warning("没有选择检查月份")
                return pd.DataFrame(columns=['management_id', 'chronic_mastitis'])
            
            # 合并所有DHI数据
            all_dhi = []
            for item in dhi_data_list:
                df = item['data'].copy()
                if 'somatic_cell_count' in df.columns:
                    all_dhi.append(df)
            
            if not all_dhi:
                logger.warning("没有找到包含体细胞数的DHI数据")
                return pd.DataFrame(columns=['management_id', 'chronic_mastitis'])
            
            combined_dhi = pd.concat(all_dhi, ignore_index=True)
            
            # 确定使用的ID字段（优先使用management_id，如果没有则使用ear_tag）
            if 'management_id' in combined_dhi.columns:
                id_column = 'management_id'
            elif 'ear_tag' in combined_dhi.columns:
                id_column = 'ear_tag'
            else:
                logger.error("DHI数据中没有找到management_id或ear_tag字段")
                return pd.DataFrame(columns=['management_id', 'chronic_mastitis'])
            
            # 检查必要字段（移除farm_id依赖）
            required_fields = [id_column, 'sample_date', 'somatic_cell_count']
            missing_fields = [field for field in required_fields if field not in combined_dhi.columns]
            
            if missing_fields:
                logger.error(f"DHI数据缺少必要字段: {missing_fields}")
                return pd.DataFrame(columns=[id_column, 'chronic_mastitis'])
            
            # 添加年月列（格式：YYYY年MM月）
            combined_dhi['year_month'] = pd.to_datetime(combined_dhi['sample_date']).dt.strftime('%Y年%m月')
            
            # 转换选择的月份为集合以便快速查找
            selected_months_set = set(selected_months)
            
            # 按牛分组检查指定月份的体细胞数
            results = []
            
            for cow_id, group in combined_dhi.groupby(id_column):
                try:
                    # 按月份分组，计算每月平均体细胞数
                    monthly_data = group.groupby('year_month')['somatic_cell_count'].mean()
                    
                    # 检查在所有选择的月份中，体细胞数是否都满足条件
                    is_chronic = self._check_selected_months_scc(monthly_data, selected_months_set, scc_threshold, scc_operator)
                    
                    results.append({
                        id_column: cow_id,
                        'chronic_mastitis': is_chronic
                    })
                    
                    if is_chronic:
                        logger.debug(f"识别慢性感染牛: {id_column}={cow_id}")
                        
                except Exception as e:
                    logger.warning(f"处理牛{cow_id}时出错: {e}")
                    continue
            
            result_df = pd.DataFrame(results)
            chronic_count = len(result_df[result_df['chronic_mastitis']])
            total_count = len(result_df)
            
            logger.info(f"慢性乳房炎感染牛识别完成: {chronic_count}/{total_count}头牛被识别为慢性感染")
            logger.info(f"检查条件: 在{', '.join(selected_months)}月份中体细胞数{scc_operator}{scc_threshold}万/ml")
            
            return result_df
            
        except Exception as e:
            logger.error(f"识别慢性乳房炎感染牛时出错: {e}")
            return pd.DataFrame(columns=['management_id', 'chronic_mastitis'])
    
    def _check_continuous_high_scc(self, monthly_scc: pd.Series, required_months: int, threshold: float) -> bool:
        """检查是否有连续N个月体细胞数超过阈值"""
        if len(monthly_scc) < required_months:
            return False
        
        # 创建超过阈值的布尔序列
        high_scc = monthly_scc > threshold
        
        # 检查是否有连续N个月为True
        consecutive_count = 0
        max_consecutive = 0
        
        for is_high in high_scc:
            if is_high:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
        
        return max_consecutive >= required_months

    def _check_selected_months_scc(self, monthly_scc: pd.Series, selected_months_set: set, threshold: float, operator: str = ">=") -> bool:
        """检查在选定月份中体细胞数是否都满足条件
        
        Args:
            monthly_scc: 按月份的体细胞数Series（索引为YYYY年MM月格式）
            selected_months_set: 选择的月份集合
            threshold: 体细胞数阈值
            operator: 比较操作符
            
        Returns:
            是否在所有选定月份都满足条件（必须所有月份都有数据且都满足条件）
        """
        try:
            # 检查选择的月份中是否有数据
            available_months = set(monthly_scc.index) & selected_months_set
            
            # 关键修改：必须所有选择的月份都有数据
            if len(available_months) != len(selected_months_set):
                missing_months = selected_months_set - available_months
                logger.debug(f"缺失月份数据: {missing_months}，无法满足所有月份条件")
                return False
            
            # 检查所有选择月份的体细胞数是否都满足条件
            all_months_satisfy = True
            for month in selected_months_set:
                scc_value = monthly_scc[month]
                
                # 根据操作符进行比较
                satisfies_condition = self._compare_value(scc_value, operator, threshold)
                
                if not satisfies_condition:
                    all_months_satisfy = False
                    logger.debug(f"月份{month}体细胞数{scc_value}不满足条件{operator}{threshold}")
                    break
                else:
                    logger.debug(f"月份{month}体细胞数{scc_value}满足条件{operator}{threshold}")
            
            # 必须所有选择的月份都有数据且都满足条件
            return all_months_satisfy
            
        except Exception as e:
            logger.warning(f"检查体细胞数条件时出错: {e}")
            return False
    
    def _compare_value(self, actual_value, operator: str, target_value) -> bool:
        """根据操作符比较两个值
        
        Args:
            actual_value: 实际值
            operator: 操作符 ('<', '<=', '=', '>=', '>')
            target_value: 目标值
            
        Returns:
            比较结果
        """
        try:
            if pd.isna(actual_value) or pd.isna(target_value):
                return False
            
            actual_value = float(actual_value)
            target_value = float(target_value)
            
            if operator == '<':
                return actual_value < target_value
            elif operator == '<=':
                return actual_value <= target_value
            elif operator == '=':
                return abs(actual_value - target_value) < 0.001  # 浮点数相等比较
            elif operator == '>=':
                return actual_value >= target_value
            elif operator == '>':
                return actual_value > target_value
            else:
                logger.warning(f"未知的操作符: {operator}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.warning(f"值比较时出错: {e}")
            return False
    
    def apply_treatment_decisions(self, base_data: pd.DataFrame, treatment_config: Dict[str, Any]) -> pd.DataFrame:
        """根据配置应用5种处置办法的判断逻辑
        
        Args:
            base_data: 基础数据，包含所有必要字段
            treatment_config: 处置办法配置
            
        Returns:
            包含处置办法的DataFrame
        """
        try:
            if base_data.empty:
                return pd.DataFrame()
            
            result_df = base_data.copy()
            
            # 为每头牛判断符合的处置办法
            treatment_results = []
            
            for _, cow in result_df.iterrows():
                treatments = []
                
                # 前提条件：只有慢性感染牛才能进行处置办法判断
                is_chronic = cow.get('chronic_mastitis', False)
                
                if not is_chronic:
                    # 非慢性感染牛，不需要处置
                    treatment_results.append('无')
                    continue
                
                # 1. 淘汰
                if self._check_cull_criteria(cow, treatment_config.get('cull', {})):
                    treatments.append('淘汰')
                
                # 2. 禁配隔离
                if self._check_isolate_criteria(cow, treatment_config.get('isolate', {})):
                    treatments.append('禁配隔离')
                
                # 3. 瞎乳区
                if self._check_blind_quarter_criteria(cow, treatment_config.get('blind_quarter', {})):
                    treatments.append('瞎乳区')
                
                # 4. 提前干奶
                if self._check_early_dry_criteria(cow, treatment_config.get('early_dry', {})):
                    treatments.append('提前干奶')
                
                # 5. 治疗
                if self._check_treatment_criteria(cow, treatment_config.get('treatment', {})):
                    treatments.append('治疗')
                
                # 如果没有符合任何条件，且启用了默认治疗
                if not treatments and treatment_config.get('default_treatment', True):
                    treatments.append('治疗')
                
                treatment_results.append(','.join(treatments) if treatments else '无')
            
            result_df['treatment_methods'] = treatment_results
            
            # 统计结果
            treatment_stats = {}
            chronic_count = 0
            for i, treatments in enumerate(treatment_results):
                if result_df.iloc[i].get('chronic_mastitis', False):
                    chronic_count += 1
                for treatment in treatments.split(','):
                    if treatment != '无':
                        treatment_stats[treatment] = treatment_stats.get(treatment, 0) + 1
            
            logger.info(f"处置办法判断完成: {treatment_stats}")
            logger.info(f"慢性感染牛总数: {chronic_count}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"应用处置办法判断时出错: {e}")
            return base_data
    
    def _check_cull_criteria(self, cow: pd.Series, cull_config: Dict) -> bool:
        """检查淘汰条件"""
        if not cull_config.get('enabled', False):
            return False
        
        try:
            # 检查繁殖状态
            breeding_statuses = cull_config.get('breeding_status', [])
            if breeding_statuses and cow.get('breeding_status') not in breeding_statuses:
                return False
            
            # 检查产奶量
            if 'yield_operator' in cull_config and 'yield_value' in cull_config:
                if not self._compare_value(
                    cow.get('recent_7day_avg_yield'), 
                    cull_config['yield_operator'], 
                    cull_config['yield_value']
                ):
                    return False
            
            # 检查发病次数
            if 'mastitis_operator' in cull_config and 'mastitis_value' in cull_config:
                if not self._compare_value(
                    cow.get('mastitis_count'), 
                    cull_config['mastitis_operator'], 
                    cull_config['mastitis_value']
                ):
                    return False
            
            # 检查泌乳天数
            if 'lactation_operator' in cull_config and 'lactation_value' in cull_config:
                if not self._compare_value(
                    cow.get('lactation_days'), 
                    cull_config['lactation_operator'], 
                    cull_config['lactation_value']
                ):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"检查淘汰条件时出错: {e}")
            return False
    
    def _check_isolate_criteria(self, cow: pd.Series, isolate_config: Dict) -> bool:
        """检查禁配隔离条件"""
        if not isolate_config.get('enabled', False):
            return False
        
        try:
            # 检查繁殖状态
            breeding_statuses = isolate_config.get('breeding_status', [])
            if breeding_statuses and cow.get('breeding_status') not in breeding_statuses:
                return False
            
            # 检查产奶量
            if 'yield_operator' in isolate_config and 'yield_value' in isolate_config:
                if not self._compare_value(
                    cow.get('recent_7day_avg_yield'), 
                    isolate_config['yield_operator'], 
                    isolate_config['yield_value']
                ):
                    return False
            
            # 检查发病次数
            if 'mastitis_operator' in isolate_config and 'mastitis_value' in isolate_config:
                if not self._compare_value(
                    cow.get('mastitis_count'), 
                    isolate_config['mastitis_operator'], 
                    isolate_config['mastitis_value']
                ):
                    return False
            
            # 检查泌乳天数
            if 'lactation_operator' in isolate_config and 'lactation_value' in isolate_config:
                if not self._compare_value(
                    cow.get('lactation_days'), 
                    isolate_config['lactation_operator'], 
                    isolate_config['lactation_value']
                ):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"检查禁配隔离条件时出错: {e}")
            return False
    
    def _check_blind_quarter_criteria(self, cow: pd.Series, blind_config: Dict) -> bool:
        """检查瞎乳区条件"""
        if not blind_config.get('enabled', False):
            return False
        
        try:
            # 检查繁殖状态
            breeding_statuses = blind_config.get('breeding_status', [])
            if breeding_statuses and cow.get('breeding_status') not in breeding_statuses:
                return False
            
            # 检查在胎天数
            if 'gestation_operator' in blind_config and 'gestation_value' in blind_config:
                if not self._compare_value(
                    cow.get('gestation_days'), 
                    blind_config['gestation_operator'], 
                    blind_config['gestation_value']
                ):
                    return False
            
            # 检查发病次数
            if 'mastitis_operator' in blind_config and 'mastitis_value' in blind_config:
                if not self._compare_value(
                    cow.get('mastitis_count'), 
                    blind_config['mastitis_operator'], 
                    blind_config['mastitis_value']
                ):
                    return False
            
            # 检查泌乳天数
            if 'lactation_operator' in blind_config and 'lactation_value' in blind_config:
                if not self._compare_value(
                    cow.get('lactation_days'), 
                    blind_config['lactation_operator'], 
                    blind_config['lactation_value']
                ):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"检查瞎乳区条件时出错: {e}")
            return False
    
    def _check_early_dry_criteria(self, cow: pd.Series, early_dry_config: Dict) -> bool:
        """检查提前干奶条件"""
        if not early_dry_config.get('enabled', False):
            return False
        
        try:
            # 检查繁殖状态
            breeding_statuses = early_dry_config.get('breeding_status', [])
            if breeding_statuses and cow.get('breeding_status') not in breeding_statuses:
                return False
            
            # 检查在胎天数
            if 'gestation_operator' in early_dry_config and 'gestation_value' in early_dry_config:
                if not self._compare_value(
                    cow.get('gestation_days'), 
                    early_dry_config['gestation_operator'], 
                    early_dry_config['gestation_value']
                ):
                    return False
            
            # 检查发病次数
            if 'mastitis_operator' in early_dry_config and 'mastitis_value' in early_dry_config:
                if not self._compare_value(
                    cow.get('mastitis_count'), 
                    early_dry_config['mastitis_operator'], 
                    early_dry_config['mastitis_value']
                ):
                    return False
            
            # 检查泌乳天数
            if 'lactation_operator' in early_dry_config and 'lactation_value' in early_dry_config:
                if not self._compare_value(
                    cow.get('lactation_days'), 
                    early_dry_config['lactation_operator'], 
                    early_dry_config['lactation_value']
                ):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"检查提前干奶条件时出错: {e}")
            return False
    
    def _check_treatment_criteria(self, cow: pd.Series, treatment_config: Dict) -> bool:
        """检查治疗条件"""
        if not treatment_config.get('enabled', False):
            return False
        
        try:
            # 检查发病次数（治疗通常是发病次数较少的）
            max_mastitis = treatment_config.get('max_mastitis_count', float('inf'))
            if cow.get('mastitis_count', float('inf')) > max_mastitis:
                return False
            
            # 其他治疗条件可以根据需要添加
            
            return True
            
        except Exception as e:
            logger.warning(f"检查治疗条件时出错: {e}")
            return False
    
    def create_mastitis_screening_report(self, screening_data: pd.DataFrame, selected_months: List[str] = None, dhi_data_list: List[Dict] = None) -> pd.DataFrame:
        """创建慢性乳房炎筛查结果报告
        
        Args:
            screening_data: 筛查数据
            selected_months: 选择的月份列表（格式：YYYY年MM月）
            dhi_data_list: DHI数据列表，用于提取体细胞数
            
        Returns:
            格式化的结果报告DataFrame
        """
        try:
            if screening_data.empty:
                return pd.DataFrame()
            
            # 提取所选月份的体细胞数据
            logger.info("开始提取所选月份的体细胞数据...")
            scc_data = self._extract_monthly_scc_data(screening_data, selected_months, dhi_data_list)
            
            if scc_data is not None:
                logger.info(f"✅ 体细胞数据提取成功，数据形状: {scc_data.shape}")
                logger.info(f"体细胞数据列: {scc_data.columns.tolist()}")
            else:
                logger.warning("❌ 体细胞数据提取失败")
            
            # 选择和重新排序列
            output_columns = [
                'ear_tag', 'treatment_methods', 'parity', 'lactation_days', 
                'recent_7day_avg_yield', 'breeding_status', 'gestation_days', 
                'mastitis_count', 'mastitis_dates'
            ]
            
            # 创建输出DataFrame
            result_df = pd.DataFrame()
            
            for col in output_columns:
                if col in screening_data.columns:
                    result_df[col] = screening_data[col]
                else:
                    result_df[col] = None
            
            # 添加所选月份的体细胞数列
            if scc_data is not None and not scc_data.empty:
                # 确定合并的字段 - 更智能的匹配逻辑
                merge_key = None
                
                # 打印调试信息
                logger.info(f"result_df columns: {result_df.columns.tolist()}")
                logger.info(f"scc_data columns: {scc_data.columns.tolist()}")
                
                if 'ear_tag' in result_df.columns and 'ear_tag' in scc_data.columns:
                    merge_key = 'ear_tag'
                elif 'management_id' in result_df.columns and 'management_id' in scc_data.columns:
                    merge_key = 'management_id'
                elif 'ear_tag' in result_df.columns and 'management_id' in scc_data.columns:
                    # 筛查结果用ear_tag，体细胞数据用management_id
                    # 假设ear_tag就是management_id
                    scc_data_copy = scc_data.copy()
                    scc_data_copy['ear_tag'] = scc_data_copy['management_id']
                    merge_key = 'ear_tag'
                    scc_data = scc_data_copy
                    logger.info("创建ear_tag字段用于合并")
                elif 'management_id' in result_df.columns and 'ear_tag' in scc_data.columns:
                    # 筛查结果用management_id，体细胞数据用ear_tag
                    scc_data_copy = scc_data.copy()
                    scc_data_copy['management_id'] = scc_data_copy['ear_tag']
                    merge_key = 'management_id'
                    scc_data = scc_data_copy
                    logger.info("创建management_id字段用于合并")
                
                if merge_key:
                    # 合并体细胞数据
                    logger.info(f"准备使用{merge_key}字段合并体细胞数据")
                    result_df = result_df.merge(scc_data, left_on=merge_key, right_on=merge_key, how='left')
                    logger.info(f"✅ 体细胞数据已使用{merge_key}字段成功合并，合并后列数: {len(result_df.columns)}")
                else:
                    logger.warning("❌ 无法找到合适的合并字段，跳过体细胞数据合并")
                    logger.warning(f"筛查结果字段: {result_df.columns.tolist()}")
                    logger.warning(f"体细胞数据字段: {scc_data.columns.tolist()}")
            
            # 重命名列为中文
            column_mapping = {
                'ear_tag': '耳号',
                'treatment_methods': '处置办法',
                'parity': '胎次',
                'lactation_days': '泌乳天数',
                'recent_7day_avg_yield': '最近七天奶厅平均奶量',
                'breeding_status': '繁殖状态',
                'gestation_days': '在胎天数',
                'mastitis_count': '乳房炎发病次数',
                'mastitis_dates': '每次乳房炎发病时间'
            }
            
            # 添加体细胞数列的中文名称映射
            if selected_months:
                for month in selected_months:
                    column_mapping[f'scc_{month}'] = f'{month}体细胞数(万/ml)'
            
            result_df = result_df.rename(columns=column_mapping)
            
            # 过滤掉没有处置办法的牛（如果需要）
            result_df = result_df[result_df['处置办法'] != '无']
            
            logger.info(f"慢性乳房炎筛查报告生成完成: {len(result_df)}头牛需要处置")
            
            return result_df
            
        except Exception as e:
            logger.error(f"创建慢性乳房炎筛查报告时出错: {e}")
            return pd.DataFrame()

    def export_mastitis_screening_results(self, result_df: pd.DataFrame, output_path: str) -> bool:
        """导出慢性乳房炎筛查结果到Excel
        
        Args:
            result_df: 结果DataFrame
            output_path: 输出文件路径
            
        Returns:
            是否成功导出
        """
        try:
            if result_df.empty:
                logger.warning("结果数据为空，无法导出")
                return False
            
            # 创建Excel写入器
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 写入主要结果
                result_df.to_excel(writer, sheet_name='慢性乳房炎筛查结果', index=False)
                
                # 添加统计信息sheet
                stats_data = self._create_mastitis_stats(result_df)
                if not stats_data.empty:
                    stats_data.to_excel(writer, sheet_name='统计信息', index=False)
            
            logger.info(f"慢性乳房炎筛查结果已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出慢性乳房炎筛查结果时出错: {e}")
            return False
    
    def _create_mastitis_stats(self, result_df: pd.DataFrame) -> pd.DataFrame:
        """创建慢性乳房炎筛查统计信息"""
        try:
            stats = []
            
            # 总体统计
            total_cows = len(result_df)
            stats.append(['总计需要处置的牛只数', total_cows])
            
            # 按处置办法统计
            if '处置办法' in result_df.columns:
                treatment_counts = {}
                for treatments in result_df['处置办法']:
                    if pd.notna(treatments) and treatments != '无':
                        for treatment in str(treatments).split(','):
                            treatment = treatment.strip()
                            treatment_counts[treatment] = treatment_counts.get(treatment, 0) + 1
                
                for treatment, count in treatment_counts.items():
                    stats.append([f'{treatment}处置办法', count])
            
            # 按胎次统计
            if '胎次' in result_df.columns:
                parity_stats = result_df['胎次'].value_counts().sort_index()
                for parity, count in parity_stats.items():
                    if pd.notna(parity):
                        stats.append([f'{int(parity)}胎牛只数', count])
            
            # 乳房炎发病次数统计
            if '乳房炎发病次数' in result_df.columns:
                mastitis_stats = result_df['乳房炎发病次数'].value_counts().sort_index()
                for count, cow_num in mastitis_stats.items():
                    if pd.notna(count):
                        stats.append([f'发病{int(count)}次的牛只数', cow_num])
            
            stats_df = pd.DataFrame(stats, columns=['统计项目', '数量'])
            return stats_df
            
        except Exception as e:
            logger.error(f"创建统计信息时出错: {e}")
            return pd.DataFrame()

    # 删除临时分析文件
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_files = ['analyze_test_data.py']
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"已删除临时文件: {temp_file}")
        except Exception as e:
            logger.warning(f"清理临时文件时出错: {e}")
    
    def _process_custom_cattle_info(self, file_path: str, field_mappings: Dict[str, str]) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理自定义系统的牛群基础信息表"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"自定义系统牛群基础信息表原始列名: {list(df.columns)}")
            
            # 检查字段映射是否完整
            required_fields = ['耳号', '胎次', '泌乳天数', '繁育状态', '在胎天数', '最近产犊日期']
            missing_mappings = []
            for field in required_fields:
                if field not in field_mappings or not field_mappings[field]:
                    missing_mappings.append(field)
            
            if missing_mappings:
                return False, f"缺少字段映射: {missing_mappings}", None
            
            # 检查表头列是否存在
            missing_columns = []
            for field, column_name in field_mappings.items():
                if column_name not in df.columns:
                    missing_columns.append(f"{field}({column_name})")
            
            if missing_columns:
                return False, f"表格中缺少列: {missing_columns}", None
            
            # 标准化数据
            result_df = pd.DataFrame()
            result_df['ear_tag'] = df[field_mappings['耳号']].astype(str).str.lstrip('0').replace('', '0')
            result_df['parity'] = pd.to_numeric(df[field_mappings['胎次']], errors='coerce')
            result_df['lactation_days'] = pd.to_numeric(df[field_mappings['泌乳天数']], errors='coerce')
            result_df['breeding_status'] = df[field_mappings['繁育状态']].astype(str)
            result_df['gestation_days'] = pd.to_numeric(df[field_mappings['在胎天数']], errors='coerce')
            result_df['last_calving_date'] = pd.to_datetime(df[field_mappings['最近产犊日期']], errors='coerce')
            
            # 如果有最近七天奶厅平均奶量字段，也处理它
            if '最近七天奶厅平均奶量' in field_mappings and field_mappings['最近七天奶厅平均奶量']:
                column_name = field_mappings['最近七天奶厅平均奶量']
                if column_name in df.columns:
                    result_df['recent_7day_avg_yield'] = pd.to_numeric(df[column_name], errors='coerce')
            
            # 清理数据
            result_df = result_df.dropna(subset=['ear_tag'])
            result_df = result_df[result_df['ear_tag'] != 'nan']
            
            logger.info(f"自定义系统牛群基础信息表处理完成: {len(result_df)}条记录")
            return True, f"成功处理{len(result_df)}条牛群基础信息", result_df
            
        except Exception as e:
            logger.error(f"处理自定义系统牛群基础信息表出错: {e}")
            return False, str(e), None
    
    def _process_custom_disease(self, file_path: str, field_mappings: Dict[str, str]) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """处理自定义系统的发病查询导出表"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"自定义系统发病查询导出表原始列名: {list(df.columns)}")
            
            # 检查字段映射是否完整
            required_fields = ['耳号', '发病日期', '疾病种类']
            missing_mappings = []
            for field in required_fields:
                if field not in field_mappings or not field_mappings[field]:
                    missing_mappings.append(field)
            
            if missing_mappings:
                return False, f"缺少字段映射: {missing_mappings}", None
            
            # 检查表头列是否存在
            missing_columns = []
            for field, column_name in field_mappings.items():
                if column_name not in df.columns:
                    missing_columns.append(f"{field}({column_name})")
            
            if missing_columns:
                return False, f"表格中缺少列: {missing_columns}", None
            
            # 标准化数据
            result_df = pd.DataFrame()
            result_df['ear_tag'] = df[field_mappings['耳号']].astype(str).str.lstrip('0').replace('', '0')
            result_df['disease_date'] = pd.to_datetime(df[field_mappings['发病日期']], errors='coerce')
            result_df['disease_type'] = df[field_mappings['疾病种类']].astype(str)
            
            # 筛选乳房炎相关疾病
            mastitis_keywords = ['乳房炎', '乳房疾病', '乳房感染']
            mastitis_condition = result_df['disease_type'].str.contains('|'.join(mastitis_keywords), na=False)
            result_df = result_df[mastitis_condition]
            
            # 清理数据
            result_df = result_df.dropna(subset=['ear_tag', 'disease_date'])
            result_df = result_df[result_df['ear_tag'] != 'nan']
            
            logger.info(f"自定义系统发病查询导出表处理完成: {len(result_df)}条乳房炎记录")
            return True, f"成功处理{len(result_df)}条乳房炎发病记录", result_df
            
        except Exception as e:
            logger.error(f"处理自定义系统发病查询导出表出错: {e}")
            return False, str(e), None

    def _extract_monthly_scc_data(self, screening_data: pd.DataFrame, selected_months: List[str], dhi_data_list: List[Dict]) -> Optional[pd.DataFrame]:
        """从DHI数据中提取所选月份的体细胞数
        
        Args:
            screening_data: 筛查数据
            selected_months: 选择的月份列表
            dhi_data_list: DHI数据列表
            
        Returns:
            包含体细胞数的DataFrame，列为ear_tag和各月份的体细胞数
        """
        try:
            if not selected_months or not dhi_data_list or screening_data.empty:
                logger.warning("体细胞数据提取失败：参数为空")
                return None
            
            logger.info(f"开始提取体细胞数据，选择月份: {selected_months}")
            logger.info(f"筛查数据列: {screening_data.columns.tolist()}")
            logger.info(f"筛查数据行数: {len(screening_data)}")
            
            # 合并所有DHI数据
            all_dhi = []
            for item in dhi_data_list:
                df = item['data'].copy()
                if 'somatic_cell_count' in df.columns:
                    all_dhi.append(df)
            
            if not all_dhi:
                logger.warning("没有找到包含体细胞数的DHI数据")
                return None
            
            combined_dhi = pd.concat(all_dhi, ignore_index=True)
            
            # 确定使用的ID字段
            if 'management_id' in combined_dhi.columns:
                dhi_id_column = 'management_id'
            elif 'ear_tag' in combined_dhi.columns:
                dhi_id_column = 'ear_tag'
            else:
                logger.warning("DHI数据中没有找到management_id或ear_tag字段")
                return None
            
            # 检查必要字段（移除farm_id依赖）
            required_fields = [dhi_id_column, 'sample_date', 'somatic_cell_count']
            missing_fields = [field for field in required_fields if field not in combined_dhi.columns]
            
            if missing_fields:
                logger.warning(f"DHI数据缺少必要字段: {missing_fields}")
                return None
            
            # 添加年月列（格式：YYYY年MM月）
            combined_dhi['year_month'] = pd.to_datetime(combined_dhi['sample_date']).dt.strftime('%Y年%m月')
            
            # 检查筛查数据中使用的ID字段，并与DHI数据匹配
            if 'ear_tag' in screening_data.columns and 'ear_tag' in combined_dhi.columns:
                # 两边都有ear_tag字段
                id_column = 'ear_tag'
                cow_ids = screening_data['ear_tag'].unique()
            elif 'management_id' in screening_data.columns and 'management_id' in combined_dhi.columns:
                # 两边都有management_id字段
                id_column = 'management_id'
                cow_ids = screening_data['management_id'].unique()
            elif 'ear_tag' in screening_data.columns and 'management_id' in combined_dhi.columns:
                # 筛查数据用ear_tag，DHI数据用management_id，尝试匹配
                id_column = 'management_id'  # 使用DHI数据的字段
                # 假设ear_tag就是management_id（乳房炎筛查中通常如此）
                cow_ids = screening_data['ear_tag'].unique()
                logger.info("筛查数据使用ear_tag，DHI数据使用management_id，将尝试直接匹配")
            elif 'management_id' in screening_data.columns and 'ear_tag' in combined_dhi.columns:
                # 筛查数据用management_id，DHI数据用ear_tag
                id_column = 'ear_tag'  # 使用DHI数据的字段
                cow_ids = screening_data['management_id'].unique()
                logger.info("筛查数据使用management_id，DHI数据使用ear_tag，将尝试直接匹配")
            else:
                logger.error("无法在筛查数据和DHI数据之间找到匹配的ID字段")
                return None
            
            # 初始化结果DataFrame
            result_data = {id_column: cow_ids}
            
            # 为每个选择的月份提取体细胞数
            for month in selected_months:
                # 筛选该月份的数据
                month_data = combined_dhi[combined_dhi['year_month'] == month]
                
                if month_data.empty:
                    # 该月份没有数据，填充空值
                    result_data[f'scc_{month}'] = [None] * len(cow_ids)
                    logger.debug(f"月份{month}没有体细胞数据")
                    continue
                
                # 按ID分组，计算该月的平均体细胞数
                month_scc = month_data.groupby(id_column)['somatic_cell_count'].mean()
                
                # 为每个ID获取体细胞数
                scc_values = []
                valid_count = 0
                for cow_id in cow_ids:
                    if cow_id in month_scc.index:
                        scc_values.append(round(month_scc[cow_id], 1))
                        valid_count += 1
                    else:
                        scc_values.append(None)
                
                result_data[f'scc_{month}'] = scc_values
                
                logger.info(f"月份{month}体细胞数提取完成，有数据的牛只: {valid_count}/{len(cow_ids)}")
            
            result_df = pd.DataFrame(result_data)
            
            logger.info(f"✅ 体细胞数据提取完成: {len(selected_months)}个月份，{len(cow_ids)}头牛")
            logger.info(f"返回的体细胞数据列: {result_df.columns.tolist()}")
            logger.info(f"返回的体细胞数据行数: {len(result_df)}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"提取月度体细胞数据时出错: {e}")
            return None