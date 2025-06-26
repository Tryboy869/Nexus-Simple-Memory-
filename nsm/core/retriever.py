"""
NSMRetriever - Récupérateur pour Nexus Simple Memory
"""
import json
import os
from typing import List, Tuple, Dict, Any

# Imports locaux
from .utils import cosine_similarity, SimpleEmbedding
from ..compression.advanced import NSMCompressor
from ..core.format import NSMFormat

class NSMRetriever:
    def __init__(self, nsm_file_path: str):
        self.nsm_file_path = nsm_file_path
        self.nsm_format = NSMFormat()
        self.compressor = NSMCompressor()
        
        # Charger les données
        self.chunks = []
        self.embeddings = []
        self.embedding_model = SimpleEmbedding()
        self.metadata = {}
        
        self._load_nsm_file()
    
    def _load_nsm_file(self):
        """Charge le fichier NSM"""
        try:
            # Lire le fichier NSM
            compressed_data, index, metadata = self.nsm_format.read_nsm_file(self.nsm_file_path)
            self.metadata = metadata
            
            # Décompresser
            algorithm = index.get('algorithm', 'none')
            decompressed_data = self.compressor.decompress(compressed_data, algorithm)
            
            # Parser les données
            data = json.loads(decompressed_data.decode('utf-8'))
            self.chunks = data.get('chunks', [])
            self.embeddings = data.get('embeddings', [])
            
            # Reconstruire le modèle d'embedding
            if self.chunks:
                texts = [chunk['text'] for chunk in self.chunks]
                self.embedding_model.fit(texts)
            
            print(f"✅ NSM chargé: {len(self.chunks)} chunks")
            
        except Exception as e:
            print(f"❌ Erreur chargement NSM: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Recherche sémantique dans le fichier NSM"""
        if not self.chunks or not self.embeddings:
            return []
        
        # Créer l'embedding de la requête
        query_embedding = self.embedding_model.transform(query)
        
        # Calculer les similarités
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            if similarity >= threshold:
                similarities.append((i, similarity))
        
        # Trier par similarité décroissante
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retourner les top_k résultats
        results = []
        for i, similarity in similarities[:top_k]:
            chunk_text = self.chunks[i]['text']
            results.append((chunk_text, similarity))
        
        return results
    
    def get_chunk_by_id(self, chunk_id: str) -> Dict[str, Any]:
        """Récupère un chunk par son ID"""
        for chunk in self.chunks:
            if chunk['id'] == chunk_id:
                return chunk
        return {}
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retourne tous les chunks"""
        return self.chunks
    
    def extract_all(self, output_dir: str):
        """Extrait tout le contenu vers un répertoire"""
        os.makedirs(output_dir, exist_ok=True)
        
        for chunk in self.chunks:
            # Créer un nom de fichier basé sur l'ID du chunk
            filename = f"{chunk['id']}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Source: {chunk.get('source', 'Unknown')}\n")
                f.write(f"Chunk Index: {chunk.get('chunk_index', 0)}\n")
                f.write("-" * 50 + "\n")
                f.write(chunk['text'])
        
        print(f"✅ {len(self.chunks)} chunks extraits vers {output_dir}")
    
    def get_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le fichier NSM"""
        return {
            'file_path': self.nsm_file_path,
            'chunks_count': len(self.chunks),
            'metadata': self.metadata,
            'total_text_size': sum(len(chunk['text']) for chunk in self.chunks),
            'embedding_model': self.metadata.get('embedding_model', 'unknown')
        }
