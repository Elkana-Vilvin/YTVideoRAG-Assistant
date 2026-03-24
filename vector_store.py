import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


class VectorStore:

    def __init__(self):

        self.index = None

        self.texts = []

    def build(self, chunks):

        embeddings = embedding_model.encode(chunks)

        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)

        self.index.add(np.array(embeddings))

        self.texts = chunks

    def search(self, query, k=5):

        q_embedding = embedding_model.encode([query])

        D, I = self.index.search(np.array(q_embedding), k)

        results = []

        for i in I[0]:
            results.append(self.texts[i])

        return results
        