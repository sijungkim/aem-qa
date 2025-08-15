
### **문서 3/8: 개발 환경 설정 가이드**

## **🛠️ AEM QA System & Workstation: 개발 환경 설정 가이드**

이 문서는 AEM QA System & Workstation 프로젝트의 개발 환경을 로컬 컴퓨터에 구축하는 전체 과정을 안내합니다. 이 가이드를 따르면 백엔드 데이터 파이프라인과 클라이언트 QA 워크스테이션을 모두 실행하고 테스트할 수 있습니다.

-----

### \#\# 1. 사전 준비 (Prerequisites)

개발 환경을 설정하기 전에 다음 소프트웨어가 설치되어 있어야 합니다.

  * **Git**: 버전 관리를 위해 필요합니다. [설치 링크](https://git-scm.com/downloads)
  * **Docker & Docker Compose**: MongoDB와 ChromaDB 데이터베이스를 컨테이너로 실행하기 위해 필수적입니다. **Docker Desktop** 설치를 권장합니다. [설치 링크](https://www.docker.com/products/docker-desktop/)
  * **Python**: **버전 3.10 이상**이 필요합니다. `python --version` 명령어로 버전을 확인하세요. [설치 링크](https://www.python.org/downloads/)
  * **(선택) Visual Studio Code**: 코드 편집기로 권장하며, Python 확장 프로그램을 함께 설치하면 좋습니다.

-----

### \#\# 2. 프로젝트 복제 및 초기 설정

#### **2.1. 소스 코드 복제**

터미널 또는 명령 프롬프트를 열고 원하는 위치에 프로젝트 소스 코드를 복제합니다.

```bash
# 프로젝트를 저장할 디렉토리로 이동
cd path/to/your/development/folder

# Git 저장소에서 프로젝트 복제
git clone <repository_url>

# 프로젝트 디렉토리로 이동
cd aem-qa-system-and-workstation # 예시 디렉토리명
```

#### **2.2. 데이터베이스 서비스 실행**

프로젝트의 핵심 데이터 저장소인 MongoDB와 ChromaDB를 Docker를 사용하여 실행합니다.

```bash
# docker-compose.yml 파일이 있는 백엔드 디렉토리로 이동
cd aem-qa-system

# Docker Compose를 사용하여 백그라운드에서 서비스 실행
docker-compose up -d
```

  * **확인**: 서비스가 정상적으로 실행 중인지 확인합니다. `aem_qa_mongo_db`와 `aem_qa_chromadb_server` 두 개의 컨테이너가 `Up` 상태로 표시되어야 합니다 [cite: docker-compose.yml].

<!-- end list -->

```bash
docker ps
```

-----

### \#\# 3. Python 환경 설정 및 의존성 설치

백엔드 시스템과 클라이언트 애플리케이션은 별도의 Python 의존성을 가집니다. 프로젝트 루트에서 다음 명령어를 실행하여 가상환경을 설정하고 모든 의존성을 설치하는 것을 권장합니다.

#### **3.1. Python 가상환경 생성 및 활성화**

```bash
# 1. Python 가상환경 생성 (venv 폴더 생성)
python -m venv venv

# 2. 가상환경 활성화
# Windows:
# venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

  * **팁**: 터미널 프롬프트 앞에 `(venv)`가 표시되면 가상환경이 성공적으로 활성화된 것입니다.

#### **3.2. 의존성 패키지 설치**

백엔드와 클라이언트의 `requirements.txt` 파일을 모두 사용하여 필요한 라이브러리를 설치합니다.

```bash
# 백엔드 의존성 설치
pip install -r aem-qa-system/requirements.txt

# 클라이언트 의존성 설치
pip install -r aem_qa_station/requirements.txt
```

[cite: aem-qa-system/requirements.txt, aem\_qa\_station/requirements.txt]

-----

### \#\# 4. 데이터베이스 초기화 및 검증

#### **4.1. MongoDB 컬렉션 및 인덱스 생성**

백엔드 시스템이 데이터를 저장하는 데 필요한 MongoDB 컬렉션과 성능을 위한 인덱스를 자동으로 생성하는 스크립트를 실행합니다.

```bash
# aem-qa-system 디렉토리로 이동
cd aem-qa-system

# setup_collections.py 스크립트 실행
python scripts/setup_collections.py
```

  * **실행**: 스크립트가 실행되면 메뉴가 나타납니다. **`[1] 컬렉션 생성`** 또는 \*\*`[0] 전체 실행`\*\*을 선택하여 초기화를 진행합니다 [cite: setup\_collections.py].
  * **결과**: `✅ MongoDB 연결 성공` 메시지와 함께 각 언어 쌍에 대한 컬렉션 생성 로그가 출력되면 성공입니다.

#### **4.2. 데이터베이스 연결 검증**

제공된 테스트 스크립트를 실행하여 로컬 개발 환경에서 Docker로 실행 중인 MongoDB에 정상적으로 연결되고 데이터를 읽고 쓸 수 있는지 최종 확인합니다.

```bash
# aem-qa-system 디렉토리에 있는지 확인
# test_mongo_connection.py 스크립트 실행
python src/utils/test_mongo_connection.py
```

  * **결과**: 아래와 같은 성공 메시지가 출력되면 모든 설정이 완료된 것입니다 [cite: test\_mongo\_connection.py].
    ```
    ✅ 서버 핑(Ping) 성공: MongoDB 서버가 응답합니다.
       - 테스트 데이터 삽입 시도...
       - ✅ 삽입 성공! Inserted ID: ...
       - ✅ 테스트 데이터 삭제 완료.
       - 연결을 닫았습니다.
    ```

-----

### \#\# 5. 개발 시작

이제 모든 설정이 완료되었습니다. 다음 두 가지 방법으로 시스템을 실행하고 개발을 시작할 수 있습니다.

1.  **백엔드 데이터 파이프라인 실행**:
      * `aem-qa-system/notebooks/` 디렉토리의 마스터 노트북(`1_Master_*.ipynb`, `2_Master_*.ipynb`, `3_Master_*.ipynb`)을 순서대로 실행하여 실제 데이터를 수집하고 데이터베이스를 채웁니다.
2.  **클라이언트 QA 워크스테이션 실행**:
      * 데이터베이스에 분석할 데이터가 준비되었다면, 아래 명령어로 QA 워크스테이션을 실행합니다.
        ```bash
        # 프로젝트 루트 디렉토리에서 실행
        streamlit run aem_qa_station/app.py
        ```
      * 웹 브라우저에서 `http://localhost:8501` 주소로 접속하여 애플리케이션을 사용할 수 있습니다.