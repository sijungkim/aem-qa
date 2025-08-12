# src/collectors/data_models.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class FileInfo:
    """다운로드된 파일의 정보를 담는 데이터 클래스"""
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    page_path: Optional[str] = None
    version_name: Optional[str] = None