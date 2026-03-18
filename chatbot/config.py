# chatbot/config.py
"""
Configuration centrale du projet.
Charge les variables d'environnement et définit les chemins.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Gemini ---
API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- Modèle Gemini ---
GEMINI_MODEL = "gemini-2.5-flash"

# --- Chemins ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIRECTORY = os.path.join(BASE_DIR, "pdf_files")
EXCEL_DIRECTORY = os.path.join(BASE_DIR, "output", "excel")
JSON_DIRECTORY = os.path.join(BASE_DIR, "output", "json")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "output", "faiss_index.bin")
DOCUMENTS_MAP_PATH = os.path.join(BASE_DIR, "output", "documents_map.json")
DB_PATH = os.path.join(BASE_DIR, "database.db")

# --- Paramètres RAG ---
MAX_RESPONSE_WORDS = 400
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
TOP_N_RESULTS = 5

# --- Paramètres application ---
APP_TITLE = "Assistance IA Télécom"
APP_ICON = "📡"
