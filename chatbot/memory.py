# chatbot/memory.py
"""
Gestion de la mémoire conversationnelle.
Garde le contexte des échanges récents pour une meilleure cohérence.
"""


class ChatMemory:
    """Gère l'historique de conversation en mémoire."""

    def __init__(self, max_history: int = 20):
        self.history = []
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        """Ajoute un message à l'historique."""
        self.history.append({"role": role, "content": content})
        # Limiter la taille de l'historique
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_context(self, last_n: int = 6) -> list:
        """Retourne les n derniers échanges pour le contexte."""
        return self.history[-last_n:]

    def get_formatted_history(self) -> list:
        """Retourne l'historique formaté pour l'affichage."""
        formatted = []
        for i in range(0, len(self.history) - 1, 2):
            if i + 1 < len(self.history):
                formatted.append({
                    "user": self.history[i]["content"],
                    "bot": self.history[i + 1]["content"]
                })
        return formatted

    def clear(self):
        """Efface tout l'historique."""
        self.history = []

    def __len__(self):
        return len(self.history)
