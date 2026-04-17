"""
Gemini Provider - Google Gemini API implementation

Uses the modern `google-genai` SDK (replacing the deprecated
`google-generativeai` package).
"""
import os
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types as genai_types

from .base_provider import BaseLLMProvider
from .retry import with_retries
from ..logger import setup_logger


logger = setup_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider (google-genai SDK)"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var
            model: Model name to use. If None, uses default model

        Raises:
            ValueError: If API key is not provided and not in environment
        """
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key must be provided or set in GOOGLE_API_KEY environment variable"
            )

        super().__init__(api_key=api_key, model=model or self.default_model)

        # New SDK uses an explicit Client object
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"Gemini provider initialized with model: {self.model}")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    @with_retries(max_attempts=4, base_delay=2.0, max_delay=60.0)
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate a response using Gemini API.

        Wrapped with retry logic for transient errors (429 rate limit,
        503 unavailable, 5xx service errors).

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            **kwargs: Additional Gemini-specific parameters

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails after all retry attempts
        """
        try:
            logger.debug(f"Calling Gemini API with {len(messages)} messages")

            # Flatten our messages list into a single prompt string
            # (Gemini doesn't natively use the same role-based format as Claude/OpenAI;
            # collapsing into a single user prompt is the simplest correct approach.)
            prompt = self._convert_messages_to_gemini_format(messages)

            # Generation config — note: types.GenerateContentConfig replaces the old
            # genai.types.GenerationConfig
            config = genai_types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )

            if response.text:
                return response.text

            raise Exception("No response received from Gemini")

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 2000,
        max_iterations: int = 8,
        tool_handler: Optional[callable] = None,
        **kwargs
    ) -> str:
        """
        Generate a response with tool calling support.

        Currently a passthrough to generate() — full tool-calling support
        in Gemini would require porting the tool definitions to the new
        SDK's `types.Tool` format. Not currently used by this app.
        """
        try:
            logger.debug(f"Calling Gemini API with tools, max_iterations={max_iterations}")
            return self.generate(messages, max_tokens=max_tokens, **kwargs)
        except Exception as e:
            logger.error(f"Gemini API error with tools: {str(e)}", exc_info=True)
            raise

    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert standard message format to a single Gemini prompt string.

        Args:
            messages: List of message dicts

        Returns:
            Formatted prompt string for Gemini
        """
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)
