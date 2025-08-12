# scripts/setup_collections.py

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from src.config import MONGO_CONNECTION_STRING, DB_NAME, SUPPORTED_LANGUAGE_PAIRS

def create_separation_collections():
    """분리용 컬렉션들 생성 및 인덱싱"""
    
    print("🗄️ MongoDB 컬렉션 생성 시작")
    print(f"   - 연결: {MONGO_CONNECTION_STRING}")
    print(f"   - 데이터베이스: {DB_NAME}")
    print(f"   - 언어 쌍: {SUPPORTED_LANGUAGE_PAIRS}")
    print("=" * 60)
    
    try:
        # MongoDB 연결
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        
        # 연결 테스트
        db.admin.command('ping')
        print("✅ MongoDB 연결 성공")
        
        created_collections = []
        
        for source_lang, target_lang in SUPPORTED_LANGUAGE_PAIRS:
            lang_suffix = f"{source_lang}_{target_lang}"
            
            print(f"\n🌐 {source_lang.upper()}-{target_lang.upper()} 컬렉션 생성 중...")
            
            # === Clean TM 컬렉션 생성 ===
            clean_collection_name = f"clean_translation_memory_{lang_suffix}"
            clean_collection = db[clean_collection_name]
            
            # Clean TM 인덱스 생성
            clean_collection.create_index([("source_text", "text")])
            clean_collection.create_index("page_path")
            clean_collection.create_index("component_path")
            clean_collection.create_index([("text_quality_score", -1)])
            clean_collection.create_index([("version_name", 1), ("version_number", -1)])
            clean_collection.create_index([("page_path", 1), ("component_path", 1)])
            # 🆕 세그먼트 순서 인덱스 추가
            clean_collection.create_index([("segment_index", 1)])
            clean_collection.create_index([("original_component_order", 1), ("segment_index", 1)])
            clean_collection.create_index([("is_segmented", 1)])
            
            created_collections.append(clean_collection_name)
            print(f"   ✅ Clean TM: {clean_collection_name}")
            
            # === HTML Archive 컬렉션 생성 ===
            html_collection_name = f"html_component_archive_{lang_suffix}"
            html_collection = db[html_collection_name]
            
            # HTML Archive 인덱스 생성
            html_collection.create_index("page_path")
            html_collection.create_index("component_path")
            html_collection.create_index("html_detection.html_complexity")
            html_collection.create_index("html_detection.detected_tags")
            html_collection.create_index([("version_name_source", 1), ("version_name_target", 1)])
            html_collection.create_index([("page_path", 1), ("component_path", 1)])
            
            created_collections.append(html_collection_name)
            print(f"   ✅ HTML Archive: {html_collection_name}")
            
            # === 통계 컬렉션 생성 ===
            stats_collection_name = f"tm_separation_stats_{lang_suffix}"
            stats_collection = db[stats_collection_name]
            
            # 통계 인덱스 생성
            stats_collection.create_index([("language_pair", 1), ("separation_date", -1)])
            stats_collection.create_index([("separation_date", -1)])
            
            created_collections.append(stats_collection_name)
            print(f"   ✅ 통계: {stats_collection_name}")
        
        print(f"\n🎉 모든 컬렉션 생성 완료!")
        print(f"📊 총 생성된 컬렉션: {len(created_collections)}개")
        
        # 생성된 컬렉션 목록 출력
        print(f"\n📋 생성된 컬렉션 목록:")
        for collection_name in created_collections:
            collection_type = "Clean TM" if "clean_translation_memory" in collection_name else \
                             "HTML Archive" if "html_component_archive" in collection_name else "통계"
            print(f"   - {collection_type:>12} | {collection_name}")
        
        return created_collections
        
    except Exception as e:
        print(f"❌ 컬렉션 생성 실패: {str(e)}")
        return []
    
    finally:
        if 'client' in locals():
            client.close()

def verify_collections():
    """생성된 컬렉션 검증"""
    
    print(f"\n🔍 컬렉션 검증 시작")
    print("=" * 40)
    
    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        
        all_collections = db.list_collection_names()
        
        # 분리 관련 컬렉션 분류
        clean_tm_collections = [c for c in all_collections if c.startswith("clean_translation_memory_")]
        html_archive_collections = [c for c in all_collections if c.startswith("html_component_archive_")]
        stats_collections = [c for c in all_collections if c.startswith("tm_separation_stats_")]
        
        print(f"📊 컬렉션 현황:")
        print(f"   - Clean TM: {len(clean_tm_collections)}개")
        print(f"   - HTML Archive: {len(html_archive_collections)}개") 
        print(f"   - 통계: {len(stats_collections)}개")
        print(f"   - 전체: {len(all_collections)}개")
        
        # 각 컬렉션의 인덱스 확인
        print(f"\n🔍 인덱스 검증:")
        
        for collection_name in clean_tm_collections[:1]:  # 첫 번째만 샘플 체크
            collection = db[collection_name]
            indexes = list(collection.list_indexes())
            print(f"   - {collection_name}: {len(indexes)}개 인덱스")
            for idx in indexes:
                print(f"     • {idx.get('name', 'unnamed')}")
        
        print(f"✅ 검증 완료")
        
    except Exception as e:
        print(f"❌ 검증 실패: {str(e)}")
    
    finally:
        if 'client' in locals():
            client.close()

def show_collection_details():
    """컬렉션 상세 정보 표시"""
    
    print(f"\n📋 컬렉션 상세 정보")
    print("=" * 50)
    
    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        
        for source_lang, target_lang in SUPPORTED_LANGUAGE_PAIRS:
            lang_suffix = f"{source_lang}_{target_lang}"
            
            print(f"\n🌐 {source_lang.upper()}-{target_lang.upper()} 컬렉션 상세:")
            
            # Clean TM 컬렉션 정보
            clean_name = f"clean_translation_memory_{lang_suffix}"
            try:
                clean_collection = db[clean_name]
                clean_count = clean_collection.count_documents({})
                print(f"   📊 Clean TM: {clean_count:,}개 문서")
            except Exception as e:
                print(f"   ❌ Clean TM: 접근 실패 - {e}")
            
            # HTML Archive 컬렉션 정보
            html_name = f"html_component_archive_{lang_suffix}"
            try:
                html_collection = db[html_name]
                html_count = html_collection.count_documents({})
                print(f"   📊 HTML Archive: {html_count:,}개 문서")
            except Exception as e:
                print(f"   ❌ HTML Archive: 접근 실패 - {e}")
            
            # 통계 컬렉션 정보
            stats_name = f"tm_separation_stats_{lang_suffix}"
            try:
                stats_collection = db[stats_name]
                stats_count = stats_collection.count_documents({})
                print(f"   📊 통계: {stats_count:,}개 문서")
                
                # 최신 통계 조회
                if stats_count > 0:
                    latest_stats = stats_collection.find_one({}, sort=[("processing_date", -1)])
                    if latest_stats:
                        print(f"      └ 최신 처리: {latest_stats.get('processing_date', 'N/A')}")
                        print(f"      └ 처리 방법: {latest_stats.get('method', 'N/A')}")
                        
            except Exception as e:
                print(f"   ❌ 통계: 접근 실패 - {e}")
        
    except Exception as e:
        print(f"❌ 상세 정보 조회 실패: {str(e)}")
    
    finally:
        if 'client' in locals():
            client.close()

def cleanup_test_data():
    """테스트 데이터 정리 (개발용)"""
    
    print(f"\n🗑️ 테스트 데이터 정리")
    print("⚠️ 이 작업은 모든 분리 컬렉션의 데이터를 삭제합니다!")
    
    confirm = input("정말로 진행하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("취소되었습니다.")
        return
    
    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        
        deleted_collections = []
        
        for source_lang, target_lang in SUPPORTED_LANGUAGE_PAIRS:
            lang_suffix = f"{source_lang}_{target_lang}"
            
            collection_names = [
                f"clean_translation_memory_{lang_suffix}",
                f"html_component_archive_{lang_suffix}",
                f"tm_separation_stats_{lang_suffix}"
            ]
            
            for collection_name in collection_names:
                try:
                    collection = db[collection_name]
                    result = collection.delete_many({})
                    deleted_collections.append(f"{collection_name}: {result.deleted_count}개 삭제")
                except Exception as e:
                    deleted_collections.append(f"{collection_name}: 삭제 실패 - {e}")
        
        print(f"\n🎯 정리 결과:")
        for result in deleted_collections:
            print(f"   - {result}")
        
    except Exception as e:
        print(f"❌ 정리 실패: {str(e)}")
    
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("🚀 MongoDB 컬렉션 설정 시작")
    
    # 메뉴 선택
    print("\n📋 실행할 작업을 선택하세요:")
    print("   [1] 컬렉션 생성")
    print("   [2] 컬렉션 검증") 
    print("   [3] 상세 정보 조회")
    print("   [4] 테스트 데이터 정리")
    print("   [0] 전체 실행 (생성 + 검증)")
    
    try:
        choice = input("\n선택 (0-4): ").strip()
        
        if choice == "1":
            created = create_separation_collections()
            if created:
                print(f"\n✅ 컬렉션 생성 완료!")
        
        elif choice == "2":
            verify_collections()
        
        elif choice == "3":
            show_collection_details()
        
        elif choice == "4":
            cleanup_test_data()
        
        elif choice == "0":
            # 전체 실행
            created = create_separation_collections()
            if created:
                verify_collections()
                show_collection_details()
                print(f"\n🎉 모든 설정 완료! 이제 의미 분할을 실행할 수 있습니다.")
            else:
                print(f"\n❌ 설정 실패. MongoDB 연결을 확인하세요.")
        
        else:
            print("❌ 잘못된 선택입니다.")
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️ 사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 실행 중 오류: {str(e)}")