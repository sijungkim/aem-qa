# src/utils/collection_manager.py

from pymongo import MongoClient
from ..config import MONGO_CONNECTION_STRING, DB_NAME, SUPPORTED_LANGUAGE_PAIRS

class CollectionManager:
    """HTML 분리를 위한 컬렉션 관리"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.client[DB_NAME]
    
    def create_separation_collections(self):
        """분리용 컬렉션들 생성"""
        created_collections = []
        
        for source_lang, target_lang in SUPPORTED_LANGUAGE_PAIRS:
            lang_suffix = f"{source_lang}_{target_lang}"
            
            # Clean TM 컬렉션
            clean_name = f"clean_translation_memory_{lang_suffix}"
            self._create_clean_tm_collection(clean_name)
            created_collections.append(clean_name)
            
            # HTML Archive 컬렉션  
            html_name = f"html_component_archive_{lang_suffix}"
            self._create_html_archive_collection(html_name)
            created_collections.append(html_name)
            
            # 통계 컬렉션
            stats_name = f"tm_separation_stats_{lang_suffix}"
            self._create_stats_collection(stats_name)
            created_collections.append(stats_name)
        
        return created_collections
    
    def _create_clean_tm_collection(self, collection_name: str):
        """Clean TM 컬렉션 생성 및 인덱싱"""
        collection = self.db[collection_name]
        
        # 인덱스 생성
        collection.create_index([("source_text", "text")])
        collection.create_index("page_path")
        collection.create_index("component_path")
        collection.create_index([("text_quality_score", -1)])
        collection.create_index([("version_name", 1), ("version_number", -1)])
        collection.create_index([("page_path", 1), ("component_path", 1)])
        
        # 세그먼트 순서 인덱스 추가
        collection.create_index([("segment_index", 1)])
        collection.create_index([("original_component_order", 1), ("segment_index", 1)])
        collection.create_index([("is_segmented", 1)])
        
        print(f"✅ Created Clean TM collection: {collection_name}")
    
    def _create_html_archive_collection(self, collection_name: str):
        """HTML Archive 컬렉션 생성 및 인덱싱"""
        collection = self.db[collection_name]
        
        # 인덱스 생성
        collection.create_index("page_path")
        collection.create_index("component_path")
        collection.create_index("html_detection.html_complexity")
        collection.create_index("html_detection.detected_tags")
        collection.create_index([("version_name_source", 1), ("version_name_target", 1)])
        collection.create_index([("page_path", 1), ("component_path", 1)])
        
        print(f"✅ Created HTML Archive collection: {collection_name}")
    
    def _create_stats_collection(self, collection_name: str):
        """통계 컬렉션 생성 및 인덱싱"""
        collection = self.db[collection_name]
        
        # 인덱스 생성
        collection.create_index([("language_pair", 1), ("separation_date", -1)])
        collection.create_index([("separation_date", -1)])
        
        print(f"✅ Created Stats collection: {collection_name}")
    
    def get_collection_info(self):
        """현재 컬렉션 정보 조회"""
        all_collections = self.db.list_collection_names()
        
        separation_collections = {
            "clean_tm": [c for c in all_collections if c.startswith("clean_translation_memory_")],
            "html_archive": [c for c in all_collections if c.startswith("html_component_archive_")],
            "stats": [c for c in all_collections if c.startswith("tm_separation_stats_")]
        }
        
        return separation_collections
    
    def verify_collection_structure(self, collection_name: str) -> Dict:
        """특정 컬렉션의 구조 검증"""
        collection = self.db[collection_name]
        
        # 인덱스 정보
        indexes = list(collection.list_indexes())
        
        # 샘플 문서 구조
        sample_doc = collection.find_one({})
        
        # 문서 수
        doc_count = collection.count_documents({})
        
        return {
            "collection_name": collection_name,
            "document_count": doc_count,
            "index_count": len(indexes),
            "indexes": [idx.get("name", "unnamed") for idx in indexes],
            "sample_fields": list(sample_doc.keys()) if sample_doc else [],
            "has_data": doc_count > 0
        }
    
    def cleanup_old_collections(self, confirm: bool = False):
        """기존 TM 컬렉션 정리 (주의: 데이터 삭제)"""
        if not confirm:
            print("⚠️ 이 함수는 기존 데이터를 삭제합니다. confirm=True로 호출하세요.")
            return
        
        # 기존 TM 컬렉션들 찾기
        all_collections = self.db.list_collection_names()
        old_tm_collections = [
            c for c in all_collections 
            if c.startswith("translation_memory_") and not c.startswith("clean_translation_memory_")
        ]
        
        print(f"🗑️ 정리 대상 컬렉션: {len(old_tm_collections)}개")
        
        for collection_name in old_tm_collections:
            # 백업 생성 (선택적)
            backup_name = f"backup_{collection_name}_{datetime.now().strftime('%Y%m%d')}"
            
            # 원본을 백업으로 이름 변경
            self.db[collection_name].rename(backup_name)
            print(f"   - {collection_name} → {backup_name} (백업)")
        
        print(f"✅ 정리 완료. 백업 컬렉션들이 생성되었습니다.")
    
    def get_storage_statistics(self) -> Dict:
        """저장소 통계 정보"""
        stats = {}
        
        # 분리 관련 컬렉션들의 크기 정보
        separation_collections = self.get_collection_info()
        
        for category, collections in separation_collections.items():
            category_stats = []
            
            for collection_name in collections:
                collection = self.db[collection_name]
                doc_count = collection.count_documents({})
                
                # 컬렉션 크기 정보 (MongoDB 4.4+)
                try:
                    collection_stats = self.db.command("collStats", collection_name)
                    size_bytes = collection_stats.get("size", 0)
                    avg_doc_size = collection_stats.get("avgObjSize", 0)
                except:
                    size_bytes = 0
                    avg_doc_size = 0
                
                category_stats.append({
                    "name": collection_name,
                    "document_count": doc_count,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_bytes / 1024 / 1024, 2),
                    "avg_document_size": round(avg_doc_size, 2)
                })
            
            stats[category] = category_stats
        
        return stats