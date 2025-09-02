"""Routing logic for graph transitions"""

from graph.models import ChatbotState
from langgraph.graph import END


def route_from_introduction(state: ChatbotState) -> str:
    """Route from introduction based on whether user data was collected"""
    return "auth" if state.get("user_data") else END


def route_from_auth(state: ChatbotState) -> str:
    """Route from auth based on verification result"""
    return "chatbot" if state.get("user_verified") else END


def route_from_chatbot(state: ChatbotState) -> str:
    """Route from chatbot based on detected intent"""
    intent = state.get("intent", END)
    if intent in ["list", "confirm", "cancel"]:
        return intent
    return END


def entry_point_routing(state: ChatbotState) -> str:
    """Smart entry: skip intro/auth if user already verified"""
    if state.get("user_verified") and state.get("user_data", {}).get("user_id"):
        return "chatbot"  # Skip to chatbot if already authenticated
    return "introduction"  # Normal flow for new users
