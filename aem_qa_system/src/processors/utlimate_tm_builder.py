# src/processors/ultimate_tm_builder.py

from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Tuple
import re
from .semantic_segmenter import SemanticSegmenter
from ..config import MONGO_CONNECTION_STRING, DB_NAME

class HTMLDetector:
    """HTML 검출 및 분석"""
    
    def __init__(self):
        self.html_patterns = [
            r'<[^>]+>',           # HTML 태그
            r'&[a-zA-Z]+;',       # HTML 엔티티
            r'&#+\d+;',           # 숫자 엔티티
        ]
    
    def contains_html(self, text: str) -> bool:
        """HTML 포함 여부 정확 검출"""
        if not isinstance(text, str):
            return False
            
        for pattern in self.html_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def detect_html_in_component(self, component_content: Dict) -> Dict:
        """컴포넌트 전체에서 HTML 검출"""
        html_fields = []
        
        # 모든 텍스트 필드 검사
        for key, value in component_content.items():
            if isinstance(value, str) and self.contains_html(value):
                html_fields.append({
                    "field": key,
                    "value": value,
                    "detected_tags": self._extract_tags(value)
                })
        
        return {
            "has_html": len(html_fields) > 0,
            "html_fields": html_fields,
            "total_html_fields": len(html_fields)
        }
    
    def _extract_tags(self, text: str) -> List[str]:
        """HTML 태그 추출"""
        tags = re.findall(r'<([^/>]+)[^>]*>', text)
        return list(set(tags))

class MetadataPreserver:
    """메타데이터 100% 보존 처리"""
    
    def preserve_all_metadata(self, original_record: Dict) -> Dict:
        """원본 레코드의 모든 메타데이터 보존"""
        
        # 핵심: 원본 데이터 100% 복사
        preserved = original_record.copy()
        
        # 페이지 복구를 위한 필수 메타데이터 확인
        required_fields = [
            'page_path', 'component_path', 'component_type',
            'version_name', 'version_number', 'component_order',
            'parent_component_path', 'snapshot_timestamp',
            'snapshot_hash', 'component_hash', 'original_filepath'
        ]
        
        for field in required_fields:
            if field not in preserved:
                print(f"⚠️ Missing required field: {field}")
        
        return preserved

class UltimateTMBuilder:
    """HTML 분리 + 의미 분할 통합 TM 빌더"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.client[DB_NAME]
        self.html_detector = HTMLDetector()
        self.metadata_preserver = MetadataPreserver()
        self.semantic_segmenter = SemanticSegmenter()
        
        print("🚀 Ultimate TM Builder 초기화 완료")
        print("   - HTML 분리 기능 ✅")
        print("   - 의미 기반 분할 기능 ✅")
        print("   - 메타데이터 100% 보존 ✅")
    
    def build_ultimate_tm(self, source_version: str, target_version: str, lang_suffix: str):
        """최고급 TM 구축: HTML 분리 + 의미 분할"""
        
        print(f"🎯 Ultimate TM 구축 시작: {lang_suffix}")
        print(f"   Source: {source_version}, Target: {target_version}")
        
        # 1. 원본 TM 데이터 로드
        raw_tm_data = self._load_raw_tm_data(source_version, target_version)
        print(f"   - 원본 TM: {len(raw_tm_data)}개 레코드")
        
        # 결과 저장용
        clean_segments = []
        html_components = []
        processing_stats = {
            'total_input': len(raw_tm_data),
            'html_separated': 0,
            'clean_processed': 0,
            'segments_created': 0,
            'segmentation_applied': 0
        }
        
        # 2. 각 레코드 처리
        for i, tm_record in enumerate(raw_tm_data):
            if i % 100 == 0:
                print(f"   - 진행률: {i}/{len(raw_tm_data)} ({i/len(raw_tm_data)*100:.1f}%)")
            
            try:
                if self._contains_html(tm_record):
                    # HTML 컴포넌트 → Archive 저장
                    html_archive_record = self._prepare_html_archive(tm_record)
                    html_components.append(html_archive_record)
                    processing_stats['html_separated'] += 1
                    
                else:
                    # Clean 텍스트 → 의미 분할 처리
                    segments = self._process_with_semantic_segmentation(tm_record, lang_suffix)
                    clean_segments.extend(segments)
                    
                    processing_stats['clean_processed'] += 1
                    processing_stats['segments_created'] += len(segments)
                    if len(segments) > 1:
                        processing_stats['segmentation_applied'] += 1
                        
            except Exception as e:
                print(f"   ⚠️ 레코드 {i} 처리 실패: {str(e)}")
                continue
        
        print(f"   - 처리 완료: Clean {len(clean_segments)}개, HTML {len(html_components)}개")
        
        # 3. 결과 저장
        self._save_ultimate_results(clean_segments, html_components, lang_suffix, processing_stats)
        
        return processing_stats
    
    def _load_raw_tm_data(self, source_version: str, target_version: str) -> List[Dict]:
        """원본 TM 데이터 로드"""
        # 기존 TM 컬렉션에서 데이터 로드
        # 이 부분은 기존 TM 구조에 따라 조정 필요
        tm_collection = self.db["translation_memory_en_ko"]  # 예시
        
        query = {
            '$or': [
                {'version_name': source_version},
                {'version_name': target_version}
            ]
        }
        
        return list(tm_collection.find(query))
    
    def _contains_html(self, tm_record: Dict) -> bool:
        """TM 레코드에 HTML 포함 여부 검사"""
        source_text = tm_record.get("source_text", "")
        target_text = tm_record.get("target_text", "")
        
        return (self.html_detector.contains_html(source_text) or 
                self.html_detector.contains_html(target_text))
    
    def _prepare_html_archive(self, tm_record: Dict) -> Dict:
        """HTML Archive 레코드 준비"""
        # 메타데이터 100% 보존
        html_record = self.metadata_preserver.preserve_all_metadata(tm_record)
        
        # HTML 분석 정보 추가
        source_text = tm_record.get("source_text", "")
        target_text = tm_record.get("target_text", "")
        
        html_analysis = {
            "detected_tags": self._extract_all_tags(source_text, target_text),
            "html_complexity": self._assess_html_complexity(source_text, target_text),
            "tag_count": len(self._extract_all_tags(source_text, target_text)),
            "has_inline_styles": self._has_inline_styles(source_text, target_text),
            "has_scripts": self._has_scripts(source_text, target_text)
        }
        
        # HTML 관련 정보 추가
        html_record.update({
            "source_component_content": {"text": source_text},  # 실제로는 전체 컴포넌트 내용
            "target_component_content": {"text": target_text},  # 실제로는 전체 컴포넌트 내용
            "html_detection": html_analysis,
            "extracted_source_text": self._clean_html(source_text),
            "extracted_target_text": self._clean_html(target_text),
            "separation_reason": "html_tags_detected",
            "is_html_component": True,
            "processed_at": datetime.utcnow()
        })
        
        return html_record
    
    def _process_with_semantic_segmentation(self, tm_record: Dict, lang_suffix: str) -> List[Dict]:
        """의미 분할을 적용한 Clean 텍스트 처리"""
        
        source_text = tm_record.get("source_text", "")
        target_text = tm_record.get("target_text", "")
        
        # 언어 추론
        source_lang, target_lang = self._infer_languages(lang_suffix)
        
        # 의미 기반 분할 실행
        segments = self.semantic_segmenter.segment_text_pair(
            source_text=source_text,
            target_text=target_text,
            source_lang=source_lang,
            target_lang=target_lang,
            original_metadata=tm_record
        )
        
        return segments
    
    def _infer_languages(self, lang_suffix: str) -> Tuple[str, str]:
        """언어 쌍 추론"""
        lang_map = {
            'en_ko': ('en', 'ko'),
            'en_ja': ('en', 'ja'),
            # 필요시 추가
        }
        return lang_map.get(lang_suffix, ('en', 'ko'))
    
    def _save_ultimate_results(self, clean_segments: List[Dict], html_components: List[Dict], 
                              lang_suffix: str, stats: Dict):
        """최종 결과 저장"""
        
        # MongoDB 저장
        if clean_segments:
            clean_collection_name = f"clean_translation_memory_{lang_suffix}"
            clean_collection = self.db[clean_collection_name]
            clean_collection.delete_many({})  # 기존 데이터 삭제
            clean_collection.insert_many(clean_segments)
            print(f"   ✅ Clean TM 저장: {len(clean_segments)}개 세그먼트")
        
        if html_components:
            html_collection_name = f"html_component_archive_{lang_suffix}"
            html_collection = self.db[html_collection_name]
            html_collection.delete_many({})  # 기존 데이터 삭제
            html_collection.insert_many(html_components)
            print(f"   ✅ HTML Archive 저장: {len(html_components)}개 컴포넌트")
        
        # 통계 저장
        stats_record = {
            'language_pair': lang_suffix,
            'processing_date': datetime.utcnow(),
            'method': 'html_separation_semantic_segmentation',
            'embedding_model': 'intfloat/multilingual-e5-large',
            **stats,
            'segmentation_ratio': stats['segmentation_applied'] / stats['clean_processed'] if stats['clean_processed'] > 0 else 0,
            'average_segments_per_record': stats['segments_created'] / stats['clean_processed'] if stats['clean_processed'] > 0 else 0
        }
        
        stats_collection_name = f"tm_separation_stats_{lang_suffix}"
        stats_collection = self.db[stats_collection_name]
        stats_collection.delete_many({})
        stats_collection.insert_one(stats_record)
        print(f"   ✅ 통계 저장 완료")
    
    def _extract_all_tags(self, source_text: str, target_text: str) -> List[str]:
        """모든 HTML 태그 추출"""
        all_text = source_text + " " + target_text
        tags = re.findall(r'<([^/>]+)[^>]*>', all_text)
        return list(set(tags))
    
    def _assess_html_complexity(self, source_text: str, target_text: str) -> str:
        """HTML 복잡도 평가"""
        all_text = source_text + " " + target_text
        tag_count = len(re.findall(r'<[^>]+>', all_text))
        
        if tag_count == 0:
            return "none"
        elif tag_count <= 3:
            return "simple"
        elif tag_count <= 8:
            return "medium"
        else:
            return "complex"
    
    def _has_inline_styles(self, source_text: str, target_text: str) -> bool:
        """인라인 스타일 포함 여부"""
        all_text = source_text + " " + target_text
        return 'style=' in all_text
    
    def _has_scripts(self, source_text: str, target_text: str) -> bool:
        """스크립트 포함 여부"""
        all_text = source_text + " " + target_text
        return '<script' in all_text.lower()
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        
        # HTML 태그 제거
        cleaned = re.sub(r'<[^>]+>', '', text)
        
        # HTML 엔티티 디코딩
        html_entities = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', 
            '&quot;': '"', '&#39;': "'", '&nbsp;': ' '
        }
        for entity, char in html_entities.items():
            cleaned = cleaned.replace(entity, char)
        
        # 연속된 공백 정리
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()