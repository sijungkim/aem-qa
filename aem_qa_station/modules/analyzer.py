# aem_qa_station/modules/analyzer.py (Enhanced Version)

import streamlit as st
from typing import Dict, List, Tuple, Optional
from .connections import get_db

class PageAnalyzer:
    """페이지의 구조 변경사항을 분석하는 클래스 (버전 지원 확장)"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db["page_components"]
    
    def analyze_page_changes(self, page_path: str, 
                           source_version: str = "lm-en", 
                           target_version: str = "spac-ko_KR") -> Dict:
        """페이지의 변경사항을 분석하여 반환 (최신 버전 사용)"""
        # 최신 버전 자동 사용
        source_components = self._get_latest_components(page_path, source_version)
        target_components = self._get_latest_components(page_path, target_version)
        
        changes = self._compare_components(source_components, target_components)
        
        return {
            'page_path': page_path,
            'source_version': source_version,
            'target_version': target_version,
            'source_version_number': self._get_latest_version_number(page_path, source_version),
            'target_version_number': self._get_latest_version_number(page_path, target_version),
            'source_count': len(source_components),
            'target_count': len(target_components),
            'changes': changes,
            'analysis_summary': self._create_summary(changes)
        }
    
    def analyze_page_changes_with_versions(self, page_path: str,
                                         source_version: str,
                                         source_version_number: int,
                                         target_version: str,
                                         target_version_number: int) -> Dict:
        """특정 버전 번호로 페이지 변경사항 분석"""
        # 지정된 버전으로 컴포넌트 조회
        source_components = self._get_specific_version_components(
            page_path, source_version, source_version_number
        )
        target_components = self._get_specific_version_components(
            page_path, target_version, target_version_number
        )
        
        changes = self._compare_components(source_components, target_components)
        
        return {
            'page_path': page_path,
            'source_version': source_version,
            'source_version_number': source_version_number,
            'target_version': target_version,
            'target_version_number': target_version_number,
            'source_count': len(source_components),
            'target_count': len(target_components),
            'changes': changes,
            'analysis_summary': self._create_summary(changes)
        }
    
    def _get_latest_components(self, page_path: str, version_name: str) -> List[Dict]:
        """특정 페이지와 버전의 최신 컴포넌트들을 가져옵니다"""
        pipeline = [
            {"$match": {"page_path": page_path, "version_name": version_name}},
            {"$sort": {"version_number": -1}},
            {"$group": {
                "_id": "$component_path",
                "latest": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest"}},
            {"$sort": {"component_order": 1}}
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def _get_specific_version_components(self, page_path: str, version_name: str, version_number: int) -> List[Dict]:
        """특정 버전 번호의 컴포넌트들을 가져옵니다"""
        pipeline = [
            {
                "$match": {
                    "page_path": page_path,
                    "version_name": version_name,
                    "version_number": version_number
                }
            },
            {"$sort": {"component_order": 1}}
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def _get_latest_version_number(self, page_path: str, version_name: str) -> int:
        """특정 페이지와 버전의 최신 버전 번호를 반환"""
        pipeline = [
            {
                "$match": {
                    "page_path": page_path,
                    "version_name": version_name
                }
            },
            {
                "$group": {
                    "_id": None,
                    "max_version": {"$max": "$version_number"}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        if result and result[0]["max_version"]:
            return result[0]["max_version"]
        return 1
    
    def _compare_components(self, source_components: List[Dict], 
                          target_components: List[Dict]) -> Dict:
        """두 버전의 컴포넌트를 비교하여 변경사항을 찾습니다"""
        source_paths = {comp['component_path']: comp for comp in source_components}
        target_paths = {comp['component_path']: comp for comp in target_components}
        
        added = []      # 소스에만 있음 (번역 필요)
        removed = []    # 타겟에만 있음 (삭제됨)
        modified = []   # 둘 다 있지만 내용이 다름
        unchanged = []  # 둘 다 있고 내용이 같음
        
        # 소스 기준으로 비교
        for path, source_comp in source_paths.items():
            if path not in target_paths:
                added.append({
                    'component_path': path,
                    'component_type': source_comp.get('component_type'),
                    'content': self._extract_text(source_comp.get('component_content', {})),
                    'change_type': 'added'
                })
            else:
                target_comp = target_paths[path]
                source_text = self._extract_text(source_comp.get('component_content', {}))
                target_text = self._extract_text(target_comp.get('component_content', {}))
                
                if source_text != target_text:
                    modified.append({
                        'component_path': path,
                        'component_type': source_comp.get('component_type'),
                        'source_content': source_text,
                        'target_content': target_text,
                        'change_type': 'modified'
                    })
                else:
                    unchanged.append({
                        'component_path': path,
                        'component_type': source_comp.get('component_type'),
                        'content': source_text,
                        'change_type': 'unchanged'
                    })
        
        # 타겟에만 있는 컴포넌트 (제거된 것들)
        for path, target_comp in target_paths.items():
            if path not in source_paths:
                removed.append({
                    'component_path': path,
                    'component_type': target_comp.get('component_type'),
                    'content': self._extract_text(target_comp.get('component_content', {})),
                    'change_type': 'removed'
                })
        
        return {
            'added': added,
            'removed': removed, 
            'modified': modified,
            'unchanged': unchanged
        }
    
    def _extract_text(self, component_content: Dict) -> str:
        """컴포넌트 내용에서 텍스트를 추출합니다"""
        if not isinstance(component_content, dict):
            return ""
        
        # 우선순위에 따라 텍스트 추출 시도
        for key in ['text', 'jcr:title', 'title']:
            if isinstance(component_content.get(key), str):
                text = component_content[key].strip()
                # 의미있는 텍스트인지 검증
                if self._is_meaningful_text(text):
                    return text
        return ""
    
    def _is_meaningful_text(self, text: str) -> bool:
        """의미있는 텍스트인지 판단 (쓰레기 데이터 필터링)"""
        if not text or not text.strip():
            return False
        
        # HTML 태그만 있는 경우 제외
        import re
        html_tag_pattern = r'^<[^>]+>$'
        if re.match(html_tag_pattern, text.strip()):
            return False
        
        # 너무 짧은 텍스트 제외 (단, 의미있는 짧은 텍스트는 허용)
        if len(text.strip()) < 2:
            return False
        
        # 숫자나 특수문자만 있는 경우 제외
        if re.match(r'^[\d\s\-_.,;:!?]+$', text.strip()):
            return False
        
        # 공백이나 개행만 있는 경우 제외
        if text.strip() in ['', '\n', '\t', ' ']:
            return False
            
        return True
    
    def _create_summary(self, changes: Dict) -> Dict:
        """변경사항 요약을 생성합니다"""
        return {
            'total_added': len(changes['added']),
            'total_removed': len(changes['removed']),
            'total_modified': len(changes['modified']),
            'total_unchanged': len(changes['unchanged']),
            'needs_translation': len([c for c in changes['added'] if c['content'].strip()]),
            'needs_review': len([c for c in changes['modified'] if c['source_content'].strip()])
        }

# 편의 함수들
def analyze_single_page(page_path: str, source_version: str = "lm-en", target_version: str = "spac-ko_KR") -> Dict:
    """단일 페이지 분석을 위한 편의 함수"""
    analyzer = PageAnalyzer()
    return analyzer.analyze_page_changes(page_path, source_version, target_version)

def analyze_single_page_with_versions(page_path: str, 
                                    source_version: str, source_version_number: int,
                                    target_version: str, target_version_number: int) -> Dict:
    """특정 버전으로 단일 페이지 분석"""
    analyzer = PageAnalyzer()
    return analyzer.analyze_page_changes_with_versions(
        page_path, source_version, source_version_number, target_version, target_version_number
    )

def get_text_changes_only(analysis_result: Dict) -> List[Dict]:
    """텍스트가 있는 변경사항만 필터링합니다"""
    changes = analysis_result['changes']
    text_changes = []
    
    # 추가된 텍스트들
    for item in changes['added']:
        if item['content'].strip():
            text_changes.append(item)
    
    # 수정된 텍스트들  
    for item in changes['modified']:
        if item['source_content'].strip():
            text_changes.append(item)
    
    return text_changes

def batch_analyze_pages(page_paths: List[str], 
                       source_version: str, source_version_number: int,
                       target_version: str, target_version_number: int) -> Dict[str, Dict]:
    """여러 페이지 일괄 분석"""
    analyzer = PageAnalyzer()
    results = {}
    
    for page_path in page_paths:
        try:
            analysis = analyzer.analyze_page_changes_with_versions(
                page_path, source_version, source_version_number, 
                target_version, target_version_number
            )
            results[page_path] = analysis
        except Exception as e:
            results[page_path] = {
                'error': str(e),
                'page_path': page_path
            }
    
    return results

# 텍스트 품질 개선 함수들
def clean_extracted_text(text: str) -> str:
    """추출된 텍스트를 정제합니다"""
    if not text:
        return ""
    
    import re
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    return text

def is_translation_worthy(text: str) -> bool:
    """번역할 가치가 있는 텍스트인지 판단"""
    if not text or len(text.strip()) < 3:
        return False
    
    # 의미있는 단어가 포함되어 있는지 체크
    import re
    word_pattern = r'[a-zA-Z가-힣]{2,}'
    words = re.findall(word_pattern, text)
    
    return len(words) > 0