"""
NSMEncoder - Encodeur pour Nexus Simple Memory
"""
import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

# Imports locaux
from .utils import chunk_text, safe_read_text, scan_directory, SimpleEmbedding
from ..security.tokens import NSMTokenManager
from ..compression.advanced import NSMCompressor
from ..core.format import NSMFormat

class NSMEncoder:
    def __init__(self, license_key: str):
        self.license_key = license_key
        self.token_manager = NSMTokenManager(license_key)
        self.compressor = NSMCompressor()
        self.nsm_format = NSMFormat()
        
        # Données à encoder
        self.chunks = []
        self.index = {}
        self.metadata = {
            'license_key_hash': self._hash_license(license_key),
            'chunks_count': 0,
            'total_size': 0
        }
        
        # Embedding simple
        self.embedding_model = SimpleEmbedding()
        
    def _hash_license(self, license_key: str) -> str:
        """Hash de la licence pour vérification"""
        import hashlib
        return hashlib.sha256(license_key.encode()).hexdigest()[:16]
    
    def add_text(self, text: str, source: str = "manual", chunk_size: int = 1000):
        """Ajoute du texte à encoder"""
        if not text.strip():
            return
        
        chunks = chunk_text(text, chunk_size)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{source}_{len(self.chunks)}"
            self.chunks.append({
                'id': chunk_id,
                'text': chunk,
                'source': source,
                'chunk_index': i,
                'size': len(chunk)
            })
        
        print(f"✅ Ajouté {len(chunks)} chunks depuis {source}")
    
    def add_file(self, file_path: str, chunk_size: int = 1000):
        """Ajoute un fichier à encoder"""
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            return
        
        try:
            text = safe_read_text(file_path)
            self.add_text(text, source=file_path, chunk_size=chunk_size)
        except Exception as e:
            print(f"❌ Erreur lecture {file_path}: {e}")
    
    def add_directory(self, directory: str, extensions: Optional[List[str]] = None):
        """Ajoute tous les fichiers d'un répertoire"""
        if extensions is None:
            extensions = ['.txt', '.md', '.py', '.js', '.html', '.json', '.log']
        
        files = scan_directory(directory, extensions)
        
        for file_path in files:
            self.add_file(file_path)
        
        print(f"✅ Traité {len(files)} fichiers du répertoire {directory}")
    
    def build_nsm(self, output_path: str):
        """Construit le fichier NSM final"""
        if not self.chunks:
            print("❌ Aucune donnée à encoder")
            return
        
        # Vérifier les tokens
        total_size_gb = sum(chunk['size'] for chunk in self.chunks) / (1024**3)
        if not self.token_manager.consume_tokens(total_size_gb):
            print(f"❌ Tokens insuffisants pour {total_size_gb:.2f} GB")
            return
        
        print(f"🔧 Construction NSM avec {len(self.chunks)} chunks...")
        
        # Préparer les données
        all_texts = [chunk['text'] for chunk in self.chunks]
        
        # Entraîner l'embedding simple
        print("🧠 Entraînement du modèle d'embedding...")
        self.embedding_model.fit(all_texts)
        
        # Créer les embeddings
        embeddings = []
        for chunk in self.chunks:
            embedding = self.embedding_model.transform(chunk['text'])
            embeddings.append(embedding)
        
        # Construire l'index
        self.index = {
            'chunks': self.chunks,
            'embeddings': embeddings,
            'embedding_dim': len(embeddings[0]) if embeddings else 0
        }
        
        # Sérialiser les données
        data_to_compress = json.dumps({
            'chunks': self.chunks,
            'embeddings': embeddings
        }, ensure_ascii=False).encode('utf-8')
        
        # Compresser
        print("📦 Compression des données...")
        compressed_data, algo, ratio = self.compressor.auto_compress(data_to_compress)
        
        # Métadonnées finales
        self.metadata.update({
            'chunks_count': len(self.chunks),
            'total_size': len(data_to_compress),
            'compressed_size': len(compressed_data),
            'compression_algo': algo,
            'compression_ratio': ratio,
            'embedding_model': 'simple_tfidf'
        })
        
        # Créer le fichier NSM
        self.nsm_format.create_nsm_file(
            data=compressed_data,
            index={'type': 'compressed_chunks', 'algorithm': algo},
            metadata=self.metadata,
            output_path=output_path
        )
        
        print(f"✅ Fichier NSM créé: {output_path}")
        print(f"📊 Taux de compression: {(1-ratio)*100:.1f}%")
        print(f"💾 Taille finale: {len(compressed_data)/1024:.1f} KB")
