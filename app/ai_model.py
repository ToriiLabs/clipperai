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
        logger.info("Loading Qwen2.5-32B — first load may take 20-60 seconds...")
        llm = ChatOllama(
            model="qwen2.5:32b",
            temperature=0.7,
            num_ctx=32768,
            num_thread=32,
            top_p=0.9,
        )
        logger.info("Qwen2.5-32B ready!")
    return llm

async def generate_with_reflection(user_message: str, session_id: str = "default"):
    try:
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        system_prompt = "You are Clipper — a precise, creative, and rigorously analytical thinking partner."

        # Phase 1: Thinking
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory clips:\n{memory_context}\n\nUser query: {user_message}\n\nThink step-by-step and produce your best initial response.")
        ]
        initial_response = await get_llm().ainvoke(initial_messages)

        # Phase 2: Reflecting
        reflection_prompt = f"""Review your initial response:
{initial_response.content}

Critique it rigorously and output only the polished final version."""

        reflection_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=reflection_prompt)
        ]
        final_response = await get_llm().ainvoke(reflection_messages)

        # Save final answer
        try:
            conv = Conversation(session_id=session_id, user_message=user_message, ai_response=final_response.content.strip())
            db.session.add(conv)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return final_response.content.strip()

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return "Sorry, something went wrong with the model."
