"""Data models and state definitions"""

from typing import TypedDict, Annotated, Optional
from pydantic import BaseModel, field_validator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class UserData(BaseModel):
    """Simple user data model"""

    full_name: str
    phone_number: str
    date_of_birth: str

    @field_validator("phone_number")
    def format_phone(cls, v):
        digits = "".join(filter(str.isdigit, v))
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        return v  # Return as-is if not 10 digits


class UserDataExtraction(BaseModel):
    """Structured output for user data extraction"""

    data_complete: bool
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    message: str  # Natural response to user


class IntentDecision(BaseModel):
    """Structured output for intent detection"""

    intent: str  # list, confirm, cancel, end
    message: str  # Natural response to user


class CancellationDecision(BaseModel):
    """Structured output for cancellation decisions"""

    cancel_appointment: bool
    appointment_id: Optional[int] = None
    message: str  # Natural response to user


class ConfirmationDecision(BaseModel):
    """Structured output for confirmation decisions"""

    confirm_appointment: bool
    appointment_id: Optional[int] = None
    message: str  # Natural response to user


class GeneralResponse(BaseModel):
    """Structured output for general conversational responses"""

    message: str  # Natural response to user


class ChatbotState(TypedDict):
    """Simple state for healthcare chatbot"""

    messages: Annotated[list[BaseMessage], add_messages]
    user_verified: bool
    user_data: dict
    available_appointments: list[dict]
    intent: str
