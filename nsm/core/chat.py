"""
NSMChat - Interface de chat pour NSM
"""

from typing import List, Dict, Any, Optional
from .retriever import NSMRetriever
import os
import json
from datetime import datetime

class NSMChat:
    def __init__(self, nsm_file_path: str):
        self.retriever = NSMRetriever(nsm_file_path)
        self.conversation_history = []

    def ask(self, question: str, context_chunks: int = 3) -> str:
        """Pose une question et obtient une réponse basée sur le contenu NSM"""
        results = self.retriever.search(question, top_k=context_chunks)

        if not results:
            return "❌ Aucune information pertinente trouvée dans la base NSM."

        context = "\n\n".join([chunk for chunk, _ in results])

        response = f"📚 Contexte trouvé ({len(results)} sources):\n\n"
        for i, (chunk, score) in enumerate(results, 1):
            response += f"{i}. [Pertinence: {score:.2f}]\n"
            response += f"   {chunk[:200]}{'...' if len(chunk) > 200 else ''}\n\n"

        self.conversation_history.append({
            'question': question,
            'context_chunks': len(results),
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })

        return response

    def get_history(self) -> List[Dict[str, Any]]:
        return self.conversation_history

    def clear_history(self):
        self.conversation_history = []

    def save_history(self, output_path: str = "chat_history.json"):
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            return f"✅ Historique sauvegardé dans {output_path}"
        except Exception as e:
            return f"❌ Erreur sauvegarde: {e}"

    def load_history(self, input_path: str = "chat_history.json"):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                self.conversation_history = json.load(f)
            return f"✅ Historique chargé depuis {input_path}"
        except Exception as e:
            return f"❌ Erreur chargement: {e}"


class NSMChatManager:
    def __init__(self, nsm_file_path: str):
        self.chat = NSMChat(nsm_file_path)
        self.file_path = nsm_file_path
        self.last_answer = ""

    def run_interactive(self):
        print("🧠 Bienvenue dans NSMChatManager ! Tapez 'exit' pour quitter.")
        while True:
            question = input("\n❓ Question > ")
            if question.lower() in {"exit", "quit"}:
                print("👋 Fin de session.")
                break
            response = self.chat.ask(question)
            self.last_answer = response
            print("\n" + response)

    def quick_ask(self, question: str) -> str:
        self.last_answer = self.chat.ask(question)
        return self.last_answer

    def save(self, filename: Optional[str] = None) -> str:
        if not filename:
            filename = f"chat_history_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        return self.chat.save_history(filename)

    def load(self, filename: str) -> str:
        return self.chat.load_history(filename)

    def export_last_answer(self, output_file: str = "last_answer.txt") -> str:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(self.last_answer)
            return f"✅ Réponse exportée dans {output_file}"
        except Exception as e:
            return f"❌ Erreur export : {e}"
