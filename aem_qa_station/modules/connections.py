# aem_qa_station/modules/connections.py

import streamlit as st
from pymongo import MongoClient
from chromadb import PersistentClient

# config.py 대신 앱 설정을 여기서 직접 관리하거나, 별도 config 파일을 둘 수 있습니다.
MONGO_CONNECTION_STRING = "mongodb://localhost:27017/"
DB_NAME = "aem_qa_system"
CHROMA_DB_PATH = "../aem_qa_system/rag_database/chroma_db_store/"

@st.cache_resource
def get_mongo_client():
    """MongoDB 클라이언트를 반환합니다. Streamlit 캐시에 저장하여 재사용합니다."""
    print("Attempting to connect to MongoDB...")
    client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
    # 서버에 대한 연결을 테스트합니다.
    client.admin.command('ping')
    print("MongoDB connection successful.")
    return client

@st.cache_resource
def get_chroma_client():
    """ChromaDB 클라이언트를 반환합니다. Streamlit 캐시에 저장하여 재사용합니다."""
    print("Attempting to connect to ChromaDB...")
    client = PersistentClient(path=CHROMA_DB_PATH)
    print("ChromaDB connection successful.")
    return client

def get_db():
    """MongoDB 데이터베이스 객체를 반환합니다."""
    mongo_client = get_mongo_client()
    return mongo_client[DB_NAME]