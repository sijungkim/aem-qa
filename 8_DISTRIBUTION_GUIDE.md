네, 알겠습니다.

문서 시리즈의 마지막, 여덟 번째 문서인 \*\*'배포 가이드'\*\*를 작성하여 전달합니다. 이 문서는 개발이 완료된 `AEM QA Station` 애플리케이션을 실제 서버에 배포하여 여러 사용자가 안정적으로 접속하고 사용할 수 있도록 하는 기술적인 절차를 안내합니다.

-----

### **문서 8/8: 배포 가이드**

## **🚀 AEM QA Station: 배포 가이드**

이 문서는 `AEM QA Station` Streamlit 애플리케이션을 로컬 개발 환경에서 벗어나 실제 운영 서버(Production/Staging)에 배포하는 방법을 안내합니다. 이 가이드를 따르면 애플리케이션을 안정적인 서비스로 실행하고, 여러 사용자가 웹 브라우저를 통해 접속할 수 있도록 설정할 수 있습니다.

-----

### \#\# 1. 배포 아키텍처

운영 환경에서는 안정성과 보안을 위해 **Nginx 웹 서버**를 \*\*리버스 프록시(Reverse Proxy)\*\*로 사용하는 표준 아키텍처를 권장합니다.

```mermaid
graph TD
    U[사용자 (웹 브라우저)] -- HTTPS (port 443) --> N[Nginx 웹 서버];
    N -- HTTP (port 8501) --> S[Streamlit 애플리케이션<br/>(systemd 서비스로 실행)];
    S -- DB Connection --> D[데이터베이스<br/>(MongoDB & ChromaDB)];

    subgraph "운영 서버 (예: Ubuntu 22.04)"
        N
        S
    end
```

  * **사용자**: 웹 브라우저를 통해 표준 HTTPS 포트(443)로 서버에 접속합니다.
  * **Nginx**: 사용자의 모든 요청을 가장 먼저 받습니다. HTTPS 트래픽을 처리(SSL/TLS 종료)하고, 요청을 내부에서 실행 중인 Streamlit 애플리케이션(일반적으로 8501 포트)으로 전달합니다.
  * **Streamlit 애플리케이션**: `systemd` 서비스를 통해 백그라운드에서 항상 실행되며, Nginx로부터 전달받은 요청을 처리하고 데이터베이스와 통신합니다.

-----

### \#\# 2. 사전 준비

배포를 진행할 서버(예: Ubuntu 22.04 LTS)에 다음 소프트웨어가 설치되어 있어야 합니다.

  * **Python 3.10 이상** 및 `pip`, `venv`
  * **Nginx**: 웹 서버 및 리버스 프록시
  * **Git**: 소스 코드 복제
  * **Docker & Docker Compose**: 데이터베이스 서비스를 실행하기 위해 필요. (백엔드 시스템과 동일한 서버에 배포하는 경우)

-----

### \#\# 3. 배포 절차

#### **ขั้นตอนที่ 1: 소스 코드 및 데이터베이스 준비**

1.  **소스 코드 복제**: 서버에 `aem_qa_station` 코드를 복제하거나 업로드합니다.
    ```bash
    git clone <repository_url>
    cd aem_qa_station
    ```
2.  **데이터베이스 연결 확인**:
      * 배포 서버에서 `aem-qa-system`의 Docker Compose로 실행 중인 데이터베이스 컨테이너에 접근할 수 있는지 확인합니다.
      * 만약 DB가 다른 서버에 있다면, 방화벽 규칙을 확인하고 `aem_qa_station/config.py`의 `MONGO_CONNECTION_STRING`과 `CHROMA_DB_PATH`를 올바른 주소로 수정해야 합니다.

#### **ขั้นตอนที่ 2: 애플리케이션 환경 설정**

1.  **Python 가상환경 생성 및 의존성 설치**:

    ```bash
    # aem_qa_station 디렉토리 내에서 실행
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

2.  **(권장) 설정 파일 외부화**:
    운영 환경에서는 민감한 정보(DB 접속 주소 등)를 코드에 직접 넣는 대신, 환경 변수를 사용하도록 `config.py`와 `connections.py`를 수정하는 것이 안전합니다.

    **예시: `connections.py` 수정**

    ```python
    # 기존
    # from config import MONGO_CONNECTION_STRING

    # 수정 후
    import os
    MONGO_CONNECTION_STRING = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    ```

#### **ขั้นตอนที่ 3: `systemd`를 이용한 서비스 등록**

`systemd`를 사용하면 Streamlit 앱이 서버 부팅 시 자동으로 시작되고, 예기치 않게 종료될 경우 자동으로 재시작되어 서비스 안정성이 크게 향상됩니다.

1.  **`systemd` 서비스 파일 생성**:

    ```bash
    sudo nano /etc/systemd/system/aem_qa_station.service
    ```

2.  **서비스 파일 내용 작성**: 아래 내용을 붙여넣고, `User`, `WorkingDirectory`, `ExecStart` 경로를 실제 환경에 맞게 수정합니다.

    ```ini
    [Unit]
    Description=AEM QA Station Streamlit Service
    After=network.target

    [Service]
    User=ubuntu  # 실제 서버 사용자 계정으로 변경
    Group=www-data
    WorkingDirectory=/home/ubuntu/aem_qa_station # 프로젝트 경로로 변경
    ExecStart=/home/ubuntu/aem_qa_station/venv/bin/streamlit run app.py --server.port 8501 --server.headless true

    # 환경 변수를 사용하는 경우 여기에 추가
    # Environment="MONGO_URI=mongodb://db_user:db_pass@remote_db_host:27017/"

    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

3.  **서비스 활성화 및 시작**:

    ```bash
    # systemd 데몬 리로드
    sudo systemctl daemon-reload

    # 서비스 시작
    sudo systemctl start aem_qa_station

    # 서버 부팅 시 자동 시작 활성화
    sudo systemctl enable aem_qa_station

    # 서비스 상태 확인
    sudo systemctl status aem_qa_station
    ```

      * `Active: active (running)` 메시지가 표시되면 성공입니다.

#### **ขั้นตอนที่ 4: Nginx 리버스 프록시 설정**

1.  **Nginx 설정 파일 생성**:

    ```bash
    sudo nano /etc/nginx/sites-available/aem_qa_station
    ```

2.  **Nginx 설정 파일 내용 작성**: `server_name`을 실제 사용할 도메인이나 서버 IP로 변경합니다.

    ```nginx
    server {
        listen 80;
        server_name your_domain.com; # 예: qa.mycompany.com 또는 서버 IP 주소

        location / {
            proxy_pass http://localhost:8501; # systemd에서 실행 중인 Streamlit 앱 주소
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

3.  **설정 활성화 및 Nginx 재시작**:

    ```bash
    # 생성한 설정을 sites-enabled에 링크하여 활성화
    sudo ln -s /etc/nginx/sites-available/aem_qa_station /etc/nginx/sites-enabled/

    # Nginx 설정 문법 오류 검사
    sudo nginx -t

    # Nginx 재시작
    sudo systemctl restart nginx
    ```

4.  **(선택, 강력 권장) HTTPS 설정**: Certbot을 사용하면 무료로 SSL 인증서를 발급받고 HTTPS를 쉽게 설정할 수 있습니다.

    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d your_domain.com
    ```

이제 웹 브라우저에서 설정한 도메인(`http://your_domain.com` 또는 HTTPS 설정 후 `https://your_domain.com`)으로 접속하면 AEM QA Station을 사용할 수 있습니다.

-----

### \#\# 4. 유지보수 및 업데이트

  * **애플리케이션 업데이트**:
    1.  `aem_qa_station` 디렉토리에서 `git pull`로 최신 코드를 받습니다.
    2.  `pip install -r requirements.txt`로 변경된 의존성을 설치합니다.
    3.  `sudo systemctl restart aem_qa_station` 명령어로 서비스를 재시작하여 변경사항을 적용합니다.
  * **데이터 업데이트**: 백엔드 파이프라인(`aem-qa-system`)의 노트북을 재실행하여 데이터베이스의 내용을 최신으로 업데이트하면, QA 워크스테이션에 자동으로 반영됩니다.