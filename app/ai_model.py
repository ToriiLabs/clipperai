# app/ai_model.py
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from .vector_memory import VectorMemory
from .models import Conversation, db

logger = logging.getLogger(__name__)

vector_memory = VectorMemory()

llm = None

def get_llm():
    global llm
    if llm is None:
        logger.info("Loading Qwen2.5-32B (q5_K_M) — this may take 20-60 seconds on first run...")
        llm = ChatOllama(
            model="qwen2.5:32b-q5_K_M",
            temperature=0.7,
            num_ctx=32768,
            num_thread=32,           # Full use of your 32 cores
            top_p=0.9,
        )
        logger.info("Qwen2.5-32B ready!")
    return llm

async def generate_with_reflection(user_message: str, session_id: str = "default"):
    """High-intelligence agent with explicit reflection step"""
    try:
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        system_prompt = """You are Clipper — a precise, creative, and rigorously analytical thinking partner.
You always reference relevant Memory clips when they add value. Think deeply, critique your own ideas, and deliver the highest-quality response possible."""

        # Step 1: Deep initial reasoning
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory clips:\n{memory_context}\n\nUser query: {user_message}\n\nThink step-by-step and produce your best initial response.")
        ]

        initial_response = await get_llm().ainvoke(initial_messages)
        initial_text = initial_response.content.strip()

        # Step 2: Self-reflection & refinement (this is what dramatically improves quality)
        reflection_prompt = f"""Review your initial response:
{initial_text}

Critique it rigorously:
- How well did you use the memory clips?
- Is the reasoning creative and non-obvious?
- Is it clear, concise, and maximally useful?
- What one improvement would make it significantly better?

Then output only the polished final response."""

        reflection_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=reflection_prompt)
        ]

        final_response = await get_llm().ainvoke(reflection_messages)
        final_text = final_response.content.strip()

        # Save conversation
        try:
            conv = Conversation(session_id=session_id, user_message=user_message, ai_response=final_text)
            db.session.add(conv)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return final_text

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return "Sorry, something went wrong with the model."
