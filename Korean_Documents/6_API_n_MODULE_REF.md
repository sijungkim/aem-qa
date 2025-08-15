
### **문서 6/8: API 및 모듈 레퍼런스**

## **📚 API 및 모듈 레퍼런스 가이드**

이 문서는 AEM QA System & Workstation 프로젝트를 구성하는 핵심 Python 모듈과 클래스에 대한 상세한 API 레퍼런스를 제공합니다. 각 모듈의 역할, 주요 클래스 및 함수의 파라미터와 반환 값 등을 기술합니다.

---

### ## 1. 백엔드 (`aem-qa-system`)

데이터 수집, 처리, 인덱싱을 담당하는 백엔드 시스템의 주요 모듈입니다.

#### **1.1. Collectors (`src/collectors`)**

외부 소스로부터 데이터를 수집하는 모듈 그룹입니다.

* **`aem_collector.py`** [cite: aem_collector.py]
    * **`AEMCollector` 클래스**: AEM 서버로부터 페이지 스냅샷을 수집합니다.
        * `__init__(self, username, password, workers=16, retries=3)`: AEM 인증 정보와 병렬 처리 워커 수를 설정하여 초기화합니다.
        * `collect_snapshots_for_batch(self, page_paths: list[str]) -> list[FileInfo]`: 페이지 경로 리스트를 입력받아, 정의된 모든 버전의 스냅샷을 병렬로 다운로드하고 `FileInfo` 객체 리스트를 반환합니다.

* **`excel_processor.py`** [cite: excel_processor.py]
    * `create_base_tm_from_folder(input_folder: str, output_path: str)`: `tm` 하위 폴더의 모든 Excel 파일을 읽어 `mappings.py` 규칙에 따라 표준 `base_tm.csv` 파일을 생성합니다.
    * `create_glossary_from_folder(input_folder: str, output_path: str)`: `glossary` 하위 폴더의 모든 Excel 파일을 읽어 `glossary.csv` 파일을 생성합니다. 모든 시트를 순회하며 처리합니다.

* **`package_builder.py`** [cite: package_builder.py]
    * `create_package(package_name: str, all_files: list[FileInfo]) -> str`: `FileInfo` 객체 리스트를 받아, 모든 파일을 ZIP으로 압축하고 `manifest.json`을 포함시켜 최종 데이터 패키지를 생성합니다. 생성된 ZIP 파일의 경로를 반환합니다.

#### **1.2. Processors (`src/processors`)**

수집된 데이터를 가공하여 최종 TM을 구축하는 핵심 로직 모듈 그룹입니다.

* **`data_ingestor.py`** [cite: data_ingestor.py]
    * **`DataIngestor` 클래스**: 데이터 패키지를 MongoDB에 적재합니다.
        * `ingest_package(self, package_path: str)`: ZIP 패키지를 읽어, 변경된 AEM 스냅샷만 식별하여 `page_components` 컬렉션에 분해하여 저장합니다.

* **`aem_tm_builder.py`** [cite: aem_tm_builder.py]
    * **`AEMTMBuilder` 클래스**: `page_components` 데이터로부터 초기 TM을 생성합니다.
        * `build(self, source_version: str, target_version: str, lang_suffix: str)`: 두 버전을 비교하여 페이지 구조가 일치하는 컴포넌트들로부터 번역 쌍을 추출하고 `translation_memory_*` 컬렉션에 저장합니다.

* **`utlimate_tm_builder.py`** [cite: utlimate_tm_builder.py]
    * **`UltimateTMBuilder` 클래스**: 초기 TM을 HTML 포함 여부에 따라 분리하고 의미 분할을 호출하는 최종 TM 빌더입니다.
        * `build_ultimate_tm(self, source_version: str, target_version: str, lang_suffix: str)`: 전체 TM 정제 및 분할 파이프라인을 실행하여 `clean_translation_memory_*`와 `html_component_archive_*` 컬렉션을 생성합니다.

* **`semantic_segmenter.py`** [cite: semantic_segmenter.py]
    * **`SemanticSegmenter` 클래스**: AI 모델을 사용하여 긴 텍스트를 의미 단위로 분할합니다.
        * `segment_text_pair(self, source_text: str, target_text: str, source_lang: str, target_lang: str, original_metadata: dict) -> list[dict]`: 소스/타겟 텍스트 쌍을 받아 의미적으로 분할된 세그먼트 딕셔너리 리스트를 반환합니다. 원본 메타데이터는 각 세그먼트에 상속됩니다.

#### **1.3. Indexing (`src/indexing`)**

* **`chroma_indexer.py`** [cite: chroma_indexer.py]
    * **`ChromaIndexer` 클래스**: 정제된 TM을 ChromaDB에 인덱싱합니다.
        * `create_index(self, lang_suffix: str)`: `clean_translation_memory_*` 컬렉션의 데이터를 읽어 `source_text`를 벡터로 변환하고, 관련 메타데이터와 함께 ChromaDB에 저장합니다.

---

### ## 2. 클라이언트 (`aem_qa_station`)

Streamlit 웹 애플리케이션의 비즈니스 로직을 담당하는 모듈입니다.

#### **2.1. Core Modules (`modules/`)**

* **`analyzer.py`** [cite: analyzer.py]
    * **`PageAnalyzer` 클래스**: MongoDB의 `page_components` 컬렉션을 직접 조회하여 버전 간 페이지 변경사항을 분석합니다.
        * `analyze_page_changes_with_versions(self, page_path: str, source_version: str, source_version_number: int, target_version: str, target_version_number: int) -> dict`: 사용자가 선택한 특정 버전 번호를 기준으로 페이지 내 컴포넌트의 추가/수정/삭제/유지 상태를 분석한 결과 딕셔너리를 반환합니다.

* **`searcher.py`** [cite: searcher.py]
    * **`TranslationSearcher` 클래스**: ChromaDB에 쿼리하여 AI 번역 추천을 생성합니다.
        * `search_similar_translations(self, query_text: str, top_k: int = 3) -> list[dict]`: 검색어(`query_text`)를 벡터로 변환한 후 ChromaDB에서 의미적으로 가장 유사한 `top_k`개의 번역 사례를 찾아 리스트로 반환합니다.
        * `format_recommendation_for_display(recommendation: dict) -> str`: 검색 결과를 Streamlit UI에 표시하기 좋은 포맷의 문자열로 변환합니다.

* **`version_manager.py`** [cite: version_manager.py]
    * **`VersionManager` 클래스**: MongoDB를 조회하여 사용 가능한 AEM 버전 목록을 관리합니다.
        * `get_available_versions(self) -> dict`: `page_components` 컬렉션에 저장된 모든 `version_name`과 `version_number`를 그룹화하고, 최신 스냅샷 날짜 등의 정보와 함께 딕셔너리로 반환합니다.
    * `create_version_selector(label: str, version_type: str) -> tuple[str, int]`: Streamlit UI에 버전명과 버전 번호를 선택할 수 있는 드롭다운 위젯을 생성하고, 사용자가 선택한 값을 튜플로 반환합니다.

* **`connections.py`** [cite: connections.py]
    * `get_mongo_client() -> MongoClient`: MongoDB 연결 클라이언트를 생성하고, `@st.cache_resource`를 사용하여 애플리케이션 전체에서 연결을 재사용합니다.
    * `get_chroma_client() -> PersistentClient`: ChromaDB 연결 클라이언트를 생성하고 캐싱하여 재사용합니다.