

### **AEM QA System & Workstation: Integrated Technical Documentation Guide**

This document serves as the top-level guide for the entire technical documentation set of the AEM QA System & Workstation project. By specifying the core content and main readers of each document, it aims to help all project participants quickly find information relevant to their roles.

-----

## 🎯 Role-Based Recommended Documentation Guide

Based on your role in the project, refer to the guide below to quickly understand the system by reading the documents.

| Role | Recommended Documents (Priority Order) | Description |
|------|----------------------------------------|-------------|
| **New Developer** | 1. README<br/>2. Development Environment Setup Guide<br/>3. Integrated Architecture Guide | Get all the information needed to quickly adapt to the project and run code locally. |
| **System Architect** | 2. Integrated Architecture Guide<br/>5. Data Model & Schema<br/>4. Backend Pipeline Workflow | Understand the overall system structure, data flow, and design principles to make technical decisions. |
| **Backend Developer** | 4. Backend Pipeline Workflow<br/>6. API & Module Reference<br/>5. Data Model & Schema | Deeply understand data processing logic and develop specific modules or new features. |
| **Client Developer** | 7. User Manual<br/>6. API & Module Reference<br/>5. Data Model & Schema | Understand the application's user experience and improve the Streamlit UI or modify logic in `analyzer` and `searcher` modules. |
| **QA Specialist / End User** | 7. User Manual<br/>1. README | Understand all features of the AEM QA Station application and utilize them for actual translation quality review work. |
| **DevOps Engineer** | 8. Deployment Guide<br/>2. Integrated Architecture Guide<br/>3. Development Environment Setup Guide | Deploy the Streamlit application to production servers and provide stable service using Nginx and systemd. |

-----

## 📚 Complete Document List & Summary

#### **1. Project README**

* **Summary**: The **project gateway** that provides project goals, core features, technology stack, directory structure, and Quick Start methods.
* **Main Readers**: All participants, especially **new developers**.
* **When to read this document**:
    * When first joining the project and wanting to understand the overall overview.
    * When wanting to quickly install and run the system in a local environment.

#### **2. Integrated Architecture Guide**

* **Summary**: The **top-level design diagram** explaining the components, hierarchical structure, data flow, and design principles of backend and client systems.
* **Main Readers**: **System Architects**, all **developers**.
* **When to read this document**:
    * When wanting to understand the overall operation of the system.
    * When technical decisions are needed, such as adding new features or changing existing structures.

#### **3. Development Environment Setup Guide**

* **Summary**: The **A to Z procedure** for building a local development environment, from Docker and Python virtual environment setup to database initialization and connection verification.
* **Main Readers**: All **developers**.
* **When to read this document**:
    * When starting project development on a new computer.
    * When problems occur with local environment setup and you want to recheck the procedures.

#### **4. Backend Pipeline Workflow**

* **Summary**: A **technically in-depth analysis document** of the 4 stages (Legacy Asset Processing → AEM Content Collection → Data Loading → TM Cleaning/Segmentation/Indexing) from data collection to final processing into a form suitable for AI search.
* **Main Readers**: **Backend Developers**, **System Architects**.
* **When to read this document**:
    * When needing to understand or modify data processing logic.
    * When debugging issues occurring at specific stages of the pipeline.

#### **5. Data Model & Schema Definition**

* **Summary**: A **data dictionary** that details the structure (collections, fields, indexes) of data stored in MongoDB and ChromaDB.
* **Main Readers**: **Backend and Client Developers**.
* **When to read this document**:
    * When writing queries to the database.
    * When wanting to check the meaning or data type of specific fields.

#### **6. API & Module Reference**

* **Summary**: A **technical reference for developers** describing the roles, parameters, and return values of core Python classes and functions in backend and client.
* **Main Readers**: All **developers**.
* **When to read this document**:
    * When wanting to find which functions to use to implement specific features.
    * When modifying code and wanting to check the exact usage of functions or classes.

#### **7. AEM QA Station - User Manual**

* **Summary**: A **step-by-step application usage guide for non-developer users** such as QA specialists and translators. Guides through the entire process from CSV upload to checking AI translation recommendations and downloading reports.
* **Main Readers**: **QA Specialists**, **Content Managers**, **Project Managers**.
* **When to read this document**:
    * When first using AEM QA Station and needing to learn the features.
    * When wanting to recheck the usage of specific features (e.g., Excel report generation).

#### **8. Deployment Guide**

* **Summary**: A **technical procedure** for deploying and serving the completed `AEM QA Station` to production servers using Nginx and `systemd`.
* **Main Readers**: **DevOps Engineers**, **Server Administrators**, **Senior Developers**.
* **When to read this document**:
    * When needing to deploy an application that has finished local development to a server for actual user access.
    * When updates or restarts of operational services are needed.