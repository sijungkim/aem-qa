``` mermaid
graph TD
    A[Start] --> B(Input: 원본 패키지명, 샘플 페이지 수);
    B --> C{파일 존재 여부 확인};
    C -- No --> D[❌ 오류 출력 및 종료];
    
    C -- Yes --> E[try...except 블록 시작];
    E --> F["with zipfile.ZipFile(...) as source_zip"];
    
    F --> G["Helper 1 호출<br>_read_manifest_from_zip"];
    G --> H1[manifest.json 읽고 파싱];
    H1 --> I["Helper 2 호출<br>_get_sampled_page_paths"];
    I --> J[페이지 경로 추출 및 샘플링];
    J --> K[샘플 정보 필터링];
    K --> L["Helper 3 호출<br>_write_new_package"];
    L --> M[새 ZIP 파일 생성 및 저장];
    M --> N[✅ 성공 메시지 출력];
    N --> Z[End];

    E -.-> X[Catch Exception];
    X --> Y[❌ 오류 메시지 출력];
    Y --> Z;

    %% Styling
    style A fill:#BDEB9A,stroke:#333,stroke-width:2px
    style Z fill:#BDEB9A,stroke:#333,stroke-width:2px
    style D fill:#FFB8B8,stroke:#333,stroke-width:2px
    style Y fill:#FFB8B8,stroke:#333,stroke-width:2px

```
