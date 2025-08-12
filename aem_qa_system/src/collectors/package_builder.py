# src/collectors/package_builder.py

import os
import zipfile
import json
from datetime import datetime
from src.config import DOWNLOADED_DIR, PACKAGES_DIR
from src.collectors.data_models import FileInfo

def create_package(package_name: str, all_files: list[FileInfo]) -> str:
    """
    수집된 모든 파일들을 상대 경로를 사용하여 하나의 ZIP 패키지로 묶습니다.
    """
    os.makedirs(PACKAGES_DIR, exist_ok=True)
    package_path = os.path.join(PACKAGES_DIR, f"{package_name}.zip")
    
    print(f"\n📦 최종 패키지 생성을 시작합니다: {package_name}.zip")

    # manifest에 저장할 파일 정보 리스트를 새로 만듭니다.
    manifest_files = []

    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_info in all_files:
            # DOWNLOADED_DIR를 기준으로 상대 경로를 계산합니다.
            arcname = os.path.relpath(file_info.file_path, DOWNLOADED_DIR)
            
            # ZIP 파일에 파일을 추가합니다.
            zipf.write(file_info.file_path, arcname)
            
            # ▼▼▼▼▼ 핵심 변경사항 ▼▼▼▼▼
            # manifest에는 절대 경로(file_info.file_path) 대신
            # 방금 계산한 상대 경로(arcname)를 저장합니다.
            file_info_dict = file_info.__dict__
            file_info_dict['file_path'] = arcname.replace('\\', '/') # 경로 구분자를 '/'로 통일
            manifest_files.append(file_info_dict)
            # ▲▲▲▲▲ 핵심 변경사항 ▲▲▲▲▲

        # manifest.json 생성
        manifest = {
            "packageName": package_name,
            "creationDate": datetime.now().isoformat(),
            "totalFiles": len(manifest_files),
            "files": manifest_files
        }
        zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

    print(f"\n   - ✅ 패키지 생성 완료! -> {package_path}")
    return package_path
