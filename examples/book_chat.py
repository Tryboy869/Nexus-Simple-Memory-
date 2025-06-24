#!/usr/bin/env python3
"""
Book memory example using chat_with_memory
"""

import sys
import os

from nsm.config import VIDEO_FILE_TYPE

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()


from nsm import NSMEncoder, chat_with_memory

# Book PDF path - NSM will handle PDF parsing automatically
book_pdf = "data/bitcoin.pdf"  # Replace with your PDF path

# Build memory memory from PDF
memory_path = f"output/book_memory.{VIDEO_FILE_TYPE}"
index_path = "output/book_memory_index.json"

# Create output directory with subdirectory for sessions
os.makedirs("output/book_chat", exist_ok=True)

# Encode PDF to memory - NSM handles all PDF parsing internally
encoder = NSMEncoder()
encoder.add_pdf(book_pdf)  # Simple one-liner to add PDF content
encoder.build_memory(memory_path, index_path)
print(f"Created book memory memory: {memory_path}")

# Get API key from environment or use your own
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("\nNote: Set OPENAI_API_KEY environment variable for full LLM responses.")
    print("Without it, you'll only see raw context chunks.\n")

# Chat with the book - interactive session
print("\n📚 Chat with your book! Ask questions about the content.")
print("Example questions:")
print("- 'What is this document about?'")
print("- 'What are the key concepts explained?'\n")

chat_with_memory(memory_path, index_path, api_key=api_key, session_dir="output/book_chat")