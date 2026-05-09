# app/ai_model.py
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from .vector_memory import VectorMemory

logger = logging.getLogger(__name__)

vector_memory = VectorMemory()
llm = None

def get_llm():
    global llm
    if llm is None:
        logger.info("=== LOADING QWEN2.5-14B (Grok-style streaming) ===")
        llm = ChatOllama(
            model="qwen2.5:14b",
            temperature=0.85,      # more personality & creativity
            num_ctx=16384,         # balanced for Codespaces
            num_thread=12,
            top_p=0.95,
        )
        logger.info("✅ Qwen2.5-14B loaded for streaming!")
    return llm

def generate_with_reflection(user_message: str):
    """Grok-style streaming generator with your reflection logic"""
    try:
        # Get relevant memory (exactly as you had)
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        # Grok-inspired system prompt
        system_prompt = """You are Clipper — a witty, direct, maximally truth-seeking AI inspired by Grok from xAI.
You are helpful, concise when possible, occasionally sarcastic or fun, and always clear.
Never be overly formal. Think like Grok."""

        # === Thinking phase ===
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory clips:\n{memory_context}\n\nUser: {user_message}\n\nThink step-by-step and produce your best initial response.")
        ]
        initial_response = get_llm().invoke(initial_messages)

        # === Reflection phase ===
        reflection_prompt = f"""Review your initial response:
{initial_response.content}

Critique it rigorously and output ONLY the polished final version."""

        reflection_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=reflection_prompt)
        ]
        final_response = get_llm().invoke(reflection_messages)

        final_text = final_response.content.strip()

        # === Stream like Grok (token by token) ===
        for token in final_text.split():
            yield token + " "

    except Exception as e:
        logger.error(f"❌ MODEL ERROR: {str(e)}", exc_info=True)
        yield f"Model error: {str(e)}"
