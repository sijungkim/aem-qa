# src/processors/tm_cleaner.py

import re
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pymongo import MongoClient
from collections import Counter
from src.config import MONGO_CONNECTION_STRING, DB_NAME

class TMCleaner:
    """번역 메모리 정제 클래스 - 메타데이터 완전 보존"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.client[DB_NAME]
        
        # 정제 규칙 정의
        self.noise_patterns = [
            r'<[^>]+>',                    # HTML 태그
            r'jcr:[a-zA-Z_]+',             # JCR 속성
            r'sling:[a-zA-Z_]+',           # Sling 속성
            r'cq:[a-zA-Z_]+',              # CQ 속성
            r'dam:[a-zA-Z_]+',             # DAM 속성
            r'^\s*$',                      # 빈 문자열
            r'^[\s\n\t\r]+$',              # 공백만
            r'^[^\w\s가-힣ぁ-ゟァ-ヾ一-龯]+$',  # 특수문자만 (다국어 지원)
        ]
        
        # 추출할 텍스트 키들 (우선순위 순서)
        self.valuable_keys = [
            'text', 'jcr:title', 'title', 'alt', 'linkText', 
            'label', 'placeholder', 'value', 'description'
        ]
        
        print("✅ TM Cleaner 초기화 완료")
    
    def clean_translation_memory(self, lang_suffix: str) -> Dict:
        """번역 메모리 정제 메인 함수"""
        print(f"🧹 [{lang_suffix}] 번역 메모리 정제 시작...")
        
        # 컬렉션 이름 설정
        raw_tm_collection_name = f"translation_memory_{lang_suffix}"
        clean_tm_collection_name = f"clean_translation_memory_{lang_suffix}"
        stats_collection_name = f"tm_cleaning_stats_{lang_suffix}"
        
        # 컬렉션 참조
        raw_tm_collection = self.db[raw_tm_collection_name]
        clean_tm_collection = self.db[clean_tm_collection_name]
        stats_collection = self.db[stats_collection_name]
        
        # 기존 정제된 TM 삭제 (새로 시작)
        clean_tm_collection.delete_many({})
        print(f"   - 기존 정제 TM 삭제 완료")
        
        # Raw TM 데이터 로드
        print(f"   - Raw TM 데이터 로딩 중...")
        raw_tm_docs = list(raw_tm_collection.find({}))
        print(f"   - 총 {len(raw_tm_docs)}개 Raw TM 로드 완료")
        
        if not raw_tm_docs:
            print("⚠️ Raw TM 데이터가 없습니다.")
            return {"status": "no_data"}
        
        # 정제 처리
        cleaned_docs = []
        stats = {
            "input_count": len(raw_tm_docs),
            "output_count": 0,
            "removed_count": 0,
            "removal_reasons": Counter(),
            "quality_distribution": Counter(),
            "text_types": Counter()
        }
        
        print(f"   - 텍스트 정제 중...")
        for i, raw_doc in enumerate(raw_tm_docs):
            if i % 1000 == 0:
                print(f"     진행률: {i}/{len(raw_tm_docs)} ({i/len(raw_tm_docs)*100:.1f}%)")
            
            # 텍스트 정제 시도
            clean_result = self._clean_text_pair(raw_doc)
            
            if clean_result["is_valid"]:
                # 메타데이터 보존하면서 정제된 문서 생성
                clean_doc = self._preserve_metadata(raw_doc, clean_result)
                cleaned_docs.append(clean_doc)
                
                stats["output_count"] += 1
                stats["quality_distribution"][clean_result["quality_tier"]] += 1
                stats["text_types"][clean_result["text_type"]] += 1
            else:
                stats["removed_count"] += 1
                for reason in clean_result["removal_reasons"]:
                    stats["removal_reasons"][reason] += 1
        
        print(f"   - 정제 완료: {stats['output_count']}/{stats['input_count']} 보존")
        
        # 정제된 TM 저장
        if cleaned_docs:
            print(f"   - MongoDB에 정제된 TM 저장 중...")
            clean_tm_collection.insert_many(cleaned_docs)
            print(f"   - ✅ {len(cleaned_docs)}개 정제 TM 저장 완료")
        
        # 통계 저장
        stats_doc = {
            "language_pair": lang_suffix,
            "cleaning_date": datetime.utcnow(),
            "input_count": stats["input_count"],
            "output_count": stats["output_count"], 
            "removed_count": stats["removed_count"],
            "removal_reasons": dict(stats["removal_reasons"]),
            "quality_distribution": dict(stats["quality_distribution"]),
            "text_types": dict(stats["text_types"]),
            "cleaning_efficiency": stats["output_count"] / stats["input_count"] if stats["input_count"] > 0 else 0
        }
        
        stats_collection.delete_many({})  # 기존 통계 삭제
        stats_collection.insert_one(stats_doc)
        print(f"   - ✅ 정제 통계 저장 완료")
        
        # 결과 요약 출력
        self._print_cleaning_summary(stats_doc)
        
        return stats_doc
    
    def _clean_text_pair(self, raw_doc: Dict) -> Dict:
        """단일 TM 문서의 텍스트 쌍을 정제"""
        source_text = raw_doc.get("source_text", "")
        target_text = raw_doc.get("target_text", "")
        
        # 텍스트 정제
        clean_source = self._clean_single_text(source_text)
        clean_target = self._clean_single_text(target_text)
        
        # 유효성 검사
        validation_result = self._validate_cleaned_text_pair(
            clean_source, clean_target, source_text, target_text
        )
        
        if not validation_result["is_valid"]:
            return validation_result
        
        # 품질 평가
        quality_score = self._calculate_quality_score(clean_source, clean_target)
        quality_tier = self._get_quality_tier(quality_score)
        text_type = self._classify_text_type(clean_source)
        
        return {
            "is_valid": True,
            "clean_source": clean_source,
            "clean_target": clean_target,
            "quality_score": quality_score,
            "quality_tier": quality_tier,
            "text_type": text_type,
            "metadata": {
                "quality_score": quality_score,
                "text_type": text_type,
                "word_count_source": len(clean_source.split()),
                "word_count_target": len(clean_target.split()),
                "cleaning_method": "html_and_noise_removal",
                "cleaned_at": datetime.utcnow()
            }
        }
    
    def _clean_single_text(self, text: str) -> str:
        """단일 텍스트 정제"""
        if not isinstance(text, str):
            return ""
        
        cleaned = text
        
        # HTML 태그 제거
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # 노이즈 패턴 제거
        for pattern in self.noise_patterns[1:]:  # HTML 태그는 이미 제거했으므로 제외
            cleaned = re.sub(pattern, '', cleaned)
        
        # 연속된 공백 정리
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 앞뒤 공백 제거
        cleaned = cleaned.strip()
        
        # HTML 엔티티 디코딩 (기본적인 것들)
        html_entities = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', 
            '&quot;': '"', '&#39;': "'", '&nbsp;': ' '
        }
        for entity, char in html_entities.items():
            cleaned = cleaned.replace(entity, char)
        
        return cleaned
    
    def _validate_cleaned_text_pair(self, clean_source: str, clean_target: str, 
                                   original_source: str, original_target: str) -> Dict:
        """정제된 텍스트 쌍의 유효성 검사"""
        removal_reasons = []
        
        # 빈 텍스트 체크
        if not clean_source.strip():
            removal_reasons.append("empty_source_text")
        
        if not clean_target.strip():
            removal_reasons.append("empty_target_text")
        
        # 최소 길이 체크
        if len(clean_source.strip()) < 2:
            removal_reasons.append("source_too_short")
        
        if len(clean_target.strip()) < 2:
            removal_reasons.append("target_too_short")
        
        # 의미있는 문자 체크 (알파벳, 한글, 일본어, 중국어)
        meaningful_pattern = r'[a-zA-Z가-힣ぁ-ゟァ-ヾ一-龯]'
        if not re.search(meaningful_pattern, clean_source):
            removal_reasons.append("source_no_meaningful_chars")
        
        if not re.search(meaningful_pattern, clean_target):
            removal_reasons.append("target_no_meaningful_chars")
        
        # 숫자나 특수문자만 있는 경우
        if re.match(r'^[\d\s\-_.,;:!?()[\]{}]+$', clean_source.strip()):
            removal_reasons.append("source_only_numbers_symbols")
        
        if re.match(r'^[\d\s\-_.,;:!?()[\]{}]+$', clean_target.strip()):
            removal_reasons.append("target_only_numbers_symbols")
        
        # JCR/Sling 속성 체크
        if any(keyword in original_source.lower() for keyword in ['jcr:', 'sling:', 'cq:', 'dam:']):
            removal_reasons.append("jcr_sling_properties")
        
        return {
            "is_valid": len(removal_reasons) == 0,
            "removal_reasons": removal_reasons
        }
    
    def _calculate_quality_score(self, source: str, target: str) -> float:
        """텍스트 품질 점수 계산 (0.0 ~ 1.0)"""
        score = 0.0
        
        # 길이 점수 (적절한 길이일수록 높은 점수)
        source_len = len(source.split())
        target_len = len(target.split())
        avg_len = (source_len + target_len) / 2
        
        if 2 <= avg_len <= 50:
            score += 0.3
        elif avg_len > 50:
            score += 0.1
        
        # 문장 완성도 (마침표, 느낌표, 물음표 등)
        if any(source.strip().endswith(punct) for punct in '.!?。！？'):
            score += 0.2
        
        # 대소문자 적절성 (첫 글자 대문자 등)
        if source and source[0].isupper():
            score += 0.1
        
        # 특수문자 비율 (너무 많으면 감점)
        special_char_ratio = len(re.findall(r'[^\w\s가-힣ぁ-ゟァ-ヾ一-龯]', source)) / len(source) if source else 0
        if special_char_ratio < 0.3:
            score += 0.2
        
        # 번역 쌍 길이 비율 (너무 차이나면 감점)
        if source_len > 0 and target_len > 0:
            ratio = min(source_len, target_len) / max(source_len, target_len)
            if ratio > 0.3:
                score += 0.2
        
        return min(score, 1.0)
    
    def _get_quality_tier(self, score: float) -> str:
        """품질 점수를 티어로 변환"""
        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "very_low"
    
    def _classify_text_type(self, text: str) -> str:
        """텍스트 유형 분류"""
        if not text:
            return "empty"
        
        text_lower = text.lower()
        
        # 제목 형태 (짧고 첫 글자 대문자)
        if len(text.split()) <= 5 and text[0].isupper() and not text.endswith('.'):
            return "title"
        
        # 문장 형태 (마침표로 끝남)
        if text.endswith('.') or text.endswith('。'):
            return "sentence"
        
        # 링크 텍스트 (특정 키워드 포함)
        if any(keyword in text_lower for keyword in ['learn more', 'read more', 'click here', '자세히', '더보기']):
            return "link_text"
        
        # 라벨 형태 (콜론으로 끝남)
        if text.endswith(':') or text.endswith('：'):
            return "label"
        
        # 일반 텍스트
        return "plain_text"
    
    def _preserve_metadata(self, raw_doc: Dict, clean_result: Dict) -> Dict:
        """원본 메타데이터를 100% 보존하면서 정제된 데이터 추가"""
        # 원본 문서 전체 복사
        clean_doc = raw_doc.copy()
        
        # 원본 텍스트 백업
        clean_doc["original_source_text"] = raw_doc.get("source_text", "")
        clean_doc["original_target_text"] = raw_doc.get("target_text", "")
        
        # 정제된 텍스트로 교체
        clean_doc["source_text"] = clean_result["clean_source"]
        clean_doc["target_text"] = clean_result["clean_target"]
        
        # 정제 메타데이터 추가
        clean_doc.update(clean_result["metadata"])
        
        return clean_doc
    
    def _print_cleaning_summary(self, stats: Dict):
        """정제 결과 요약 출력"""
        print(f"\n📊 [{stats['language_pair']}] TM 정제 결과 요약:")
        print(f"   🔢 입력: {stats['input_count']:,}개")
        print(f"   ✅ 보존: {stats['output_count']:,}개 ({stats['cleaning_efficiency']:.1%})")
        print(f"   🗑️ 제거: {stats['removed_count']:,}개")
        
        print(f"\n📈 제거 이유:")
        for reason, count in sorted(stats['removal_reasons'].items(), key=lambda x: x[1], reverse=True):
            print(f"   - {reason}: {count:,}개")
        
        print(f"\n🏆 품질 분포:")
        for tier, count in sorted(stats['quality_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"   - {tier}: {count:,}개")
        
        print(f"\n📝 텍스트 유형:")
        for text_type, count in sorted(stats['text_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"   - {text_type}: {count:,}개")

# 편의 함수들
def clean_all_language_pairs():
    """모든 언어 쌍의 TM 정제"""
    from src.config import SUPPORTED_LANGUAGE_PAIRS
    
    cleaner = TMCleaner()
    results = {}
    
    for source_lang, target_lang in SUPPORTED_LANGUAGE_PAIRS:
        lang_suffix = f"{source_lang}_{target_lang}"
        print(f"\n🌐 {source_lang.upper()}-{target_lang.upper()} TM 정제 시작...")
        
        try:
            result = cleaner.clean_translation_memory(lang_suffix)
            results[lang_suffix] = result
        except Exception as e:
            print(f"❌ {lang_suffix} 정제 실패: {str(e)}")
            results[lang_suffix] = {"status": "error", "error": str(e)}
    
    return results

def get_cleaning_stats(lang_suffix: str) -> Optional[Dict]:
    """특정 언어 쌍의 정제 통계 조회"""
    client = MongoClient(MONGO_CONNECTION_STRING)
    db = client[DB_NAME]
    stats_collection = db[f"tm_cleaning_stats_{lang_suffix}"]
    
    return stats_collection.find_one({}, sort=[("cleaning_date", -1)])