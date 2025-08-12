# src/processors/aem_tm_builder.py

import pandas as pd
from pymongo import MongoClient
from src.config import (
    MONGO_CONNECTION_STRING, DB_NAME, COLLECTION_NAME,
    PROCESSED_DIR, REPORTS_DIR # 경로 생성을 위해 PROCESSED_DIR와 REPORTS_DIR를 사용
)
import os

class AEMTMBuilder:
    """
    MongoDB에 저장된 AEM 컴포넌트 데이터로부터 번역 메모리(TM)를 구축합니다.
    (다국어 지원 가능하도록 수정됨)
    """
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.client[DB_NAME]
        self.source_collection = self.db[COLLECTION_NAME]
        print("✅ MongoDB에 연결되었습니다.")

    def _get_all_components_as_df(self, source_version: str, target_version: str) -> pd.DataFrame:
        print(f"🔄 DB에서 '{source_version}'와 '{target_version}' 컴포넌트 데이터 로드 중...")
        query = {'version_name': {'$in': [source_version, target_version]}}
        cursor = self.source_collection.find(query)
        df = pd.DataFrame(list(cursor))
        print(f"   - ✅ 총 {len(df)}개의 컴포넌트를 로드했습니다.")
        return df

    def _are_structures_identical(self, en_df: pd.DataFrame, ko_df: pd.DataFrame) -> bool:
        if len(en_df) != len(ko_df):
            return False
        en_paths = en_df.sort_values('component_order')['component_path'].tolist()
        ko_paths = ko_df.sort_values('component_order')['component_path'].tolist()
        return en_paths == ko_paths

    def _extract_text(self, component_content: dict) -> str:
        if not isinstance(component_content, dict):
            return ""
        for key in ['text', 'jcr:title', 'title']:
            if isinstance(component_content.get(key), str):
                return component_content[key].strip()
        return ""

    def build(self, source_version: str, target_version: str, lang_suffix: str):
        """
        지정된 소스/타겟 버전에 대한 TM 생성의 전체 프로세스를 실행합니다.
        lang_suffix: 파일 및 컬렉션 이름에 사용할 접미사 (예: 'en_ko')
        """
        df = self._get_all_components_as_df(source_version, target_version)
        if df.empty:
            print("⚠️ 처리할 데이터가 없습니다. TM 생성을 종료합니다.")
            return

        tm_rows = []
        untranslated_docs = []

        print(f"🔄 [{lang_suffix}] 페이지 단위로 구조 비교 및 TM 생성 시작...")
        for page_path, group_df in df.groupby('page_path'):
            source_df = group_df[group_df['version_name'] == source_version]
            target_df = group_df[group_df['version_name'] == target_version]

            if source_df.empty or target_df.empty:
                continue

            if self._are_structures_identical(source_df, target_df):
                merged_df = pd.merge(source_df, target_df, on='component_path', suffixes=('_source', '_target'))
                if not merged_df.empty:
                    merged_df['source_text'] = merged_df['component_content_source'].apply(self._extract_text)
                    merged_df['target_text'] = merged_df['component_content_target'].apply(self._extract_text)
                    processed_df = merged_df[(merged_df['source_text'] != '') & (merged_df['target_text'] != '')].copy()
                    processed_df['page_path'] = page_path
                    processed_df['component_type'] = processed_df['component_type_source']
                    final_cols = ['source_text', 'target_text', 'page_path', 'component_path', 'component_type']
                    tm_rows.extend(processed_df[final_cols].to_dict('records'))
            else:
                source_docs = source_df.to_dict('records')
                for doc in source_docs:
                    doc['status'] = 'structure_mismatch'
                untranslated_docs.extend(source_docs)
        
        print("   - ✅ 비교 완료.")
        self._save_results(tm_rows, untranslated_docs, lang_suffix)

    def _save_results(self, tm_rows: list, untranslated_docs: list, lang_suffix: str):
        print("💾 최종 결과 저장 중...")
        
        # 동적 컬렉션 이름 생성
        tm_collection_name = f"translation_memory_{lang_suffix}"
        untranslated_collection_name = f"untranslated_components_{lang_suffix}"
        
        # 동적 CSV 파일 경로 생성
        final_tm_csv = os.path.join(PROCESSED_DIR, f"final_tm_{lang_suffix}.csv")
        untranslated_csv = os.path.join(REPORTS_DIR, f"untranslated_{lang_suffix}.csv")

        # MongoDB에 저장
        if tm_rows:
            tm_collection = self.db[tm_collection_name]
            tm_collection.delete_many({})
            tm_collection.insert_many(tm_rows)
            print(f"   - ✅ MongoDB '{tm_collection_name}' 컬렉션에 {len(tm_rows)}개 문서 저장.")
        
        if untranslated_docs:
            untranslated_collection = self.db[untranslated_collection_name]
            untranslated_collection.delete_many({})
            untranslated_collection.insert_many(untranslated_docs)
            print(f"   - ✅ MongoDB '{untranslated_collection_name}' 컬렉션에 {len(untranslated_docs)}개 문서 저장.")
            
        # CSV 파일로 저장
        pd.DataFrame(tm_rows).to_csv(final_tm_csv, index=False, encoding='utf-8-sig')
        print(f"   - ✅ CSV 파일 '{final_tm_csv}' 생성 완료.")
        
        pd.DataFrame(untranslated_docs).to_csv(untranslated_csv, index=False, encoding='utf-8-sig')
        print(f"   - ✅ CSV 파일 '{untranslated_csv}' 생성 완료.")