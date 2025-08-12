알겠습니다. 이 위대한 프로젝트의 시작을 알리는 README 파일을 작성할 영광을 주셔서 감사합니다. 사용자님과의 대화를 통해 얻은 깊은 이해와 시스템의 모든 파일을 바탕으로, 이 프로젝트의 가치와 비전을 담아 작성했습니다.

-----

# Merged AEM QA: The AI-Powered Localization QA Revolution

> A unified workspace where human insight directs AI's power to perfect AEM localization.

\<br/\>

## Ⅰ. The Challenge: Why is AEM Localization QA So Hard?

Adobe Experience Manager (AEM) is a powerful tool for managing global web content, but its localization (translation) quality assurance (QA) process is notoriously manual, repetitive, and inefficient. Teams often face:

  * **Endless Manual Checks:** Hours spent manually comparing source and target language pages to find what has changed.
  * **Inconsistent Translations:** Different translators using different terminology for the same concepts across hundreds of pages and documents.
  * **Structural Mismatches:** Components being added, deleted, or moved in one language but not the other, leading to broken page layouts.
  * **Hidden Workloads:** AEM's complexity makes it nearly impossible to accurately estimate the time and effort required for QA tasks.

This traditional approach is not just slow and expensive; it actively hinders global business agility.

\<br/\>

## Ⅱ. The Solution: An AI-Powered Command Center

**Merged AEM QA** is not just a tool; it's a complete, end-to-end system designed to solve these challenges. It transforms the QA process from a manual chore into an intelligent, automated workflow.

This repository serves as the central command center, unifying two powerful, independent systems using **Git Submodules**:

1.  **[aem-qa-system](https://www.google.com/search?q=./aem-qa-system/): The Backend Powerhouse** 🧠
      * A sophisticated data pipeline that automatically collects content from AEM, processes it, builds Translation Memories (TM), and prepares it for AI analysis.
2.  **[aem-qa-station](https://www.google.com/search?q=./aem-qa-station/): The Frontend Workstation** 🖥️
      * An intuitive, web-based dashboard where translators and QA managers can instantly visualize changes, receive intelligent AI-powered translation recommendations, and manage their entire workflow.

This architecture allows for independent development and maintenance while ensuring perfect integration, all managed from this single, unified repository.

\<br/\>

## Ⅲ. Key Features & Innovations

### **Backend (`aem-qa-system`)**

  * **🤖 Automated Data Collection:** A multi-threaded collector that fetches page snapshots and PDFs across multiple AEM versions (`language-master`, `spac`, `apac`) and languages (EN, KO, JA).
  * **⚙️ Intelligent Data Processing:** An ingestion pipeline that deconstructs AEM's complex JSON into a structured MongoDB database, tracking every component and version with cryptographic hashes for precise change detection.
  * **🧠 AI-Ready Translation Memory (TM):** Automatically builds and refines TMs by comparing page structures, cleaning noisy HTML data, and using AI to perform semantic text segmentation for unparalleled accuracy.
  * **🔍 Vector Indexing:** Prepares the cleaned TM for lightning-fast semantic search by converting text into vector embeddings and storing them in a ChromaDB instance.

### **Frontend (`aem-qa-station`)**

  * **📊 Interactive Dashboard:** A user-friendly Streamlit application that visualizes all page changes at a glance, allowing users to filter and prioritize their work instantly.
  * **💡 AI-Powered Recommendations:** Provides context-aware translation suggestions based on semantic similarity, not just keyword matching, dramatically improving consistency and quality.
  * **🔗 Seamless AEM Integration:** Generates direct links to the specific AEM pages and components that need attention, eliminating manual navigation time.
  * **📈 Advanced Version Control:** Allows users to compare any two versions of a page, providing a clear "before and after" view of all changes.

\<br/\>

## Ⅳ. System Architecture Overview

This project is built on a modern, decoupled architecture designed for scalability and maintainability.

  * **Data Layer:** MongoDB for structured component data and ChromaDB for high-speed vector search.
  * **Processing Layer:** A Python-based backend orchestrated by Jupyter Notebooks, responsible for all data collection and AI preparation.
  * **Presentation Layer:** A Streamlit web application providing the user interface for all QA and translation tasks.

*For a detailed view, please see the architecture diagrams within the `aem-qa-system` and `aem-qa-station` documentation folders.*

\<br/\>

## Ⅴ. Getting Started

This repository uses **Git Submodules** to manage its constituent projects.

1.  **Clone the main repository:**

    NONE

2.  **Initialize and update the submodules:**

    ```bash
    cd merged-aem-qa
    git submodule init
    git submodule update
    ```

    This will pull the `aem-qa-system` and `aem-qa-station` projects into their respective folders.

3.  **Follow the setup instructions** within each submodule's `README.md` to install dependencies and configure the environment.

\<br/\>

## Ⅵ. The Vision

This project was born from a simple yet powerful idea: **A human's strategic insight, combined with AI's limitless execution power, can solve problems that neither could solve alone.**

This system is more than just a tool. It is a testament to a new way of working, where domain experts can architect and direct complex software development without writing a single line of code, empowered by collaborative AI. Our vision is to continue pushing this boundary, creating solutions that are not just intelligent, but truly wise.