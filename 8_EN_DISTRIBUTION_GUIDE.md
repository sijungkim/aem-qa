### **Document 8/8: Deployment Guide**

## **🚀 AEM QA Station: Deployment Guide**

This document guides you through deploying the `AEM QA Station` Streamlit application from a local development environment to an actual production server (Production/Staging). Following this guide, you can run the application as a stable service and configure it so multiple users can access it through web browsers.

-----

## 1. Deployment Architecture

For production environments, we recommend a standard architecture using **Nginx web server** as a **reverse proxy** for stability and security.

```mermaid
graph TD
    U["Users (Web Browser)"] --> N["Nginx Web Server"]
    N --> S["Streamlit Application<br/>(Running as systemd service)"]
    S --> D["Database<br/>(MongoDB & ChromaDB)"]

    subgraph Server["Production Server (e.g., Ubuntu 22.04)"]
        N
        S
    end
    
    U -.->|"HTTPS (port 443)"| N
    N -.->|"HTTP (port 8501)"| S
    S -.->|"DB Connection"| D
```

* **Users**: Access the server through web browsers via the standard HTTPS port (443).
* **Nginx**: Receives all user requests first. Handles HTTPS traffic (SSL/TLS termination) and forwards requests to the internally running Streamlit application (typically port 8501).
* **Streamlit Application**: Always runs in the background through `systemd` service, processes requests forwarded from Nginx, and communicates with the database.

-----

## 2. Prerequisites

The following software must be installed on the deployment server (e.g., Ubuntu 22.04 LTS):

* **Python 3.10 or higher** and `pip`, `venv`
* **Nginx**: Web server and reverse proxy
* **Git**: Source code cloning
* **Docker & Docker Compose**: Required to run database services (if deploying on the same server as the backend system)

-----

## 3. Deployment Procedure

#### **Step 1: Source Code and Database Preparation**

1. **Clone Source Code**: Clone or upload the `aem_qa_station` code to the server.
   ```bash
   git clone <repository_url>
   cd aem_qa_station
   ```

2. **Verify Database Connection**:
   * Confirm that the deployment server can access database containers running via Docker Compose from `aem-qa-system`.
   * If the DB is on a different server, check firewall rules and modify `MONGO_CONNECTION_STRING` and `CHROMA_DB_PATH` in `aem_qa_station/config.py` to the correct addresses.

#### **Step 2: Application Environment Setup**

1. **Create Python Virtual Environment and Install Dependencies**:

   ```bash
   # Execute within aem_qa_station directory
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **(Recommended) Externalize Configuration Files**:
   For production environments, it's safer to modify `config.py` and `connections.py` to use environment variables instead of putting sensitive information (DB connection addresses, etc.) directly in the code.

   **Example: Modifying `connections.py`**

   ```python
   # Before
   # from config import MONGO_CONNECTION_STRING

   # After
   import os
   MONGO_CONNECTION_STRING = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
   ```

#### **Step 3: Service Registration Using `systemd`**

Using `systemd` significantly improves service stability by automatically starting the Streamlit app when the server boots and automatically restarting it if it terminates unexpectedly.

1. **Create `systemd` Service File**:

   ```bash
   sudo nano /etc/systemd/system/aem_qa_station.service
   ```

2. **Write Service File Content**: Paste the content below and modify the `User`, `WorkingDirectory`, and `ExecStart` paths to match your actual environment.

   ```ini
   [Unit]
   Description=AEM QA Station Streamlit Service
   After=network.target

   [Service]
   User=ubuntu  # Change to actual server user account
   Group=www-data
   WorkingDirectory=/home/ubuntu/aem_qa_station # Change to project path
   ExecStart=/home/ubuntu/aem_qa_station/venv/bin/streamlit run app.py --server.port 8501 --server.headless true

   # Add environment variables here if using them
   # Environment="MONGO_URI=mongodb://db_user:db_pass@remote_db_host:27017/"

   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and Start Service**:

   ```bash
   # Reload systemd daemon
   sudo systemctl daemon-reload

   # Start service
   sudo systemctl start aem_qa_station

   # Enable automatic start on server boot
   sudo systemctl enable aem_qa_station

   # Check service status
   sudo systemctl status aem_qa_station
   ```

   * Success is indicated by the `Active: active (running)` message.

#### **Step 4: Nginx Reverse Proxy Configuration**

1. **Create Nginx Configuration File**:

   ```bash
   sudo nano /etc/nginx/sites-available/aem_qa_station
   ```

2. **Write Nginx Configuration File Content**: Change `server_name` to the actual domain or server IP you will use.

   ```nginx
   server {
       listen 80;
       server_name your_domain.com; # e.g., qa.mycompany.com or server IP address

       location / {
           proxy_pass http://localhost:8501; # Streamlit app address running in systemd
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

3. **Activate Configuration and Restart Nginx**:

   ```bash
   # Link created configuration to sites-enabled to activate
   sudo ln -s /etc/nginx/sites-available/aem_qa_station /etc/nginx/sites-enabled/

   # Check Nginx configuration syntax errors
   sudo nginx -t

   # Restart Nginx
   sudo systemctl restart nginx
   ```

4. **(Optional, Strongly Recommended) HTTPS Setup**: Using Certbot, you can easily obtain free SSL certificates and set up HTTPS.

   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your_domain.com
   ```

Now you can access AEM QA Station by navigating to the configured domain (`http://your_domain.com` or `https://your_domain.com` after HTTPS setup) in a web browser.

-----

## 4. Maintenance and Updates

* **Application Updates**:
  1. Get the latest code with `git pull` in the `aem_qa_station` directory.
  2. Install changed dependencies with `pip install -r requirements.txt`.
  3. Apply changes by restarting the service with `sudo systemctl restart aem_qa_station`.

* **Data Updates**: When you re-run the backend pipeline (`aem-qa-system`) notebooks to update the database content to the latest version, it will automatically be reflected in the QA workstation.