# chatbot/rag_pipeline.py
"""
Pipeline RAG (Retrieval-Augmented Generation).
- Recherche sémantique avec FAISS
- Génération de réponses avec Gemini 2.5 Flash
"""

import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from google import genai
from chatbot.config import (
    API_KEY, GEMINI_MODEL, FAISS_INDEX_PATH,
    DOCUMENTS_MAP_PATH, EMBEDDING_MODEL, TOP_N_RESULTS, MAX_RESPONSE_WORDS
)

# --- Chargement des modèles (lazy loading) ---
_encoder = None
_faiss_index = None
_chunks_data = None
_gemini_client = None


def get_encoder():
    """Charge le modèle d'embedding (singleton)."""
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(EMBEDDING_MODEL)
    return _encoder


def get_faiss_index():
    """Charge l'index FAISS."""
    global _faiss_index
    if _faiss_index is None and os.path.exists(FAISS_INDEX_PATH):
        _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    return _faiss_index


def get_chunks_data():
    """Charge les données des chunks."""
    global _chunks_data
    if _chunks_data is None:
        chunks_path = FAISS_INDEX_PATH.replace(".bin", "_chunks.json")
        if os.path.exists(chunks_path):
            with open(chunks_path, "r", encoding="utf-8") as f:
                _chunks_data = json.load(f)
        else:
            _chunks_data = []
    return _chunks_data


def get_gemini_client():
    """Initialise le client Gemini."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=API_KEY)
    return _gemini_client


def search_faiss(query: str, top_n: int = TOP_N_RESULTS) -> list:
    """
    Recherche les documents les plus pertinents via FAISS.
    Retourne une liste de tuples (texte_chunk, score).
    """
    index = get_faiss_index()
    chunks = get_chunks_data()
    encoder = get_encoder()

    if index is None or not chunks:
        return []

    # Encodage de la requête
    query_vector = encoder.encode([query], convert_to_numpy=True)
    
    # Recherche FAISS
    distances, indices = index.search(query_vector, min(top_n, len(chunks)))

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks) and idx >= 0:
            results.append((chunks[idx]["text"], float(distances[0][i])))

    return results


def get_answer(query: str, context: str, conversation_history: list | None = None) -> str:
    """
    Génère une réponse en utilisant Gemini avec le contexte RAG.
    """
    client = get_gemini_client()

    # Construction du prompt système
    system_prompt = f"""Tu es un assistant IA spécialisé dans la réglementation des télécommunications au Burkina Faso. 

RÈGLES IMPORTANTES :
1. Réponds UNIQUEMENT en te basant sur le contexte fourni ci-dessous.
2. Si l'information n'est pas dans le contexte, dis-le clairement.
3. Limite ta réponse à {MAX_RESPONSE_WORDS} mots maximum.
4. Réponds en français.
5. Sois précis et structure ta réponse de manière claire.
6. Cite les sources ou articles de loi quand c'est possible.

CONTEXTE DOCUMENTAIRE :
{context}
"""

    # Construction des messages
    contents = []
    
    # Ajouter l'historique de conversation si disponible
    if conversation_history:
        for msg in conversation_history[-6:]:  # Garder les 6 derniers messages
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["content"]}]
            })

    # Ajouter la question actuelle
    contents.append({
        "role": "user",
        "parts": [{"text": query}]
    })

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.3,
                "max_output_tokens": 800,
            }
        )
        return (response.text or "Aucune réponse générée.").strip()
    except Exception as e:
        return f"❌ Erreur lors de la génération de la réponse : {str(e)}"
