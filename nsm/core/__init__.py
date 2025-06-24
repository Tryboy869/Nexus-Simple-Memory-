"""
NSM - QR Code Memory-Based AI Memory Library
"""

__version__ = "0.1.0"

from .encoder import NSMEncoder
from .retriever import NSMRetriever
from .chat import NSMChat
from .interactive import chat_with_memory, quick_chat
from .llm_client import LLMClient, create_llm_client

__all__ = ["NSMEncoder", "NSMRetriever", "NSMChat", "chat_with_memory", "quick_chat", "LLMClient", "create_llm_client"]
