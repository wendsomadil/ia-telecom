# chatbot/extraction.py
"""
Extraction de texte à partir de fichiers PDF.
Supporte l'extraction récursive dans les sous-dossiers.
"""

import os
import json
import fitz  # PyMuPDF
import openpyxl
from chatbot.config import PDF_DIRECTORY, EXCEL_DIRECTORY, JSON_DIRECTORY, DOCUMENTS_MAP_PATH


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrait le texte complet d'un fichier PDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            page_text = page.get_text()
            if isinstance(page_text, str):
                text += page_text + "\n"
        doc.close()
    except Exception as e:
        print(f"Erreur lors de l'extraction de {pdf_path}: {e}")
    return text.strip()


def save_text_to_excel(text: str, output_path: str):
    """Sauvegarde le texte extrait dans un fichier Excel."""
    wb = openpyxl.Workbook()
    ws = wb.active
    if ws is None:
        ws = wb.create_sheet("Texte Extrait")
    else:
        ws.title = "Texte Extrait"
    ws.append(["Contenu"])
    
    # Découpe le texte en lignes pour Excel
    for line in text.split("\n"):
        if line.strip():
            ws.append([line.strip()])
    
    wb.save(output_path)


def process_pdfs_in_directory(pdf_dir: str | None = None, excel_dir: str | None = None):
    """
    Parcourt récursivement le dossier PDF et extrait le texte.
    Sauvegarde dans Excel et construit une map des documents.
    """
    if pdf_dir is None:
        pdf_dir = PDF_DIRECTORY
    if excel_dir is None:
        excel_dir = EXCEL_DIRECTORY

    os.makedirs(excel_dir, exist_ok=True)
    os.makedirs(JSON_DIRECTORY, exist_ok=True)

    documents_map = {}
    doc_index = 0

    # Parcours récursif de tous les sous-dossiers
    for root, dirs, files in os.walk(pdf_dir):
        for filename in sorted(files):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, filename)
                
                # Nom relatif pour identifier le document
                relative_path = os.path.relpath(pdf_path, pdf_dir)
                safe_name = relative_path.replace(os.sep, "_").replace(".pdf", "")
                
                print(f"[{doc_index + 1}] Extraction : {relative_path}")
                
                text = extract_text_from_pdf(pdf_path)
                
                if text:
                    # Sauvegarde Excel
                    excel_path = os.path.join(excel_dir, f"{safe_name}.xlsx")
                    save_text_to_excel(text, excel_path)
                    
                    # Ajouter à la map
                    documents_map[safe_name] = {
                        "pdf_path": pdf_path,
                        "excel_path": excel_path,
                        "relative_path": relative_path,
                        "text_length": len(text),
                        "index": doc_index
                    }
                    doc_index += 1
                else:
                    print(f"  ⚠ Aucun texte extrait de : {relative_path}")

    # Sauvegarde de la map des documents
    with open(DOCUMENTS_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(documents_map, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {doc_index} documents traités et indexés.")
    return documents_map


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Découpe un texte en morceaux (chunks) avec chevauchement.
    Essentiel pour une bonne indexation RAG.
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks
