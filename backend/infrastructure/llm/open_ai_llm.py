import os
import logging
import google.generativeai as genai
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class GeminiLLMService:
    """Service for interacting with Google Gemini 2.0 Flash API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini LLM Service.
        
        Args:
            api_key: Google Gemini API key. If not provided, will try to get from environment variable GEMINI_API_KEY.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided either as parameter or environment variable")
        
        # Configure the API key
        genai.configure(api_key=self.api_key)
        
        # Initialize the model - Using Gemini 2.0 Flash
        # Model name: gemini-2.0-flash-exp (experimental) or gemini-2.0-flash-latest
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            logger.warning(f"Failed to load gemini-2.0-flash-exp, trying gemini-2.0-flash-latest: {e}")
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash-latest')
            except Exception as e2:
                logger.warning(f"Failed to load gemini-2.0-flash-latest, falling back to gemini-1.5-flash: {e2}")
                self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_content_with_Structured_schema(
        self, 
        system_instruction: str, 
        query: str, 
        response_schema: BaseModel
    ) -> BaseModel:
        """
        Generate content with structured schema using Gemini API.
        
        Args:
            system_instruction: System instruction/prompt
            query: User query
            response_schema: Pydantic BaseModel schema for structured output
            
        Returns:
            Instance of response_schema with generated content
        """
        try:
            # Combine system instruction and query
            full_prompt = f"{system_instruction}\n\n{query}"
            
            # Generate content with response schema
            # Gemini API supports structured output via response_mime_type and response_schema
            # Get schema for Pydantic v2
            if hasattr(response_schema, 'model_json_schema'):
                schema = response_schema.model_json_schema()
            elif hasattr(response_schema, 'schema'):
                schema = response_schema.schema()
            else:
                # Fallback: try to get schema from Pydantic BaseModel
                schema = response_schema.__pydantic_model__.schema() if hasattr(response_schema, '__pydantic_model__') else {}
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=schema
                )
            )
            
            # Parse JSON response and create schema instance
            import json
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            response_dict = json.loads(response_text)
            
            # Create instance of response_schema
            return response_schema(**response_dict)
            
        except Exception as e:
            logger.error(f"Error generating content with structured schema: {e}")
            # Return empty schema instance on error
            try:
                return response_schema(**{})
            except:
                # If schema requires fields, create with defaults
                return response_schema.model_construct(**{})
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content without structured schema.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text content
        """
        try:
            response = self.model.generate_content(prompt, **kwargs)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

