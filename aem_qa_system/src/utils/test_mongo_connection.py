# test_mongo_connection.py

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# MongoDB에 연결을 시도합니다.
# config.py와 동일한 연결 문자열을 사용합니다.
client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)

try:
    # 1. 서버에 대한 연결을 강제로 시도하고 정보를 확인합니다.
    client.admin.command('ping')
    print("✅ 서버 핑(Ping) 성공: MongoDB 서버가 응답합니다.")
    
    # 2. 우리 프로젝트의 데이터베이스와 컬렉션을 선택합니다.
    db = client['aem_qa_system']
    collection = db['connection_test']
    
    # 3. 아주 간단한 테스트 문서를 하나 삽입합니다.
    print("   - 테스트 데이터 삽입 시도...")
    result = collection.insert_one({"status": "ok", "value": 1})
    print(f"   - ✅ 삽입 성공! Inserted ID: {result.inserted_id}")
    
    # 4. 삽입한 문서를 삭제하여 테스트 환경을 깨끗하게 유지합니다.
    collection.delete_one({"_id": result.inserted_id})
    print("   - ✅ 테스트 데이터 삭제 완료.")

except ConnectionFailure as e:
    print(f"❌ 연결 실패: MongoDB 서버에 연결할 수 없습니다. -> {e}")
except Exception as e:
    print(f"❌ 작업 중 오류 발생: {e}")
finally:
    # 5. 연결을 닫습니다.
    client.close()
    print("   - 연결을 닫았습니다.")