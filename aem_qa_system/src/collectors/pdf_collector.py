# src/collectors/pdf_collector.py

import os
import requests
import pandas as pd
import time
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.collectors.data_models import FileInfo
from src.config import PDF_DOWNLOAD_DIR, AEM_HOST

class PDFCollector:
    """PDF 파일 수집을 담당하는 클래스"""

    def __init__(self, username, password, workers=8, retries=3):
        self.credentials = (username, password)
        self.workers = workers
        self.retries = retries
        self.session = requests.Session()
        self.session.auth = self.credentials

    def collect_pdfs_for_batch(self, batch_csv_path: str, language_pair: tuple = ('en', 'ko')) -> list[FileInfo]:
        """주어진 CSV 배치 파일에 명시된 모든 PDF를 수집합니다."""
        source_lang, target_lang = language_pair
        df = pd.read_csv(batch_csv_path)
        
        tasks = []
        
        # 언어별 컬럼명 매핑 (원본 규칙 따름)
        column_mapping = {
            'en': 'EN_Path',
            'ko': 'KR_Path',  # KO_Path가 아니라 KR_Path!
            'ja': 'JA_Path'
        }
        
        # 소스 언어 수집
        source_col = column_mapping.get(source_lang)
        if source_col:
            for _, row in df.iterrows():
                if pd.notna(row.get(source_col)):
                    tasks.append((source_lang, row[source_col]))
        
        # 타겟 언어 수집  
        target_col = column_mapping.get(target_lang)
        if target_col:
            for _, row in df.iterrows():
                if pd.notna(row.get(target_col)):
                    tasks.append((target_lang, row[target_col]))

        print(f"   - 총 {len(tasks)}개 PDF 수집 작업 시작 (워커: {self.workers}개)")
        
        collected_files = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_task = {executor.submit(self._download_pdf_with_retry, task): task for task in tasks}
            
            for i, future in enumerate(as_completed(future_to_task)):
                result = future.result()
                if result:
                    collected_files.append(result)
                print(f"\r   - 진행률: {i+1}/{len(tasks)}", end="")
        
        print("\n   - 수집 완료.")
        return collected_files

    def _download_pdf_with_retry(self, task):
        """재시도 로직을 포함한 단일 PDF 다운로드"""
        lang, pdf_path = task
        for attempt in range(self.retries):
            try:
                return self._download_single_pdf(lang, pdf_path)
            except Exception as e:
                print(f"\n   - ⚠️ 오류 (재시도 {attempt+1}/{self.retries}): {pdf_path} - {e}")
                time.sleep(1)
        print(f"\n   - ❌ 최종 실패: {pdf_path}")
        return None

    def _download_single_pdf(self, lang: str, pdf_path: str) -> FileInfo:
        """단일 PDF를 다운로드하고 FileInfo 객체를 반환합니다."""
        save_dir = os.path.join(PDF_DOWNLOAD_DIR, lang)
        os.makedirs(save_dir, exist_ok=True)
        
        filename = unquote(pdf_path).split('/')[-1]
        local_path = os.path.join(save_dir, filename)

        if os.path.exists(local_path):
            return FileInfo(
                file_path=local_path, file_name=filename,
                file_size=os.path.getsize(local_path), file_type=f"pdf_{lang}"
            )

        full_url = AEM_HOST + pdf_path
        response = self.session.get(full_url, stream=True, timeout=120)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return FileInfo(
            file_path=local_path, file_name=filename,
            file_size=os.path.getsize(local_path), file_type=f"pdf_{lang}"
        )