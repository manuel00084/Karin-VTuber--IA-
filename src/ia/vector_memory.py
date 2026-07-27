import os, json, threading, time, hashlib
import numpy as np
from src import PROJECT_ROOT

CHROMA_OK = False
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_OK = True
except ImportError:
    pass

CHROMA_DIR = os.path.join(PROJECT_ROOT, "data", "chroma_db")
FALLBACK_FILE = os.path.join(PROJECT_ROOT, "data", "vector_memory_fallback.json")

_instances = {}
_embed_model = None
_embed_lock = threading.Lock()


def _get_embedder():
    global _embed_model
    if _embed_model is None:
        with _embed_lock:
            if _embed_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception:
                    _embed_model = False
    return _embed_model if _embed_model is not False else None


def _embed(texts):
    model = _get_embedder()
    if model:
        return model.encode(texts, normalize_embeddings=True).tolist()
    return None


class VectorMemory:
    def __init__(self, collection_name="twitch_memories"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._fallback = {}
        self._ready = False
        self._load_fallback()
        self._init_chroma()

    def _init_chroma(self):
        if not CHROMA_OK:
            return
        try:
            self._client = chromadb.PersistentClient(
                path=CHROMA_DIR,
                settings=Settings(anonymized_telemetry=False, allow_reset=False)
            )
            try:
                self._collection = self._client.get_collection(self.collection_name)
            except Exception:
                self._collection = self._client.create_collection(self.collection_name)
            self._ready = True
        except Exception:
            self._ready = False

    def _load_fallback(self):
        try:
            if os.path.exists(FALLBACK_FILE):
                with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
                    self._fallback = json.load(f)
        except Exception:
            self._fallback = {}

    def _save_fallback(self):
        try:
            with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(self._fallback, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _make_id(self, text, user):
        raw = f"{user}:{text.strip().lower()}:{time.time()}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def add(self, text, user="user", role="user", metadata=None):
        if not text or len(text.strip()) < 2:
            return
        text = text.strip()
        doc_id = self._make_id(text, user)
        meta = {"user": user, "role": role, "time": time.time()}
        if metadata:
            meta.update(metadata)

        if self._ready:
            emb = _embed([text])
            if emb:
                try:
                    self._collection.add(
                        ids=[doc_id],
                        embeddings=emb,
                        documents=[text],
                        metadatas=[meta]
                    )
                    return
                except Exception:
                    pass

        user_key = f"{user}_{role}"
        if user_key not in self._fallback:
            self._fallback[user_key] = []
        self._fallback[user_key].append({"text": text, "time": time.time(), "id": doc_id})
        if len(self._fallback[user_key]) > 100:
            self._fallback[user_key] = self._fallback[user_key][-100:]
        self._save_fallback()

    def search(self, query, n_results=5, user=None):
        if not query:
            return []

        if self._ready:
            q_emb = _embed([query])
            if q_emb:
                try:
                    where = {"user": user} if user else None
                    results = self._collection.query(
                        query_embeddings=q_emb,
                        n_results=n_results,
                        where=where
                    )
                    docs = results.get("documents", [[]])[0]
                    metas = results.get("metadatas", [[]])[0]
                    dists = results.get("distances", [[]])[0]
                    out = []
                    for i, doc in enumerate(docs):
                        if doc:
                            out.append({
                                "text": doc,
                                "user": metas[i].get("user", "unknown") if metas and i < len(metas) else "unknown",
                                "role": metas[i].get("role", "user") if metas and i < len(metas) else "user",
                                "score": 1.0 - dists[i] if dists and i < len(dists) else 0.5
                            })
                    return out
                except Exception:
                    pass

        results = []
        for user_key, entries in self._fallback.items():
            if user and user not in user_key:
                continue
            for entry in entries:
                text = entry.get("text", "")
                if query.lower() in text.lower():
                    results.append({
                        "text": text,
                        "user": user_key.split("_")[0] if "_" in user_key else "unknown",
                        "role": user_key.split("_")[1] if "_" in user_key and len(user_key.split("_")) > 1 else "user",
                        "score": 0.5
                    })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]

    def search_relevant(self, query, n_results=3):
        return self.search(query, n_results=n_results)

    def get_recent(self, user=None, limit=20):
        if self._ready:
            try:
                where = {"user": user} if user else None
                results = self._collection.get(where=where, limit=limit)
                docs = results.get("documents", [])
                metas = results.get("metadatas", [])
                out = []
                for i, doc in enumerate(docs):
                    out.append({
                        "text": doc,
                        "user": metas[i].get("user", "unknown") if metas and i < len(metas) else "unknown",
                        "role": metas[i].get("role", "user") if metas and i < len(metas) else "user"
                    })
                return out
            except Exception:
                pass
        return []

    def get_context_for_prompt(self, query, user=None, max_items=5):
        results = self.search(query, n_results=max_items, user=user)
        if not results:
            return ""
        lines = []
        for r in results:
            role_label = "Usuario" if r["role"] == "user" else "Karin"
            lines.append(f"[{role_label}]: {r['text']}")
        return "\n".join(lines)

    def count(self):
        if self._ready:
            try:
                return self._collection.count()
            except Exception:
                pass
        total = sum(len(v) for v in self._fallback.values())
        return total

    def clear(self):
        self._fallback = {}
        self._save_fallback()
        if self._ready:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.create_collection(self.collection_name)
            except Exception:
                pass

    @property
    def is_ready(self):
        return self._ready or (not CHROMA_OK and bool(self._fallback))


_default_memory = None

def get_vector_memory():
    global _default_memory
    if _default_memory is None:
        _default_memory = VectorMemory()
    return _default_memory

def search_memory(query, n_results=5, user=None):
    return get_vector_memory().search(query, n_results=n_results, user=user)

def add_to_memory(text, user="user", role="user"):
    get_vector_memory().add(text, user=user, role=role)

def get_memory_context(query, user=None):
    return get_vector_memory().get_context_for_prompt(query, user=user)

def clear_vector_memory():
    get_vector_memory().clear()

def memory_stats():
    mem = get_vector_memory()
    return {"count": mem.count(), "mode": "chromadb" if mem.is_ready and CHROMA_OK else "fallback"}
