import json
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class NSMTokenManager:
    def __init__(self, license_key: str):
        self.license_key = license_key
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
    def validate_license(self) -> bool:
        """Valide la clé de licence NSM"""
        return len(self.license_key) == 32 and self.license_key.isalnum()
        
    def consume_tokens(self, gb_compressed: float) -> bool:
        """Consomme des tokens selon la taille compressée"""
        tokens_needed = max(1, int(gb_compressed))
        remaining = self.get_remaining_tokens()
        return remaining >= tokens_needed
        
    def get_remaining_tokens(self) -> int:
        """Retourne le nombre de tokens restants"""
        # Simulation - en production, ceci serait connecté à une API
        return 100
    
    def generate_session_token(self) -> str:
        """Génère un token de session temporaire"""
        timestamp = datetime.now().isoformat()
        data = f"{self.license_key}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
