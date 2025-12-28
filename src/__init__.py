"""
AI Scientist for SCI - CIAS-X Implementation

An AI Scientist system for SCI domain based on CIAS-X algorithm.
"""

__version__ = "4.0.0"
__author__ = "AI Scientist Team"


# LLM client
from .llm.client import LLMClient

__all__ = [
    # LLM
    "LLMClient",
]
