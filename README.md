<<<<<<< HEAD
# 📡 Assistance IA Télécom

Chatbot intelligent utilisant l'approche **RAG (Retrieval-Augmented Generation)** et l'API **Google Gemini 2.5 Flash** pour répondre à des questions contextuelles basées sur la réglementation des télécommunications au Burkina Faso.

## ✨ Fonctionnalités

- **Authentification** : Inscription et connexion sécurisées avec stockage SQLite
- **Chat intelligent** : Pipeline RAG (FAISS + Gemini) pour des réponses précises
- **Sauvegarde des conversations** : Historique persistant par utilisateur
- **Thème sombre / clair** : Basculer entre les deux modes d'affichage
- **Indexation récursive** : Support des sous-dossiers dans `pdf_files/`
- **Lecture vocale** : Écouter les réponses de l'assistant
- **Feedback** : Système de retour utilisateur intégré
- **Réponses concises** : Limitées à 400 mots maximum

## 🚀 Installation

### 1. Cloner le projet et créer l'environnement virtuel

```bash
python -m venv fid_env
# Windows
.\fid_env\Scripts\activate
# Linux/Mac
source fid_env/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configurer la clé API

Créez un fichier `.env` à la racine du projet :

```
GEMINI_API_KEY=Votre_Cle_API_Gemini
```

### 3. Ajouter vos documents PDF

Placez vos fichiers PDF dans le dossier `pdf_files/`. Les sous-dossiers sont supportés :

```
pdf_files/
├── lois/
│   ├── loi_telecom_2024.pdf
│   └── decret_arcep.pdf
├── reglements/
│   └── cahier_charges.pdf
└── rapport_annuel.pdf
```

### 4. Indexer les documents

```bash
python init_index.py
```

### 5. Lancer l'application

```bash
streamlit run app.py
```

## 📁 Structure du projet

```
fid/
├── pdf_files/                  # Documents PDF à indexer (avec sous-dossiers)
├── output/
│   ├── excel/                  # Textes extraits en Excel
│   ├── json/                   # Données JSON
│   ├── faiss_index.bin         # Index FAISS
│   └── faiss_index_chunks.json # Chunks indexés
├── css/
│   └── styles.css              # Thème clair/sombre
├── assets/                     # Logos et images
├── chatbot/
│   ├── __init__.py             # Module chatbot
│   ├── config.py               # Configuration centralisée
│   ├── database.py             # Gestion SQLite (users + conversations)
│   ├── extraction.py           # Extraction PDF récursive + chunking
│   ├── utils.py                # Fonctions utilitaires
│   ├── rag_pipeline.py         # Pipeline RAG (FAISS + Gemini)
│   └── memory.py               # Mémoire conversationnelle
├── app.py                      # Application Streamlit principale
├── init_index.py               # Script d'indexation
├── requirements.txt            # Dépendances
├── database.db                 # Base SQLite (créée automatiquement)
├── .env                        # Clé API (non versionné)
└── README.md                   # Documentation
```

## 🔧 Architecture technique

### Pipeline RAG

1. **Extraction** : PyMuPDF extrait le texte des PDF récursivement
2. **Chunking** : Le texte est découpé en morceaux de ~500 mots avec chevauchement
3. **Embedding** : `all-MiniLM-L6-v2` génère les vecteurs sémantiques
4. **Indexation** : FAISS stocke et permet la recherche vectorielle rapide
5. **Recherche** : La question utilisateur est vectorisée et comparée aux chunks
6. **Génération** : Gemini 2.5 Flash produit une réponse basée sur le contexte retrouvé

### Base de données

- **users** : Stockage des comptes utilisateurs
- **conversations** : Historique des sessions de chat
- **messages** : Contenu des échanges (question + réponse)

## 📝 Notes

- La première exécution de `init_index.py` peut prendre quelques minutes selon le volume de PDF
- Les réponses sont limitées à 400 mots pour rester concises
- Le fichier `.env` ne doit jamais être partagé ou versionné
=======
# ia-telecom
>>>>>>> b868d66a9f47f0b14460101ea07a764c6a0834a6
