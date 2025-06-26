"""
NSMChat - Interface de chat pour NSM
"""
from typing import List, Dict, Any
from .retriever import NSMRetriever

class NSMChat:
    def __init__(self, nsm_file_path: str):
        self.retriever = NSMRetriever(nsm_file_path)
        self.conversation_history = []
    
    def ask(self, question: str, context_chunks: int = 3) -> str:
        """Pose une question et obtient une réponse basée sur le contenu NSM"""
        # Rechercher les chunks pertinents
        results = self.retriever.search(question, top_k=context_chunks)
        
        if not results:
            return "❌ Aucune information pertinente trouvée dans la base NSM."
        
        # Construire le contexte
        context = "\n\n".join([chunk for chunk, score in results])
        
        # Réponse simple basée sur le contexte
        response = f"📚 Contexte trouvé ({len(results)} sources):\n\n"
        
        for i, (chunk, score) in enumerate(results, 1):
            response += f"{i}. [Pertinence: {score:.2f}]\n"
            response += f"   {chunk[:200]}{'...' if len(chunk) > 200 else ''}\n\n"
        
        # Sauvegarder dans l'historique
        self.conversation_history.append({
            'question': question,
            'context_chunks': len(results),
            'response': response
        })
        
        return response
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique des conversations"""
        return self.conversation_history
    
    def clear_history(self):
        """Efface l'historique"""
        self.conversation_history = []
