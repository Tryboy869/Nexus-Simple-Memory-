import json  
import uuid  
from typing import List, Dict, Any, Optional, Tuple  
from datetime import datetime  
  
  
class NSMChat:  
    """Système de chat pour NSM avec historique de conversation"""  
      
    def __init__(self, retriever, model_name: str = "gpt-3.5-turbo",   
                 system_prompt: Optional[str] = None, session_id: Optional[str] = None):  
        self.retriever = retriever  
        self.model_name = model_name  
        self.conversation_history: List[Dict[str, str]] = []  
          
        self.system_prompt = system_prompt or "Vous êtes un assistant IA qui aide à rechercher et analyser des informations."  
        self.session_id = session_id or str(uuid.uuid4())  
        self.created_at = datetime.now().isoformat()  
          
    def chat(self, user_message: str, context_chunks: int = 3) -> str:  
        """Dialogue avec contexte depuis NSM"""  
        # Rechercher du contexte pertinent  
        search_results = self.retriever.search(user_message, top_k=context_chunks)  
        context = "\n\n".join([chunk for chunk, _ in search_results])  
          
        # Construire le message avec contexte  
        enhanced_message = f"""  
Contexte depuis NSM:  
{context}  
  
Question de l'utilisateur:  
{user_message}  
"""  
          
        # Simuler une réponse (en production, connecter à un vrai LLM)  
        response = self._generate_response(enhanced_message)  
          
        # Ajouter à l'historique  
        self.conversation_history.append({  
            "role": "user",  
            "content": user_message,  
            "timestamp": datetime.now().isoformat()  
        })  
          
        self.conversation_history.append({  
            "role": "assistant",   
            "content": response,  
            "timestamp": datetime.now().isoformat()  
        })  
          
        return response  
      
    def _generate_response(self, message: str) -> str:  
        """Génère une réponse simulée (à remplacer par un vrai LLM)"""  
        # Simulation basique - à remplacer par OpenAI, Anthropic, etc.  
        if "?" in message:  
            return f"Basé sur le contexte NSM, voici une réponse à votre question: [Réponse simulée pour: {message[:50]}...]"  
        else:  
            return f"J'ai analysé le contexte NSM. [Analyse simulée pour: {message[:50]}...]"  
      
    def get_history(self) -> List[Dict[str, str]]:  
        """Retourne l'historique de conversation"""  
        return self.conversation_history  
      
    def clear_history(self) -> None:  
        """Efface l'historique de conversation"""  
        self.conversation_history = []  
      
    def save_session(self, filepath: str) -> None:  
        """Sauvegarde la session de chat"""  
        session_data = {  
            "session_id": self.session_id,  
            "created_at": self.created_at,  
            "model_name": self.model_name,  
            "system_prompt": self.system_prompt,  
            "conversation_history": self.conversation_history  
        }  
          
        with open(filepath, 'w', encoding='utf-8') as f:  
            json.dump(session_data, f, indent=2, ensure_ascii=False)  
      
    def load_session(self, filepath: str) -> None:  
        """Charge une session de chat"""  
        with open(filepath, 'r', encoding='utf-8') as f:  
            session_data = json.load(f)  
          
        self.session_id = session_data.get("session_id", self.session_id)  
        self.created_at = session_data.get("created_at", self.created_at)  
        self.model_name = session_data.get("model_name", self.model_name)  
        self.system_prompt = session_data.get("system_prompt", self.system_prompt)  
        self.conversation_history = session_data.get("conversation_history", [])  
  
  
class NSMChatManager:  
    """Gestionnaire de sessions de chat NSM"""  
      
    def __init__(self, retriever):  
        self.retriever = retriever  
        self.active_sessions: Dict[str, NSMChat] = {}  
      
    def create_session(self, session_id: Optional[str] = None,   
                      model_name: str = "gpt-3.5-turbo",  
                      system_prompt: Optional[str] = None) -> NSMChat:  
        """Crée une nouvelle session de chat"""  
        session_id = session_id or str(uuid.uuid4())  
          
        chat_session = NSMChat(  
            retriever=self.retriever,  
            model_name=model_name,  
            system_prompt=system_prompt,  
            session_id=session_id  
        )  
          
        self.active_sessions[session_id] = chat_session  
        return chat_session  
      
    def get_session(self, session_id: str) -> Optional[NSMChat]:  
        """Récupère une session de chat"""  
        return self.active_sessions.get(session_id)  
      
    def delete_session(self, session_id: str) -> bool:  
        """Supprime une session de chat"""  
        if session_id in self.active_sessions:  
            del self.active_sessions[session_id]  
            return True  
        return False  
      
    def list_sessions(self) -> List[str]:  
        """Liste toutes les sessions actives"""  
        return list(self.active_sessions.keys())  
  
  
# Classes pour intégration LLM (optionnel)  
class OpenAIClient:  
    """Client OpenAI pour NSM (nécessite openai package)"""  
      
    def __init__(self, api_key: Optional[str] = None,   
                 model: Optional[str] = None):  
        self.api_key = api_key  
        self.model = model or "gpt-3.5-turbo"  
          
    def generate_response(self, messages: List[Dict[str, str]]) -> str:  
        """Génère une réponse via OpenAI"""  
        # Implémentation à ajouter avec le package openai  
        return "Réponse OpenAI (non implémentée)"  
  
  
class AnthropicClient:  
    """Client Anthropic pour NSM (nécessite anthropic package)"""  
      
    def __init__(self, api_key: Optional[str] = None):  
        self.api_key = api_key  
          
    def generate_response(self, messages: List[Dict[str, str]]) -> str:  
        """Génère une réponse via Anthropic"""  
        # Implémentation à ajouter avec le package anthropic  
        return "Réponse Anthropic (non implémentée)"
