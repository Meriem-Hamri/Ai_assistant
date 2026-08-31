# from sentence_transformers import SentenceTransformer

# print("Chargement du modèle...")

# model = SentenceTransformer("BAAI/bge-m3")

# print("Modèle chargé.")

# embedding = model.encode("Bonjour tout le monde.")

# print(type(embedding))
# print(embedding.shape)

from app.embeddings.models.bge_m3 import BGEM3Embedding

model = BGEM3Embedding()

print(model)

embedding = model.embed("Bonjour tout le monde.")

print(type(embedding))
print(embedding.shape)

embeddings = model.embed_batch([
    "Bonjour",
    "Bonsoir",
    "Le chat dort."
])

print(embeddings.shape)