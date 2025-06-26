#!/bin/bash

# Script pour corriger les modules manquants NSM
echo "🔧 Correction des modules NSM manquants..."

cd "$HOME/Nexus-Simple-Memory-"

# Créer nsm/core/utils.py manquant
echo "📝 Création de nsm/core/utils.py..."
cat > nsm/core/utils.py << 'EOF'
"""
Utilitaires pour NSM (Nexus Simple Memory)
"""
import os
import hashlib
import json
import math
from typing import List, Dict, Any, Optional
from pathlib import Path

def calculate_file_hash(file_path: str) -> str:
    """Calcule le hash SHA256 d'un fichier"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""

def get_file_size(file_path: str) -> int:
    """Retourne la taille d'un fichier en bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0

def safe_read_text(file_path: str, encoding='utf-8', fallback_encoding='latin-1') -> str:
    """Lecture sécurisée d'un fichier texte avec fallback d'encodage"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding=fallback_encoding) as f:
                return f.read()
        except Exception:
            return f"[Erreur lecture fichier: {file_path}]"
    except Exception:
        return f"[Fichier inaccessible: {file_path}]"

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Découpe un texte en chunks avec chevauchement"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Essayer de couper à un espace pour éviter de couper les mots
        if end < len(text) and text[end] != ' ':
            last_space = chunk.rfind(' ')
            if last_space > chunk_size // 2:  # Au moins la moitié du chunk
                chunk = chunk[:last_space]
                end = start + last_space
        
        chunks.append(chunk.strip())
        start = max(start + chunk_size - overlap, end)
        
        if start >= len(text):
            break
    
    return [c for c in chunks if c]  # Retirer les chunks vides

def format_bytes(bytes_count: int) -> str:
    """Formate une taille en bytes en format lisible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"

def is_text_file(file_path: str) -> bool:
    """Détermine si un fichier est un fichier texte"""
    text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log'}
    return Path(file_path).suffix.lower() in text_extensions

def scan_directory(directory: str, include_extensions: Optional[List[str]] = None) -> List[str]:
    """Scanne un répertoire et retourne la liste des fichiers"""
    files = []
    try:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if include_extensions:
                    if any(filename.lower().endswith(ext.lower()) for ext in include_extensions):
                        files.append(file_path)
                else:
                    files.append(file_path)
    except Exception as e:
        print(f"Erreur scan répertoire {directory}: {e}")
    
    return files

class SimpleEmbedding:
    """Embedding simple basé sur TF-IDF pour éviter les dépendances lourdes"""
    
    def __init__(self):
        self.vocabulary = {}
        self.idf_scores = {}
        
    def fit(self, texts: List[str]):
        """Entraîne le modèle sur une liste de textes"""
        # Construire le vocabulaire
        word_counts = {}
        doc_counts = {}
        
        for text in texts:
            words = set(text.lower().split())
            for word in words:
                doc_counts[word] = doc_counts.get(word, 0) + 1
            
            for word in text.lower().split():
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Calculer IDF
        num_docs = len(texts)
        for word, count in doc_counts.items():
            self.idf_scores[word] = math.log(num_docs / count)
        
        # Créer vocabulaire
        self.vocabulary = {word: i for i, word in enumerate(word_counts.keys())}
    
    def transform(self, text: str) -> List[float]:
        """Transforme un texte en vecteur"""
        if not self.vocabulary:
            return [0.0] * 100  # Vecteur par défaut
        
        vector = [0.0] * len(self.vocabulary)
        words = text.lower().split()
        word_counts = {}
        
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # TF-IDF
        for word, count in word_counts.items():
            if word in self.vocabulary:
                tf = count / len(words)
                idf = self.idf_scores.get(word, 1.0)
                vector[self.vocabulary[word]] = tf * idf
        
        return vector

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calcule la similarité cosinus entre deux vecteurs"""
    try:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    except Exception:
        return 0.0
EOF

# Corriger les imports dans encoder.py pour éviter les dépendances manquantes
echo "🔧 Correction de nsm/core/encoder.py..."
cat > nsm/core/encoder.py << 'EOF'
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
EOF

# Corriger retriever.py
echo "🔧 Correction de nsm/core/retriever.py..."
cat > nsm/core/retriever.py << 'EOF'
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
EOF

# Corriger chat.py pour éviter les dépendances
echo "🔧 Correction de nsm/core/chat.py..."
cat > nsm/core/chat.py << 'EOF'
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
EOF

echo "✅ Modules manquants créés avec succès!"
echo "🧪 Test d'import en cours..."

# Test d'import
python3 << 'PYTHON_TEST'
try:
    import sys
    sys.path.insert(0, '.')
    
    from nsm.core.utils import chunk_text, SimpleEmbedding
    from nsm.core.encoder import NSMEncoder
    from nsm.core.retriever import NSMRetriever
    from nsm.core.chat import NSMChat
    
    print("✅ Tous les imports fonctionnent!")
    
    # Test rapide
    embedding = SimpleEmbedding()
    texts = ["test 1", "test 2"]
    embedding.fit(texts)
    vec = embedding.transform("test")
    print(f"✅ Embedding test: dimension {len(vec)}")
    
except Exception as e:
    print(f"❌ Erreur d'import: {e}")
PYTHON_TEST
