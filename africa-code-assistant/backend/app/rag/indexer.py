import os, glob
class DocIndex:
    def __init__(self, embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = embedding_model; self.index = None; self.docs = []
    def build(self, directory):
        files = []
        for ext in ("*.md","*.txt","*.py"):
            files += glob.glob(os.path.join(directory, "**", ext), recursive=True)
        self.docs = []
        for f in files:
            try:
                with open(f, encoding="utf-8", errors="ignore") as fh:
                    self.docs.append((os.path.basename(f), fh.read()))
            except Exception:
                pass
        try:
            from sentence_transformers import SentenceTransformer
            import faiss, numpy as np
            m = SentenceTransformer(self.embedding_model)
            emb = m.encode([d[1] for d in self.docs])
            self.index = faiss.IndexFlatL2(emb.shape[1])
            self.index.add(np.array(emb).astype("float32"))
        except Exception:
            self.index = None
    def search(self, query, top_k=5):
        if not self.index or not self.docs: return []
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            m = SentenceTransformer(self.embedding_model)
            q = m.encode([query])
            D, I = self.index.search(np.array(q).astype("float32"), top_k)
            return [{"source": self.docs[i][0], "text": self.docs[i][1][:500]} for i in I[0] if i < len(self.docs)]
        except Exception:
            return []
