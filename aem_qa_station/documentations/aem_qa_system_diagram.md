``` mermaid
graph TB
    %% External Sources
    subgraph "🌐 External Data Sources"
        AEM["`**AEM Server**
        prod-author.illumina.com
        
        **Versions:**
        • lm-en, lm-ko, lm-ja
        • spac-ko_KR  
        • apac-en, apac-ja_JP`"]
        
        Excel["`**Excel Assets**
        • Translation Memory
        • Glossary Files
        • Source Materials`"]
    end

    %% Input Management
    subgraph "📥 Input Management"
        InputFolder["`**data/1_input/**
        
        **Master Files:**
        • aem_pages_master.txt
        • pdf_list_master_en_ko.csv
        • pdf_list_master_en_ja.csv
        
        **Batch Folders:**
        • aem_batches_todo/
        • pdf_batches_todo/
        • source_excels/`"]
    end

    %% Collection Components
    subgraph "🤖 Data Collection"
        AEMCollector["`**AEM Collector**
        src/collectors/aem_collector.py
        
        • Multi-threaded download
        • 6 version support
        • JSON snapshot format
        • Retry logic with 404 handling`"]
        
        PDFCollector["`**PDF Collector** 
        src/collectors/pdf_collector.py
        
        • Multi-language support
        • Concurrent downloads
        • Language pair processing`"]
        
        ManifestBuilder["`**Manifest Builder**
        src/collectors/manifest_builder.py
        
        • File inventory scanning
        • Metadata generation
        • Path normalization`"]
        
        PackageBuilder["`**Package Builder**
        src/collectors/package_builder.py
        
        • ZIP package creation
        • Relative path handling
        • Manifest integration`"]
    end

    %% Processing Components  
    subgraph "⚙️ Data Processing"
        DataIngestor["`**Data Ingestor**
        src/processors/data_ingestor.py
        
        • ZIP to MongoDB ingestion
        • Component decomposition
        • Hash-based change detection
        • Version management`"]
        
        AEMTMBuilder["`**TM Builder**
        src/processors/aem_tm_builder.py
        
        • Structure comparison
        • Translation pair extraction
        • Multi-language TM generation
        • Quality filtering`"]
        
        StructureAnalyzer["`**Structure Analyzer**
        src/analyzers/page_structure_analyzer.py
        
        • Page diff analysis
        • Component change detection
        • Mismatch reporting`"]
    end

    %% Storage Layer
    subgraph "💾 Storage Systems"
        MongoDB["`**MongoDB**
        Database: aem_qa_system
        
        **Collections:**
        • page_components
        • translation_memory_en_ko
        • translation_memory_en_ja
        • untranslated_components_*`"]
        
        ChromaDB["`**ChromaDB Vector Store**
        rag_database/chroma_db_store/
        
        **Collections:**
        • tm_en_ko (Korean vectors)
        • tm_en_ja (Japanese vectors)
        
        **Features:**
        • Semantic search
        • Similarity scoring`"]
        
        FileSystem["`**File System**
        
        **Downloaded Assets:**
        • data/2_downloaded/aem_snapshots/
        • data/2_downloaded/pdfs/
        
        **Processed Data:**
        • data/3_processed/packages/
        • data/3_processed/final_tm_*.csv
        
        **Reports:**
        • reports/page_structure_diff_*.csv
        • reports/untranslated_*.csv`"]
    end

    %% AI/ML Components
    subgraph "🧠 AI/ML Processing"
        ChromaIndexer["`**Chroma Indexer**
        src/indexing/chroma_indexer.py
        
        • Text embedding generation
        • Vector index creation
        • Batch processing
        • GPU acceleration`"]
        
        EmbeddingModel["`**Embedding Model**
        intfloat/multilingual-e5-large
        
        • Multi-language support
        • CUDA/CPU optimization
        • Semantic similarity`"]
        
        LLMModel["`**LLM Integration**
        llama3:8b
        
        • Text processing
        • Quality enhancement
        • Content analysis`"]
    end

    %% Workflow Management
    subgraph "📋 Workflow Orchestration"
        Notebooks["`**Jupyter Notebooks**
        
        **Processing Pipeline:**
        1. Process linguist assets
        2. Setup batches
        3. Run multilingual collection  
        4. Run data processing
        5. Build final TM
        6. Analyze structure differences
        7. Create vector index
        8. Test search functionality`"]
        
        BatchUtils["`**Batch Utilities**
        src/utils/batch_utils.py
        
        • Batch file creation
        • Load balancing
        • Progress tracking`"]
        
        Config["`**Configuration**
        src/config.py
        
        • Path management
        • Database settings
        • Language pair definitions
        • Processing modes`"]
    end

    %% Data Flow - Collection Phase
    Excel --> InputFolder
    AEM --> AEMCollector
    InputFolder --> AEMCollector
    InputFolder --> PDFCollector
    AEMCollector --> ManifestBuilder
    PDFCollector --> ManifestBuilder
    ManifestBuilder --> PackageBuilder
    PackageBuilder --> FileSystem

    %% Data Flow - Processing Phase
    FileSystem --> DataIngestor
    DataIngestor --> MongoDB
    MongoDB --> AEMTMBuilder
    AEMTMBuilder --> MongoDB
    AEMTMBuilder --> StructureAnalyzer
    StructureAnalyzer --> FileSystem

    %% Data Flow - AI/ML Phase  
    MongoDB --> ChromaIndexer
    ChromaIndexer --> ChromaDB
    EmbeddingModel --> ChromaIndexer
    LLMModel --> AEMTMBuilder

    %% Workflow Control
    Notebooks --> DataIngestor
    Notebooks --> AEMTMBuilder
    Notebooks --> StructureAnalyzer
    Notebooks --> ChromaIndexer
    BatchUtils --> Notebooks
    Config --> AEMCollector
    Config --> PDFCollector
    Config --> DataIngestor

    %% Multi-language Support
    subgraph "🌐 Language Support"
        LangConfig["`**Language Pairs**
        
        **Supported:**
        • EN-KO (English ↔ Korean)
        • EN-JA (English ↔ Japanese)
        
        **Extensible:**
        • EN-ZH (Chinese)
        • EN-DE (German)
        • KO-JA (Korean-Japanese)`"]
    end

    LangConfig -.-> AEMCollector
    LangConfig -.-> AEMTMBuilder
    LangConfig -.-> ChromaIndexer

    %% Styling
    classDef external fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef input fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef collection fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef processing fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef ai fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef workflow fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef language fill:#e0f2f1,stroke:#00695c,stroke-width:2px

    class AEM,Excel external
    class InputFolder input
    class AEMCollector,PDFCollector,ManifestBuilder,PackageBuilder collection
    class DataIngestor,AEMTMBuilder,StructureAnalyzer processing
    class MongoDB,ChromaDB,FileSystem storage
    class ChromaIndexer,EmbeddingModel,LLMModel ai
    class Notebooks,BatchUtils,Config workflow
    class LangConfig language
```

🏗️ AEM QA System (백엔드)
핵심 역할: 데이터 수집, 처리, AI 모델 학습

데이터 수집: AEM 서버에서 다국어 페이지/PDF 수집
데이터 처리: MongoDB 저장, TM 구축, 구조 분석
AI 준비: ChromaDB 벡터 인덱싱, 임베딩 모델 학습