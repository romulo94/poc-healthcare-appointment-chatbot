"""Graph construction for ReAct agent"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from graph.models import AgentState
from graph.nodes import agent_node, should_continue
from app.tools import verify_patient, get_appointments, update_appointment_status


def create_healthcare_chatbot():
    """Create ReAct agent for healthcare appointments"""

    workflow = StateGraph(AgentState)
    
    # Create ToolNode with all tools
    tools = [verify_patient, get_appointments, update_appointment_status]
    tool_node = ToolNode(tools)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # Add edges - ReAct pattern
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        }
    )
    workflow.add_edge("tools", "agent")  # Always return to agent after tools

    # Compile with memory
    memory = InMemorySaver()
    return workflow.compile(checkpointer=memory)