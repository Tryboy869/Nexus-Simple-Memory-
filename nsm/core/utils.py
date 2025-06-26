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
