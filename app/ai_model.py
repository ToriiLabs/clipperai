from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from .vector_memory import vector_memory

logger = logging.getLogger(__name__)

llm = None

def get_llm():
    global llm
    if llm is None:
        logger.info("=== LOADING QWEN2.5-14B ===")
        llm = ChatOllama(
            model="qwen2.5:14b",
            temperature=0.85,
            num_ctx=16384,
            num_thread=8,
            top_p=0.95,
        )
        logger.info("Model loaded successfully!")
    return llm

def generate_with_reflection(user_message: str):
    """Streaming with full RAG context from vector DB"""
    try:
        yield "PHASE:thinking\n"

        # RAG retrieval
        context = "\n\n".join(vector_memory.search_memory(user_message, n_results=5))
        rag_prompt = f"Relevant knowledge from your documents:\n{context}\n\n" if context else ""

        system_prompt = f"""You are Clipper — a witty, direct, maximally truth-seeking AI inspired by Grok.
Use the provided document knowledge when relevant. Always be helpful and accurate.

{rag_prompt}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        response = get_llm().invoke(messages)
        final_text = response.content.strip()

        yield "PHASE:reflecting\n"
        yield "PHASE:final\n"

        for word in final_text.split():
            yield f"TOKEN:{word} \n"

    except Exception as e:
        logger.error(f"Model error: {str(e)}", exc_info=True)
        yield "PHASE:final\n"
        yield f"TOKEN:Error: {str(e)}\n"
