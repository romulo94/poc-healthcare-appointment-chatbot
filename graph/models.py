"""Data models and state definitions"""

from typing import TypedDict, Annotated, Optional
from pydantic import BaseModel, field_validator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime


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

    @field_validator("date_of_birth", mode='before')
    def normalize_date(cls, v):
        """Normaliza data para formato YYYY-MM-DD tentando múltiplos formatos"""
        if not v:
            return v
            
        # Lista de formatos comuns para tentar
        date_formats = [
            "%Y-%m-%d",  # 1985-03-15 (formato alvo)
            "%d/%m/%Y",  # 15/03/1985 (BR)
            "%m/%d/%Y",  # 03/15/1985 (US)
            "%d-%m-%Y",  # 15-03-1985
            "%d.%m.%Y",  # 15.03.1985
            "%Y/%m/%d",  # 1985/03/15
            "%d %m %Y",  # 15 03 1985
            "%d-%m-%y",  # 15-03-85 (ano com 2 dígitos)
            "%d/%m/%y",  # 15/03/85
            "%m/%d/%y",  # 03/15/85
        ]
        
        # Tentar cada formato
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(v).strip(), fmt)
                # Retornar no formato padrão YYYY-MM-DD
                print(f"DEBUG: Parsed date: {parsed_date}")
                return parsed_date.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        
        # Se nenhum formato funcionou, retornar original
        # A LLM pode ter extraído já no formato correto
        return v


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
