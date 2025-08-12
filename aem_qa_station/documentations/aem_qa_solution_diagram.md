``` mermaid
graph TB
    %% External Data Sources
    subgraph "🌐 External Sources"
        AEM[AEM Server<br/>prod-author.illumina.com]
        Excel[Excel Files<br/>TM & Glossary]
    end

    %% Input Layer
    subgraph "📥 Input Management"
        InputDir["`**data/1_input/**
        • aem_pages_master.txt
        • pdf_list_master_*.csv
        • source_excels/`"]
        
        BatchTodo["`**Batch Processing**
        • aem_batches_todo/
        • pdf_batches_todo/`"]
    end

    %% Collection Layer - aem_qa_system
    subgraph "🤖 Data Collection Layer"
        AEMCol["`**AEM Collector**
        Multi-threaded
        6 versions support`"]
        
        PDFCol["`**PDF Collector** 
        Multi-language
        EN/KO/JA support`"]
        
        PackageBuild["`**Package Builder**
        ZIP creation
        Manifest generation`"]
    end

    %% Processing Layer
    subgraph "⚙️ Processing Layer"
        DataIngest["`**Data Ingestor**
        ZIP → MongoDB
        Component parsing`"]
        
        TMBuilder["`**TM Builder**
        Structure comparison
        Multi-language TM`"]
        
        StructAnalyzer["`**Structure Analyzer**
        Page diff analysis
        Change detection`"]
    end

    %% Storage Layer
    subgraph "💾 Storage Layer"
        MongoDB["`**MongoDB**
        • page_components
        • translation_memory_*
        • untranslated_components_*`"]
        
        ChromaDB["`**ChromaDB**
        • tm_en_ko vectors
        • tm_en_ja vectors
        • Embedding search`"]
        
        FileStorage["`**File Storage**
        • ZIP packages
        • CSV reports
        • Downloaded assets`"]
    end

    %% AI Layer
    subgraph "🧠 AI/ML Layer"
        EmbedModel["`**Embedding Model**
        multilingual-e5-large
        GPU accelerated`"]
        
        LLMModel["`**LLM Model**
        llama3:8b
        Text processing`"]
    end

    %% UI Layer - aem_qa_station
    subgraph "🖥️ QA Workstation (Streamlit)"
        StreamlitApp["`**Main App**
        app.py
        Dashboard & Analysis`"]
        
        Connections["`**connections.py**
        DB connections
        Cache management`"]
        
        Analyzer["`**analyzer.py**
        Page change analysis
        Component comparison`"]
        
        Searcher["`**searcher.py**
        AI translation search
        Similarity ranking`"]
    end

    %% Workflow Layer
    subgraph "📋 Notebook Workflow"
        Workflow["`**Sequential Processing**
        1. Process linguist assets
        2. Setup batches  
        3. Run collection
        4. Run processing
        5. Build TM
        6. Analyze structure
        7. Create vector index
        8. Test search`"]
    end

    %% Language Support
    subgraph "🌐 Multi-Language Support"
        Languages["`**Supported Pairs**
        • EN-KO (English-Korean)
        • EN-JA (English-Japanese)
        
        **AEM Versions**
        • lm-en, lm-ko, lm-ja
        • spac-ko_KR
        • apac-en, apac-ja_JP`"]
    end

    %% Data Flow - Collection
    Excel --> InputDir
    AEM --> AEMCol
    AEM --> PDFCol
    InputDir --> BatchTodo
    BatchTodo --> AEMCol
    BatchTodo --> PDFCol
    AEMCol --> PackageBuild
    PDFCol --> PackageBuild

    %% Data Flow - Processing  
    PackageBuild --> FileStorage
    FileStorage --> DataIngest
    DataIngest --> MongoDB
    MongoDB --> TMBuilder
    TMBuilder --> MongoDB
    TMBuilder --> ChromaDB
    TMBuilder --> StructAnalyzer

    %% Data Flow - AI
    ChromaDB --> EmbedModel
    MongoDB --> LLMModel

    %% Data Flow - UI
    MongoDB --> Connections
    ChromaDB --> Connections
    Connections --> StreamlitApp
    Connections --> Analyzer
    Connections --> Searcher
    Analyzer --> StreamlitApp
    Searcher --> StreamlitApp
    EmbedModel --> Searcher

    %% Workflow connections
    Workflow --> DataIngest
    Workflow --> TMBuilder
    Workflow --> StructAnalyzer

    %% Language flow
    Languages -.-> AEMCol
    Languages -.-> TMBuilder
    Languages -.-> ChromaDB
```

🏗️ aem_qa_system (백엔드 데이터 처리)

데이터 수집: AEM 서버에서 다국어 페이지 스냅샷과 PDF 파일 수집
데이터 처리: MongoDB에 저장 후 번역 메모리(TM) 구축
AI 인덱싱: ChromaDB에 벡터 임베딩으로 검색 가능한 형태로 저장

🖥️ aem_qa_station (프론트엔드 워크스테이션)

페이지 분석: 구조 변경사항 분석 및 번역 필요 항목 식별
AI 번역 추천: 유사한 번역 사례를 AI가 자동으로 검색하여 추천
직관적 UI: Streamlit 기반의 사용자 친화적 인터페이스

🔄 주요 워크플로우

데이터 수집 → 2. 배치 설정 → 3. 다국어 수집 → 4. DB 저장
TM 구축 → 6. 구조 분석 → 7. 벡터 인덱싱 → 8. QA 워크스테이션 사용

🌐 다국어 지원

언어 쌍: 영어-한국어, 영어-일본어
AEM 버전: Language Master, SPAC, APAC 등 다양한 지역별 버전 지원

이 시스템의 핵심은 AI 기반 번역 품질 보증으로, 기존 번역 데이터를 학습하여 새로운 번역 작업에 대한 추천을 제공하는 것입니다!


🏗️ 시스템 구성

1. 데이터 수집 (aem_qa_system)
AEM 서버에서 다국어 페이지 스냅샷 수집
PDF 파일 다운로드 및 관리
배치 처리를 통한 효율적 수집

2. 데이터 처리
MongoDB에 컴포넌트 단위로 저장
언어별 번역 메모리(TM) 구축
페이지 구조 변경사항 분석

3. AI/ML 기능
ChromaDB 벡터 검색으로 유사 번역 찾기
GPU 가속 임베딩 모델 활용
실시간 번역 추천

4. QA 워크스테이션 (aem_qa_station)
Streamlit 기반 웹 인터페이스
페이지별 변경사항 대시보드
AI 번역 추천 시스템

5. 다국어 지원
영어-한국어, 영어-일본어 번역 쌍
여러 AEM 버전 동시 지원
이 시스템은 번역 품질 보증을 자동화하여 번역가와 QA 담당자의 작업 효율성을 크게 향상시키는 것이 목표입니다!




