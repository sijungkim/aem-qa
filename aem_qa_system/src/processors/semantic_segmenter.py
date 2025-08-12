# src/processors/semantic_segmenter.py

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import spacy
from typing import List, Dict, Tuple
from datetime import datetime
import re

class SemanticSegmenter:
    """의미 임베딩 기반 지능형 텍스트 분할"""
    
    def __init__(self):
        # 다국어 임베딩 모델 (기존 ChromaDB와 동일)
        self.embedding_model = SentenceTransformer('intfloat/multilingual-e5-large')
        
        # 문장 분할 모델들
        self.nlp_models = {}
        self._load_spacy_models()
        
        # 분할 설정 (적응적 분할 최적화)
        self.config = {
            'min_segment_length': 15,      # 최소 세그먼트 길이 (더 유연하게)
            'max_segment_length': 150,     # 최대 세그먼트 길이
            'optimal_length': 70,          # 목표 길이 (약간 줄임)
            'similarity_threshold': 0.72,  # 의미 유사도 임계값 (약간 낮춤)
            'min_sentence_length': 8,      # 최소 문장 길이 (더 유연하게)
            
            # 적응적 분할 기준들
            'very_long_threshold': 300,    # 매우 긴 텍스트 기준
            'long_threshold': 200,         # 긴 텍스트 기준  
            'medium_threshold': 120,       # 중간 길이 기준
            'max_sentences_threshold': 3,  # 최대 문장 수 기준
            'complexity_threshold': 0.7,   # 복잡도 임계값
            'length_ratio_threshold': 0.6  # 길이 비율 임계값
        }
        
        print("✅ Semantic Segmenter 초기화 완료")
        print(f"   - 임베딩 모델: {self.embedding_model}")
        print(f"   - 설정: {self.config}")
    
    def _load_spacy_models(self):
        """spaCy 모델 로드"""
        models = {
            'en': 'en_core_web_sm',
            'ko': 'ko_core_news_sm',  # pip install spacy-koNLPy
            'ja': 'ja_core_news_sm'
        }
        
        for lang, model_name in models.items():
            try:
                self.nlp_models[lang] = spacy.load(model_name)
                print(f"   ✅ {lang}: {model_name} 로드 완료")
            except OSError:
                print(f"   ⚠️ {lang}: {model_name} 모델 없음 - 기본 분할 사용")
                self.nlp_models[lang] = None
    
    def segment_text_pair(self, source_text: str, target_text: str, 
                         source_lang: str, target_lang: str,
                         original_metadata: Dict) -> List[Dict]:
        """메인 함수: 텍스트 쌍을 의미 기반으로 분할"""
        
        # 분할 필요성 검사
        if not self._needs_segmentation(source_text, target_text):
            return [{
                **original_metadata,
                'source_text': source_text,
                'target_text': target_text,
                'segment_index': 0,
                'total_segments': 1,
                'segment_order': 0,
                'original_component_order': original_metadata.get('component_order', 0),
                'segment_type': 'no_split_needed',
                'is_segmented': False,
                'segmentation_reason': 'below_threshold',
                'segmentation_conditions_checked': {
                    'max_length': max(len(source_text), len(target_text)),
                    'avg_length': (len(source_text) + len(target_text)) / 2,
                    'source_sentences': self._count_sentences(source_text, 'source'),
                    'target_sentences': self._count_sentences(target_text, 'target'),
                    'complexity_score': self._calculate_text_complexity(source_text, target_text),
                    'length_imbalance': self._has_length_imbalance(source_text, target_text)
                }
            }]
        
        print(f"🔍 적응적 분할 시작: {len(source_text)}자 vs {len(target_text)}자")
        print(f"   목표: 의미 일관성 유지하며 {self.config['optimal_length']}자 내외 세그먼트 생성")
        
        try:
            # 1. 초기 문장 분할
            source_sentences = self._split_into_sentences(source_text, source_lang)
            target_sentences = self._split_into_sentences(target_text, target_lang)
            
            print(f"   - 문장 분할: Source {len(source_sentences)}개, Target {len(target_sentences)}개")
            
            # 2. 임베딩 계산
            source_embeddings = self._compute_embeddings(source_sentences)
            target_embeddings = self._compute_embeddings(target_sentences)
            
            # 3. 의미 기반 세그먼트 생성
            source_segments = self._create_semantic_segments(source_sentences, source_embeddings)
            target_segments = self._create_semantic_segments(target_sentences, target_embeddings)
            
            print(f"   - 세그먼트 생성: Source {len(source_segments)}개, Target {len(target_segments)}개")
            
            # 4. 번역 쌍 정렬
            aligned_pairs = self._align_translation_pairs(
                source_segments, target_segments, 
                source_embeddings, target_embeddings
            )
            
            print(f"   - 정렬 완료: {len(aligned_pairs)}개 쌍")
            
            # 5. 메타데이터 보존하여 최종 결과 생성
            segmented_records = self._create_segmented_records(
                aligned_pairs, original_metadata, source_text, target_text
            )
            
            return segmented_records
            
        except Exception as e:
            print(f"❌ 분할 실패: {str(e)} - 원본 반환")
            return [{
                **original_metadata,
                'source_text': source_text,
                'target_text': target_text,
                'segment_index': 0,
                'total_segments': 1,
                'segment_order': 0,
                'original_component_order': original_metadata.get('component_order', 0),
                'segment_type': 'segmentation_failed',
                'is_segmented': False,
                'segmentation_error': str(e)
            }]
    
    def _needs_segmentation(self, source_text: str, target_text: str) -> bool:
        """적응적 분할 필요성 판단"""
        max_length = max(len(source_text), len(target_text))
        avg_length = (len(source_text) + len(target_text)) / 2
        
        # 문장 수 계산 (언어별 패턴)
        source_sentences = self._count_sentences(source_text, 'source')
        target_sentences = self._count_sentences(target_text, 'target')
        max_sentences = max(source_sentences, target_sentences)
        
        # 복잡도 점수 계산
        complexity_score = self._calculate_text_complexity(source_text, target_text)
        
        # 적응적 분할 조건 (여러 조건 중 하나라도 만족하면 분할)
        conditions = {
            'very_long': max_length > 300,                    # 매우 긴 텍스트
            'long_text': max_length > 200,                    # 긴 텍스트
            'multiple_sentences': max_sentences > 3,          # 다중 문장
            'medium_multi': max_length > 120 and max_sentences > 2,  # 중간 길이 + 복수 문장
            'complex_text': complexity_score > 0.7,           # 복잡한 텍스트
            'length_imbalance': self._has_length_imbalance(source_text, target_text)  # 길이 불균형
        }
        
        # 분할 사유 저장 (디버깅용)
        triggered_conditions = [k for k, v in conditions.items() if v]
        
        needs_split = len(triggered_conditions) > 0
        
        if needs_split:
            print(f"   🔍 분할 조건 충족: {triggered_conditions}")
            print(f"      길이: {len(source_text)}↔{len(target_text)}, 문장: {source_sentences}↔{target_sentences}")
        
        return needs_split
    
    def _count_sentences(self, text: str, text_type: str) -> int:
        """언어 패턴을 고려한 문장 수 계산"""
        if not text.strip():
            return 0
        
        # 다국어 문장 종료 패턴
        sentence_patterns = [
            r'[.!?]+\s+',     # 영어: 마침표+공백
            r'[。！？]+\s*',   # 일본어: 일본어 마침표
            r'[.!?。]+\s*'    # 한국어: 혼합 패턴
        ]
        
        max_sentence_count = 0
        for pattern in sentence_patterns:
            sentences = re.split(pattern, text.strip())
            sentences = [s.strip() for s in sentences if s.strip()]
            max_sentence_count = max(max_sentence_count, len(sentences))
        
        return max_sentence_count
    
    def _calculate_text_complexity(self, source_text: str, target_text: str) -> float:
        """텍스트 복잡도 점수 계산 (0.0-1.0)"""
        complexity_score = 0.0
        
        # 1. 특수문자 밀도
        for text in [source_text, target_text]:
            special_chars = len(re.findall(r'[^\w\s가-힣ぁ-ゟァ-ヾ一-龯]', text))
            if len(text) > 0:
                special_ratio = special_chars / len(text)
                complexity_score += special_ratio * 0.3
        
        # 2. 긴 단어 비율
        for text in [source_text, target_text]:
            words = text.split()
            if words:
                long_words = [w for w in words if len(w) > 8]
                long_word_ratio = len(long_words) / len(words)
                complexity_score += long_word_ratio * 0.2
        
        # 3. 연속된 대문자 (약어/기술용어)
        for text in [source_text, target_text]:
            caps_sequences = re.findall(r'[A-Z]{2,}', text)
            if len(text) > 0:
                caps_ratio = len(''.join(caps_sequences)) / len(text)
                complexity_score += caps_ratio * 0.3
        
        # 4. 괄호, 콜론 등 구조적 요소
        structural_elements = 0
        for text in [source_text, target_text]:
            structural_elements += len(re.findall(r'[():;,\-–—]', text))
        
        if len(source_text) + len(target_text) > 0:
            structural_ratio = structural_elements / (len(source_text) + len(target_text))
            complexity_score += structural_ratio * 0.2
        
        return min(complexity_score / 2, 1.0)  # 2로 나누어 정규화
    
    def _has_length_imbalance(self, source_text: str, target_text: str) -> bool:
        """번역 쌍 길이 불균형 검사"""
        if not source_text or not target_text:
            return False
        
        ratio = min(len(source_text), len(target_text)) / max(len(source_text), len(target_text))
        
        # 길이 비율이 너무 차이나고, 둘 중 하나가 충분히 길면 분할 고려
        return ratio < 0.6 and max(len(source_text), len(target_text)) > 150
    
    def _split_into_sentences(self, text: str, language: str) -> List[str]:
        """언어별 문장 분할"""
        nlp = self.nlp_models.get(language)
        
        if nlp:
            # spaCy 기반 지능형 분할
            doc = nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # 폴백: 규칙 기반 분할
            sentences = self._rule_based_split(text, language)
        
        # 너무 짧은 문장 필터링
        sentences = [s for s in sentences if len(s) >= self.config['min_sentence_length']]
        
        return sentences
    
    def _rule_based_split(self, text: str, language: str) -> List[str]:
        """규칙 기반 문장 분할 (폴백)"""
        patterns = {
            'en': r'[.!?]+\s+(?=[A-Z])',
            'ko': r'[.!?。]+\s*',
            'ja': r'[。！？]+\s*'
        }
        
        pattern = patterns.get(language, r'[.!?]+\s+')
        sentences = re.split(pattern, text.strip())
        return [s.strip() for s in sentences if s.strip()]
    
    def _compute_embeddings(self, sentences: List[str]) -> np.ndarray:
        """문장 임베딩 계산"""
        if not sentences:
            return np.array([])
        
        embeddings = self.embedding_model.encode(
            sentences, 
            show_progress_bar=False,
            convert_to_tensor=False,
            normalize_embeddings=True  # 코사인 유사도 최적화
        )
        
        return embeddings
    
    def _create_semantic_segments(self, sentences: List[str], embeddings: np.ndarray) -> List[Dict]:
        """의미적 유사도 기반 세그먼트 생성"""
        if len(sentences) <= 1:
            return [{'text': ' '.join(sentences), 'sentences': sentences, 'embedding': embeddings[0] if len(embeddings) > 0 else None}]
        
        # 동적 프로그래밍으로 최적 분할점 찾기
        segments = self._find_optimal_segments(sentences, embeddings)
        
        return segments
    
    def _find_optimal_segments(self, sentences: List[str], embeddings: np.ndarray) -> List[Dict]:
        """동적 프로그래밍으로 최적 세그먼트 찾기"""
        n = len(sentences)
        if n == 0:
            return []
        
        # DP 테이블: dp[i] = 0부터 i까지의 최적 분할 점수
        dp = [float('-inf')] * (n + 1)
        dp[0] = 0
        parent = [-1] * (n + 1)  # 역추적용
        
        for i in range(1, n + 1):
            for j in range(i):
                # j부터 i-1까지를 하나의 세그먼트로 만들 때의 점수
                segment_sentences = sentences[j:i]
                segment_text = ' '.join(segment_sentences)
                
                # 세그먼트 품질 점수 계산
                quality_score = self._calculate_segment_quality(
                    segment_text, segment_sentences, embeddings[j:i]
                )
                
                if dp[j] + quality_score > dp[i]:
                    dp[i] = dp[j] + quality_score
                    parent[i] = j
        
        # 역추적으로 최적 분할 복원
        segments = []
        i = n
        while i > 0:
            j = parent[i]
            segment_sentences = sentences[j:i]
            segment_text = ' '.join(segment_sentences)
            segment_embedding = np.mean(embeddings[j:i], axis=0)
            
            segments.append({
                'text': segment_text,
                'sentences': segment_sentences,
                'embedding': segment_embedding,
                'start_idx': j,
                'end_idx': i-1
            })
            i = j
        
        segments.reverse()  # 순서 복원
        return segments
    
    def _calculate_segment_quality(self, text: str, sentences: List[str], embeddings: np.ndarray) -> float:
        """세그먼트 품질 점수 계산"""
        if len(embeddings) == 0:
            return float('-inf')
        
        score = 0.0
        
        # 1. 길이 점수 (가우시안 분포)
        length = len(text)
        optimal_length = self.config['optimal_length']
        length_score = np.exp(-((length - optimal_length) ** 2) / (2 * (optimal_length/3) ** 2))
        score += length_score * 100
        
        # 2. 길이 제약 (하드 제약)
        if length < self.config['min_segment_length'] or length > self.config['max_segment_length']:
            return float('-inf')
        
        # 3. 의미적 응집도 점수
        if len(embeddings) > 1:
            # 문장 간 평균 유사도
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i+1, len(embeddings)):
                    sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                    similarities.append(sim)
            
            if similarities:
                coherence_score = np.mean(similarities)
                score += coherence_score * 50
        
        # 4. 문장 수 균형 점수 (너무 많거나 적으면 감점)
        sentence_count = len(sentences)
        if 1 <= sentence_count <= 3:
            score += 20
        elif sentence_count > 5:
            score -= 10
        
        return score
    
    def _align_translation_pairs(self, source_segments: List[Dict], target_segments: List[Dict],
                                source_embeddings: np.ndarray, target_embeddings: np.ndarray) -> List[Dict]:
        """번역 쌍 정렬 (Cross-lingual Alignment)"""
        
        # 세그먼트 임베딩 계산
        source_seg_embeddings = np.array([seg['embedding'] for seg in source_segments])
        target_seg_embeddings = np.array([seg['embedding'] for seg in target_segments])
        
        # 크로스 언어 유사도 행렬 계산
        similarity_matrix = cosine_similarity(source_seg_embeddings, target_seg_embeddings)
        
        # 헝가리안 알고리즘 또는 그리디 매칭으로 최적 정렬
        aligned_pairs = self._greedy_alignment(
            source_segments, target_segments, similarity_matrix
        )
        
        return aligned_pairs
    
    def _greedy_alignment(self, source_segments: List[Dict], target_segments: List[Dict], 
                         similarity_matrix: np.ndarray) -> List[Dict]:
        """그리디 방식으로 번역 쌍 정렬"""
        aligned_pairs = []
        used_target_indices = set()
        
        for i, source_seg in enumerate(source_segments):
            # 가장 유사한 타겟 세그먼트 찾기
            best_target_idx = -1
            best_similarity = -1
            
            for j, target_seg in enumerate(target_segments):
                if j not in used_target_indices:
                    similarity = similarity_matrix[i][j]
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_target_idx = j
            
            if best_target_idx >= 0:
                aligned_pairs.append({
                    'source_segment': source_segments[i],
                    'target_segment': target_segments[best_target_idx],
                    'alignment_confidence': best_similarity,
                    'source_index': i,
                    'target_index': best_target_idx
                })
                used_target_indices.add(best_target_idx)
            else:
                # 매칭되지 않는 소스 세그먼트 처리
                aligned_pairs.append({
                    'source_segment': source_segments[i],
                    'target_segment': None,
                    'alignment_confidence': 0.0,
                    'source_index': i,
                    'target_index': -1
                })
        
        # 매칭되지 않은 타겟 세그먼트들도 추가
        for j, target_seg in enumerate(target_segments):
            if j not in used_target_indices:
                aligned_pairs.append({
                    'source_segment': None,
                    'target_segment': target_segments[j],
                    'alignment_confidence': 0.0,
                    'source_index': -1,
                    'target_index': j
                })
        
        return aligned_pairs
    
    def _create_segmented_records(self, aligned_pairs: List[Dict], 
                                 original_metadata: Dict,
                                 original_source: str, original_target: str) -> List[Dict]:
        """메타데이터 100% 보존하여 세그먼트 레코드 생성"""
        segmented_records = []
        total_segments = len(aligned_pairs)
        
        for i, pair in enumerate(aligned_pairs):
            # 원본 메타데이터 100% 복사
            segment_record = original_metadata.copy()
            
            # 텍스트 정보 업데이트
            source_text = pair['source_segment']['text'] if pair['source_segment'] else ""
            target_text = pair['target_segment']['text'] if pair['target_segment'] else ""
            
            # 세그먼트 정보 추가
            segment_record.update({
                # === 핵심 텍스트 데이터 ===
                'source_text': source_text,
                'target_text': target_text,
                
                # === 원본 보존 ===
                'original_source_text': original_source,
                'original_target_text': original_target,
                
                # === 세그먼트 메타데이터 ===
                'segment_index': i,
                'total_segments': total_segments,
                'segment_order': i,  # 명시적 순서 필드
                'original_component_order': original_metadata.get('component_order', 0),  # 원본 컴포넌트 순서
                'segment_type': 'semantic_embedding_split',
                'is_segmented': total_segments > 1,
                
                # === 세그먼트 품질 정보 ===
                'alignment_confidence': pair['alignment_confidence'],
                'source_sentence_count': len(pair['source_segment']['sentences']) if pair['source_segment'] else 0,
                'target_sentence_count': len(pair['target_segment']['sentences']) if pair['target_segment'] else 0,
                'source_segment_length': len(source_text),
                'target_segment_length': len(target_text),
                
                # === 임베딩 정보 ===
                'has_source_embedding': pair['source_segment'] is not None,
                'has_target_embedding': pair['target_segment'] is not None,
                'cross_lingual_similarity': pair['alignment_confidence'],
                
                # === 분할 메타데이터 ===
                'segmentation_method': 'semantic_embedding_dp',
                'embedding_model': 'intfloat/multilingual-e5-large',
                'segmentation_config': self.config,
                'segmentation_timestamp': datetime.utcnow(),
                
                # === 품질 메트릭 ===
                'length_optimization_score': self._calculate_length_score(source_text, target_text),
                'semantic_coherence_score': self._calculate_coherence_score(pair),
                'translation_alignment_score': pair['alignment_confidence']
            })
            
            segmented_records.append(segment_record)
        
        return segmented_records
    
    def _calculate_length_score(self, source_text: str, target_text: str) -> float:
        """길이 최적화 점수 계산"""
        avg_length = (len(source_text) + len(target_text)) / 2
        optimal_length = self.config['optimal_length']
        
        # 가우시안 점수 (0-1)
        return np.exp(-((avg_length - optimal_length) ** 2) / (2 * (optimal_length/3) ** 2))
    
    def _calculate_coherence_score(self, pair: Dict) -> float:
        """의미 일관성 점수 계산"""
        # 소스와 타겟 모두 있는 경우만 계산
        if not (pair['source_segment'] and pair['target_segment']):
            return 0.0
        
        # 세그먼트 내 문장 수가 적절한지 확인
        source_sentences = len(pair['source_segment']['sentences'])
        target_sentences = len(pair['target_segment']['sentences'])
        
        # 문장 수 균형 점수
        if source_sentences == target_sentences and 1 <= source_sentences <= 3:
            return 1.0
        elif abs(source_sentences - target_sentences) <= 1:
            return 0.8
        else:
            return 0.5