# src/processors/translation_pair_generator.py

import numpy as np
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import RAG_EMBEDDING_MODEL

class TranslationPairGenerator:
    """임베딩 유사도를 사용하여 번역 쌍을 생성하는 클래스"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.embedding_model = None

    def load_embedding_model(self):
        """임베딩 모델을 로드합니다."""
        print("🤖 임베딩 모델을 로드하는 중...")
        self.embedding_model = SentenceTransformer(RAG_EMBEDDING_MODEL)
        print("✅ 임베딩 모델 로드 완료.")

    def generate_pairs(self, source_segments: List[str], target_segments: List[str], 
                      target_pdf_path: str, source_lang: str = 'en', target_lang: str = 'ko') -> List[Dict]:
        """소스와 타겟 언어 세그먼트에서 번역 쌍을 생성합니다."""
        if not self.embedding_model:
            self.load_embedding_model()
        
        if not source_segments or not target_segments:
            return []
        
        # 임베딩 계산
        source_embeddings = self._compute_embeddings(source_segments)
        target_embeddings = self._compute_embeddings(target_segments)
        
        # 유사도 매칭
        return self._match_by_similarity(
            source_segments, target_segments, 
            source_embeddings, target_embeddings,
            target_pdf_path, source_lang, target_lang
        )

    def _compute_embeddings(self, segments: List[str]) -> np.ndarray:
        """텍스트 세그먼트들의 임베딩을 계산합니다."""
        return self.embedding_model.encode(segments, show_progress_bar=False)

    def _match_by_similarity(self, source_segments: List[str], target_segments: List[str],
                           source_embeddings: np.ndarray, target_embeddings: np.ndarray,
                           target_pdf_path: str, source_lang: str, target_lang: str) -> List[Dict]:
        """유사도 기반으로 번역 쌍을 매칭합니다."""
        pairs = []
        target_filename = Path(target_pdf_path).name
        used_target_indices = set()
        
        for i, source_segment in enumerate(source_segments):
            # 유사도 계산
            similarities = cosine_similarity([source_embeddings[i]], target_embeddings)[0]
            
            # 가장 높은 유사도 찾기
            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]
            
            # 임계값 이상이고 아직 사용되지 않은 경우
            if (best_similarity >= self.similarity_threshold and 
                best_idx not in used_target_indices):
                
                pairs.append({
                    'source_text': source_segment.strip(),
                    'target_text': target_segments[best_idx].strip(),
                    'similarity_score': round(float(best_similarity), 4),
                    'source_file': target_filename,
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'pair_type': 'pdf_extracted'
                })
                
                used_target_indices.add(best_idx)
        
        return pairs