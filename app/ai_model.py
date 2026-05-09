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
        logger.info("=== LOADING QWEN2.5-14B (Hokusai Wave Thinking) ===")
        llm = ChatOllama(
            model="qwen2.5:14b",
            temperature=0.85,
            num_ctx=16384,
            num_thread=12,
            top_p=0.95,
        )
        logger.info("✅ Qwen2.5-14B loaded!")
    return llm

def generate_with_reflection(user_message: str):
    """Streams thinking process with Hokusai wave phases"""
    try:
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        system_prompt = """You are Clipper — a witty, direct, maximally truth-seeking AI inspired by Grok."""

        # PHASE 1: THINKING
        yield "PHASE:THINKING"
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory clips:\n{memory_context}\n\nUser: {user_message}\n\nThink step-by-step and show your reasoning.")
        ]
        initial_response = get_llm().invoke(initial_messages)
        for word in initial_response.content.strip().split():
            yield f"THINKING:{word} "

        # PHASE 2: REFLECTING
        yield "PHASE:REFLECTING"
        reflection_prompt = f"""Review your initial thinking:
{initial_response.content}

Critique it rigorously and output ONLY the polished final version."""
        
        reflection_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=reflection_prompt)
        ]
        final_response = get_llm().invoke(reflection_messages)
        final_text = final_response.content.strip()

        # PHASE 3: FINAL ANSWER (smooth character streaming)
        yield "PHASE:FINAL"
        for char in final_text:
            yield f"FINAL:{char}"

    except Exception as e:
        logger.error(f"❌ MODEL ERROR: {str(e)}", exc_info=True)
        yield f"PHASE:ERROR\nModel error: {str(e)}"
