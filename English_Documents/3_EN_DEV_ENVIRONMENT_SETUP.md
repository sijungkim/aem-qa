### **Document 3/8: Development Environment Setup Guide**

## **🛠️ AEM QA System & Workstation: Development Environment Setup Guide**

This document guides you through the complete process of setting up the development environment for the AEM QA System & Workstation project on your local computer. Following this guide, you will be able to run and test both the backend data pipeline and the client QA workstation.

-----

## 1. Prerequisites

Before setting up the development environment, the following software must be installed:

* **Git**: Required for version control. [Installation Link](https://git-scm.com/downloads)
* **Docker & Docker Compose**: Essential for running MongoDB and ChromaDB databases as containers. **Docker Desktop** installation is recommended. [Installation Link](https://www.docker.com/products/docker-desktop/)
* **Python**: **Version 3.10 or higher** is required. Check your version with the `python --version` command. [Installation Link](https://www.python.org/downloads/)
* **(Optional) Visual Studio Code**: Recommended as a code editor, and it's good to install the Python extension as well.

-----

## 2. Project Cloning and Initial Setup

#### **2.1. Source Code Cloning**

Open a terminal or command prompt and clone the project source code to your desired location.

```bash
# Navigate to the directory where you want to store the project
cd path/to/your/development/folder

# Clone project from Git repository
git clone <repository_url>

# Navigate to project directory
cd aem-qa-system-and-workstation # Example directory name
```

#### **2.2. Database Service Execution**

Run MongoDB and ChromaDB, the core data storage of the project, using Docker.

```bash
# Navigate to the backend directory containing docker-compose.yml
cd aem-qa-system

# Run services in the background using Docker Compose
docker-compose up -d
```

* **Verification**: Check if the services are running normally. Two containers, `aem_qa_mongo_db` and `aem_qa_chromadb_server`, should be displayed in `Up` status.

```bash
docker ps
```

-----

## 3. Python Environment Setup and Dependency Installation

The backend system and client application have separate Python dependencies. It is recommended to set up a virtual environment and install all dependencies by running the following commands from the project root.

#### **3.1. Python Virtual Environment Creation and Activation**

```bash
# 1. Create Python virtual environment (creates venv folder)
python -m venv venv

# 2. Activate virtual environment
# Windows:
# venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

* **Tip**: If `(venv)` appears before the terminal prompt, the virtual environment has been successfully activated.

#### **3.2. Dependency Package Installation**

Install the required libraries using both backend and client `requirements.txt` files.

```bash
# Install backend dependencies
pip install -r aem-qa-system/requirements.txt

# Install client dependencies
pip install -r aem_qa_station/requirements.txt
```

-----

## 4. Database Initialization and Verification

#### **4.1. MongoDB Collection and Index Creation**

Run the script that automatically creates MongoDB collections and performance indexes required for the backend system to store data.

```bash
# Navigate to aem-qa-system directory
cd aem-qa-system

# Run setup_collections.py script
python scripts/setup_collections.py
```

* **Execution**: When the script runs, a menu will appear. Select **`[1] Create Collections`** or **`[0] Execute All`** to proceed with initialization.
* **Result**: Success is indicated by the `✅ MongoDB connection successful` message along with collection creation logs for each language pair.

#### **4.2. Database Connection Verification**

Run the provided test script to finally confirm that you can successfully connect to MongoDB running in Docker in your local development environment and read and write data.

```bash
# Ensure you are in the aem-qa-system directory
# Run test_mongo_connection.py script
python src/utils/test_mongo_connection.py
```

* **Result**: If the following success message is output, all setup is complete:
  ```
  ✅ Server ping successful: MongoDB server is responding.
     - Attempting to insert test data...
     - ✅ Insertion successful! Inserted ID: ...
     - ✅ Test data deletion complete.
     - Connection closed.
  ```

-----

## 5. Starting Development

All setup is now complete. You can start development by running the system in the following two ways:

1. **Run Backend Data Pipeline**:
   * Execute the master notebooks in the `aem-qa-system/notebooks/` directory (`1_Master_*.ipynb`, `2_Master_*.ipynb`, `3_Master_*.ipynb`) in order to collect actual data and populate the database.

2. **Run Client QA Workstation**:
   * If data for analysis is ready in the database, run the QA workstation with the following command:
     ```bash
     # Run from project root directory
     streamlit run aem_qa_station/app.py
     ```
   * You can access and use the application by navigating to `http://localhost:8501` in your web browser.