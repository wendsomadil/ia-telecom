# init_index.py
"""
Script d'initialisation de l'index FAISS.
Extrait les textes des PDF (récursivement), les découpe en chunks,
génère les embeddings et crée l'index FAISS.

Usage : python init_index.py
"""

import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from chatbot.extraction import process_pdfs_in_directory, chunk_text
from chatbot.utils import load_text_data
from chatbot.config import (
    FAISS_INDEX_PATH, EMBEDDING_MODEL, EMBEDDING_DIM,
    PDF_DIRECTORY, EXCEL_DIRECTORY
)


def create_faiss_index(embedding_dim: int = EMBEDDING_DIM):
    """Initialise un index FAISS avec une dimension spécifique."""
    return faiss.IndexFlatL2(embedding_dim)


def build_chunks_from_texts(texts: dict, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Découpe chaque document en chunks et retourne une liste structurée.
    Chaque chunk contient le texte et le nom du document source.
    """
    all_chunks = []
    
    for doc_name, text in texts.items():
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc_name,
                "chunk_index": i
            })
    
    return all_chunks


def index_chunks_with_faiss(chunks: list, encoder, index):
    """Génère des embeddings pour les chunks et les indexe dans FAISS."""
    if not chunks:
        print("Aucun chunk à indexer.")
        return index

    texts = [c["text"] for c in chunks]
    
    print(f"Génération des embeddings pour {len(texts)} chunks...")
    embeddings = encoder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    index.add(embeddings)
    return index


if __name__ == "__main__":
    print("=" * 60)
    print("  INITIALISATION DE L'INDEX FAISS")
    print("=" * 60)
    
    # Vérifier le dossier PDF
    if not os.path.exists(PDF_DIRECTORY):
        os.makedirs(PDF_DIRECTORY, exist_ok=True)
        print(f"\n⚠ Le dossier '{PDF_DIRECTORY}' a été créé.")
        print("  Placez vos fichiers PDF dedans, puis relancez ce script.")
        exit(0)
    
    # Compter les PDF
    pdf_count = sum(
        1 for root, _, files in os.walk(PDF_DIRECTORY) 
        for f in files if f.lower().endswith('.pdf')
    )
    print(f"\n📂 {pdf_count} fichier(s) PDF trouvé(s) dans '{PDF_DIRECTORY}'")
    
    if pdf_count == 0:
        print("⚠ Aucun PDF trouvé. Ajoutez vos fichiers et relancez.")
        exit(0)

    # Étape 1 : Extraction des PDF
    print("\n📄 Étape 1/4 : Extraction des textes des PDF...")
    documents_map = process_pdfs_in_directory()

    # Étape 2 : Chargement des textes
    print("\n📚 Étape 2/4 : Chargement des textes extraits...")
    texts = load_text_data()

    if not texts:
        print("❌ Aucun texte trouvé à indexer. Vérifiez vos fichiers.")
        exit(1)

    print(f"  → {len(texts)} document(s) chargé(s)")

    # Étape 3 : Découpage en chunks
    print("\n✂️  Étape 3/4 : Découpage en chunks...")
    chunks = build_chunks_from_texts(texts, chunk_size=500, overlap=50)
    print(f"  → {len(chunks)} chunks créés")

    # Étape 4 : Indexation FAISS
    print(f"\n🧠 Étape 4/4 : Création de l'index FAISS...")
    encoder = SentenceTransformer(EMBEDDING_MODEL)
    faiss_index = create_faiss_index(EMBEDDING_DIM)
    faiss_index = index_chunks_with_faiss(chunks, encoder, faiss_index)

    # Sauvegarde
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(faiss_index, FAISS_INDEX_PATH)
    
    # Sauvegarde des chunks pour la recherche
    chunks_path = FAISS_INDEX_PATH.replace(".bin", "_chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Index FAISS sauvegardé : {FAISS_INDEX_PATH}")
    print(f"✅ Chunks sauvegardés : {chunks_path}")
    print(f"\n🎉 Indexation terminée ! Vous pouvez lancer l'application :")
    print(f"   streamlit run app.py")
