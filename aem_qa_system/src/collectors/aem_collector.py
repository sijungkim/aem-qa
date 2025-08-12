# src/collectors/aem_collector.py

import os
import requests
import json
import time
from datetime import datetime
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.collectors.data_models import FileInfo
from src.config import AEM_SNAPSHOTS_DIR, AEM_HOST

class AEMCollector:
    """AEM 페이지 스냅샷 수집을 담당하는 클래스"""

    def __init__(self, username, password, workers=16, retries=3):
        self.credentials = (username, password)
        self.workers = workers
        self.retries = retries
        self.session = requests.Session()
        self.session.auth = self.credentials

    def collect_snapshots_for_batch(self, page_paths: list[str]) -> list[FileInfo]:
        """주어진 페이지 경로 목록(배치)에 대한 모든 버전의 스냅샷을 수집합니다."""
        versions = ["sot-en", "lm-en", "lm-ko", "spac-ko_KR", "apac-en", "apac-ja_JP"]
        tasks = [(path, ver) for path in page_paths for ver in versions]
        
        print(f"   - 총 {len(tasks)}개 스냅샷 수집 작업 시작 (워커: {self.workers}개)")
        
        collected_files = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_task = {executor.submit(self._download_snapshot_with_retry, task): task for task in tasks}
            
            for i, future in enumerate(as_completed(future_to_task)):
                result = future.result()
                if result:
                    collected_files.append(result)
                # 진행률 표시
                print(f"\r   - 진행률: {i+1}/{len(tasks)}", end="")
        
        print("\n   - 수집 완료.")
        return collected_files

    def _download_snapshot_with_retry(self, task):
        """재시도 로직을 포함한 단일 스냅샷 다운로드"""
        page_path, version = task
        for attempt in range(self.retries):
            try:
                return self._download_single_snapshot(page_path, version)
            except requests.exceptions.HTTPError as e:
                # 404 Not Found는 재시도하지 않고 바로 실패 처리
                if e.response.status_code == 404:
                    # ▼▼▼ 404 오류 로그 출력 활성화 ▼▼▼
                    print(f"\n   - ⚠️ 404 Not Found (건너뛰기): {page_path} ({version})")
                    return None
                print(f"\n   - ⚠️ 오류 (재시도 {attempt+1}/{self.retries}): {page_path} ({version}) - {e}")
                time.sleep(1) # 재시도 전 잠시 대기
            except Exception as e:
                print(f"\n   - ⚠️ 오류 (재시도 {attempt+1}/{self.retries}): {page_path} ({version}) - {e}")
                time.sleep(1)
        # print(f"\n   - ❌ 최종 실패: {page_path} ({version})")
        return None

    def _download_single_snapshot(self, page_path: str, version: str) -> FileInfo:
        """단일 스냅샷을 다운로드하고 FileInfo 객체를 반환합니다."""
        # 1. URL 생성
        url = self._build_aem_url(page_path, version)
        
        # 2. 저장 경로 및 파일명 생성
        # ▼▼▼ 경로 정리를 여기서도 수행하여 폴더명을 표준화 ▼▼▼
        clean_page_path = self._clean_page_path(page_path)
        sanitized_folder_name = clean_page_path.lstrip('/').replace('/', '_')
        page_dir = os.path.join(AEM_SNAPSHOTS_DIR, sanitized_folder_name)
        os.makedirs(page_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{version}_{timestamp}.json"
        file_path = os.path.join(page_dir, filename)

        # 3. 다운로드
        response = self.session.get(url, timeout=60)
        response.raise_for_status() # 200 OK가 아니면 에러 발생
        
        # 4. 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
            
        return FileInfo(
            file_path=file_path, file_name=filename,
            file_size=os.path.getsize(file_path), file_type="aem_snapshot",
            page_path=page_path, version_name=version
        )

    def _clean_page_path(self, page_path: str) -> str:
        """
        [신규 추가] 다양한 형식의 페이지 경로를 표준 형식으로 정제합니다.
        예: '/content/illumina-marketing/en/test' -> '/test'
        """
        clean_path = page_path.strip()
        # 가장 긴 접두사부터 순서대로 제거 시도
        prefixes_to_remove = [
            '/content/illumina-marketing/language-master/en',
            '/content/illumina-marketing/language-master/ko',
            '/content/illumina-marketing/spac/ko_KR',
            '/content/illumina-marketing/en',
            '/content/illumina-marketing/apac/en',
            '/content/illumina-marketing/apac/ja_JP'
        ]
        for prefix in prefixes_to_remove:
            if clean_path.startswith(prefix):
                clean_path = clean_path[len(prefix):]
                break
        
        if not clean_path.startswith('/'):
            return '/' + clean_path
        return clean_path

    def _build_aem_url(self, page_path: str, version: str) -> str:
        """
        [수정됨] 페이지 경로와 버전을 조합하여 실제 다운로드 URL을 만듭니다.
        """
        # ▼▼▼ 경로 정제 로직 호출 추가 ▼▼▼
        clean_path = self._clean_page_path(page_path)
        
        path_templates = {
            "sot-en":     f"/content/illumina-marketing/en{clean_path}.model.json",
            "lm-en":      f"/content/illumina-marketing/language-master/en{clean_path}.model.json",
            "lm-ko":      f"/content/illumina-marketing/language-master/ko{clean_path}.model.json",
            "spac-ko_KR": f"/content/illumina-marketing/spac/ko_KR{clean_path}.model.json",
            "apac-en":    f"/content/illumina-marketing/apac/en{clean_path}.model.json",
            "apac-ja_JP": f"/content/illumina-marketing/apac/ja_JP{clean_path}.model.json"
        }
        
        # .format()을 호출하여 {page_path}를 실제 값(clean_path)으로 바꿉니다.
        url_path_template = path_templates.get(version)
        if not url_path_template:
            raise ValueError(f"알 수 없는 버전입니다: {version}")
        
        url_path = url_path_template.format(page_path=clean_path)
        # ▲▲▲▲▲ 여기가 수정된 부분입니다 ▲▲▲▲▲
            
        return urljoin(AEM_HOST, url_path)


    # def _build_aem_url(self, page_path: str, version: str) -> str:
    #     """
    #     [핵심 로직] 페이지 경로와 버전을 조합하여 실제 다운로드 URL을 만듭니다.
    #     """
    #     # AEM의 URL 구조 규칙을 정의한 '설계도'
    #     path_templates = {
    #         "sot-en":     "/content/illumina-marketing/en{page_path}.model.json",
    #         "lm-en":      "/content/illumina-marketing/language-master/en{page_path}.model.json",
    #         "lm-ko":      "/content/illumina-marketing/language-master/ko{page_path}.model.json",
    #         "spac-ko_KR": "/content/illumina-marketing/spac/ko_KR{page_path}.model.json",
    #         "apac-en": "/content/illumina-marketing/apac/en{page_path}.model.json",
    #         "apac-ja_JP": "/content/illumina-marketing/apac/ja_JP{page_path}.model.json"
    #     }
        
    #     # page_path 예시: "/products/sequencing/sequencers/iseq-100"
    #     url_path = path_templates.get(version, "").format(page_path=page_path)
        
    #     if not url_path:
    #         raise ValueError(f"알 수 없는 버전입니다: {version}")
            
    #     # 최종 URL 조합 (예: "https://...com" + "/content/...")
    #     return urljoin(AEM_HOST, url_path)