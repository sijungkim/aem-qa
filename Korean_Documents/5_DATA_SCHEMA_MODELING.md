
### **문서 5/8: 데이터 모델 및 스키마 정의서**

## **💾 데이터 모델 및 스키마 정의서**

이 문서는 AEM QA System & Workstation에서 사용하는 데이터베이스의 스키마를 정의합니다. 시스템의 데이터는 **MongoDB**와 **ChromaDB**에 저장되며, 각 데이터베이스는 명확히 구분된 역할을 수행합니다.

---

### ## 1. 데이터베이스 개요

* **MongoDB**: AEM에서 수집한 원본 컴포넌트 데이터와 처리 단계별 번역 메모리(TM) 등 **구조화된 문서 데이터**의 주 저장소 역할을 합니다. 데이터의 버전 관리, 메타데이터 보존, 상세 분석의 기반이 됩니다.
* **ChromaDB**: 최종 정제된 번역 메모리의 `source_text`를 벡터로 변환하여 저장하는 **벡터 데이터베이스**입니다. AI 기반의 빠르고 정확한 의미 기반 유사도 검색을 담당합니다.

---

### ## 2. MongoDB 스키마

* **Database Name**: `aem_qa_system` [cite: config.py]

#### **2.1. `page_components` 컬렉션**

AEM에서 수집한 모든 콘텐츠 스냅샷을 개별 컴포넌트 단위로 분해하여 버전별로 저장하는 핵심 원본 데이터 컬렉션입니다.

* **역할**: 모든 분석의 시작점이 되는 원본 데이터 저장소 (Source of Truth).
* **생성 주체**: `src/processors/data_ingestor.py` [cite: data_ingestor.py]
* **주요 필드**:
    * `_id` (ObjectId): MongoDB 자동 생성 고유 ID.
    * `page_path` (String): 컴포넌트가 속한 AEM 페이지 경로 (예: `/products/sequencing/iseq-100`).
    * `version_name` (String): AEM의 콘텐츠 버전명 (예: `lm-en`, `spac-ko_KR`).
    * `version_number` (Int): 시스템이 부여하는 선형 증가 버전 번호 (예: `1`, `2`).
    * `snapshot_hash` (String): 페이지 전체 JSON의 SHA256 해시. 동일 해시는 변경 없음으로 간주.
    * `component_path` (String): 페이지 내에서 컴포넌트의 고유 경로 (예: `root/:items/container/:items/text`).
    * `component_order` (Int): 페이지 내에서 컴포넌트의 렌더링 순서.
    * `component_type` (String): AEM 리소스 타입 (예: `core/wcm/components/text/v2/text`).
    * `component_content` (Object): 해당 컴포넌트의 원본 JSON 내용 전체.
    * `snapshot_timestamp` (ISODate): 원본 스냅샷이 수집된 시간.

#### **2.2. `clean_translation_memory_{lang_pair}` 컬렉션**

모든 정제 및 분할 과정을 거친 최종 번역 메모리. QA 워크스테이션의 AI 검색 데이터베이스(ChromaDB)를 구축하는 원천 데이터입니다.

* **역할**: 고품질 번역 쌍 저장, AI 학습 및 검색 데이터 소스.
* **생성 주체**: `src/processors/utlimate_tm_builder.py` [cite: utlimate_tm_builder.py]
* **주요 필드**:
    * `source_text` (String): **(핵심)** 정제 및 분할된 소스 언어 텍스트.
    * `target_text` (String): **(핵심)** 정제 및 분할된 타겟 언어 텍스트.
    * `is_segmented` (Boolean): `semantic_segmenter`에 의해 분할되었는지 여부 [cite: semantic_segmenter.py].
    * `segment_index` (Int): 분할된 경우, 세그먼트의 순서 (0부터 시작).
    * `total_segments` (Int): 총 몇 개의 세그먼트로 분할되었는지.
    * `alignment_confidence` (Float): 분할된 소스-타겟 쌍의 의미적 유사도 점수.
    * `quality_score` (Float): `tm_cleaner`가 부여한 0.0 ~ 1.0 사이의 품질 점수 [cite: tm_cleaner.py].
    * `text_type` (String): 텍스트의 유형 (예: `title`, `sentence`, `link_text`).
    * `original_source_text` (String): 정제/분할되기 전의 원본 소스 텍스트.
    * `page_path`, `component_path`, `version_name` 등 원본 컴포넌트의 주요 메타데이터를 **모두 상속**받아 콘텐츠의 출처를 추적할 수 있습니다.

#### **2.3. `html_component_archive_{lang_pair}` 컬렉션**

번역 텍스트에 HTML 태그가 포함되어 있어 `clean_translation_memory`에서 제외된 컴포넌트를 보관하는 컬렉션입니다.

* **역할**: HTML을 포함한 복잡한 컴포넌트의 원본 데이터 아카이빙.
* **생성 주체**: `src/processors/utlimate_tm_builder.py` [cite: utlimate_tm_builder.py]
* **주요 필드**:
    * `source_component_content` (Object): 소스 버전의 원본 컴포넌트 JSON.
    * `target_component_content` (Object): 타겟 버전의 원본 컴포넌트 JSON.
    * `html_detection` (Object): HTML 분석 정보.
        * `detected_tags` (Array): 검출된 HTML 태그 목록 (예: `['p', 'strong']`).
        * `html_complexity` (String): HTML 복잡도 (`simple`, `medium`, `complex`).
    * `page_path`, `component_path` 등 원본 메타데이터를 모두 상속받습니다.

#### **2.4. 기타 컬렉션**

* `translation_memory_{lang_pair}`: `aem_tm_builder`가 생성한 초기 TM. 후속 처리 과정의 중간 산출물.
* `untranslated_components_{lang_pair}`: 버전 간 구조가 달라 번역 쌍을 만들지 못한 컴포넌트 목록. `page_structure_analyzer`가 이 컬렉션을 사용하여 구조 차이 리포트를 생성합니다 [cite: page_structure_analyzer.py].

---

### ## 3. ChromaDB 스키마

* **역할**: AI 기반의 빠른 유사도 검색을 위한 벡터 인덱스 저장소.
* **Collection Naming**: `tm_{lang_pair}` (예: `tm_en_ko`, `tm_en_ja`) [cite: chroma_indexer.py]

각 컬렉션의 개별 항목은 다음과 같은 구조를 가집니다.

* **Document**:
    * **내용**: `clean_translation_memory` 컬렉션의 `source_text` 필드.
    * **역할**: 임베딩 벡터를 생성하는 원본 텍스트이자, 검색 결과의 소스 텍스트로 사용됩니다.
* **Embedding**:
    * **내용**: `SentenceTransformer` 모델이 Document(`source_text`)를 변환한 고차원 벡터.
    * **역할**: 벡터 공간에서 다른 텍스트와의 의미적 거리(유사도)를 계산하는 데 사용됩니다.
* **Metadata**:
    * **내용**: 벡터와 함께 저장되는 추가 정보. QA 워크스테이션에서 검색 결과를 풍부하게 만드는 데 필수적입니다 [cite: searcher.py].
        * `target_text` (String): **(핵심)** `source_text`에 해당하는 번역문.
        * `page_path` (String): 번역문의 원본 AEM 페이지 경로.
        * `component_path` (String): 번역문의 원본 컴포넌트 경로.
    * **역할**: 유사한 `source_text`를 찾은 후, 사용자에게 실제 필요한 번역문과 그 출처 정보를 제공합니다.
* **ID**:
    * **내용**: `clean_translation_memory` 문서의 MongoDB `_id`를 문자열로 변환한 값.
    * **역할**: ChromaDB의 검색 결과를 MongoDB의 원본 상세 데이터와 연결하는 고유한 키 역할을 합니다.