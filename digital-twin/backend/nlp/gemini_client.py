"""
Gemini API Client for TOON DSL Translation.

Responsibilities:
- Load API key from environment
- Send prompt to Gemini
- Return raw TOON text
- Zero business logic

Implementation rules:
- Use google-generativeai
- No retries
- No streaming
- No temperature randomness
- No prompt memory
- Hard-fail on empty or malformed response
"""

import os
import google.generativeai as genai


class GeminiClient:
    """
    Simple Gemini API client for text-to-text translation.
    
    Stateless - no memory, no retries, no streaming.
    """
    
    def __init__(self):
        """
        Initialize Gemini client with API key from environment.
        
        Raises:
            RuntimeError: If GEMINI_API_KEY is not set
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        
        genai.configure(api_key=api_key)
        # Use Gemini 1.5 Flash for fast, low-latency translation
        self.model = genai.GenerativeModel("models/gemini-pro")
    
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
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            }
        )
        
        if not response:
            raise RuntimeError("Gemini returned empty response")
        
        # Handle both response.text and response.candidates access patterns
        # (newer versions of google-generativeai may require candidates access)
        try:
            text = response.text
        except (AttributeError, TypeError):
            # Fallback to candidates access pattern
            if not response.candidates or len(response.candidates) == 0:
                raise RuntimeError("Gemini returned empty response")
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                raise RuntimeError("Gemini returned empty response")
            text = candidate.content.parts[0].text
        
        if not text:
            raise RuntimeError("Gemini returned empty response")
        
        return text.strip()
