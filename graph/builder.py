"""Graph construction and workflow definition"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from graph.models import ChatbotState
from graph.nodes import *
from graph.routing import *


def create_healthcare_chatbot():
    """Create the healthcare chatbot following the diagram"""

    workflow = StateGraph(ChatbotState)

    # Add all nodes
    workflow.add_node("introduction", introduction_node)
    workflow.add_node("auth", auth_node)
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("list", list_node)
    workflow.add_node("confirm", confirm_node)
    workflow.add_node("cancel", cancel_node)

    # MODIFICATION: Smart entry with auth bypass
    # Instead of: workflow.add_edge(START, "introduction")
    # Use conditional routing for returning authenticated users
    workflow.add_conditional_edges(
        START,
        entry_point_routing,  # Use new routing function
        {"chatbot": "chatbot", "introduction": "introduction"},
    )

    # Following the diagram exactly:
    # Introduction -> Auth (conditional: if data collected)
    workflow.add_conditional_edges(
        "introduction", route_from_introduction, {"auth": "auth", END: END}
    )

    # Auth -> Chatbot OR End (conditional: if verified)
    workflow.add_conditional_edges(
        "auth", route_from_auth, {"chatbot": "chatbot", END: END}
    )

    # Chatbot -> List/Confirm/Cancel/End (conditional: based on intent)
    workflow.add_conditional_edges(
        "chatbot",
        route_from_chatbot,
        {"list": "list", "confirm": "confirm", "cancel": "cancel", END: END},
    )

    # All feature nodes -> End (simple edges)
    workflow.add_edge("list", END)
    workflow.add_edge("confirm", END)
    workflow.add_edge("cancel", END)

    # Compile with memory for thread persistence
    memory = InMemorySaver()
    return workflow.compile(checkpointer=memory)
