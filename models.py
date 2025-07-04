from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date


class FilterConfig(BaseModel):
    """筛选条件配置"""
    field: str
    enabled: bool = True
    required: bool = False
    min: Optional[float] = None
    max: Optional[float] = None
    allowed: Optional[List[str]] = None
    default_start: Optional[str] = None
    default_end: Optional[str] = None
    include_null_as_match: bool = False  # 是否将数据为空的判定为符合


class UploadResponse(BaseModel):
    """文件上传响应"""
    success: bool
    message: str
    file_id: Optional[str] = None
    detected_date: Optional[str] = None
    row_count: Optional[int] = None


class FilterRequest(BaseModel):
    """筛选请求"""
    file_id: str
    filters: Dict[str, Any]
    date_range: Optional[Dict[str, str]] = None


class FilterResult(BaseModel):
    """筛选结果"""
    success: bool
    message: str
    total_rows: int
    filtered_rows: int
    download_url: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None


class FileInfo(BaseModel):
    """文件信息"""
    filename: str
    size: int
    upload_time: datetime
    detected_date: Optional[str] = None
    status: str = "uploaded"  # uploaded, processing, completed, error


class FieldMapping(BaseModel):
    """字段映射"""
    chinese_name: str
    english_name: str
    data_type: str = "string"  # string, numeric, date
    required: bool = False


class BatchUploadFile(BaseModel):
    """批量上传单个文件信息"""
    filename: str
    message: str
    row_count: int
    date_range: Optional[Dict[str, str]] = None


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    success: bool
    message: str
    success_files: List[BatchUploadFile]
    failed_files: List[Dict[str, str]]
    overall_date_range: Optional[Dict[str, str]] = None
    farm_ids: List[str] = []


class BatchFilterRequest(BaseModel):
    """批量筛选请求"""
    selected_files: List[str]
    filters: Dict[str, Any]
    display_fields: List[str] 