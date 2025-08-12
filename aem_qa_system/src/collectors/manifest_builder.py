# src/collectors/manifest_builder.py

import os
from src.config import DOWNLOADED_DIR
from src.collectors.data_models import FileInfo

def build_fileinfo_from_downloads() -> list[FileInfo]:
    """
    data/2_downloaded/ 폴더 전체를 스캔하여, AEM 스냅샷과 PDF 파일 모두에 대한
    FileInfo 리스트를 완벽하게 재생성합니다.
    """
    print("🔄 '재고 조사' 시작: 다운로드된 모든 파일(AEM+PDF)을 스캔합니다...")
    
    all_files = []
    
    # --- 1. AEM 스냅샷 폴더 스캔 ---
    aem_snapshots_dir = os.path.join(DOWNLOADED_DIR, "aem_snapshots")
    if os.path.exists(aem_snapshots_dir):
        print("   - AEM 스냅샷 스캔 중...")
        for folder_name in os.listdir(aem_snapshots_dir):
            # 폴더명으로부터 page_path 복원
            page_path = "/" + folder_name.replace('_', '/')
            folder_path = os.path.join(aem_snapshots_dir, folder_name)
            
            if os.path.isdir(folder_path):
                for filename in os.listdir(folder_path):
                    if filename.endswith(".json"):
                        file_path = os.path.join(folder_path, filename)
                        # 파일명으로부터 version_name 복원
                        version_name = filename.split('_')[0]
                        
                        all_files.append(FileInfo(
                            file_path=file_path,
                            file_name=filename,
                            file_size=os.path.getsize(file_path),
                            file_type='aem_snapshot',
                            page_path=page_path,
                            version_name=version_name
                        ))

    # --- 2. PDF 폴더 스캔 ---
    pdf_dir = os.path.join(DOWNLOADED_DIR, "pdfs")
    if os.path.exists(pdf_dir):
        print("   - PDF 파일 스캔 중...")
        for lang_folder in ['en', 'ko']:
            lang_path = os.path.join(pdf_dir, lang_folder)
            if os.path.exists(lang_path):
                for filename in os.listdir(lang_path):
                    if filename.endswith(".pdf"):
                        file_path = os.path.join(lang_path, filename)
                        all_files.append(FileInfo(
                            file_path=file_path,
                            file_name=filename,
                            file_size=os.path.getsize(file_path),
                            file_type=f'pdf_{lang_folder}'
                        ))
    
    print(f"   - ✅ '재고 조사' 완료: 총 {len(all_files)}개의 파일 정보를 복원했습니다.")
    return all_files