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
        logger.info("=== LOADING AGENTIC QWEN2.5-14B (lighter & faster) ===")
        llm = ChatOllama(
            model="qwen2.5:14b",
            temperature=0.75,
            num_ctx=16384,
            num_thread=12,
            top_p=0.9,
        )
        logger.info("✅ Agentic model loaded!")
    return llm

def generate_with_reflection(user_message: str):
    """Light agentic version — uses memory + reflection, streams reliably"""
    try:
        # 1. Search memory (always available)
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        # 2. Strong agent-style system prompt
        system_prompt = """You are Clipper — a witty, direct, truth-seeking AI agent inspired by Grok.
You have access to your long-term memory. Use it when relevant.
Think step-by-step, be helpful, and give clear answers."""

        # 3. First pass (agent thinking)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory clips:\n{memory_context}\n\nUser: {user_message}\n\nThink step-by-step and plan your response.")
        ]
        initial = get_llm().invoke(messages)

        # 4. Reflection pass (polish the answer)
        reflection_prompt = f"""Review your previous response:
{initial.content}

Make it clearer, more concise, and more helpful. Output ONLY the final polished answer."""

        final = get_llm().invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=reflection_prompt)
        ])

        # 5. Stream the final answer (Grok-style)
        final_text = final.content.strip()
        for token in final_text.split():
            yield token + " "

    except Exception as e:
        logger.error(f"AGENT ERROR: {str(e)}", exc_info=True)
        yield f"Agent error: {str(e)}"
