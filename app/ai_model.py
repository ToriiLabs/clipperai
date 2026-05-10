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
        logger.info("=== LOADING AGENTIC QWEN2.5-14B (stable + tools) ===")
        llm = ChatOllama(
            model="qwen2.5:14b",
            temperature=0.75,
            num_ctx=16384,
            num_thread=12,
            top_p=0.9,
        )
        logger.info("✅ Agentic model loaded!")
    return llm

def calculate(expression: str) -> str:
    """Simple calculator tool"""
    try:
        return str(eval(expression))
    except:
        return "Invalid calculation"

def generate_with_reflection(user_message: str):
    """Agentic version: memory + tool use + reflection + streaming"""
    try:
        # 1. Search memory
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        # Agentic system prompt
        system_prompt = """You are Clipper — a witty, direct, maximally truth-seeking AI agent inspired by Grok.
You have access to memory and a calculator tool. Use tools when helpful.
Think step-by-step. Be clear and helpful."""

        # Initial agent thinking pass
        initial_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""Memory clips:\n{memory_context}

User query: {user_message}

Think step-by-step. If you need to calculate something, say CALCULATE: expression
Otherwise just reason and prepare your answer.""")
        ]
        initial_response = get_llm().invoke(initial_messages)

        # Check if calculator was requested
        content = initial_response.content
        if "CALCULATE:" in content:
            try:
                expr = content.split("CALCULATE:")[1].split("\n")[0].strip()
                result = calculate(expr)
                content += f"\n\nCalculator result: {result}"
            except:
                content += "\n\nCalculator failed."

        # Reflection & polishing pass
        reflection_prompt = f"""Review your previous response:
{content}

Critique it rigorously and output ONLY the polished final version."""

        final_response = get_llm().invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=reflection_prompt)
        ])

        final_text = final_response.content.strip()

        # Stream the final answer (Grok-style)
        for token in final_text.split():
            yield token + " "

    except Exception as e:
        logger.error(f"❌ AGENT ERROR: {str(e)}", exc_info=True)
        yield f"Agent error: {str(e)}"
