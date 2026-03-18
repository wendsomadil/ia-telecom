# chatbot/database.py
"""
Gestion de la base de données SQLite.
- Utilisateurs (inscription / connexion)
- Conversations (sauvegarde / chargement)
"""

import sqlite3
import hashlib
import datetime
import json
import os
from chatbot.config import DB_PATH


def get_connection():
    """Crée et retourne une connexion SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialise les tables si elles n'existent pas."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT DEFAULT 'Nouvelle conversation',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash un mot de passe avec SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(nom: str, prenom: str, email: str, password: str) -> dict:
    """
    Inscrit un nouvel utilisateur.
    Retourne {"success": True, "user_id": ...} ou {"success": False, "error": ...}
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (nom, prenom, email, password_hash) VALUES (?, ?, ?, ?)",
            (nom.strip(), prenom.strip(), email.strip().lower(), hash_password(password))
        )
        conn.commit()
        return {"success": True, "user_id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Cet email est déjà utilisé."}
    finally:
        conn.close()


def login_user(email: str, password: str) -> dict:
    """
    Connecte un utilisateur.
    Retourne {"success": True, "user": {...}} ou {"success": False, "error": ...}
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (email.strip().lower(), hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return {
            "success": True,
            "user": {
                "id": user["id"],
                "nom": user["nom"],
                "prenom": user["prenom"],
                "email": user["email"]
            }
        }
    return {"success": False, "error": "Email ou mot de passe incorrect."}


def create_conversation(user_id: int, title: str = "Nouvelle conversation") -> int:
    """Crée une nouvelle conversation et retourne son ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )
    conn.commit()
    conv_id = cursor.lastrowid or 0
    conn.close()
    return conv_id


def get_user_conversations(user_id: int) -> list:
    """Retourne toutes les conversations d'un utilisateur (les plus récentes en premier)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    conversations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return conversations


def add_message(conversation_id: int, role: str, content: str):
    """Ajoute un message à une conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content)
    )
    # Met à jour la date de modification de la conversation
    cursor.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    conn.commit()
    conn.close()


def get_conversation_messages(conversation_id: int) -> list:
    """Retourne tous les messages d'une conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,)
    )
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages


def update_conversation_title(conversation_id: int, title: str):
    """Met à jour le titre d'une conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET title = ? WHERE id = ?",
        (title, conversation_id)
    )
    conn.commit()
    conn.close()


def delete_conversation(conversation_id: int):
    """Supprime une conversation et tous ses messages."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()


# Initialiser la base au chargement du module
init_database()
