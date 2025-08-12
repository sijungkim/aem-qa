``` mermaid
graph TD
    A[📄 PDF 파일 쌍] --> B[EN PDF]
    A --> C[JA PDF]
    
    B --> D[🔍 PyMuPDF로 텍스트 추출]
    C --> E[🔍 PyMuPDF로 텍스트 추출]
    
    D --> F[📝 EN Raw Text<br/>9550 문자]
    E --> G[📝 JA Raw Text<br/>6814 문자]
    
    F --> H[⚡ 청크 분할<br/>터보모드: 15000자<br/>일반모드: 3000자]
    G --> I[⚡ 청크 분할<br/>터보모드: 15000자<br/>일반모드: 3000자]
    
    H --> J[🤖 LLM 처리<br/>EN 청크 1/4]
    H --> K[🤖 LLM 처리<br/>EN 청크 2/4]
    H --> L[🤖 LLM 처리<br/>EN 청크 3/4]
    H --> M[🤖 LLM 처리<br/>EN 청크 4/4]
    
    I --> N[🤖 LLM 처리<br/>JA 청크 1/3]
    I --> O[🤖 LLM 처리<br/>JA 청크 2/3]
    I --> P[🤖 LLM 처리<br/>JA 청크 3/3]
    
    J --> Q[📋 JSON 파싱<br/>문장 세그먼트 추출]
    K --> Q
    L --> Q
    M --> Q
    
    N --> R[📋 JSON 파싱<br/>문장 세그먼트 추출]
    O --> R
    P --> R
    
    Q --> S[🔍 품질 필터링<br/>• 길이 체크<br/>• 신뢰도 체크<br/>• 의미 있는 단어 확인]
    R --> T[🔍 품질 필터링<br/>• 길이 체크<br/>• 신뢰도 체크<br/>• 의미 있는 단어 확인]
    
    S --> U[✅ EN 세그먼트<br/>10개 완성]
    T --> V[✅ JA 세그먼트<br/>13개 완성]
    
    U --> W[🧠 임베딩 모델<br/>SentenceTransformer]
    V --> W
    
    W --> X[📊 코사인 유사도 계산<br/>임계값: 0.65]
    
    X --> Y{유사도 >= 0.65?}
    
    Y -->|Yes| Z[✨ 번역 쌍 생성<br/>• source_text<br/>• target_text<br/>• similarity_score<br/>• category<br/>• confidence]
    Y -->|No| AA[❌ 매칭 실패<br/>버림]
    
    Z --> BB[📎 메타데이터 추가<br/>• PDF 파일명<br/>• 경로 정보<br/>• 생성 일시<br/>• 품질 점수]
    
    BB --> CC[💾 최종 TM 엔트리<br/>CSV로 저장]
    
    subgraph "LLM 프롬프트 최적화"
        DD[🇯🇵 일본어 프롬프트<br/>「できるだけ多くの完全な文を抽出」]
        EE[🇰🇷 한국어 프롬프트<br/>「가능한 많은 완전한 문장을 추출」]
        FF[🇺🇸 영어 프롬프트<br/>「Extract as many complete sentences」]
    end
    
    subgraph "성능 최적화 모드"
        GG[⚡ 터보 모드<br/>• 15000자 청크<br/>• 1500 토큰 제한<br/>• Temperature 0.0]
        HH[🚀 빠른 모드<br/>• 8000자 청크<br/>• 2000 토큰 제한<br/>• Temperature 0.0]
        II[🎯 일반 모드<br/>• 3000자 청크<br/>• 무제한 토큰<br/>• Temperature 0.1]
    end
    
    style A fill:#e1f5fe
    style CC fill:#c8e6c9
    style Z fill:#fff3e0
    style W fill:#f3e5f5
```