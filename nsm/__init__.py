"""
NSM - Nexus Simple Memory
Stockage compressé intelligent avec recherche sémantique
"""

__version__ = "1.0.0"
__author__ = "NSM Team"
__license__ = "MIT"

# Imports principaux
try:
    from .core.encoder import NSMEncoder
    from .core.retriever import NSMRetriever
    from .security.tokens import NSMTokenManager
    from .compression.advanced import NSMCompressor
    from .core.format import NSMFormat
    
    __all__ = [
        "NSMEncoder",
        "NSMRetriever", 
        "NSMTokenManager",
        "NSMCompressor",
        "NSMFormat"
    ]
    
except ImportError as e:
    # Gestion gracieuse des imports manqués
    print(f"⚠️  Attention: Certains modules NSM ne sont pas disponibles: {e}")
    __all__ = []
