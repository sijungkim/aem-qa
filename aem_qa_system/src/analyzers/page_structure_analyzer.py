# src/analyzers/page_structure_analyzer.py

import pandas as pd
from pymongo import MongoClient
import os
from src.config import (
    MONGO_CONNECTION_STRING, DB_NAME, COLLECTION_NAME,
    REPORTS_DIR 
)

class PageStructureAnalyzer:
    """
    TM 생성에 실패한 페이지들의 구조적 차이를 분석하여 리포트를 생성합니다.
    (다국어 지원 가능하도록 수정됨)
    """
    def __init__(self):
        """데이터베이스 연결을 초기화합니다."""
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.client[DB_NAME]
        self.source_collection = self.db[COLLECTION_NAME]
        print("✅ MongoDB에 연결되었습니다.")

    def _get_mismatched_page_paths(self, untranslated_collection_name: str) -> list:
        """지정된 컬렉션에서 구조 불일치 페이지 경로 목록을 가져옵니다."""
        print(f"🔄 '{untranslated_collection_name}' 컬렉션에서 페이지 목록을 가져오는 중...")
        untranslated_collection = self.db[untranslated_collection_name]
        paths = untranslated_collection.distinct('page_path')
        print(f"   - ✅ 분석 대상 페이지 {len(paths)}개를 찾았습니다.")
        return paths

    def _get_component_paths(self, page_path: str, version_name: str) -> list:
        """특정 페이지와 버전의 컴포넌트 경로 목록을 순서대로 가져옵니다."""
        cursor = self.source_collection.find(
            {'page_path': page_path, 'version_name': version_name},
            {'component_path': 1, 'component_order': 1, '_id': 0}
        ).sort('component_order', 1)
        return [doc['component_path'] for doc in cursor]

    def analyze(self, source_version: str, target_version: str, lang_suffix: str):
        """지정된 언어 쌍에 대한 구조 차이 분석을 실행하고 결과를 CSV로 저장합니다."""
        untranslated_collection_name = f"untranslated_components_{lang_suffix}"
        
        mismatched_pages = self._get_mismatched_page_paths(untranslated_collection_name)
        if not mismatched_pages:
            print(f"✅ '{untranslated_collection_name}'에 구조가 다른 페이지가 없습니다. 분석을 종료합니다.")
            return

        report_data = []
        print(f"🔄 [{lang_suffix}] 페이지별 구조 차이 분석 시작...")
        for page_path in mismatched_pages:
            source_paths = self._get_component_paths(page_path, source_version)
            target_paths = self._get_component_paths(page_path, target_version)
            
            source_only = list(set(source_paths) - set(target_paths))
            target_only = list(set(target_paths) - set(source_paths))
            
            report_data.append({
                'page_path': page_path,
                'source_component_count': len(source_paths), # 컬럼명 수정
                'target_component_count': len(target_paths), # 컬럼명 수정
                'components_only_in_source': source_only,
                'components_only_in_target': target_only
            })
        
        print("   - ✅ 분석 완료.")
        
        # 동적으로 리포트 파일 경로 생성
        report_csv_path = os.path.join(REPORTS_DIR, f"page_structure_diff_{lang_suffix}.csv")
        report_df = pd.DataFrame(report_data)
        report_df.to_csv(report_csv_path, index=False, encoding='utf-8-sig')
        print(f"🎉 리포트 생성 완료! -> {report_csv_path}")