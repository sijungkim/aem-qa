# src/processors/llm_pdf_tm_generator.py

import re
import json
from typing import List, Dict
from pathlib import Path
import ollama
from src.config import LLM_MODEL

class LLMPDFTMGenerator:
    """LLM을 활용한 고품질 PDF 번역 메모리 생성기"""
    
    def __init__(self, model_name: str = LLM_MODEL, fast_mode: bool = False, turbo_mode: bool = False):
        self.model_name = model_name
        self.fast_mode = fast_mode  
        self.turbo_mode = turbo_mode
        
    def generate_meaningful_segments(self, raw_text: str, source_lang: str = 'en', target_lang: str = 'ko') -> List[Dict]:
        """PDF 원문을 LLM을 통해 번역 메모리에 적합한 의미있는 세그먼트로 재구성"""
        # 1단계: 텍스트 전처리 및 청크 분할
        chunks = self._split_into_chunks(raw_text)
        
        all_segments = []
        for i, chunk in enumerate(chunks):
            if not self.turbo_mode:
                print(f"   - 청크 {i+1}/{len(chunks)} 처리 중...")
            
            # 2단계: LLM으로 의미단위 재구성
            structured_segments = self._restructure_with_llm(chunk, source_lang, target_lang)
            
            # 3단계: 품질 필터링
            quality_segments = self._filter_quality_segments(structured_segments)
            
            all_segments.extend(quality_segments)
        
        return all_segments
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """긴 텍스트를 LLM 처리 가능한 크기로 분할"""
        # 모드별 청크 크기 설정
        if self.turbo_mode:
            max_chunk_size = 15000
        elif self.fast_mode:
            max_chunk_size = 8000
        else:
            max_chunk_size = 3000
        
        # 터보 모드에서는 단순 분할
        if self.turbo_mode:
            return [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
        
        # 일반 모드: 단락 단위 분할
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _restructure_with_llm(self, text_chunk: str, source_lang: str, target_lang: str) -> List[Dict]:
        """LLM을 사용해 텍스트를 번역 메모리용 세그먼트로 재구성"""
        
        # 프롬프트 생성
        if self.turbo_mode:
            prompt = self._get_turbo_prompt(text_chunk, source_lang, target_lang)
        else:
            prompt = self._get_detailed_prompt(text_chunk, source_lang, target_lang)
        
        # LLM 옵션 설정
        llm_options = self._get_llm_options()
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options=llm_options
            )
            
            response_text = response['message']['content']
            if not self.turbo_mode:
                print(f"   - LLM 응답 미리보기: {response_text[:200]}...")
            
            # JSON 파싱
            segments = self._parse_json_response(response_text, text_chunk)
            return segments
            
        except Exception as e:
            if not self.turbo_mode:
                print(f"   - ⚠️ LLM 처리 오류: {e}")
            return self._fallback_sentence_split(text_chunk)
    
    def _get_turbo_prompt(self, text_chunk: str, source_lang: str, target_lang: str) -> str:
        """터보 모드용 간단한 프롬프트"""
        if source_lang == 'ja':
            return f"""日本語のPDFテキストからできるだけ多くの完全な文を抽出してください。短い文も含めてください。

必ずJSON形式で回答:
{{"segments": [{{"text": "文1", "category": "other", "confidence": 0.8}}, {{"text": "文2", "category": "other", "confidence": 0.8}}]}}

テキスト: {text_chunk[:3000]}"""
        elif source_lang == 'ko':
            return f"""한국어 PDF 텍스트에서 가능한 많은 완전한 문장을 추출하세요. 짧은 문장도 포함하세요.

반드시 JSON 형식으로 응답:
{{"segments": [{{"text": "문장1", "category": "other", "confidence": 0.8}}, {{"text": "문장2", "category": "other", "confidence": 0.8}}]}}

텍스트: {text_chunk[:3000]}"""
        else:  # English
            return f"""Extract as many complete sentences as possible from this PDF text. Include shorter sentences too.

Respond ONLY in JSON format:
{{"segments": [{{"text": "sentence1", "category": "other", "confidence": 0.8}}, {{"text": "sentence2", "category": "other", "confidence": 0.8}}]}}

Text: {text_chunk[:3000]}"""
    
    def _get_detailed_prompt(self, text_chunk: str, source_lang: str, target_lang: str) -> str:
        """상세 모드용 프롬프트"""
        return f"""다음 {source_lang} PDF 텍스트를 {source_lang}-{target_lang} 번역 메모리(TM)용으로 의미있는 문장 단위로 재구성해주세요.

목적: {target_lang} 번역을 위한 고품질 원문 세그먼트 생성

규칙:
1. 완전하고 독립적인 문장으로 만들기
2. 제품명, 기술용어는 문맥과 함께 보존  
3. 번역하기 적합한 길이 (10-100단어)
4. {target_lang} 번역자가 이해하기 쉬운 완전한 문장

입력 텍스트:
```
{text_chunk}
```

반드시 다음 JSON 형식으로만 응답해주세요:
```json
{{
  "segments": [
    {{"text": "완전한 문장1", "category": "product_description", "confidence": 0.95}},
    {{"text": "완전한 문장2", "category": "technical_spec", "confidence": 0.90}}
  ]
}}
```"""
    
    def _get_llm_options(self) -> dict:
        """모드별 LLM 옵션 반환"""
        if self.turbo_mode:
            return {
                "temperature": 0.0,
                "top_p": 0.8,
                "num_predict": 1500,  # 500→1500 (더 많은 세그먼트)
                "repeat_penalty": 1.0,
                "top_k": 10
            }
        elif self.fast_mode:
            return {
                "temperature": 0.0,
                "top_p": 0.9,
                "num_predict": 2000,  # 1000→2000
                "repeat_penalty": 1.1
            }
        else:
            return {
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
    
    def _parse_json_response(self, response_text: str, text_chunk: str) -> List[Dict]:
        """LLM 응답에서 JSON 파싱"""
        if self.turbo_mode:
            # 빠른 파싱
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
            else:
                print(f"   - ⚠️ JSON 찾기 실패, 폴백 사용. 응답: {response_text[:100]}...")
                return self._fallback_sentence_split(text_chunk)
        else:
            # 상세 파싱
            json_str = self._extract_json_from_response(response_text)
            if not json_str:
                if not self.turbo_mode:
                    print(f"   - ⚠️ JSON 형식을 찾을 수 없음")
                return self._fallback_sentence_split(text_chunk)
        
        try:
            parsed = json.loads(json_str)
            segments = parsed.get('segments', [])
            if not self.turbo_mode:
                print(f"   - ✅ JSON 파싱 성공: {len(segments)}개 세그먼트")
            return segments
        except json.JSONDecodeError as e:
            if not self.turbo_mode:
                print(f"   - ⚠️ JSON 파싱 오류: {e}")
            print(f"   - 문제 JSON: {json_str[:100]}...")
            return self._fallback_sentence_split(text_chunk)
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """응답 텍스트에서 JSON 추출"""
        # 패턴 1: ```json 블록
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # 패턴 2: ``` 블록
        json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # 패턴 3: 직접 JSON
        if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
            return response_text.strip()
        
        # 패턴 4: 첫 번째 { } 쌍
        brace_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
        if brace_match:
            return brace_match.group(0)
        
        return None
    
    def _fallback_sentence_split(self, text: str) -> List[Dict]:
        """LLM 처리 실패시 기본 문장 분할"""
        sentences = re.split(r'[.!?]+\s+', text)
        return [
            {
                "text": sent.strip(),
                "category": "other",
                "confidence": 0.5
            }
            for sent in sentences 
            if len(sent.strip()) > 20
        ]
    
    def _filter_quality_segments(self, segments: List[Dict]) -> List[Dict]:
        """품질 기준에 따라 세그먼트 필터링"""
        quality_segments = []
        
        for segment in segments:
            text = segment.get('text', '')
            confidence = segment.get('confidence', 0)
            
            if self._is_high_quality_segment(text, confidence):
                quality_segments.append(segment)
        
        return quality_segments
    
    def _is_high_quality_segment(self, text: str, confidence: float) -> bool:
        """세그먼트 품질 판정 (완화된 기준)"""
        # 터보/빠른 모드에서는 매우 관대한 필터링
        if self.turbo_mode or self.fast_mode:
            return len(text) > 8 and len(text.split()) > 1
        
        # 일반 모드도 기준 완화
        if len(text) < 10 or len(text) > 800:  # 15→10, 500→800
            return False
        
        if confidence < 0.5:  # 0.7→0.5
            return False
        
        word_count = len(text.split())
        if word_count < 2:  # 3→2
            return False
        
        # 순수 숫자나 특수문자만 있는 경우 제외
        if re.match(r'^[\d\s\-\.]+$', text.strip()):
            return False
    
    def create_translation_pairs_with_context(self, source_segments: List[Dict], 
                                            target_segments: List[Dict], 
                                            source_pdf_path: str,
                                            target_pdf_path: str,
                                            source_lang: str = 'en',
                                            target_lang: str = 'ko') -> List[Dict]:
        """문맥 정보를 포함한 고품질 번역 쌍 생성"""
        from processors._translation_pair_generator import TranslationPairGenerator
        from pathlib import Path
        import os
        
        # 기본 임베딩 매칭 (임계값 낮춤)
        generator = TranslationPairGenerator(similarity_threshold=0.65)  # 0.75 → 0.65
        
        # 텍스트만 추출하여 기존 매칭 로직 사용
        source_texts = [seg['text'] for seg in source_segments]
        target_texts = [seg['text'] for seg in target_segments]
        
        # 기존 함수와 호환성 확인
        try:
            basic_pairs = generator.generate_pairs(
                source_texts, target_texts, target_pdf_path, source_lang, target_lang
            )
        except TypeError:
            # 기존 함수가 적은 인자를 받는 경우
            basic_pairs = generator.generate_pairs(
                source_texts, target_texts, target_pdf_path
            )
            # 언어 정보를 수동으로 추가
            for pair in basic_pairs:
                pair['source_lang'] = source_lang
                pair['target_lang'] = target_lang
        
        # 향상된 출처 정보 추가
        enhanced_pairs = []
        for pair in basic_pairs:
            try:
                # 원본 세그먼트 정보 찾기
                source_idx = source_texts.index(pair['source_text'])
                target_idx = target_texts.index(pair['target_text'])
                
                enhanced_pair = {
                    **pair,
                    # 상세한 출처 정보
                    'source_pdf_file': Path(source_pdf_path).name,
                    'target_pdf_file': Path(target_pdf_path).name,
                    'source_pdf_path': str(Path(source_pdf_path).relative_to(Path(source_pdf_path).parents[2])),
                    'target_pdf_path': str(Path(target_pdf_path).relative_to(Path(target_pdf_path).parents[2])),
                    
                    # 세그먼트별 메타데이터
                    'source_category': source_segments[source_idx].get('category', 'other'),
                    'target_category': target_segments[target_idx].get('category', 'other'),
                    'source_confidence': source_segments[source_idx].get('confidence', 0.5),
                    'target_confidence': target_segments[target_idx].get('confidence', 0.5),
                    
                    # TM 품질 정보
                    'extraction_method': 'llm_enhanced',
                    'tm_quality_score': round((
                        source_segments[source_idx].get('confidence', 0.5) + 
                        target_segments[target_idx].get('confidence', 0.5) + 
                        pair['similarity_score']
                    ) / 3, 3),
                    
                    # 추적 정보
                    'created_date': __import__('datetime').datetime.now().isoformat()[:19],
                    'processing_notes': f"LLM-processed from {source_lang}-{target_lang} PDF pair"
                }
                enhanced_pairs.append(enhanced_pair)
            except (ValueError, IndexError) as e:
                # 인덱스 오류 시 기본 정보만 포함
                enhanced_pair = {
                    **pair,
                    'source_pdf_file': Path(source_pdf_path).name,
                    'target_pdf_file': Path(target_pdf_path).name,
                    'extraction_method': 'llm_enhanced',
                    'created_date': __import__('datetime').datetime.now().isoformat()[:19]
                }
                enhanced_pairs.append(enhanced_pair)
        
        return enhanced_pairs
        
    
    def create_translation_pairs_with_context(self, source_segments: List[Dict], 
                                            target_segments: List[Dict], 
                                            source_pdf_path: str,
                                            target_pdf_path: str,
                                            source_lang: str = 'en',
                                            target_lang: str = 'ko') -> List[Dict]:
        """문맥 정보를 포함한 고품질 번역 쌍 생성"""
        from processors._translation_pair_generator import TranslationPairGenerator
        from pathlib import Path
        import os
        
        # 기본 임베딩 매칭 (임계값 낮춤)
        generator = TranslationPairGenerator(similarity_threshold=0.65)  # 0.75 → 0.65
        
        # 텍스트만 추출하여 기존 매칭 로직 사용
        source_texts = [seg['text'] for seg in source_segments]
        target_texts = [seg['text'] for seg in target_segments]
        
        # 기존 함수와 호환성 확인
        try:
            basic_pairs = generator.generate_pairs(
                source_texts, target_texts, target_pdf_path, source_lang, target_lang
            )
        except TypeError:
            # 기존 함수가 적은 인자를 받는 경우
            basic_pairs = generator.generate_pairs(
                source_texts, target_texts, target_pdf_path
            )
            # 언어 정보를 수동으로 추가
            for pair in basic_pairs:
                pair['source_lang'] = source_lang
                pair['target_lang'] = target_lang
        
        # 향상된 출처 정보 추가
        enhanced_pairs = []
        for pair in basic_pairs:
            # 원본 세그먼트 정보 찾기
            source_idx = source_texts.index(pair['source_text'])
            target_idx = target_texts.index(pair['target_text'])
            
            enhanced_pair = {
                **pair,
                # 상세한 출처 정보
                'source_pdf_file': Path(source_pdf_path).name,
                'target_pdf_file': Path(target_pdf_path).name,
                'source_pdf_path': str(Path(source_pdf_path).relative_to(Path(source_pdf_path).parents[2])),
                'target_pdf_path': str(Path(target_pdf_path).relative_to(Path(target_pdf_path).parents[2])),
                
                # 세그먼트별 메타데이터
                'source_category': source_segments[source_idx].get('category', 'other'),
                'target_category': target_segments[target_idx].get('category', 'other'),
                'source_confidence': source_segments[source_idx].get('confidence', 0.5),
                'target_confidence': target_segments[target_idx].get('confidence', 0.5),
                
                # TM 품질 정보
                'extraction_method': 'llm_enhanced',
                'tm_quality_score': round((
                    source_segments[source_idx].get('confidence', 0.5) + 
                    target_segments[target_idx].get('confidence', 0.5) + 
                    pair['similarity_score']
                ) / 3, 3),
                
                # 추적 정보
                'created_date': __import__('datetime').datetime.now().isoformat()[:19],
                'processing_notes': f"LLM-processed from {source_lang}-{target_lang} PDF pair"
            }
            enhanced_pairs.append(enhanced_pair)
        
        return enhanced_pairs