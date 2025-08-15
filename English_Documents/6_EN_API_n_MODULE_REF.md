### **Document 6/8: API and Module Reference**

## **📚 API and Module Reference Guide**

This document provides detailed API reference for the core Python modules and classes that comprise the AEM QA System & Workstation project. It describes the role of each module, parameters and return values of key classes and functions.

---

## 1. Backend (`aem-qa-system`)

Key modules of the backend system responsible for data collection, processing, and indexing.

#### **1.1. Collectors (`src/collectors`)**

Module group that collects data from external sources.

* **`aem_collector.py`**
    * **`AEMCollector` class**: Collects page snapshots from AEM servers.
        * `__init__(self, username, password, workers=16, retries=3)`: Initializes with AEM authentication information and number of parallel processing workers.
        * `collect_snapshots_for_batch(self, page_paths: list[str]) -> list[FileInfo]`: Takes a list of page paths as input, downloads snapshots of all defined versions in parallel, and returns a list of `FileInfo` objects.

* **`excel_processor.py`**
    * `create_base_tm_from_folder(input_folder: str, output_path: str)`: Reads all Excel files in the `tm` subfolder and generates a standard `base_tm.csv` file according to `mappings.py` rules.
    * `create_glossary_from_folder(input_folder: str, output_path: str)`: Reads all Excel files in the `glossary` subfolder and generates a `glossary.csv` file. Processes all sheets iteratively.

* **`package_builder.py`**
    * `create_package(package_name: str, all_files: list[FileInfo]) -> str`: Takes a list of `FileInfo` objects, compresses all files into ZIP format, includes `manifest.json`, and creates the final data package. Returns the path of the generated ZIP file.

#### **1.2. Processors (`src/processors`)**

Core logic module group that processes collected data to build the final TM.

* **`data_ingestor.py`**
    * **`DataIngestor` class**: Loads data packages into MongoDB.
        * `ingest_package(self, package_path: str)`: Reads ZIP packages, identifies only changed AEM snapshots, and stores them decomposed in the `page_components` collection.

* **`aem_tm_builder.py`**
    * **`AEMTMBuilder` class**: Generates initial TM from `page_components` data.
        * `build(self, source_version: str, target_version: str, lang_suffix: str)`: Compares two versions to extract translation pairs from components with matching page structures and stores them in the `translation_memory_*` collection.

* **`ultimate_tm_builder.py`**
    * **`UltimateTMBuilder` class**: Final TM builder that separates initial TM based on HTML inclusion and calls semantic segmentation.
        * `build_ultimate_tm(self, source_version: str, target_version: str, lang_suffix: str)`: Executes the complete TM cleaning and segmentation pipeline to generate `clean_translation_memory_*` and `html_component_archive_*` collections.

* **`semantic_segmenter.py`**
    * **`SemanticSegmenter` class**: Uses AI models to segment long text into semantic units.
        * `segment_text_pair(self, source_text: str, target_text: str, source_lang: str, target_lang: str, original_metadata: dict) -> list[dict]`: Takes source/target text pairs and returns a list of semantically segmented segment dictionaries. Original metadata is inherited by each segment.

#### **1.3. Indexing (`src/indexing`)**

* **`chroma_indexer.py`**
    * **`ChromaIndexer` class**: Indexes refined TM into ChromaDB.
        * `create_index(self, lang_suffix: str)`: Reads data from the `clean_translation_memory_*` collection, converts `source_text` to vectors, and stores them in ChromaDB along with related metadata.

---

## 2. Client (`aem_qa_station`)

Modules responsible for the business logic of the Streamlit web application.

#### **2.1. Core Modules (`modules/`)**

* **`analyzer.py`**
    * **`PageAnalyzer` class**: Directly queries the `page_components` collection in MongoDB to analyze inter-version page changes.
        * `analyze_page_changes_with_versions(self, page_path: str, source_version: str, source_version_number: int, target_version: str, target_version_number: int) -> dict`: Analyzes the addition/modification/deletion/maintenance status of components within a page based on specific version numbers selected by the user and returns a result dictionary.

* **`searcher.py`**
    * **`TranslationSearcher` class**: Queries ChromaDB to generate AI translation recommendations.
        * `search_similar_translations(self, query_text: str, top_k: int = 3) -> list[dict]`: Converts the search term (`query_text`) to a vector, then finds the `top_k` most semantically similar translation cases in ChromaDB and returns them as a list.
        * `format_recommendation_for_display(recommendation: dict) -> str`: Converts search results to a string format suitable for display in the Streamlit UI.

* **`version_manager.py`**
    * **`VersionManager` class**: Manages the list of available AEM versions by querying MongoDB.
        * `get_available_versions(self) -> dict`: Groups all `version_name` and `version_number` stored in the `page_components` collection and returns them as a dictionary along with information such as the latest snapshot date.
    * `create_version_selector(label: str, version_type: str) -> tuple[str, int]`: Creates dropdown widgets in the Streamlit UI for selecting version names and version numbers, and returns the user-selected values as a tuple.

* **`connections.py`**
    * `get_mongo_client() -> MongoClient`: Creates a MongoDB connection client and uses `@st.cache_resource` to reuse connections throughout the application.
    * `get_chroma_client() -> PersistentClient`: Creates and caches a ChromaDB connection client for reuse.