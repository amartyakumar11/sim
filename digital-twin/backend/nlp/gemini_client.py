"""
Gemini API Client for TOON DSL Translation.

Responsibilities:
- Load API key from environment
- Send prompt to Gemini
- Return raw TOON text
- Zero business logic

Implementation rules:
- Use supported google-genai client
- No retries
- No streaming
- No temperature randomness
- No prompt memory
- Hard-fail on empty or malformed response
"""

import logging
import os
from google import genai

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Simple Gemini API client for text-to-text translation.
    
    Stateless - no memory, no retries, no streaming.
    """
    
    DEFAULT_MODEL = "gemini-2.5-flash"  # free-tier quota; override with GEMINI_MODEL

    def __init__(self):
        """
        Initialize Gemini client with API key from environment.
        """
        api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment")
        self.client = genai.Client(api_key=api_key)
        self.model = (os.environ.get("GEMINI_MODEL") or "").strip() or self.DEFAULT_MODEL
    
    def generate_toon(self, prompt: str) -> str:
        """
        Generate TOON DSL from natural language prompt.
        
        Args:
            prompt: System prompt with user input and TOON grammar
            
        Returns:
            Raw TOON DSL text (stripped)
            
        Raises:
            RuntimeError: If Gemini returns empty or malformed response
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 1,
                },
            )
        except Exception as e:
            logger.warning("Gemini request failed: %s", e, exc_info=True)
            raise RuntimeError("Gemini request failed") from e
        
        if not response or not getattr(response, "candidates", None):
            raise RuntimeError("Gemini returned no candidates")
        
        try:
            text = (
                response.candidates[0]
                .content.parts[0]
                .text.strip()
            )
        except (AttributeError, IndexError):
            raise RuntimeError("Gemini returned malformed response")
        
        if not text:
            raise RuntimeError("Gemini returned empty response")
        
        return text
