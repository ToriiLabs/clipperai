from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import logging

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
        logger.info("✅ Model loaded successfully!")
    return llm


def generate_with_reflection(user_message: str):
    """Streaming version"""
    try:
        yield "PHASE:thinking\n"

        system_prompt = "You are Clipper — a witty, direct, maximally truth-seeking AI inspired by Grok."

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        response = get_llm().invoke(messages)
        final_text = response.content.strip()

        yield "PHASE:reflecting\n"
        yield "PHASE:final\n"

        # Stream word by word
        for word in final_text.split():
            yield f"TOKEN:{word} \n"

    except Exception as e:
        logger.error(f"Model error: {str(e)}", exc_info=True)
        yield "PHASE:final\n"
        yield f"TOKEN:❌ Error: {str(e)}\n"
