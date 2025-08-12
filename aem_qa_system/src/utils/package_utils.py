# src/utils/package_utils.py

import os
import zipfile
import json
import random
from datetime import datetime
from src.config import PACKAGES_DIR

# --- 비공개 보조 함수들 (Helper Functions) ---

def _read_manifest_from_zip(source_zip_file) -> dict:
    """ZIP 파일에서 manifest.json을 읽고 파싱하여 반환합니다."""
    print("   - 1. 원본 manifest.json을 읽는 중...")
    manifest_content = source_zip_file.read('manifest.json').decode('utf-8')
    return json.loads(manifest_content)

def _get_sampled_page_paths(all_files_info: list, num_pages: int) -> list:
    """전체 파일 정보에서 고유한 페이지 목록을 뽑아 무작위로 샘플링합니다."""
    all_page_paths = sorted(list(set(
        info['page_path'] for info in all_files_info if info.get('page_path')
    )))
    print(f"   - 2. 원본에서 {len(all_page_paths)}개의 고유 페이지 확인.")

    if len(all_page_paths) <= num_pages:
        print(f"   - ⚠️ 전체 페이지 수가 샘플 수보다 적거나 같아, {len(all_page_paths)}개 전체를 사용합니다.")
        return all_page_paths
    
    print(f"   - 3. {num_pages}개 페이지를 무작위로 샘플링했습니다.")
    return random.sample(all_page_paths, num_pages)

def _write_new_package(sample_zip_path: str, source_zip_file, sample_files_info: list, source_package_name: str):
    """샘플 파일들과 새로운 manifest.json을 담은 새 ZIP 패키지를 생성합니다."""
    print(f"   - 5. 새로운 샘플 패키지 '{os.path.basename(sample_zip_path)}'를 생성하는 중...")
    with zipfile.ZipFile(sample_zip_path, 'w', zipfile.ZIP_DEFLATED) as sample_zip:
        # 5a. 필터링된 파일들을 원본 zip에서 새 zip으로 복사
        for file_info in sample_files_info:
            file_path_in_zip = file_info['file_path']
            sample_zip.writestr(file_path_in_zip, source_zip_file.read(file_path_in_zip))

        # 5b. 새로운 manifest 생성 및 저장
        new_manifest = {
            "packageName": f"sample_{os.path.basename(sample_zip_path)}",
            "creationDate": datetime.now().isoformat(),
            "totalFiles": len(sample_files_info),
            "sourcePackage": source_package_name,
            "files": sample_files_info
        }
        sample_zip.writestr("manifest.json", json.dumps(new_manifest, indent=2))


# --- 공개 함수 (Public Function) ---

def create_sample_package(source_package_name: str, num_pages: int):
    """
    원본 패키지에서 지정된 페이지 수만큼 무작위로 샘플링하여 
    새로운 샘플 패키지를 생성합니다. (이제 감독 역할만 수행)
    """
    source_zip_path = os.path.join(PACKAGES_DIR, source_package_name)
    if not os.path.exists(source_zip_path):
        print(f"❌ 오류: 원본 패키지 파일을 찾을 수 없습니다 -> {source_zip_path}")
        return

    print(f"🚀 샘플 패키지 생성을 시작합니다...")
    print(f"   - 원본: {source_package_name}")
    print(f"   - 샘플 페이지 수: {num_pages}개")

    try:
        with zipfile.ZipFile(source_zip_path, 'r') as source_zip:
            # 각 단계를 보조 함수에 위임
            manifest = _read_manifest_from_zip(source_zip)
            sample_page_paths = _get_sampled_page_paths(manifest['files'], num_pages)
            
            # 샘플에 포함될 파일 정보만 필터링
            sample_files_info = [
                info for info in manifest['files'] if info.get('page_path') in sample_page_paths
            ]
            print(f"   - 4. 샘플 페이지에 해당하는 {len(sample_files_info)}개 파일을 필터링했습니다.")
            
            # 새 패키지 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            sample_zip_name = f"sample_data_package_{timestamp}.zip"
            sample_zip_path = os.path.join(PACKAGES_DIR, sample_zip_name)
            
            _write_new_package(sample_zip_path, source_zip, sample_files_info, source_package_name)

        print(f"\n🎉 샘플 패키지 생성 완료! -> {sample_zip_path}")

    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {e}")