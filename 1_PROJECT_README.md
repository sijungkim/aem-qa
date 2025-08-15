

### **문서 1/8: 프로젝트 README**

# **AEM QA System & Workstation**

[](https://github.com)
[](https://github.com)
[](https://github.com)

AEM(Adobe Experience Manager) 콘텐츠의 번역 품질 관리를 위한 통합 솔루션입니다. 이 시스템은 데이터를 수집, 처리, 인덱싱하는 백엔드 파이프라인(`aem-qa-system`)과, QA 전문가가 버전 간 변경사항을 분석하고 AI 번역 추천을 받는 웹 기반 워크스테이션(`aem_qa_station`)으로 구성됩니다.

## **✨ 주요 기능**

### **백엔드: 데이터 파이프라인 (`aem-qa-system`)**

  * **레거시 자산 통합**: 다양한 포맷의 레거시 번역 메모리(TM) 및 용어집(Glossary) Excel 파일을 자동으로 표준화하고 통합.
  * **AEM 콘텐츠 수집**: 지정된 AEM 페이지 목록에 대해 다국어 버전의 콘텐츠 스냅샷을 병렬로 수집하고 단일 패키지로 아카이빙.
  * **PDF 기반 TM 구축**: 다국어 PDF 문서 쌍에서 텍스트를 추출하고, 임베딩 유사도 비교를 통해 번역 쌍을 자동으로 생성.
  * **지능형 TM 처리**:
      * **HTML/텍스트 분리**: TM에서 HTML 태그가 포함된 컴포넌트를 분리하여 순수 텍스트만 정제.
      * **의미 기반 분할 (Semantic Segmentation)**: 긴 문장이나 복잡한 텍스트를 의미적 일관성을 유지하며 최적의 길이로 자동 분할.
  * **벡터 인덱싱**: 정제된 TM을 고성능 다국어 임베딩 모델을 사용하여 벡터로 변환하고, ChromaDB에 인덱싱하여 AI 검색 기반을 마련.

### **클라이언트: QA 워크스테이션 (`aem_qa_station`)**

  * **버전 간 변경사항 분석**: 사용자가 업로드한 페이지 목록에 대해 두 AEM 버전 간의 컴포넌트 추가/수정/삭제 내역을 시각적으로 분석.
  * **AI 번역 추천**: 수정되거나 추가된 텍스트에 대해, ChromaDB에 인덱싱된 TM을 기반으로 가장 유사한 번역 사례를 실시간으로 추천.
  * **동적 버전 관리**: 데이터베이스에 수집된 모든 AEM 버전 정보를 동적으로 조회하여 분석 대상을 선택할 수 있는 UI 제공.
  * **상세 분석 및 리포팅**: 분석 결과를 대시보드에서 필터링 및 정렬하고, 전체 내용을 상세한 Excel 리포트로 다운로드하는 기능 제공.

## **🏗️ 아키텍처 개요**

본 시스템은 데이터 처리 파이프라인과 사용자용 애플리케이션이 MongoDB와 ChromaDB를 통해 데이터를 주고받는 분리된 구조를 가집니다.

```mermaid
graph TD
    subgraph A[외부 소스]
        F1[📄 Excel 파일]
        F2[📝 AEM 페이지 목록]
        F3[📑 PDF 문서]
    end

    subgraph B[백엔드: aem-qa-system]
        P1[데이터 수집/처리 파이프라인<br/>(Jupyter Notebooks)]
        P1 -- 실행 --> C[Collectors]
        P1 -- 실행 --> R[Processors]
        P1 -- 실행 --> I[Indexer]
    end

    subgraph D[데이터베이스 (Docker)]
        DB1[MongoDB<br/>(컴포넌트, TM 저장)]
        DB2[ChromaDB<br/>(벡터 인덱스 저장)]
    end

    subgraph E[클라이언트: aem_qa_station]
        APP[🔍 Streamlit QA 워크스테이션]
    end

    A --> B
    B -- Write --> D
    E -- Read --> D

    style B fill:#e1f5fe,stroke:#333,stroke-width:2px
    style E fill:#e8f5e9,stroke:#333,stroke-width:2px
```

## **🛠️ 기술 스택**

| 구분          | 기술                                                                                                         |
| :------------ | :----------------------------------------------------------------------------------------------------------- |
| **Backend** | Python, Jupyter Notebook, Pandas, PyMuPDF                                                                    |
| **AI/ML** | Sentence-Transformers, Scikit-learn, Spacy, PyTorch                                                          |
| **Database** | MongoDB (pymongo), ChromaDB                                                                                  |
| **Frontend** | Streamlit                                                                                                    |
| **DevOps** | Docker, Docker Compose                                                                                       |

## **📂 디렉토리 구조**

```
.
├── aem-qa-system/                # 백엔드: 데이터 처리 파이프라인
│   ├── data/                     # 1_input, 2_downloaded, 3_processed 데이터
│   ├── notebooks/                # 1, 2, 3단계 실행을 위한 마스터 노트북
│   ├── src/                      # 백엔드 핵심 소스 코드 (collectors, processors 등)
│   ├── docker-compose.yml        # DB 서비스 정의
│   └── requirements.txt          # 백엔드 Python 의존성
└── aem_qa_station/               # 클라이언트: Streamlit 웹 애플리케이션
    ├── app.py                    # Streamlit 애플리케이션 메인 파일
    ├── modules/                  # 클라이언트 핵심 로직 (analyzer, searcher 등)
    └── requirements.txt          # 클라이언트 Python 의존성
```

## **🚀 빠른 시작 (Quick Start)**

### **1. 전제 조건**

  * Git
  * Docker & Docker Compose
  * Python 3.10 이상

### **2. 설치 및 설정**

```bash
# 1. 프로젝트 복제
git clone <repository_url>
cd <repository_name>

# 2. 백엔드 서비스(DB) 실행
docker-compose -f aem-qa-system/docker-compose.yml up -d

# 3. 백엔드/클라이언트 의존성 설치
pip install -r aem-qa-system/requirements.txt
pip install -r aem_qa_station/requirements.txt

# 4. 데이터베이스 컬렉션 및 인덱스 초기화
python aem-qa-system/scripts/setup_collections.py
```

### **3. 시스템 실행**

#### **1단계: 데이터 파이프라인 실행 (백엔드)**

`aem-qa-system/notebooks/` 디렉토리의 마스터 노트북들을 **반드시 순서대로** 실행하여 데이터를 준비합니다.

1.  **`1_Master_Process_Excels.ipynb`**: `data/1_input/source_excels`에 있는 Excel 파일들을 처리하여 `base_tm.csv`와 `glossary.csv`를 생성합니다.
2.  **`2_Master_Create_Package.ipynb`**: AEM 페이지 목록을 기반으로 콘텐츠 스냅샷을 수집하고 `aem_content_package.zip`을 생성합니다.
      * **⚠️ 주의**: 이 노트북은 `collection_pipeline.py`의 버그로 인해 `NameError`가 발생할 수 있습니다. `aem-qa-system/src/collectors/collection_pipeline.py` 파일 83번째 줄의 `manifest_data`를 `collection_results`로 수정해야 합니다.
3.  **`3_Master_Ingest_Data.ipynb`**: 생성된 패키지와 CSV를 MongoDB에 적재하고, 최종 TM을 구축하여 ChromaDB에 인덱싱합니다.
      * **⚠️ 주의**: 이 노트북은 경로 설정 문제로 `ModuleNotFoundError`가 발생할 수 있습니다. 노트북 상단의 `PROJECT_ROOT` 경로가 올바른지 확인하고 커널을 재시작해야 할 수 있습니다.

#### **2단계: QA 워크스테이션 실행 (클라이언트)**

데이터 준비가 완료되면 Streamlit 애플리케이션을 실행합니다.

```bash
streamlit run aem_qa_station/app.py
```

이후 웹 브라우저에 나타나는 `AEM Translation QA Workstation` 화면을 통해 작업을 시작할 수 있습니다.