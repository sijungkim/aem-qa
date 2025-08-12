``` mermaid
graph TD
    subgraph TM 생성 파이프라인
        A[Start: create_base_tm_from_excels] --> B{1. 기반(Foundation) TM 처리};
        B --> C{Call: _load_and_tag_excels_from_folder};
        C --> D{Data Found?};
        D -- Yes --> E{Call: _transform_df with<br>FOUNDATION_TM_MAP};
        D -- No --> F[Skip Foundation TM];
        E --> G[Append to Transformed List];
        F --> G;

        G --> H{2. 업데이트(Update) TM 처리};
        H --> I{Call: _load_and_tag_excels_from_folder};
        I --> J{Data Found?};
        J -- Yes --> K{Call: _transform_df with<br>UPDATE_REQUEST_TM_MAP};
        J -- No --> L[Skip Update TM];
        K --> M[Append to Transformed List];
        L --> M;

        M --> N{Transformed List is Empty?};
        N -- Yes --> O[End: No files to process];
        N -- No --> P[3. 모든 DataFrame 통합];
        P --> Q[4. 중복 처리 (Update 우선)];
        Q --> R[5. 빈 값 제거];
        R --> S[6. 고유 ID 추가 및 컬럼 순서 정리];
        S --> T[7. 최종 base_tm.csv 파일로 저장];
        T --> U[End: TM Generation Complete];
    end

    subgraph Helper 1: _load_and_tag_excels_from_folder
        L1[Start Helper] --> L2{glob: Find all *.xlsx files};
        L2 --> L3{Files Found?};
        L3 -- No --> L4[Return None];
        L3 -- Yes --> L5[Loop through each file];
        L5 --> L6[Read Excel into DataFrame];
        L6 --> L7[Add 'Source_File' column];
        L7 --> L8[Append to list];
        L8 --> L5;
        L5 -- Loop End --> L9[Concat all DataFrames];
        L9 --> L10[Return Combined DataFrame];
    end

    subgraph Helper 2: _transform_df
        T1[Start Helper] --> T2{Filter mapping for<br>columns that exist in DataFrame};
        T2 --> T3[Select only the existing columns];
        T3 --> T4[Rename columns to standard names];
        T4 --> T5[Return Transformed DataFrame];
    end

    style A fill:#BDEB9A,stroke:#333,stroke-width:2px
    style U fill:#BDEB9A,stroke:#333,stroke-width:2px
    style O fill:#FFB8B8,stroke:#333,stroke-width:2px
```