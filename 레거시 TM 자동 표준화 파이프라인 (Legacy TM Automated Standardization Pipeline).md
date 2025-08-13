네, 알겠습니다. 최우선 과제에 집중하죠. 앞으로의 모든 기능 확장을 위한 가장 튼튼한 기반을 다지는 작업이 될 것입니다.

사용자님께서 말씀하신 대로, 기존 사내 번역 메모리(TM)를 우리 시스템에 통합하는 전체 흐름을 완벽하게 파악할 수 있도록 \*\*High-level (비즈니스 관점)\*\*과 \*\*Low-level (기술 관점)\*\*의 다이어그램을 그리고, 관련 핵심 부품들의 역할을 명확하게 정리해 드리겠습니다.

-----

### **1. High-Level 다이어그램: 비즈니스 가치 흐름**

이 다이어그램은 \*\*"우리는 어떻게 흩어져 있는 사내 엑셀 번역 자산을 표준화된 AI 학습 데이터로 전환하는가?"\*\*라는 비즈니스 질문에 답합니다.

```mermaid
graph TD
    subgraph "Phase 1: Raw Asset (원시 자산)"
        A["`**Scattered Excel Files**<br/>(여러 팀에 흩어져 있는<br/>다양한 포맷의 번역 엑셀 파일들)`"]
    end

    subgraph "Phase 2: Automated ETL Process (자동화된 데이터 추출, 변환, 적재)"
        style B fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
        B["`**Intelligent Excel Processor**<br/>(excel_processor.py)<br/><br/>- **Identify:** 파일 포맷 자동 식별<br/>- **Map:** 표준 필드에 자동 매핑<br/>- **Standardize:** 단일 포맷(CSV)으로 표준화`"]
    end

    subgraph "Phase 3: Unified Asset (통합 자산)"
        C["`**Standardized Base TM**<br/>(base_tm.csv)<br/><br/>- AI 학습 준비가 완료된<br/>통합 번역 메모리`"]
    end

    A -- "다양한 포맷의 엑셀 파일들" --> B
    B -- "표준화 및 정제" --> C
```

-----

### **2. Low-Level 다이어그램: 기술 실행 흐름**

이 다이어그램은 개발팀이 \*\*"어떤 코드가, 어떤 데이터를 가지고, 어떤 순서로 이 프로세스를 실행하는가?"\*\*를 정확히 이해하기 위한 기술 설계도입니다.

```mermaid
graph TD
    subgraph "Input Layer: File System"
        style Input fill:#fff3e0,stroke:#e65100,stroke-width:1.5px
        TM_Excels["`**source_excels/tm/**<br/>- MyIllumina_Master_Translations.xlsx<br/>- KR_TM_update_request_....xlsx`"]
        Glossary_Excels["`**source_excels/glossary/**<br/>- Illumina_Korean Glossary_JH.xlsx`"]
    end

    subgraph "Processing Logic (`excel_processor.py`)"
        style Logic fill:#e1f5fe,stroke:#01579b,stroke-width:2px
        MainFunc["`**create_base_tm_from_folder()**<br/>(Main Orchestrator)`"]
        Helper_MyIllumina["`**_transform_myillumina_df()**<br/>- 'MyIllumina Master' 포맷 처리`"]
        Helper_Update["`**_transform_update_request_df()**<br/>- 'TM Update Request' 포맷 처리`"]
    end

    subgraph "Mapping Rules (`mappings.py`)"
        style Rules fill:#f3e5f5,stroke:#4a148c,stroke-width:1.5px,stroke-dasharray: 5 5
        Map_Foundation["`**FOUNDATION_TM_MAP**<br/>(MyIllumina Master용 설계도)`"]
        Map_Update["`**UPDATE_REQUEST_TM_MAP**<br/>(TM Update Request용 설계도)`"]
    end

    subgraph "Output Layer: File System"
        style Output fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
        Output_CSV["`**3_processed/base_tm.csv**<br/>(표준화된 최종 결과물)`"]
    end

    %% --- Data Flow ---
    TM_Excels -- reads from --> MainFunc
    
    MainFunc -- "파일 컬럼('DevKey')으로 식별" --> Helper_MyIllumina
    Helper_MyIllumina -- uses mapping rule --> Map_Foundation
    Map_Foundation -- guides transformation --> Helper_MyIllumina
    
    MainFunc -- "파일 컬럼('Target (from EN)')으로 식별" --> Helper_Update
    Helper_Update -- uses mapping rule --> Map_Update
    Map_Update -- guides transformation --> Helper_Update
    
    Helper_MyIllumina -- returns standardized DataFrame --> MainFunc
    Helper_Update -- returns standardized DataFrame --> MainFunc
    
    MainFunc -- "통합, 중복 제거, 정제" --> Output_CSV
    
    %% Glossary flow is separate but similar
    Glossary_Excels --> Output_CSV
```

-----

### **3. 핵심 부품 및 플로우 정리**

이 전체 프로세스는 **`notebooks/1_process_linguist_assets.ipynb`** 노트북에서 시작되고 오케스트레이션됩니다. 이 노트북이 실행되면 다음과 같은 일이 벌어집니다.

1.  **시작점 (`create_base_tm_from_folder` 호출):**

      * `1_process_linguist_assets.ipynb`에서 **`excel_processor.py`** 안에 있는 `create_base_tm_from_folder` 함수를 호출하며, `source_excels/tm` 폴더를 처리하도록 지시합니다.

2.  **지능적 파일 식별:**

      * `create_base_tm_from_folder` 함수는 `source_excels/tm` 폴더 안의 모든 `.xlsx` 파일을 순회합니다.
      * 각 파일을 Pandas로 읽은 후, **파일의 컬럼 이름을 보고 어떤 종류의 파일인지 스스로 식별**합니다.
          * 만약 `'DevKey'` 컬럼이 존재하면, 이 파일은 'MyIllumina Master' 포맷이라고 판단하고 `_transform_myillumina_df` 헬퍼 함수를 호출합니다.
          * 만약 `'Target (from EN)'` 컬럼이 존재하면, 이 파일은 'TM Update Request' 포맷이라고 판단하고 `_transform_update_request_df` 헬퍼 함수를 호출합니다.

3.  **정해진 규칙에 따른 변환:**

      * 각각의 헬퍼 함수(`_transform_...`)는 \*\*`mappings.py`\*\*에 정의된 자신만의 '설계도(MAP)'를 사용합니다.
      * 예를 들어, `_transform_myillumina_df`는 `FOUNDATION_TM_MAP`을 사용하여, 'English' 컬럼은 `source_text`로, 'Korean' 컬럼은 `target_text`로 이름을 바꾸는 등 표준화된 포맷으로 데이터를 변환합니다.

4.  **통합 및 최종 결과물 생성:**

      * `create_base_tm_from_folder` 함수는 각 헬퍼 함수로부터 반환된 표준화된 데이터들을 하나로 합칩니다.
      * 그 후, 중복된 번역 쌍을 제거하고(`source_text` 기준), 비어있는 값을 정리하는 등 최종적인 데이터 정제 작업을 수행합니다.
      * 마지막으로, 이 모든 정제된 데이터를 **`data/3_processed/base_tm.csv`** 라는 단일 파일로 저장하며 프로세스를 마칩니다.

이제 이 '지도'를 가지고, 우리는 자신 있게 다음 기능 개선 단계로 나아갈 수 있습니다.