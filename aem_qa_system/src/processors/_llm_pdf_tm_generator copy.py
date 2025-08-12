# src/processors/llm_pdf_tm_generator.py

import re
import json
from typing import List, Dict
from pathlib import Path
import ollama
from src.config import LLM_MODEL
import datetime

class LLMPDFTMGenerator:
    """LLM을 활용한 PDF 번역 메모리 생성기 (N:1 매핑 방식)"""

    def __init__(self, model_name: str = LLM_MODEL, fast_mode: bool = False, turbo_mode: bool = False):
        self.model_name = model_name
        self.fast_mode = fast_mode
        self.turbo_mode = turbo_mode

    def generate_meaningful_segments(self, raw_text: str, source_lang: str = 'en', target_lang: str = 'ko') -> List[Dict]:
        """PDF 원문을 LLM을 통해 번역 메모리에 적합한 의미있는 세그먼트로 재구성 (위치 정보 포함)"""
        chunks = self._split_into_chunks(raw_text)
        
        all_segments = []
        for i, chunk in enumerate(chunks):
            if not self.turbo_mode:
                print(f"  - 청크 {i+1}/{len(chunks)} 처리 중...")
            
            structured_segments = self._restructure_with_llm(chunk, source_lang, target_lang)
            quality_segments = self._filter_quality_segments(structured_segments)
            
            # 위치 정보 추가
            positioned_segments = self._add_position_info(quality_segments, chunk, i)
            all_segments.extend(positioned_segments)
        
        # 전체 텍스트 기준으로 위치 정보 정규화
        return self._normalize_position_info(all_segments, raw_text)

    def _split_into_chunks(self, text: str) -> List[str]:
        """긴 텍스트를 LLM 처리 가능한 크기로 분할"""
        if self.turbo_mode:
            max_chunk_size = 15000
        elif self.fast_mode:
            max_chunk_size = 8000
        else:
            max_chunk_size = 3000
        
        if self.turbo_mode:
            chunks = []
            while len(text) > max_chunk_size:
                split_pos = text.rfind('\n', 0, max_chunk_size)
                if split_pos == -1:
                    split_pos = max_chunk_size
                chunks.append(text[:split_pos])
                text = text[split_pos:].lstrip()
            chunks.append(text)
            return chunks

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
        if self.turbo_mode:
            prompt = self._get_turbo_prompt(text_chunk, source_lang, target_lang)
        else:
            prompt = self._get_detailed_prompt(text_chunk, source_lang, target_lang)
        
        llm_options = self._get_llm_options()
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options=llm_options
            )
            
            response_text = response['message']['content']
            if not self.turbo_mode:
                print(f"  - LLM 응답 미리보기: {response_text[:200]}...")
            
            segments = self._parse_json_response(response_text, text_chunk)
            return segments
            
        except Exception as e:
            if not self.turbo_mode:
                print(f"  - ⚠️ LLM 처리 오류: {e}")
            return self._fallback_sentence_split(text_chunk)

    def _get_turbo_prompt(self, text_chunk: str, source_lang: str, target_lang: str) -> str:
        """터보 모드용 간단한 프롬프트"""
        if source_lang == 'ja':
            return f"""日本語のPDFテキストからできるだけ多くの完全な文を抽出してください。短い文も含めてください。

必ずJSON形式で回答:
{{"segments": [{{"text": "文1", "category": "other", "confidence": 0.8}}, {{"text": "文2", "category": "other", "confidence": 0.8}}]}}

テキスト: {text_chunk}"""
        elif source_lang == 'ko':
            return f"""한국어 PDF 텍스트에서 가능한 많은 완전한 문장을 추출하세요. 짧은 문장도 포함하세요.

반드시 JSON 형식으로 응답:
{{"segments": [{{"text": "문장1", "category": "other", "confidence": 0.8}}, {{"text": "문장2", "category": "other", "confidence": 0.8}}]}}

텍스트: {text_chunk}"""
        else:
            return f"""Extract as many complete sentences as possible from this PDF text. Include shorter sentences too.

Respond ONLY in JSON format:
{{"segments": [{{"text": "sentence1", "category": "other", "confidence": 0.8}}, {{"text": "sentence2", "category": "other", "confidence": 0.8}}]}}

Text: {text_chunk}"""

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
                "num_predict": 1500,
                "repeat_penalty": 1.0,
                "top_k": 10
            }
        elif self.fast_mode:
            return {
                "temperature": 0.0,
                "top_p": 0.9,
                "num_predict": 2000,
                "repeat_penalty": 1.1
            }
        else:
            return {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 4096,
                "repeat_penalty": 1.1
            }

    def _parse_json_response(self, response_text: str, text_chunk: str) -> List[Dict]:
        """LLM 응답에서 JSON 파싱"""
        json_str = self._extract_json_from_response(response_text)
        
        if not json_str:
            if not self.turbo_mode:
                print(f"  - ⚠️ JSON 형식을 찾을 수 없음, 폴백 사용. 응답: {response_text[:100]}...")
            return self._fallback_sentence_split(text_chunk)
            
        try:
            parsed = json.loads(json_str)
            segments = parsed.get('segments', [])
            if not isinstance(segments, list):
                print(f"  - ⚠️ JSON 'segments' 키가 리스트가 아님: {type(segments)}")
                return self._fallback_sentence_split(text_chunk)

            if not self.turbo_mode:
                print(f"  - ✅ JSON 파싱 성공: {len(segments)}개 세그먼트")
            return segments
        except json.JSONDecodeError as e:
            if not self.turbo_mode:
                print(f"  - ⚠️ JSON 파싱 오류: {e}")
            print(f"  - 문제 JSON: {json_str[:200]}...")
            return self._fallback_sentence_split(text_chunk)

    def _extract_json_from_response(self, response_text: str) -> str:
        """응답 텍스트에서 JSON 추출"""
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
            return response_text.strip()
            
        brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if brace_match:
            return brace_match.group(0)

        return None

    def _fallback_sentence_split(self, text: str) -> List[Dict]:
        """LLM 처리 실패시 기본 문장 분할"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [
            {
                "text": sent.strip(),
                "category": "other",
                "confidence": 0.5
            }
            for sent in sentences 
            if 10 < len(sent.strip()) < 800
        ]

    def _filter_quality_segments(self, segments: List[Dict]) -> List[Dict]:
        """품질 기준에 따라 세그먼트 필터링"""
        quality_segments = []
        
        for segment in segments:
            text = segment.get('text', '')
            if not text:
                continue

            confidence = segment.get('confidence', 0)
            
            if self._is_high_quality_segment(text, confidence):
                quality_segments.append(segment)
        
        return quality_segments

    def _is_high_quality_segment(self, text: str, confidence: float) -> bool:
        """세그먼트 품질 판정"""
        text_stripped = text.strip()
        
        if self.turbo_mode or self.fast_mode:
            return len(text_stripped) > 8 and len(text_stripped.split()) > 1
        
        if not (10 <= len(text_stripped) <= 800):
            return False
        
        if confidence < 0.6:
            return False
        
        word_count = len(text_stripped.split())
        if word_count < 2:
            return False
        
        if re.match(r'^[\d\s\-\.]+$', text_stripped):
            return False
        
        return True

    def _add_position_info(self, segments: List[Dict], chunk_text: str, chunk_index: int) -> List[Dict]:
        """세그먼트에 위치 정보 추가"""
        paragraphs = [p.strip() for p in chunk_text.split('\n\n') if p.strip()]
        
        for segment in segments:
            text = segment['text']
            
            paragraph_idx, sentence_idx = self._find_text_position(text, paragraphs)
            structure_type = self._detect_structure_type(text)
            
            segment.update({
                'chunk_index': chunk_index,
                'paragraph_index': paragraph_idx,
                'sentence_index': sentence_idx,
                'structure_type': structure_type,
                'original_chunk': chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
            })
        
        return segments

    def _normalize_text_for_search(self, text: str) -> str:
        """검색을 위해 텍스트 정규화"""
        return re.sub(r'[\s\W_]+', '', text).lower()

    def _find_text_position(self, target_text: str, paragraphs: List[str]) -> tuple:
        """텍스트의 문단 및 문장 위치 찾기"""
        target_clean = self._normalize_text_for_search(target_text)
        if not target_clean:
            return -1, -1

        for para_idx, paragraph in enumerate(paragraphs):
            if target_clean in self._normalize_text_for_search(paragraph):
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                for sent_idx, sentence in enumerate(sentences):
                    if target_clean in self._normalize_text_for_search(sentence):
                        return para_idx, sent_idx
                return para_idx, 0
        
        return -1, -1

    def _detect_structure_type(self, text: str) -> str:
        """텍스트의 구조 타입 감지"""
        text_stripped = text.strip()
        
        if re.match(r'^\d+[\.\)]\s', text_stripped):
            return "numbered_list"
        if re.match(r'^[•·\-\*]\s', text_stripped):
            return "bullet_list"
        if (text_stripped.isupper() or text_stripped.istitle()) and len(text_stripped.split()) < 10 and not text_stripped.endswith(('.', '!', '?')):
            return "heading"
        if '\t' in text_stripped or '|' in text_stripped:
            return "table"
        if ':' in text_stripped and len(text_stripped.split(':')) == 2:
            return "specification"
        
        return "paragraph"

    def _normalize_position_info(self, all_segments: List[Dict], full_text: str) -> List[Dict]:
        """전체 텍스트 기준으로 위치 정보 정규화"""
        full_paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
        
        for segment in all_segments:
            text = segment['text']
            global_para_idx, global_sent_idx = self._find_text_position(text, full_paragraphs)
            
            segment.update({
                'global_paragraph_index': global_para_idx,
                'global_sentence_index': global_sent_idx
            })
        
        return all_segments

    def create_japanese_based_translation_mapping(self, source_segments: List[Dict], 
                                                target_segments: List[Dict], 
                                                source_pdf_path: str,
                                                target_pdf_path: str,
                                                source_lang: str = 'en',
                                                target_lang: str = 'ja') -> List[Dict]:
        """일본어 기준 N:1 번역 매핑 생성"""
        print(f"  - 🎌 {target_lang} 기준 번역 매핑 생성 중...")
        print(f"  - {target_lang} 세그먼트: {len(target_segments)}개")
        print(f"  - {source_lang} 세그먼트: {len(source_segments)}개")
        
        translation_mappings = []
        
        for i, ja_segment in enumerate(target_segments):
            if not self.turbo_mode:
                print(f"  - 매핑 {i+1}/{len(target_segments)}: {ja_segment['text'][:30]}...")
            
            related_en_segments = self._find_related_source_segments(
                ja_segment, source_segments, source_lang, target_lang
            )
            
            if related_en_segments:
                mapping = self._create_translation_mapping_entry(
                    ja_segment, related_en_segments, 
                    source_pdf_path, target_pdf_path,
                    source_lang, target_lang
                )
                translation_mappings.append(mapping)
        
        print(f"  - ✅ {len(translation_mappings)}개 번역 매핑 생성 완료")
        return translation_mappings

    def _find_related_source_segments(self, target_segment: Dict, source_segments: List[Dict], 
                                    source_lang: str, target_lang: str) -> List[Dict]:
        """타겟 언어 문장과 관련된 소스 언어 문장들을 LLM으로 찾기"""
        prioritized_sources = self._sort_by_proximity(target_segment, source_segments)
        
        max_candidates = 30
        chunks = [prioritized_sources[i:i+max_candidates] for i in range(0, len(prioritized_sources), max_candidates)]
        
        all_related = []
        for chunk in chunks:
            related = self._llm_find_related_segments_with_proximity(
                target_segment, chunk, source_lang, target_lang
            )
            all_related.extend(related)
            
            if len([r for r in all_related if r['final_score'] > 0.7]) >= 5:
                break
        
        all_related.sort(key=lambda x: x['final_score'], reverse=True)
        return all_related[:5]

    def _sort_by_proximity(self, target_segment: Dict, source_segments: List[Dict]) -> List[Dict]:
        """인접성 기준으로 소스 세그먼트 정렬"""
        target_para = target_segment.get('global_paragraph_index', -1)
        target_sent = target_segment.get('global_sentence_index', -1)
        
        if target_para == -1:
            return source_segments

        def proximity_score(source_seg):
            source_para = source_seg.get('global_paragraph_index', -1)
            source_sent = source_seg.get('global_sentence_index', -1)
            if source_para == -1:
                return 0

            para_distance = abs(target_para - source_para)
            if para_distance == 0:
                return 100 - abs(target_sent - source_sent)
            else:
                return 50 - para_distance
        
        return sorted(source_segments, key=proximity_score, reverse=True)

    def _llm_find_related_segments_with_proximity(self, target_segment: Dict, source_segments: List[Dict], 
                                                  source_lang: str, target_lang: str) -> List[Dict]:
        """LLM을 사용해 관련 소스 문장 찾기 (인접성 정보 포함)"""
        target_text = target_segment['text']
        target_position = f"문단 {target_segment.get('global_paragraph_index', '?')}, 문장 {target_segment.get('global_sentence_index', '?')}"
        
        numbered_sources = []
        for i, seg in enumerate(source_segments):
            position_info = f"(문단 {seg.get('global_paragraph_index', '?')}, 문장 {seg.get('global_sentence_index', '?')})"
            numbered_sources.append(f"{i+1}. {seg['text']} {position_info}")
        sources_text = "\n".join(numbered_sources)
        
        prompt = f"""다음 {target_lang} 문장의 번역 원문이 될 수 있는 {source_lang} 문장들을 찾아주세요.

{target_lang} 문장: "{target_text}"
위치: {target_position}

{source_lang} 문장 후보들:
{sources_text}

평가 기준:
1. 의미적 관련성 (0.0-0.8): 번역 관계의 강도
   - 직접 번역: 0.7-0.8
   - 부분 번역: 0.5-0.7
   - 문맥상 관련: 0.3-0.5
2. 인접성 보너스는 자동으로 계산됩니다.

의미 점수가 0.5 이상인 문장들만 다음 JSON 형식으로 반환해주세요:
{{"matches": [{{"number": 1, "semantic_score": 0.75, "type": "direct"}}, {{"number": 3, "semantic_score": 0.6, "type": "partial"}}]}}"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0, "num_predict": 1024}
            )
            
            response_text = response['message']['content']
            matches = self._parse_relevance_response(response_text)
            
            related_segments = []
            for match in matches:
                idx = match.get('number')
                if idx is None or not (0 < idx <= len(source_segments)):
                    continue

                source_seg = source_segments[idx - 1]
                semantic_score = match.get('semantic_score', 0.0)
                
                proximity_bonus = self._calculate_proximity_bonus(target_segment, source_seg)
                final_score = semantic_score + proximity_bonus
                
                if final_score >= 0.6:
                    related_segments.append({
                        'text': source_seg['text'],
                        'semantic_score': semantic_score,
                        'proximity_bonus': proximity_bonus,
                        'final_score': round(final_score, 3),
                        'relevance': round(final_score, 3),
                        'type': match.get('type', 'related'),
                        'position_info': {
                            'paragraph': source_seg.get('global_paragraph_index'),
                            'sentence': source_seg.get('global_sentence_index'),
                            'structure': source_seg.get('structure_type')
                        }
                    })
            
            return related_segments
            
        except Exception as e:
            if not self.turbo_mode:
                print(f"  - ⚠️ 관련 문장 찾기 오류: {e}")
            return []

    def _calculate_proximity_bonus(self, target_segment: Dict, source_segment: Dict) -> float:
        """인접성 기반 보너스 점수 계산"""
        bonus = 0.0
        target_para = target_segment.get('global_paragraph_index', -1)
        source_para = source_segment.get('global_paragraph_index', -1)
        target_sent = target_segment.get('global_sentence_index', -1)
        source_sent = source_segment.get('global_sentence_index', -1)
        
        if target_para == -1 or source_para == -1:
            return 0.0
        
        if target_para == source_para:
            bonus += 0.2
            if abs(target_sent - source_sent) <= 1:
                bonus += 0.05
        elif abs(target_para - source_para) == 1:
            bonus += 0.1
        
        target_structure = target_segment.get('structure_type', '')
        source_structure = source_segment.get('structure_type', '')
        if target_structure == source_structure and target_structure not in ['paragraph', 'unknown']:
            bonus += 0.1
        
        return round(bonus, 3)

    def _parse_relevance_response(self, response_text: str) -> List[Dict]:
        """LLM의 관련도 응답 파싱"""
        try:
            json_str = self._extract_json_from_response(response_text)
            if json_str:
                parsed = json.loads(json_str)
                matches = parsed.get('matches', [])
                if not isinstance(matches, list): return []
                
                for match in matches:
                    if 'semantic_score' not in match and 'relevance' in match:
                        match['semantic_score'] = match['relevance']
                return matches
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def _create_translation_mapping_entry(self, target_segment: Dict, related_source_segments: List[Dict],
                                        source_pdf_path: str, target_pdf_path: str,
                                        source_lang: str, target_lang: str) -> Dict:
        """번역 매핑 엔트리 생성"""
        total_score = sum(seg.get('final_score', 0) for seg in related_source_segments)
        avg_score = total_score / len(related_source_segments) if related_source_segments else 0
        
        proximity_summary = self._summarize_proximity_info(related_source_segments)
        
        try:
            s_rel_path = str(Path(source_pdf_path).relative_to(Path(source_pdf_path).parents[2]))
            t_rel_path = str(Path(target_pdf_path).relative_to(Path(target_pdf_path).parents[2]))
        except IndexError:
            s_rel_path = Path(source_pdf_path).name
            t_rel_path = Path(target_pdf_path).name

        return {
            'target_text': target_segment['text'],
            'target_language': target_lang,
            'target_category': target_segment.get('category', 'other'),
            'target_confidence': target_segment.get('confidence', 0.5),
            'target_position': {
                'paragraph': target_segment.get('global_paragraph_index'),
                'sentence': target_segment.get('global_sentence_index'),
                'structure': target_segment.get('structure_type')
            },
            
            'source_segments': related_source_segments,
            'source_language': source_lang,
            'source_count': len(related_source_segments),
            
            'mapping_method': 'llm_japanese_based_with_proximity',
            'average_final_score': round(avg_score, 3),
            'proximity_summary': proximity_summary,
            'mapping_quality_score': round((avg_score + target_segment.get('confidence', 0.5)) / 2, 3),
            
            'source_pdf_file': Path(source_pdf_path).name,
            'target_pdf_file': Path(target_pdf_path).name,
            'source_pdf_path': s_rel_path,
            'target_pdf_path': t_rel_path,
            
            'created_date': datetime.datetime.now().isoformat()[:19],
            'processing_notes': f"Japanese-based N:1 mapping with proximity analysis from {source_lang}-{target_lang} PDF pair"
        }

    def _summarize_proximity_info(self, related_segments: List[Dict]) -> Dict:
        """인접성 정보 요약"""
        if not related_segments:
            return {}
        
        same_paragraph = sum(1 for seg in related_segments if seg.get('proximity_bonus', 0) >= 0.2)
        adjacent_paragraph = sum(1 for seg in related_segments if 0.05 <= seg.get('proximity_bonus', 0) < 0.2)
        same_structure = sum(1 for seg in related_segments if seg.get('proximity_bonus', 0) % 0.1 == 0.05)
        
        return {
            'same_paragraph_count': same_paragraph,
            'adjacent_paragraph_count': adjacent_paragraph,
            'same_structure_count': same_structure,
            'avg_proximity_bonus': round(sum(seg.get('proximity_bonus', 0) for seg in related_segments) / len(related_segments), 3)
        }

    def create_translation_pairs_with_context(self, source_segments: List[Dict], 
                                            target_segments: List[Dict], 
                                            source_pdf_path: str,
                                            target_pdf_path: str,
                                            source_lang: str = 'en',
                                            target_lang: str = 'ja') -> List[Dict]:
        """하위 호환성을 위한 래퍼 함수"""
        return self.create_japanese_based_translation_mapping(
            source_segments, target_segments, source_pdf_path, target_pdf_path, source_lang, target_lang
        )
