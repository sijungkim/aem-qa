# aem_qa_station/modules/searcher.py

import streamlit as st
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import torch
from .connections import get_chroma_client

class TranslationSearcher:
    """ChromaDB를 사용한 AI 번역 추천 클래스"""
    
    def __init__(self, lang_pair: str = "en_ko"):
        self.lang_pair = lang_pair
        self.chroma_client = get_chroma_client()
        self.collection = self._get_collection()
        self.embedding_model = self._load_embedding_model()
    
    @st.cache_resource
    def _load_embedding_model(_self):
        """임베딩 모델을 로드합니다. (Streamlit 캐시 적용)"""
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = SentenceTransformer('intfloat/multilingual-e5-large', device=device)
        print(f"✅ 임베딩 모델 로드 완료 ({device})")
        return model
    
    def _get_collection(self):
        """ChromaDB 컬렉션을 가져옵니다."""
        try:
            collection_name = f"tm_{self.lang_pair}"
            collection = self.chroma_client.get_collection(name=collection_name)
            print(f"✅ ChromaDB 컬렉션 '{collection_name}' 연결 완료")
            return collection
        except Exception as e:
            print(f"❌ ChromaDB 컬렉션 연결 실패: {e}")
            return None
    
    def search_similar_translations(self, query_text: str, 
                                  top_k: int = 3,
                                  exclude_exact_match: bool = True) -> List[Dict]:
        """입력 텍스트와 유사한 번역 사례를 검색합니다."""
        if not self.collection or not query_text.strip():
            return []
        
        try:
            # 1. 검색어를 벡터로 변환
            query_embedding = self.embedding_model.encode(
                query_text, 
                convert_to_tensor=True
            ).tolist()
            
            # 2. ChromaDB에서 유사한 문서 검색 (더 많이 가져와서 필터링)
            search_limit = min(top_k * 3, 15)  # 3배 더 가져오기
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=search_limit
            )
            
            # 3. 결과 정리 및 필터링
            recommendations = []
            query_text_clean = query_text.strip().lower()
            
            for i in range(len(results['ids'][0])):
                source_text = results['documents'][0][i]
                similarity_score = 1 - results['distances'][0][i]
                
                # 자기 자신 제외 (정확히 동일한 텍스트)
                if exclude_exact_match and source_text.strip().lower() == query_text_clean:
                    continue
                
                # 유사도가 너무 낮으면 제외
                if similarity_score < 0.3:
                    continue
                    
                # 100% 유사도도 제외 (거의 동일한 텍스트)
                if similarity_score >= 0.99:
                    continue
                
                metadata = results['metadatas'][0][i]
                recommendations.append({
                    'source_text': source_text,
                    'target_text': metadata.get('target_text', 'N/A'),
                    'similarity_score': round(similarity_score, 3),
                    'page_path': metadata.get('page_path', ''),
                    'component_path': metadata.get('component_path', ''),
                    'confidence_level': self._get_confidence_level(similarity_score)
                })
                
                # 원하는 개수만큼 찾았으면 중단
                if len(recommendations) >= top_k:
                    break
            
            return recommendations
            
        except Exception as e:
            print(f"❌ 번역 검색 중 오류: {e}")
            return []
    
    def search_multiple_texts(self, texts: List[str], 
                            top_k_per_text: int = 2) -> Dict[str, List[Dict]]:
        """여러 텍스트에 대해 일괄 검색을 수행합니다."""
        results = {}
        
        for text in texts:
            if text.strip():
                recommendations = self.search_similar_translations(
                    text, 
                    top_k=top_k_per_text
                )
                results[text] = recommendations
            
        return results
    
    def _get_confidence_level(self, similarity_score: float) -> str:
        """유사도 점수에 따른 신뢰도 레벨을 반환합니다."""
        if similarity_score >= 0.8:
            return "높음"
        elif similarity_score >= 0.6:
            return "보통"
        elif similarity_score >= 0.4:
            return "낮음"
        else:
            return "매우낮음"
    
    def get_stats(self) -> Dict:
        """검색 데이터베이스의 통계 정보를 반환합니다."""
        if not self.collection:
            return {"error": "컬렉션 연결 실패"}
        
        try:
            count = self.collection.count()
            return {
                "total_translations": count,
                "language_pair": self.lang_pair,
                "status": "정상"
            }
        except Exception as e:
            return {"error": str(e)}

# 편의 함수들
def search_translation_for_text(text: str, lang_pair: str = "en_ko", 
                               top_k: int = 3) -> List[Dict]:
    """단일 텍스트에 대한 번역 추천을 위한 편의 함수"""
    searcher = TranslationSearcher(lang_pair)
    return searcher.search_similar_translations(text, top_k)

def batch_search_translations(texts: List[str], lang_pair: str = "en_ko") -> Dict:
    """여러 텍스트 일괄 검색을 위한 편의 함수"""
    searcher = TranslationSearcher(lang_pair)
    return searcher.search_multiple_texts(texts)

def format_recommendation_for_display(recommendation: Dict) -> str:
    """추천 결과를 UI 표시용으로 포맷팅합니다."""
    confidence_emoji = {
        "높음": "🟢",
        "보통": "🟡", 
        "낮음": "🟠",
        "매우낮음": "🔴"
    }
    
    emoji = confidence_emoji.get(recommendation['confidence_level'], "⚪")
    similarity = recommendation['similarity_score']
    
    return (
        f"{emoji} **{recommendation['target_text']}** "
        f"(유사도: {similarity:.1%})\n"
        f"📍 출처: `{recommendation['page_path']}`"
    )