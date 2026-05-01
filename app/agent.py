from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from .ai_model import generate_response

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

def call_llm(state: AgentState):
    last_message = state["messages"][-1]
    response = generate_response(last_message)
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("llm", call_llm)
workflow.set_entry_point("llm")
workflow.add_edge("llm", END)

agent = workflow.compile()
