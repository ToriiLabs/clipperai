# app/ai_model.py
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
import logging
from .vector_memory import VectorMemory

logger = logging.getLogger(__name__)

vector_memory = VectorMemory()
llm = None

# ====================== TOOLS ======================
@tool
def search_memory(query: str) -> str:
    """Search the vector memory for relevant past conversation clips."""
    clips = vector_memory.search_memory(query, n_results=8)
    return "\n\n".join(clips) if clips else "No relevant memory found."

@tool
def calculator(expression: str) -> str:
    """Perform simple math calculations. Example: '15 * 0.2 + 81**0.5'"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

tools = [search_memory, calculator]

# ====================== LLM ======================
def get_llm():
    global llm
    if llm is None:
        logger.info("=== LOADING FULLY AGENTIC QWEN2.5-14B ===")
        llm = ChatOllama(
            model="qwen2.5:14b",
            temperature=0.75,
            num_ctx=16384,
            num_thread=12,
            top_p=0.95,
        )
        logger.info("✅ Qwen2.5-14B Agent loaded!")
    return llm

# ====================== AGENTIC GENERATOR ======================
def generate_with_reflection(user_message: str):
    """Fully agentic ReAct loop with tools + final reflection (streams like Grok)"""
    try:
        # Create the agent
        agent = create_react_agent(
            llm=get_llm(),
            tools=tools,
            prompt=PromptTemplate.from_template(
                """You are Clipper — a witty, direct, maximally truth-seeking AI agent inspired by Grok from xAI.

You have access to the following tools:
{tools}

Use them when needed. Think step by step.

{agent_scratchpad}

User: {input}
Thought: {{thought}}
Action: {{action}}
Action Input: {{action_input}}
Observation: {{observation}}
Final Answer: """
            )
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,          # shows thinking in terminal
            max_iterations=10,
            handle_parsing_errors=True
        )

        # Run the agent
        result = agent_executor.invoke({"input": user_message})

        # Final reflection pass (makes answer cleaner and more Grok-like)
        reflection_prompt = f"""Review this answer:
{result['output']}

Make it more concise, witty, and helpful. Output ONLY the final polished version."""

        polished = get_llm().invoke([HumanMessage(content=reflection_prompt)])

        # Stream the final polished answer (slow, natural Grok-style)
        final_text = polished.content.strip()
        for token in final_text.split():
            yield token + " "

    except Exception as e:
        logger.error(f"AGENT ERROR: {str(e)}", exc_info=True)
        yield f"Agent error: {str(e)}"
