# src/indexing/chroma_indexer.py

from pymongo import MongoClient
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import torch

from src.config import (
    MONGO_CONNECTION_STRING, DB_NAME, RAG_EMBEDDING_MODEL, CHROMA_DB_PATH
)

class ChromaIndexer:
    """
    MongoDB의 TM 데이터를 읽어 ChromaDB에 벡터 인덱스로 저장합니다.
    """
    def __init__(self):
        # MongoDB 클라이언트 초기화
        self.mongo_client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.mongo_client[DB_NAME]
        
        # ChromaDB 클라이언트 초기화
        self.chroma_client = PersistentClient(path=CHROMA_DB_PATH)
        
        # 임베딩 모델 설정
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.embedding_model = SentenceTransformer(RAG_EMBEDDING_MODEL, device=self.device)
        print(f"✅ DB 연결 및 임베딩 모델({self.device}) 로드 완료.")

    def _fetch_tm_data(self, tm_collection_name: str) -> list:
        """지정된 TM 컬렉션에서 모든 문서를 가져옵니다."""
        print(f"🔄 MongoDB '{tm_collection_name}' 컬렉션에서 데이터 로드 중...")
        collection = self.db[tm_collection_name]
        data = list(collection.find({}))
        print(f"   - ✅ {len(data)}개의 TM 데이터를 로드했습니다.")
        return data

    def create_index(self, lang_suffix: str):
        """
        지정된 언어 쌍의 TM에 대한 벡터 인덱스를 생성합니다.
        기존 인덱스가 있으면 덮어씁니다.
        """
        tm_collection_name = f"translation_memory_{lang_suffix}"
        chroma_collection_name = f"tm_{lang_suffix}"

        # 1. MongoDB에서 데이터 가져오기
        tm_data = self._fetch_tm_data(tm_collection_name)
        if not tm_data:
            print("⚠️ 데이터가 없어 인덱스 생성을 건너뜁니다.")
            return

        # 2. ChromaDB에 저장할 데이터 형식으로 준비
        documents = [item['source_text'] for item in tm_data]
        metadatas = [
            {
                "target_text": item['target_text'],
                "page_path": item['page_path'],
                "component_path": item['component_path']
            } for item in tm_data
        ]
        ids = [str(item['_id']) for item in tm_data]
        
        # 3. 텍스트 임베딩 생성 (벡터 변환)
        print(f"🤖 '{RAG_EMBEDDING_MODEL}' 모델로 텍스트 임베딩 생성 중...")
        embeddings = self.embedding_model.encode(
            documents, 
            show_progress_bar=True,
            batch_size=32
        )
        print("   - ✅ 임베딩 생성 완료.")

        # 4. ChromaDB에 컬렉션 생성 및 데이터 저장
        print(f"💾 ChromaDB '{chroma_collection_name}' 컬렉션에 데이터 저장 중...")
        collection = self.chroma_client.get_or_create_collection(name=chroma_collection_name)
        
        # ChromaDB는 한 번에 많은 양을 넣으면 실패할 수 있으므로, 작은 배치로 나눠서 저장
        batch_size = 1000
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                documents=documents[i:i+batch_size]
            )
        print(f"   - ✅ 총 {len(ids)}개 벡터 저장 완료.")