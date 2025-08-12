# src/processors/hybrid_pdf_pair_extractor.py (X축 좌표 추가 버전)

import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple, Dict

class HybridPDFPairExtractor:
    """
    레이아웃(X,Y 좌표)과 의미(임베딩)를 함께 분석하여 PDF 번역쌍을 추출하는 클래스.
    """

    def __init__(self, model_name: str = 'intfloat/multilingual-e5-large'):
        """모델을 초기화합니다."""
        print("🤖 임베딩 모델을 로드하는 중... (최초 실행 시 시간이 걸릴 수 있습니다)")
        self.model = SentenceTransformer(model_name)
        print("✅ 모델 로드 완료.")

    def _get_table_areas(self, doc: fitz.Document) -> List[List[Dict]]:
        """PyMuPDF를 사용해 페이지별 테이블의 위치(bounding box)를 찾습니다."""
        areas_by_page = []
        for page in doc:
            page_areas = []
            tables = page.find_tables()
            for table in tables:
                page_areas.append({'top': table.bbox[1], 'bottom': table.bbox[3]})
            areas_by_page.append(page_areas)
        return areas_by_page

    def _extract_text_blocks(self, doc: fitz.Document, table_areas_by_page: List[List[Dict]]) -> List[List[Tuple]]:
        """PyMuPDF를 사용해 표(table) 영역을 제외한 텍스트 블록을 추출합니다."""
        blocks_by_page = []
        for i, page in enumerate(doc):
            page_blocks = []
            table_areas = table_areas_by_page[i]
            blocks = page.get_text("blocks")
            for block in blocks:
                x0, y0, x1, y1, text, _, _ = block
                text = " ".join(text.strip().split())
                if not text:
                    continue

                is_in_table = False
                for table_area in table_areas:
                    block_center_y = (y0 + y1) / 2
                    if table_area['top'] <= block_center_y <= table_area['bottom']:
                        is_in_table = True
                        break
                
                if not is_in_table:
                    page_blocks.append(block)
            blocks_by_page.append(page_blocks)
        return blocks_by_page

    def generate_pairs(self, source_pdf_path: str, target_pdf_path: str, 
                       y_tolerance: int = 10, x_tolerance: int = 50, 
                       similarity_threshold: float = 0.65) -> pd.DataFrame:
        """
        두 PDF 파일 경로를 받아 번역쌍을 생성하고 결과를 DataFrame으로 반환합니다.
        x_tolerance: X축(수평) 위치 허용 오차 (픽셀)
        """
        all_pairs = []
        source_doc = fitz.open(source_pdf_path)
        target_doc = fitz.open(target_pdf_path)

        source_table_areas = self._get_table_areas(source_doc)
        target_table_areas = self._get_table_areas(target_doc)

        source_blocks = self._extract_text_blocks(source_doc, source_table_areas)
        target_blocks = self._extract_text_blocks(target_doc, target_table_areas)

        with pdfplumber.open(source_pdf_path) as source_pdf, pdfplumber.open(target_pdf_path) as target_pdf:
            num_pages = min(len(source_pdf.pages), len(target_pdf.pages))
            
            for i in range(num_pages):
                print(f"\r   - 페이지 처리 중: {i + 1}/{num_pages}", end="")
                
                # 표 매칭
                source_tables = source_pdf.pages[i].extract_tables()
                target_tables = target_pdf.pages[i].extract_tables()
                if source_tables and len(source_tables) == len(target_tables):
                    for tbl_idx, source_table in enumerate(source_tables):
                        target_table = target_tables[tbl_idx]
                        if len(source_table) == len(target_table):
                            for row_idx, source_row in enumerate(source_table):
                                if len(source_row) == len(target_table[row_idx]):
                                    for col_idx, source_cell in enumerate(source_row):
                                        target_cell = target_table[row_idx][col_idx]
                                        if source_cell and target_cell:
                                            all_pairs.append({
                                                'source_text': " ".join(str(source_cell).split()),
                                                'target_text': " ".join(str(target_cell).split()),
                                                'similarity_score': 1.0,
                                                'page': i + 1, 'type': 'table'
                                            })
                
                # 텍스트 블록 매칭
                page_source_blocks = source_blocks[i]
                page_target_blocks = target_blocks[i]

                if not page_source_blocks or not page_target_blocks:
                    continue

                source_texts = [block[4] for block in page_source_blocks]
                target_texts = [block[4] for block in page_target_blocks]
                source_embeddings = self.model.encode(source_texts, convert_to_tensor=True)
                target_embeddings = self.model.encode(target_texts, convert_to_tensor=True)
                
                for s_idx, source_block in enumerate(page_source_blocks):
                    source_x = source_block[0]
                    source_y = (source_block[1] + source_block[3]) / 2
                    
                    best_match_score = 0
                    best_match_target_text = None

                    for t_idx, target_block in enumerate(page_target_blocks):
                        target_x = target_block[0]
                        target_y = (target_block[1] + target_block[3]) / 2
                        
                        # ▼▼▼▼▼ 핵심 변경사항 ▼▼▼▼▼
                        # Y축과 X축 위치를 모두 확인
                        if (abs(source_y - target_y) < y_tolerance and 
                            abs(source_x - target_x) < x_tolerance):
                        # ▲▲▲▲▲ 핵심 변경사항 ▲▲▲▲▲
                            similarity = util.cos_sim(source_embeddings[s_idx], target_embeddings[t_idx]).item()
                            if similarity > best_match_score:
                                best_match_score = similarity
                                best_match_target_text = target_block[4]

                    if best_match_score > similarity_threshold:
                        all_pairs.append({
                            'source_text': source_block[4],
                            'target_text': best_match_target_text,
                            'similarity_score': round(best_match_score, 4),
                            'page': i + 1, 'type': 'text'
                        })
        
        source_doc.close()
        target_doc.close()
        print("\n   - ✅ 매칭 완료.")

        if not all_pairs:
            return pd.DataFrame()

        df = pd.DataFrame(all_pairs)
        df.drop_duplicates(subset=['source_text', 'target_text'], inplace=True)
        return df