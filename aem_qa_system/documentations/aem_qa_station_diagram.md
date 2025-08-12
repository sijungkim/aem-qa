``` mermaid
graph TB
    %% User Interface Layer
    subgraph "🖥️ User Interface"
        Browser["`**Web Browser**
        
        **Access:**
        • localhost:8501
        • Streamlit interface
        • Responsive design`"]
        
        StreamlitApp["`**Main Application**
        app.py
        
        **Features:**
        • CSV file upload
        • Page selection dashboard
        • Real-time analysis
        • Multi-language support`"]
    end

    %% UI Components
    subgraph "🧩 UI Components"
        FileUpload["`**File Upload System**
        
        **Supported Formats:**
        • CSV with Page Path column
        • Auto-detection of columns
        • Sample format guide
        • Error handling`"]
        
        Dashboard["`**Analysis Dashboard**
        
        **Features:**
        • Page-wise change summary
        • Status filtering
        • Sorting options
        • Progress indicators
        • Metrics display`"]
        
        DetailView["`**Detailed Analysis View**
        
        **Components:**
        • AEM edit page links
        • Component change breakdown
        • Change type visualization
        • Expandable details`"]
        
        AIRecommend["`**AI Recommendation Panel**
        
        **Features:**
        • Translation suggestions
        • Similarity scoring
        • Confidence levels
        • Source context
        • Historical examples`"]
    end

    %% Backend Modules
    subgraph "⚙️ Backend Modules"
        Connections["`**Connection Manager**
        modules/connections.py
        
        **Responsibilities:**
        • MongoDB client caching
        • ChromaDB client caching
        • Connection health monitoring
        • Error handling`"]
        
        Analyzer["`**Page Analyzer**
        modules/analyzer.py
        
        **Functions:**
        • Component comparison
        • Change detection
        • Structure analysis
        • Text extraction
        • Summary generation`"]
        
        Searcher["`**Translation Searcher**
        modules/searcher.py
        
        **Capabilities:**
        • Semantic similarity search
        • Vector embedding
        • Batch translation lookup
        • Confidence scoring
        • Result formatting`"]
    end

    %% Data Sources (from aem_qa_system)
    subgraph "💾 Data Sources"
        MongoDB["`**MongoDB**
        aem_qa_system database
        
        **Collections Used:**
        • page_components
        • translation_memory_en_ko
        • translation_memory_en_ja
        • untranslated_components_*`"]
        
        ChromaDB["`**ChromaDB**
        Vector search database
        
        **Collections Used:**
        • tm_en_ko vectors
        • tm_en_ja vectors
        
        **Search Features:**
        • Cosine similarity
        • Top-K retrieval`"]
    end

    %% AI/ML Integration
    subgraph "🤖 AI Integration"
        EmbeddingModel["`**Embedding Model**
        intfloat/multilingual-e5-large
        
        **Usage:**
        • Real-time text encoding
        • Similarity computation
        • GPU acceleration
        • Cached in Streamlit`"]
        
        TranslationAI["`**Translation AI**
        
        **Features:**
        • Context-aware suggestions
        • Historical pattern matching
        • Quality confidence scoring
        • Multi-language support`"]
    end

    %% External Integration
    subgraph "🔗 External Integration"
        AEMLinks["`**AEM Author Links**
        
        **Generated URLs:**
        • Source page editing
        • Target page editing
        • Direct component access
        • Version-specific links`"]
        
        ReportExport["`**Report Export**
        
        **Formats:**
        • CSV download
        • Analysis summaries
        • Change tracking
        • QA checklists`"]
    end

    %% User Workflow
    subgraph "👤 User Workflow"
        UserActions["`**Typical User Journey**
        
        **Steps:**
        1. Upload page list CSV
        2. Review change dashboard
        3. Select pages for analysis
        4. View detailed changes
        5. Get AI translation suggestions
        6. Navigate to AEM for editing
        7. Export reports`"]
        
        QAProcess["`**QA Process Enhancement**
        
        **Benefits:**
        • Automated change detection
        • AI-powered recommendations
        • Reduced manual effort
        • Improved consistency
        • Faster turnaround`"]
    end

    %% Language Configuration
    subgraph "🌐 Language Configuration"
        LangSelector["`**Language Pair Selection**
        
        **Available:**
        • English → Korean
        • English → Japanese
        
        **Features:**
        • Dynamic switching
        • Language-specific UI
        • Context preservation`"]
        
        LocaleSupport["`**Internationalization**
        
        **Support:**
        • Multi-byte characters
        • Right-to-left text
        • Cultural formatting
        • Timezone handling`"]
    end

    %% Data Flow - User Interaction
    Browser --> StreamlitApp
    StreamlitApp --> FileUpload
    StreamlitApp --> Dashboard
    StreamlitApp --> DetailView
    StreamlitApp --> AIRecommend

    %% Data Flow - Backend Processing
    StreamlitApp --> Connections
    StreamlitApp --> Analyzer
    StreamlitApp --> Searcher
    
    Connections --> MongoDB
    Connections --> ChromaDB
    
    Analyzer --> MongoDB
    Searcher --> ChromaDB
    Searcher --> EmbeddingModel

    %% Data Flow - AI Integration
    EmbeddingModel --> TranslationAI
    TranslationAI --> AIRecommend

    %% Data Flow - External Integration
    DetailView --> AEMLinks
    Dashboard --> ReportExport

    %% User Flow
    UserActions --> Browser
    QAProcess --> UserActions

    %% Language Flow
    LangSelector --> StreamlitApp
    LocaleSupport --> StreamlitApp

    %% Session Management
    subgraph "💾 Session Management"
        SessionState["`**Streamlit Session State**
        
        **Cached Data:**
        • Uploaded page lists
        • Analysis results
        • Selected pages
        • User preferences
        • Connection pools`"]
        
        CacheManagement["`**Cache Management**
        
        **Strategies:**
        • @st.cache_resource for models
        • @st.cache_data for results
        • Memory optimization
        • Automatic cleanup`"]
    end

    StreamlitApp --> SessionState
    Connections --> CacheManagement
    EmbeddingModel --> CacheManagement

    %% Performance Optimization
    subgraph "⚡ Performance Features"
        LazyLoading["`**Lazy Loading**
        
        • On-demand analysis
        • Progressive rendering
        • Memory efficiency
        • Responsive UI`"]
        
        BatchProcessing["`**Batch Processing**
        
        • Multiple page analysis
        • Parallel processing
        • Progress tracking
        • Error recovery`"]
    end

    Dashboard --> LazyLoading
    Analyzer --> BatchProcessing

    %% Styling
    classDef ui fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef component fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef data fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef ai fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef external fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef workflow fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef language fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef session fill:#f3e5ab,stroke:#827717,stroke-width:2px
    classDef performance fill:#ffebee,stroke:#c62828,stroke-width:2px

    class Browser,StreamlitApp ui
    class FileUpload,Dashboard,DetailView,AIRecommend component
    class Connections,Analyzer,Searcher backend
    class MongoDB,ChromaDB data
    class EmbeddingModel,TranslationAI ai
    class AEMLinks,ReportExport external
    class UserActions,QAProcess workflow
    class LangSelector,LocaleSupport language
    class SessionState,CacheManagement session
    class LazyLoading,BatchProcessing performance
```

🖥️ AEM QA Station (프론트엔드)
핵심 역할: 사용자 인터페이스, 실시간 분석, AI 추천

사용자 인터페이스: Streamlit 기반 웹앱
페이지 분석: 실시간 변경사항 분석 및 시각화
AI 추천: 유사 번역 검색 및 추천 시스템