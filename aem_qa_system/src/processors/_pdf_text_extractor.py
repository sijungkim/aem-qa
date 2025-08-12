# src/processors/pdf_text_extractor.py

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import List

class PDFTextExtractor:
    """PDF에서 텍스트를 추출하는 단순한 클래스"""
    
    def __init__(self, min_text_length: int = 20):
        self.min_text_length = min_text_length

    def extract_segments_from_pdf(self, pdf_path: str) -> List[str]:
        """PDF에서 의미 있는 텍스트 세그먼트 리스트를 반환합니다."""
        segments = []
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    
                    # 페이지별 텍스트를 문장 단위로 분할
                    sentences = self._split_into_sentences(text)
                    segments.extend(sentences)
                    
        except Exception as e:
            print(f"   - ⚠️ PDF 읽기 오류 ({Path(pdf_path).name}): {e}")
            
        # 의미 있는 문장만 필터링
        return [seg for seg in segments if self._is_valid_segment(seg)]

    def _split_into_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할합니다."""
        # 1. 줄바꿈을 기준으로 먼저 분할 (목차, 제목 등 처리)
        lines = text.split('\n')
        sentences = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 2. 목차나 제목 형태인지 확인
            if self._is_table_of_contents_line(line):
                # 목차는 줄 단위로 처리
                sentences.append(line)
            else:
                # 3. 일반 텍스트는 문장 기호로 분할
                line_sentences = re.split(r'[.!?]+\s+', line)
                sentences.extend([s.strip() for s in line_sentences if s.strip()])
        
        return [self._clean_text(s) for s in sentences if s.strip()]

    def _is_table_of_contents_line(self, line: str) -> bool:
        """목차나 제목 라인인지 판단합니다."""
        # 점선이 많이 포함된 경우 (목차)
        if line.count('.') > 10:
            return True
        # 페이지 번호로 끝나는 경우
        if re.search(r'\d+\s*$', line):
            return True
        # 짧고 대문자가 많은 경우 (제목)
        if len(line) < 100 and sum(1 for c in line if c.isupper()) / len(line) > 0.3:
            return True
        return False

    def _clean_text(self, text: str) -> str:
        """텍스트를 정제합니다."""
        # 목차의 점선 제거
        cleaned = re.sub(r'\.{3,}', ' ', text)
        # 연속된 공백을 하나로 통합
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def _is_valid_segment(self, text: str) -> bool:
        """의미 있는 문장인지 판단합니다."""
        if len(text) < self.min_text_length:
            return False
        
        # 최소한의 알파벳이나 한글이 포함되어야 함
        if not re.search(r'[a-zA-Z가-힣]', text):
            return False
            
        # 순수 숫자는 제외
        if re.match(r'^\d+$', text.strip()):
            return False
        
        # 너무 짧은 단어들만 있는 문장 제외 (예: "A B C D")
        words = text.split()
        if len(words) > 3 and all(len(word) <= 2 for word in words):
            return False
            
        return True