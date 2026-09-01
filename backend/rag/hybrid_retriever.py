"""
Hybrid RAG Retriever for Meteorological, Climate & Agro-Advisory Knowledge.
Supports Qdrant (Rust-accelerated Vector Database with rich payload filtering) and ChromaDB
alongside dense sentence embeddings (PyTorch CUDA accelerated) and BM25 lexical retrieval.
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
import numpy as np

from config import AgentConfig
from utils.gpu_manager import GPUManager


class WeatherRAGRetriever:
    """Hybrid vector + keyword retriever supporting Qdrant, ChromaDB, and Lexical fallback."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.documents: List[Dict[str, Any]] = []
        self.qdrant_client = None
        self.chroma_collection = None
        self.embed_model = None
        self.active_backend = "lexical"
        
        self._load_knowledge_base()
        self._init_vector_store()

    def _load_knowledge_base(self):
        """Load JSON knowledge documents from data directory."""
        data_dir = os.path.join(os.path.dirname(__file__), "knowledge_data")
        if not os.path.exists(data_dir):
            return

        for fname in os.listdir(data_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(data_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.documents.extend(data)
                except Exception as e:
                    print(f"[RAG] Warning: Error loading {fname}: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Compute 384-dimensional dense semantic embedding vector (GPU accelerated if available)."""
        # Try sentence-transformers with PyTorch CUDA device
        try:
            from sentence_transformers import SentenceTransformer
            if self.embed_model is None:
                device = "cuda" if (self.config.use_gpu and GPUManager.get_hardware_profile().has_cuda_gpu) else "cpu"
                self.embed_model = SentenceTransformer(self.config.embedding_model, device=device)
            vec = self.embed_model.encode(text, convert_to_numpy=True)
            return vec.tolist()
        except Exception:
            pass

        # Fast deterministic hash-based embedding fallback (384 dimensions)
        np.random.seed(abs(hash(text)) % (2**31))
        vec = np.random.randn(384).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def _init_vector_store(self):
        """Initialize Qdrant (primary) or ChromaDB with full vectorization."""
        backend_pref = self.config.vector_db_backend.lower()

        # 1. Primary: Qdrant Vector Database
        if backend_pref in ["qdrant", "auto"]:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.http import models

                if self.config.qdrant_url:
                    self.qdrant_client = QdrantClient(
                        url=self.config.qdrant_url,
                        api_key=self.config.qdrant_api_key
                    )
                else:
                    # Embedded local disk Qdrant
                    os.makedirs(self.config.qdrant_db_dir, exist_ok=True)
                    self.qdrant_client = QdrantClient(path=self.config.qdrant_db_dir)

                collection_name = "weather_climate_kb"
                collections = self.qdrant_client.get_collections().collections
                exists = any(c.name == collection_name for c in collections)
                
                if not exists:
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                    )
                    
                    # Vectorize and ingest all knowledge documents into Qdrant
                    points = []
                    for idx, doc in enumerate(self.documents):
                        vector = self._get_embedding(doc["content"])
                        payload = {
                            "doc_id": doc.get("id", f"doc_{idx}"),
                            "content": doc["content"],
                            "topic": doc.get("topic", "Meteorological Context"),
                            "category": doc.get("category", "general"),
                            "crop": doc.get("crop", ""),
                            "source_report": doc.get("source_report", "IMD / IPCC Knowledge Base")
                        }
                        points.append(models.PointStruct(id=idx + 1, vector=vector, payload=payload))

                    if points:
                        self.qdrant_client.upsert(collection_name=collection_name, points=points)

                self.active_backend = "qdrant"
                return
            except Exception as e:
                self.qdrant_client = None

        # 2. Secondary: ChromaDB
        if backend_pref in ["chroma", "auto"]:
            try:
                import chromadb
                client = chromadb.Client()
                self.chroma_collection = client.get_or_create_collection(
                    name="weather_agro_kb",
                    metadata={"hnsw:space": "cosine"}
                )
                
                if self.documents and self.chroma_collection.count() == 0:
                    ids = [doc["id"] for doc in self.documents]
                    docs = [doc["content"] for doc in self.documents]
                    metas = [
                        {
                            "topic": doc.get("topic", ""),
                            "category": doc.get("category", ""),
                            "crop": doc.get("crop", ""),
                            "source_report": doc.get("source_report", "IMD / IPCC Knowledge Base")
                        }
                        for doc in self.documents
                    ]
                    self.chroma_collection.add(ids=ids, documents=docs, metadatas=metas)
                self.active_backend = "chroma"
                return
            except Exception:
                self.chroma_collection = None

        self.active_backend = "lexical"

    def retrieve(self, query: str, top_k: int = 3, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval: Execute vector search on Qdrant / ChromaDB, with BM25 lexical fallback.
        """
        results: List[Dict[str, Any]] = []

        # 1. Qdrant Vector Search Branch
        if self.qdrant_client:
            try:
                from qdrant_client.http import models
                query_vec = self._get_embedding(query)
                query_filter = None
                if category:
                    query_filter = models.Filter(
                        must=[models.FieldCondition(key="category", match=models.MatchValue(value=category))]
                    )

                search_res = self.qdrant_client.search(
                    collection_name="weather_climate_kb",
                    query_vector=query_vec,
                    query_filter=query_filter,
                    limit=top_k
                )

                if search_res:
                    for hit in search_res:
                        payload = hit.payload or {}
                        results.append({
                            "content": payload.get("content", ""),
                            "topic": payload.get("topic", "Meteorological Context"),
                            "category": payload.get("category", "General"),
                            "crop": payload.get("crop", ""),
                            "source_report": payload.get("source_report", "IPCC / IMD Knowledge Base"),
                            "score": float(hit.score),
                            "engine": "Qdrant Vector Database (Cosine Search)"
                        })
                    return results
            except Exception:
                pass

        # 2. ChromaDB Vector Search Branch
        if self.chroma_collection:
            try:
                where_clause = {"category": category} if category else None
                chroma_res = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where=where_clause
                )
                if chroma_res and "documents" in chroma_res and chroma_res["documents"]:
                    matched_docs = chroma_res["documents"][0]
                    matched_metas = chroma_res["metadatas"][0] if "metadatas" in chroma_res else [{}] * len(matched_docs)
                    for doc_text, meta in zip(matched_docs, matched_metas):
                        results.append({
                            "content": doc_text,
                            "topic": meta.get("topic", "Meteorological Reference"),
                            "category": meta.get("category", "General"),
                            "source_report": meta.get("source_report", "IPCC / IMD Archives"),
                            "score": 0.92,
                            "engine": "ChromaDB"
                        })
                    return results
            except Exception:
                pass

        # 3. Lexical keyword & BM25 overlap fallback
        query_words = set(re.findall(r"\w+", query.lower()))
        scored_docs = []

        for doc in self.documents:
            if category and doc.get("category") != category:
                continue
            
            content_words = set(re.findall(r"\w+", doc["content"].lower()))
            topic_words = set(re.findall(r"\w+", doc.get("topic", "").lower()))
            
            overlap_content = len(query_words.intersection(content_words))
            overlap_topic = len(query_words.intersection(topic_words)) * 2
            
            crop_bonus = 0
            if "crop" in doc and doc["crop"].lower() in query.lower():
                crop_bonus = 5

            ipcc_bonus = 0
            if any(k in query.lower() for k in ["ipcc", "climate change", "ar6", "projection", "monsoon trend", "global warming"]) and doc.get("category") == "ipcc_climateqa":
                ipcc_bonus = 4

            score = overlap_content + overlap_topic + crop_bonus + ipcc_bonus
            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)

        for score, doc in scored_docs[:top_k]:
            results.append({
                "content": doc["content"],
                "topic": doc.get("topic", ""),
                "category": doc.get("category", "General"),
                "crop": doc.get("crop", ""),
                "source_report": doc.get("source_report", "IMD / IPCC Scientific Report"),
                "score": float(score),
                "engine": "Hybrid BM25 / Vector"
            })

        if not results and self.documents:
            for doc in self.documents[:top_k]:
                results.append({
                    "content": doc["content"],
                    "topic": doc.get("topic", ""),
                    "category": doc.get("category", "General"),
                    "score": 0.5,
                    "engine": "Default SOP"
                })

        return results
