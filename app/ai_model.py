# app/ai_model.py
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from .vector_memory import VectorMemory
from .models import Conversation, db

logger = logging.getLogger(__name__)

vector_memory = VectorMemory()

# Global LLM instance
llm = None

def get_llm():
    global llm
    if llm is None:
        logger.info("Initializing Ollama (qwen2.5:14b-q5_K_M) — first load may take 10-30s...")
        llm = ChatOllama(
            model="qwen2.5:14b-q5_K_M",
            temperature=0.75,
            num_ctx=32768,
            num_thread=32,           # Your 32 cores!
            top_p=0.9,
        )
        logger.info("Ollama ready!")
    return llm

def generate_response(user_message: str, session_id: str = "default") -> str:
    """Backward compatible non-streaming version (used by old /api/chat)"""
    try:
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        system_prompt = f"""You are ClipperAI — a sharp, creative, honest brainstorming partner.
Always prioritize the Memory clips below. Use them heavily when relevant."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory clips:\n{memory_context}\n\nQuestion: {user_message}")
        ]

        response = get_llm().invoke(messages)
        ai_response = response.content.strip()

        # Save to DB
        try:
            conv = Conversation(session_id=session_id, user_message=user_message, ai_response=ai_response)
            db.session.add(conv)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return ai_response

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return "Sorry, something went wrong with the model."
