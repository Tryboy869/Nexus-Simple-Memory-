import struct
import json
from typing import Dict, Any, Tuple
from datetime import datetime

class NSMFormat:
    MAGIC_NUMBER = b'NSM\x01'
    VERSION = 1
    HEADER_SIZE = 128  # Augmenté pour plus de métadonnées
    
    def __init__(self):
        pass
        
    def create_nsm_file(self, data: bytes, index: Dict[str, Any], 
                       metadata: Dict[str, Any], output_path: str):
        """Crée un fichier NSM avec données, index et métadonnées"""
        # Ajouter timestamp de création
        metadata['created_at'] = datetime.now().isoformat()
        metadata['nsm_version'] = self.VERSION
        
        # Sérialiser l'index et métadonnées
        index_bytes = json.dumps(index, ensure_ascii=False).encode('utf-8')
        metadata_bytes = json.dumps(metadata, ensure_ascii=False).encode('utf-8')
        
        # Créer l'en-tête
        header = self._create_header(len(data), len(index_bytes), len(metadata_bytes))
        
        # Écrire le fichier
        with open(output_path, 'wb') as f:
            f.write(header)
            f.write(metadata_bytes)
            f.write(index_bytes)
            f.write(data)
    
    def _create_header(self, data_size: int, index_size: int, metadata_size: int) -> bytes:
        """Crée l'en-tête binaire du fichier NSM"""
        header = struct.pack(
            '<4sI I QQQ Q',
            self.MAGIC_NUMBER,      # 4 bytes: magic number
            self.VERSION,           # 4 bytes: version
            0,                      # 4 bytes: flags (réservé)
            metadata_size,          # 8 bytes: taille métadonnées
            index_size,             # 8 bytes: taille index
            data_size,              # 8 bytes: taille données
            0                       # 8 bytes: réservé
        )
        
        # Padding pour atteindre HEADER_SIZE
        padding_size = self.HEADER_SIZE - len(header)
        padding = b'\x00' * padding_size
        return header + padding
    
    def read_nsm_file(self, file_path: str) -> Tuple[bytes, Dict, Dict]:
        """Lit un fichier NSM et retourne (data, index, metadata)"""
        with open(file_path, 'rb') as f:
            # Lire l'en-tête
            header_data = f.read(self.HEADER_SIZE)
            if len(header_data) < self.HEADER_SIZE:
                raise ValueError("Fichier NSM tronqué")
            
            # Parser l'en-tête
            magic, version, flags, metadata_size, index_size, data_size, reserved = struct.unpack(
                '<4sI I QQQ Q', header_data[:52]
            )
            
            if magic != self.MAGIC_NUMBER:
                raise ValueError(f"Fichier NSM invalide (magic: {magic})")
            
            if version > self.VERSION:
                raise ValueError(f"Version NSM non supportée: {version}")
            
            # Lire métadonnées
            metadata = {}
            if metadata_size > 0:
                metadata_data = f.read(metadata_size)
                metadata = json.loads(metadata_data.decode('utf-8'))
            
            # Lire index
            index = {}
            if index_size > 0:
                index_data = f.read(index_size)
                index = json.loads(index_data.decode('utf-8'))
            
            # Lire données
            data = f.read(data_size)
            
            return data, index, metadata
    
    def validate_nsm_file(self, file_path: str) -> bool:
        """Valide l'intégrité d'un fichier NSM"""
        try:
            self.read_nsm_file(file_path)
            return True
        except Exception:
            return False
