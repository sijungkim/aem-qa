# src/config.py

import os

# ===================================================================
# 1. 기본 경로 설정 (프로젝트의 절대적인 기준점)
# ===================================================================
# 이 파일(config.py)이 있는 폴더(src)의 부모 폴더(aem_qa_system)를
# 프로젝트 루트로 설정하여, 어디서든 경로가 깨지지 않게 합니다.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 데이터 폴더 경로 ---
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# 1) 입력 데이터 경로
INPUT_DIR = os.path.join(DATA_DIR, "1_input")
SOURCE_EXCELS_DIR = os.path.join(INPUT_DIR, "source_excels")
AEM_PAGES_MASTER_TXT = os.path.join(INPUT_DIR, "aem_pages_master.txt")
# PDF_LIST_MASTER_CSV = os.path.join(INPUT_DIR, "pdf_list_master.csv")
# CSV 매칭 테이블 경로도 언어별로
PDF_LIST_MASTER_CSV_EN_KO = os.path.join(INPUT_DIR, "pdf_list_master_en_ko.csv")
PDF_LIST_MASTER_CSV_EN_JA = os.path.join(INPUT_DIR, "pdf_list_master_en_ja.csv")
AEM_BATCHES_TODO_DIR = os.path.join(INPUT_DIR, "aem_batches_todo")
PDF_BATCHES_TODO_DIR = os.path.join(INPUT_DIR, "pdf_batches_todo")
# 요건 나중에 확인
AEM_BATCHES_DONE_DIR = os.path.join(INPUT_DIR, "aem_batches_done")
PDF_BATCHES_DONE_DIR = os.path.join(INPUT_DIR, "pdf_batches_done")
# ---



# 2) 다운로드 데이터 경로
DOWNLOADED_DIR = os.path.join(DATA_DIR, "2_downloaded")
AEM_SNAPSHOTS_DIR = os.path.join(DOWNLOADED_DIR, "aem_snapshots")
PDF_DOWNLOAD_DIR = os.path.join(DOWNLOADED_DIR, "pdfs")


# 3) 가공 완료 데이터 경로
PROCESSED_DIR = os.path.join(DATA_DIR, "3_processed")
PACKAGES_DIR = os.path.join(PROCESSED_DIR, "packages")
# 👇 파일명 변경
BASE_TM_CSV = os.path.join(PROCESSED_DIR, "base_tm.csv")
GLOSSARY_CSV = os.path.join(PROCESSED_DIR, "glossary.csv")

# --- 기타 경로 ---
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# AEM TM관련 처리 후 경로
FINAL_TM_CSV = os.path.join(PROCESSED_DIR, "final_tm.csv")
UNTRANSLATED_CSV = os.path.join(PROCESSED_DIR, "untranslated_en.csv")

# 분석기 결과
STRUCTURE_DIFF_REPORT_CSV = os.path.join(REPORTS_DIR, "page_structure_diff.csv")



# ===================================================================
# 2. AEM 서버 설정
# ===================================================================
AEM_HOST = "https://prod-author.illumina.com"


# ===================================================================
# 3. 데이터베이스 설정
# ===================================================================
# --- MongoDB ---
MONGO_CONNECTION_STRING = "mongodb://localhost:27017/"
DB_NAME = "aem_qa_system"

# ▼▼▼▼▼ 컬렉션 이름 정의 ▼▼▼▼▼
COLLECTION_NAME = "page_components" # 원본 데이터
TM_COLLECTION_NAME = "translation_memory" # 분석 결과: TM
UNTRANSLATED_COLLECTION_NAME = "untranslated_components" # 분석 결과: 번역 필요
# ▲▲▲▲▲ 컬렉션 이름 정의 ▲▲▲▲▲


# --- ChromaDB (Vector DB) ---
DB_ROOT = os.path.join(PROJECT_ROOT, "rag_database")
CHROMA_DB_PATH = os.path.join(DB_ROOT, "chroma_db_store")


# ===================================================================
# 4. AI 모델 설정
# ===================================================================
# --- LLM 모델 ---
LLM_MODEL = "llama3:8b"

# --- 임베딩 모델 ---
ALIGNMENT_EMBEDDING_MODEL = 'intfloat/multilingual-e5-large'
RAG_EMBEDDING_MODEL = 'intfloat/multilingual-e5-large'


# ===================================================================
# 5. 처리 모드 설정
# ===================================================================
# "parallel" (병렬) 또는 "serial" (직렬) 중 선택
PROCESSING_MODE = "parallel"

# 지원하는 언어 쌍 정의
SUPPORTED_LANGUAGE_PAIRS = [
    ('en', 'ko'),  # 영어-한국어
    ('en', 'ja'),  # 영어-일본어
]



