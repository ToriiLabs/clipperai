# app/ai_model.py
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from .vector_memory import vector_memory
from .agent import agent   

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
            num_thread=12,
            top_p=0.95,
            # Removed deprecated options that were causing warnings
            # (mirostat, tfs_z, mirostat_eta, mirostat_tau)
        )
        logger.info("✅ Model loaded!")
    return llm

def generate_response(user_message: str) -> str:
    """Non-streaming version used by LangGraph agent (thinking + reflection)"""
    try:
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory."

        system_prompt = "You are Clipper — a witty, direct, maximally truth-seeking AI inspired by Grok."

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

        return final_response.content.strip()

    except Exception as e:
        logger.error(f"❌ MODEL ERROR: {str(e)}", exc_info=True)
        return f"Model error: {str(e)}"


def generate_with_reflection(user_message: str):
    """Streaming version that uses the full LangGraph agent"""
    try:
        # Use LangGraph agent for the agentic workflow
        result = agent.invoke({"messages": [user_message]})

        final_text = result["messages"][-1]   # final polished response from agent

        # Stream phases + tokens exactly as frontend expects
        yield "PHASE:thinking\n"
        yield "PHASE:reflecting\n"
        yield "PHASE:final\n"

        for word in final_text.split():
            yield f"TOKEN:{word} \n"

    except Exception as e:
        logger.error(f"❌ AGENT ERROR: {str(e)}", exc_info=True)
        yield "PHASE:error\n"
        yield f"TOKEN:Agent error: {str(e)}\n"
