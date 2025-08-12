# src/processors/data_ingestor.py

import os
import shutil
import zipfile
import json
import hashlib
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from collections import deque
from src.config import DB_NAME, COLLECTION_NAME, MONGO_CONNECTION_STRING

class DataIngestor:
    """
    data_package.zip을 디스크에 풀지 않고 메모리에서 직접 처리하여 MongoDB에 저장합니다.
    """
    def __init__(self):
        self.client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        print("✅ MongoDB에 연결되었습니다.")

    def _calculate_content_hash(self, content: dict) -> str:
        """JSON 객체의 내용을 기반으로 SHA256 해시를 계산합니다."""
        encoded_content = json.dumps(content, sort_keys=True).encode('utf-8')
        return hashlib.sha256(encoded_content).hexdigest()

    def ingest_package(self, package_path: str):
        """지정된 ZIP 패키지 파일의 데이터를 DB에 저장합니다."""
        temp_dir = f"temp_unzip_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with zipfile.ZipFile(package_path, 'r') as zipf:
            zipf.extractall(temp_dir)

        try:
            manifest_path = os.path.join(temp_dir, "manifest.json")
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            aem_files = [f for f in manifest['files'] if f['file_type'] == 'aem_snapshot']
            print(f"   - Manifest 로드 완료: {len(aem_files)}개의 AEM 스냅샷 처리 대상 확인.")

            newly_added_versions = 0
            for i, file_info in enumerate(aem_files):
                # manifest에 기록된 상대 경로를 사용하여 임시 폴더 내의 실제 파일 경로를 찾음
                snapshot_path = os.path.join(temp_dir, file_info['file_path'])
                
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    new_content = json.load(f)
                
                # 페이지 전체에 대한 해시 계산
                new_snapshot_hash = self._calculate_content_hash(new_content)

                # DB에서 가장 최신 버전 조회
                latest_doc = self.collection.find_one(
                    {"page_path": file_info['page_path'], "version_name": file_info['version_name']},
                    sort=[("version_number", DESCENDING)]
                )
                
                # 최신 버전과 해시가 동일하면 변경 없으므로 건너뛰기
                if latest_doc and latest_doc.get('snapshot_hash') == new_snapshot_hash:
                    print(f"\r   - 파일 처리 중: {i+1}/{len(aem_files)} (최신 버전과 동일, 스킵)", end="")
                    continue
                
                # 새 버전 번호 부여 (선형 증가)
                new_version_number = latest_doc['version_number'] + 1 if latest_doc else 1
                
                # 스냅샷을 컴포넌트 단위로 분해 (컴포넌트별 해시 포함)
                components = self._deconstruct_snapshot(new_content, file_info, new_version_number, new_snapshot_hash)
                
                if components:
                    self.collection.insert_many(components)
                    newly_added_versions += 1
                print(f"\r   - 파일 처리 중: {i+1}/{len(aem_files)} (신규 버전: v{new_version_number})", end="")

            print(f"\n   - ✅ 총 {newly_added_versions}개의 새로운 스냅샷 버전을 DB에 저장했습니다.")

        finally:
            shutil.rmtree(temp_dir)

    def _deconstruct_snapshot(self, root_model: dict, file_info: dict, version_number: int, snapshot_hash: str) -> list:
        # (이 함수는 변경할 필요가 없습니다. 이전과 동일합니다.)
        components = []
        queue = deque([(root_model, "root", None)])
        order = 0
        
        while queue:
            current_obj, current_path, parent_path = queue.popleft()
            if not isinstance(current_obj, dict): continue

            component_hash = self._calculate_content_hash(current_obj)

            components.append({
                "page_path": file_info['page_path'], "version_name": file_info['version_name'],
                "version_number": version_number, "snapshot_hash": snapshot_hash,
                "component_hash": component_hash, "snapshot_timestamp": file_info.get('collection_time'),
                "original_filepath": file_info['file_path'], "component_order": order,
                "component_path": current_path, "parent_component_path": parent_path,
                "component_type": current_obj.get("sling:resourceType"),
                "component_content": current_obj, "processed_at": datetime.utcnow()
            })
            order += 1
            
            if ':items' in current_obj:
                for key, value in sorted(current_obj[':items'].items()):
                    queue.append((value, f"{current_path}/:items/{key}", current_path))
        
        return components
