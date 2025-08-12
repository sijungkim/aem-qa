# src/processors/pdf_pair_matcher.py

import os
import pandas as pd
from pathlib import Path
from typing import List, Tuple
from src.config import PDF_DOWNLOAD_DIR, INPUT_DIR

class PDFPairMatcher:
    """다국어 PDF 페어를 찾는 클래스"""
    
    def __init__(self, source_lang: str = 'en', target_lang: str = 'ko'):
        """
        Args:
            source_lang: 소스 언어 (기본: 영어)
            target_lang: 타겟 언어 (한국어 또는 일본어)
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.csv_filename = f"pdf_list_master_{source_lang}_{target_lang}.csv"

    def find_pdf_pairs(self) -> List[Tuple[str, str]]:
        """지정된 언어 쌍의 PDF 페어를 반환합니다."""
        csv_path = os.path.join(INPUT_DIR, self.csv_filename)
        
        if not os.path.exists(csv_path):
            print(f"❌ 매칭 테이블을 찾을 수 없습니다: {csv_path}")
            return []
        
        # 매칭 테이블 로드
        df = pd.read_csv(csv_path)
        print(f"📋 {self.source_lang.upper()}-{self.target_lang.upper()} 매칭 테이블에서 {len(df)}개 항목을 로드했습니다.")
        
        pairs = []
        source_col = f"{self.source_lang.upper()}_Path"
        target_col = f"{self.target_lang.upper()}_Path"
        
        for _, row in df.iterrows():
            source_path = row.get(source_col)
            target_path = row.get(target_col)
            
            # 둘 다 존재하는 경우만 처리
            if pd.notna(source_path) and pd.notna(target_path):
                local_source_path = self._get_local_pdf_path(source_path, self.source_lang)
                local_target_path = self._get_local_pdf_path(target_path, self.target_lang)
                
                # 두 파일이 모두 존재하는 경우만 페어로 추가
                if local_source_path and local_target_path:
                    pairs.append((local_source_path, local_target_path))
        
        print(f"✅ 실제 존재하는 {len(pairs)}개의 {self.source_lang.upper()}-{self.target_lang.upper()} PDF 페어를 발견했습니다.")
        return pairs

    def _get_local_pdf_path(self, remote_path: str, lang: str) -> str:
        """원격 경로를 로컬 다운로드 경로로 변환하고 파일 존재 여부를 확인합니다."""
        filename = Path(remote_path).name
        local_path = os.path.join(PDF_DOWNLOAD_DIR, lang, filename)
        
        if os.path.exists(local_path):
            return local_path
        else:
            return None