``` mermaid
flowchart TD
    A[시작 create_base_tm_from_excels] --> B[기반 TM 처리]
    B --> C[_load_and_tag_excels_from_folder 호출]
    C --> D{데이터 발견?}
    D -->|예| E[FOUNDATION_TM_MAP으로 _transform_df 호출]
    D -->|아니오| F[기반 TM 건너뛰기]
    E --> G[변환된 리스트에 추가]
    F --> G
    
    G --> H[업데이트 TM 처리]
    H --> I[_load_and_tag_excels_from_folder 호출]
    I --> J{데이터 발견?}
    J -->|예| K[UPDATE_REQUEST_TM_MAP으로 _transform_df 호출]
    J -->|아니오| L[업데이트 TM 건너뛰기]
    K --> M[변환된 리스트에 추가]
    L --> M
    
    M --> N{변환된 리스트가 비어있음?}
    N -->|예| O[종료 처리할 파일 없음]
    N -->|아니오| P[모든 DataFrame 통합]
    P --> Q[중복 처리 업데이트 우선]
    Q --> R[빈 값 제거]
    R --> S[고유 ID 추가 및 컬럼 순서 정리]
    S --> T[최종 base_tm.csv 파일로 저장]
    T --> U[종료 TM 생성 완료]

    subgraph helper1 [헬퍼 1: _load_and_tag_excels_from_folder]
        L1[헬퍼 시작] --> L2[glob으로 모든 xlsx 파일 찾기]
        L2 --> L3{파일 발견?}
        L3 -->|아니오| L4[None 반환]
        L3 -->|예| L5[각 파일 반복]
        L5 --> L6[Excel을 DataFrame으로 읽기]
        L6 --> L7[Source_File 컬럼 추가]
        L7 --> L8[리스트에 추가]
        L8 --> L5
        L5 -.->|반복 종료| L9[모든 DataFrame 연결]
        L9 --> L10[결합된 DataFrame 반환]
    end

    subgraph helper2 [헬퍼 2: _transform_df]
        T1[헬퍼 시작] --> T2[DataFrame에 존재하는 컬럼만 매핑 필터링]
        T2 --> T3[존재하는 컬럼만 선택]
        T3 --> T4[표준 이름으로 컬럼 이름 변경]
        T4 --> T5[변환된 DataFrame 반환]
    end
    
    C -.-> helper1
    I -.-> helper1
    E -.-> helper2
    K -.-> helper2
    

    
    class A,U startEnd
    class O error
    class L1,L10,T1,T5 helper