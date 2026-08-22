from typing import List, Dict
from openai import AsyncOpenAI
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def generate_answer(query: str, context_chunks: List[Dict]) -> str:
    if not settings.LLM_API_KEY:
        logger.warning("No LLM API Key provided. Returning mock generation.")
        return f"[MOCK] Answer based on {len(context_chunks)} chunks for query: '{query}'"

    # We use OpenAI client. 
    # If the provider is 'anthropic', you could map it or use an OpenAI-compatible proxy (like litellm).
    # For now, standard OpenAI usage is assumed.
    try:
        client_kwargs = {"api_key": settings.LLM_API_KEY}
        if settings.LLM_BASE_URL:
            client_kwargs["base_url"] = settings.LLM_BASE_URL
        client = AsyncOpenAI(**client_kwargs)
        
        context_text = "\n\n".join([f"[{i+1}] {c['text']}" for i, c in enumerate(context_chunks)])
        
        prompt = f"""You are a helpful and precise assistant. 
Please answer the user's question using ONLY the provided context.
If you cannot answer the question using the context, simply say "I do not have enough information to answer this question."

Context:
{context_text}

Question:
{query}
"""

        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are VaaniRAG, an AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        return "An error occurred while generating the answer."
