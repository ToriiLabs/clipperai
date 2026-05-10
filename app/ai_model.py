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
        logger.info("=== LOADING STABLE QWEN2.5-14B ===")
        llm = ChatOllama(
            model="qwen2.5:14b",
            temperature=0.85,
            num_ctx=16384,
            num_thread=12,
            top_p=0.95,
        )
        logger.info("✅ Model loaded!")
    return llm

def generate_with_reflection(user_message: str):
    """Stable version - memory + thinking + reflection + smooth streaming"""
    try:
        # 1. Get relevant memory
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        system_prompt = """You are Clipper — a witty, direct, maximally truth-seeking AI inspired by Grok."""

        # Thinking phase
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory clips:\n{memory_context}\n\nUser: {user_message}\n\nThink step-by-step and show your reasoning.")
        ]
        initial_response = get_llm().invoke(initial_messages)

        # Reflection phase
        reflection_prompt = f"""Review your initial thinking:
{initial_response.content}

Critique it rigorously and output ONLY the polished final version."""

        reflection_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=reflection_prompt)
        ]
        final_response = get_llm().invoke(reflection_messages)

        final_text = final_response.content.strip()

        # Stream the final answer (Grok-style)
        for token in final_text.split():
            yield token + " "

    except Exception as e:
        logger.error(f"❌ MODEL ERROR: {str(e)}", exc_info=True)
        yield f"Model error: {str(e)}"
