# chatbot/utils.py
"""
Fonctions utilitaires pour le chargement des données textuelles.
"""

import os
import json
import openpyxl
from chatbot.config import EXCEL_DIRECTORY, DOCUMENTS_MAP_PATH


def load_text_from_excel(excel_path: str) -> str:
    """Charge le texte depuis un fichier Excel."""
    text = ""
    try:
        wb = openpyxl.load_workbook(excel_path, read_only=True)
        ws = wb.active
        if ws is None:
            wb.close()
            return text
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0]:
                text += str(row[0]) + "\n"
        wb.close()
    except Exception as e:
        print(f"Erreur lecture Excel {excel_path}: {e}")
    return text.strip()


def load_text_data(excel_dir: str | None = None) -> dict:
    """
    Charge tous les textes depuis les fichiers Excel.
    Retourne un dictionnaire {nom_document: texte}.
    """
    if excel_dir is None:
        excel_dir = EXCEL_DIRECTORY

    texts = {}

    if not os.path.exists(excel_dir):
        print(f"Dossier Excel introuvable : {excel_dir}")
        return texts

    for filename in sorted(os.listdir(excel_dir)):
        if filename.endswith(".xlsx"):
            filepath = os.path.join(excel_dir, filename)
            doc_name = filename.replace(".xlsx", "")
            text = load_text_from_excel(filepath)
            if text:
                texts[doc_name] = text

    return texts


def load_documents_map() -> dict:
    """Charge la map des documents depuis le fichier JSON."""
    if os.path.exists(DOCUMENTS_MAP_PATH):
        with open(DOCUMENTS_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
