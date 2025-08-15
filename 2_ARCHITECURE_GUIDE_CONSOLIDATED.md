
### **문서 2/8: 통합 아키텍처 가이드**

## **🏛️ AEM QA System & Workstation: 통합 아키텍처 가이드**

이 문서는 AEM QA System & Workstation의 전반적인 기술 아키텍처, 구성 요소, 데이터 흐름 및 설계 원칙을 설명합니다. 시스템을 유지보수하거나 확장하려는 개발자를 위한 최상위 기술 설계 문서입니다.

-----

### \#\# 1. 아키텍처 개요

본 시스템은 **분리된(Decoupled) 아키텍처**를 채택하고 있습니다.

  * **백엔드 시스템 (`aem-qa-system`)**: 데이터 수집, 변환, 적재(ETL) 및 인덱싱을 담당하는 데이터 파이프라인입니다. 주기적인 배치(batch) 작업으로 실행되도록 설계되었습니다.
  * **클라이언트 애플리케이션 (`aem_qa_station`)**: QA 전문가가 사용하는 실시간 웹 기반 워크스테이션입니다. 백엔드가 준비한 데이터를 조회하고 분석하여 사용자에게 가치를 제공합니다.

두 시스템은 직접 통신하지 않고, \*\*영속성 계층(Persistence Layer)\*\*인 **MongoDB**와 **ChromaDB**를 통해 **비동기적으로(Asynchronously)** 데이터를 교환합니다. 이 구조는 백엔드의 데이터 처리 작업이 클라이언트 애플리케이션의 가용성에 영향을 주지 않도록 보장하여 시스템의 안정성과 확장성을 높입니다.

-----

### \#\# 2. 시스템 구성 요소

시스템은 크게 세 가지 논리적 계층으로 구성됩니다.

#### **2.1. 백엔드 시스템 (`aem-qa-system`)**

AEM 콘텐츠와 번역 자산을 수집하고 가공하여 데이터베이스에 저장하는 역할을 수행합니다.

  * **Orchestrator (Jupyter Notebooks)**
      * `notebooks/` 디렉토리의 마스터 노트북 3개는 전체 백엔드 파이프라인의 실행 순서를 제어하는 지휘자 역할을 합니다.
  * **Collectors**
      * `excel_processor.py`: 다양한 형식의 Excel 파일(TM, Glossary)을 표준화된 CSV로 변환합니다.
      * `aem_collector.py`: AEM 서버에 접속하여 지정된 페이지들의 다국어 버전 JSON 스냅샷을 병렬로 수집합니다.
      * `pdf_collector.py`: PDF 파일 목록을 기반으로 원본 PDF 문서를 다운로드합니다.
  * **Processors**
      * `data_ingestor.py`: 수집된 AEM 스냅샷 패키지를 MongoDB의 `page_components` 컬렉션에 저장합니다.
      * `aem_tm_builder.py`: `page_components` 데이터를 기반으로 버전 간 구조를 비교하여 초기 번역 메모리(TM)를 구축합니다.
      * `tm_cleaner.py` & `utlimate_tm_builder.py`: 초기 TM에서 HTML 태그 등 노이즈를 제거하고, 순수 텍스트와 HTML 컴포넌트를 분리합니다.
      * `semantic_segmenter.py`: 정제된 텍스트 중 긴 문장을 AI 임베딩 모델을 사용하여 의미적으로 일관된 짧은 세그먼트로 자동 분할합니다.
  * **Indexer**
      * `chroma_indexer.py`: 최종 정제/분할된 TM의 텍스트를 벡터 임베딩으로 변환하여 ChromaDB에 저장, AI 유사도 검색을 준비합니다.

#### **2.2. 클라이언트 애플리케이션 (`aem_qa_station`)**

Streamlit으로 제작된 대화형 웹 애플리케이션으로, QA 전문가에게 직관적인 UI를 제공합니다.

  * **Main Application (`app.py`)**
      * Streamlit을 사용하여 전체 UI 레이아웃을 구성하고, 사용자 인터랙션을 처리하며, 다른 모듈을 호출하여 비즈니스 로직을 실행합니다.
  * **Core Modules (`modules/`)**
      * `analyzer.py`: 사용자가 선택한 두 버전에 대해 MongoDB의 `page_components` 컬렉션을 직접 쿼리하여 컴포넌트 단위의 변경사항(추가/수정/삭제)을 실시간으로 분석합니다.
      * `searcher.py`: 분석된 텍스트 변경사항을 기반으로 ChromaDB에 쿼리하여 유사한 번역 사례를 검색하고, 'AI 번역 추천' 결과를 생성합니다.
      * `version_manager.py`: MongoDB를 스캔하여 분석 가능한 모든 AEM 버전의 목록을 동적으로 생성하고, UI 선택지에 제공합니다.
      * `connections.py`: Streamlit의 캐시 기능을 활용하여 MongoDB와 ChromaDB에 대한 연결을 효율적으로 관리하고 재사용합니다.

#### **2.3. 영속성 계층 (Persistence Layer)**

백엔드와 클라이언트 간의 데이터 허브 역할을 하며, Docker Compose를 통해 관리됩니다.

  * **MongoDB**:
      * **역할**: 구조화된 데이터의 주 저장소.
      * **주요 컬렉션**: `page_components` (AEM 컴포넌트 원본), `clean_translation_memory_*` (최종 정제 TM), `html_component_archive_*` (HTML 컴포넌트) 등.
  * **ChromaDB**:
      * **역할**: 텍스트 임베딩 벡터의 저장 및 검색.
      * **주요 컬렉션**: `tm_en_ko`, `tm_en_ja` 등 언어 쌍별로 생성된 벡터 인덱스 컬렉션.

-----

### \#\# 3. 데이터 흐름도 (End-to-End Data Flow)

아래 다이어그램은 사용자의 초기 데이터 입력부터 최종 QA 분석 결과 도출까지의 전체 데이터 흐름을 보여줍니다.

```mermaid
graph LR
    subgraph Input
        direction LR
        I1[Excel Files]
        I2[AEM Page List]
    end

    subgraph Backend - aem-qa-system
        direction TB
        B1[1. Process Excels<br/>(excel_processor.py)]
        B2[2. Collect AEM<br/>(aem_collector.py)]
        B3[3. Ingest to Mongo<br/>(data_ingestor.py)]
        B4[4. Build & Clean TM<br/>(tm_cleaner.py)]
        B5[5. Segment TM<br/>(semantic_segmenter.py)]
        B6[6. Index to Chroma<br/>(chroma_indexer.py)]
        
        B1 --> B3
        B2 --> B3
        B3 --> B4 --> B5 --> B6
    end

    subgraph Database
        direction TB
        DB1[MongoDB]
        DB2[ChromaDB]
    end

    subgraph Client - aem_qa_station
        direction TB
        C1[Streamlit App<br/>(app.py)]
        C2[Page Analyzer<br/>(analyzer.py)]
        C3[AI Searcher<br/>(searcher.py)]
        
        C1 -- User Input --> C2
        C1 -- Text --> C3
    end

    Input --> Backend
    B3 -- Write --> DB1
    B5 -- Write --> DB1
    B6 -- Write --> DB2
    
    C2 -- Read --> DB1
    C3 -- Read --> DB2
    
    DB1 -- Data --> C2
    DB2 -- Vector Search --> C3
    
    C2 -- Analysis --> C1
    C3 -- Recommendations --> C1
```

-----

### \#\# 4. 아키텍처 설계 원칙

  * **모듈성 (Modularity)**: 시스템은 `collectors`, `processors`, `analyzers` 등 기능적으로 명확히 구분된 모듈로 구성되어 있어 특정 기능을 수정하거나 추가하기 용이합니다.
  * **확장성 (Scalability)**: 데이터 수집기(`aem_collector`)는 다중 워커(worker)를 사용하여 병렬 처리를 수행하며, 필요시 워커 수를 늘려 수집 성능을 확장할 수 있습니다. 또한, Streamlit 애플리케이션은 표준 웹 기술을 사용하므로 로드 밸런서 뒤에 여러 인스턴스를 배치하여 수평적으로 확장할 수 있습니다.
  * **재사용성 (Reusability)**: 데이터베이스 연결(`connections.py`), 버전 조회(`version_manager.py`) 등 공통 기능은 별도의 모듈로 분리되어 여러 컴포넌트에서 재사용됩니다. 이는 코드 중복을 줄이고 일관성을 유지하는 데 도움이 됩니다.