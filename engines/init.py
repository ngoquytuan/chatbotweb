#engines/init.py
"""
Engines module for Enterprise Chatbot
Contains all the core processing engines
"""

from .intent_classifier import IntentClassifier, IntentType, IntentResult
from .faiss_manager import FAISSCollectionManager, DocumentChunk
from .llm_provider import MultiLLMProvider, LLMProvider
from .response_generator import ContextualResponseGenerator

__all__ = [
    'IntentClassifier',
    'IntentType', 
    'IntentResult',
    'FAISSCollectionManager',
    'DocumentChunk',
    'MultiLLMProvider',
    'LLMProvider',
    'ContextualResponseGenerator'
]

__version__ = "2.0.0"