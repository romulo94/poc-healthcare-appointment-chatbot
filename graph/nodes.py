"""Graph nodes for ReAct agent"""

import os
from typing import Dict, Any, Literal
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from graph.models import AgentState
from app.tools import verify_patient, get_appointments, update_appointment_status
from dotenv import load_dotenv

load_dotenv()


def agent_node(state: AgentState) -> Dict[str, Any]:
    """Main agent node with all tools bound"""
    
    # Initialize LLM
    llm = ChatAnthropic(
        model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=0.1,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    
    # Bind all tools
    tools = [verify_patient, get_appointments, update_appointment_status]
    llm_with_tools = llm.bind_tools(tools)
    
    # System prompt
    system_prompt = """You are a healthcare appointment assistant. 

Your workflow:
1. If the user is not verified yet, collect their information (full name, phone number, date of birth) and use verify_patient tool
2. Once verified (tool confirms with patient ID), help them manage appointments:
   - Use get_appointments to list appointments (you'll need the patient_id from verification)
   - Use update_appointment_status to confirm/cancel appointments

When user says 'next appointment', it means the EARLIEST upcoming appointment.
Be conversational and helpful."""
    
    # Build conversation with system prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Invoke LLM
    response = llm_with_tools.invoke(messages)
    
    # Prepare result
    result = {"messages": [response]}
    
    # Check if verification happened in recent messages
    import re
    for msg in state.get("messages", [])[-5:]:
        if hasattr(msg, '__class__') and msg.__class__.__name__ == 'ToolMessage':
            content = str(msg.content)
            if "Patient verified successfully" in content and "ID:" in content:
                # Extract patient ID
                match = re.search(r'ID:\s*(\d+)', content)
                if match:
                    result["user_verified"] = True
                    # Extract name too
                    name_match = re.search(r'Name:\s*([^,]+)', content)
                    result["user_data"] = {
                        "user_id": int(match.group(1)),
                        "full_name": name_match.group(1) if name_match else ""
                    }
                    break
    
    return result


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """Determine whether to continue to tools or end"""
    
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    # Check if there are tool calls to execute
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    
    return "end"