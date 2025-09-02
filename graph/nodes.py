"""Graph nodes for chatbot workflow"""

import os
from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from graph.models import *
from app.tools import *
from dotenv import load_dotenv

load_dotenv()


def introduction_node(state: ChatbotState) -> Dict[str, Any]:
    """Introduction node - LLM naturally greets and collects data using structured output"""

    messages = state["messages"]
    llm = ChatAnthropic(
        model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=0.3,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Configure LLM with structured output
    llm_with_structured_output = llm.with_structured_output(UserDataExtraction)

    system_prompt = """You are a friendly healthcare appointment assistant. Your role is to:
1. Greet users warmly and professionally
2. Collect their personal information: full name, phone number, and date of birth (YYYY-MM-DD format)
3. Be conversational and helpful

Analyze the conversation and determine if the user has provided all required information (full_name, phone_number, date_of_birth).

If all information is complete:
- Set data_complete to true
- Extract the information into the respective fields
- Provide a friendly message acknowledging receipt

If information is missing:
- Set data_complete to false
- Set missing fields to null
- Provide a natural message asking for the missing information"""

    try:
        conversation = [SystemMessage(content=system_prompt)] + messages
        extraction_result = llm_with_structured_output.invoke(conversation)

        if extraction_result.data_complete:
            # Validate and create UserData
            try:
                user_data = UserData(
                    full_name=extraction_result.full_name,
                    phone_number=extraction_result.phone_number,
                    date_of_birth=extraction_result.date_of_birth,
                )
                return {
                    "user_data": user_data.model_dump(),
                    "messages": [AIMessage(content=extraction_result.message)],
                }
            except Exception as e:
                print(f"DEBUG: Validation error: {e}")
                # Generate error response using LLM
                error_llm = llm.with_structured_output(GeneralResponse)
                error_response = error_llm.invoke(
                    [
                        SystemMessage(
                            content="You are a healthcare assistant. The user provided information but it's not in the correct format. Ask them politely to provide their full name, a 10-digit phone number, and date of birth in YYYY-MM-DD format."
                        )
                    ]
                )
                return {"messages": [AIMessage(content=error_response.message)]}
        else:
            return {"messages": [AIMessage(content=extraction_result.message)]}

    except Exception as e:
        print(f"DEBUG: LLM error in introduction_node: {e}")
        # Generate fallback response using LLM
        fallback_llm = llm.with_structured_output(GeneralResponse)
        try:
            fallback_response = fallback_llm.invoke(
                [
                    SystemMessage(
                        content="You are a healthcare assistant experiencing technical difficulties. Apologize politely and ask the user to try again or provide their information."
                    )
                ]
            )
            return {"messages": [AIMessage(content=fallback_response.message)]}
        except:
            return {
                "messages": [
                    AIMessage(
                        content="Hello! I'm your healthcare assistant. How can I help you today?"
                    )
                ]
            }


def auth_node(state: ChatbotState) -> Dict[str, Any]:
    """Auth node - LLM handles verification response"""

    user_data = state.get("user_data", {})
    if not user_data:
        # Generate response using LLM
        llm = ChatAnthropic(
            model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
            temperature=0.3,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        response_llm = llm.with_structured_output(GeneralResponse)
        response = response_llm.invoke(
            [
                SystemMessage(
                    content="You are a healthcare assistant. The user needs to provide their personal information (name, phone, date of birth) before you can help them. Ask for this information politely."
                )
            ]
        )
        return {"messages": [AIMessage(content=response.message)]}

    # Verify against database
    verification_result = verify_patient.invoke(user_data)

    llm = ChatAnthropic(
        model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=0.3,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    if verification_result["verified"]:
        system_prompt = f"""You are a healthcare assistant. The user {verification_result['name']} has been successfully verified in our system. Welcome them back warmly and ask how you can help them with their appointments today."""

        try:
            response = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(
                        content="Please welcome me back and ask how you can help."
                    ),
                ]
            )
            return {
                "user_verified": True,
                "user_data": {**user_data, "user_id": verification_result["user_id"]},
                "messages": [response],
            }
        except Exception as e:
            print(f"DEBUG: LLM error in auth_node: {e}")
            # Generate fallback welcome using LLM
            fallback_llm = llm.with_structured_output(GeneralResponse)
            try:
                welcome_response = fallback_llm.invoke(
                    [
                        SystemMessage(
                            content="You are a healthcare assistant. Welcome a verified patient back warmly and ask how you can help them with their appointments."
                        )
                    ]
                )
                return {
                    "user_verified": True,
                    "user_data": {
                        **user_data,
                        "user_id": verification_result["user_id"],
                    },
                    "messages": [AIMessage(content=welcome_response.message)],
                }
            except:
                return {
                    "user_verified": True,
                    "user_data": {
                        **user_data,
                        "user_id": verification_result["user_id"],
                    },
                    "messages": [
                        AIMessage(
                            content="Welcome back! How can I help you with your appointments today?"
                        )
                    ],
                }
    else:
        system_prompt = """You are a healthcare assistant. The user's information could not be verified in our system. Politely let them know that you couldn't find their information and suggest they contact the office for assistance."""

        try:
            response = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(
                        content="I tried to verify my information but it wasn't found."
                    ),
                ]
            )
            return {"user_verified": False, "messages": [response]}
        except Exception as e:
            print(f"DEBUG: LLM error in auth_node: {e}")
            # Generate fallback using LLM
            fallback_llm = llm.with_structured_output(GeneralResponse)
            try:
                error_response = fallback_llm.invoke(
                    [
                        SystemMessage(
                            content="You are a healthcare assistant. You couldn't verify the user's information in the system. Politely suggest they contact the office for assistance."
                        )
                    ]
                )
                return {
                    "user_verified": False,
                    "messages": [AIMessage(content=error_response.message)],
                }
            except:
                return {
                    "user_verified": False,
                    "messages": [
                        AIMessage(
                            content="I couldn't verify your information. Please contact our office."
                        )
                    ],
                }


def chatbot_node(state: ChatbotState) -> Dict[str, Any]:
    """Main chatbot - LLM detects intent using structured output"""

    if not state.get("user_verified"):
        # Generate response using LLM
        llm = ChatAnthropic(
            model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
            temperature=0.1,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        response_llm = llm.with_structured_output(GeneralResponse)
        response = response_llm.invoke(
            [
                SystemMessage(
                    content="You are a healthcare assistant. The user needs to verify their identity before accessing appointment information. Ask them politely to provide their verification details."
                )
            ]
        )
        return {"messages": [AIMessage(content=response.message)]}

    messages = state["messages"]
    llm = ChatAnthropic(
        model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=0.1,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Configure LLM with structured output
    llm_with_structured_output = llm.with_structured_output(IntentDecision)

    system_prompt = """You are a healthcare appointment assistant. Based on the user's message and conversation context, determine their intent and provide a natural response.

Available intents:
- "list" - if they want to see/list their appointments
- "confirm" - if they want to confirm an appointment  
- "cancel" - if they want to cancel an appointment
- "end" - if they want to end the conversation or say goodbye

If their intent is unclear, use "end" and ask for clarification in your message.

Provide a natural, helpful response in the message field."""

    try:
        conversation = [SystemMessage(content=system_prompt)] + messages[
            -4:
        ]  # Recent context
        decision = llm_with_structured_output.invoke(conversation)

        return {
            "intent": decision.intent,
            "messages": [AIMessage(content=decision.message)],
        }

    except Exception as e:
        print(f"DEBUG: LLM error in chatbot_node: {e}")
        # Generate fallback using LLM
        fallback_llm = llm.with_structured_output(GeneralResponse)
        try:
            fallback_response = fallback_llm.invoke(
                [
                    SystemMessage(
                        content="You are a healthcare assistant. Ask the user what they'd like to do with their appointments - list, confirm, or cancel them."
                    )
                ]
            )
            return {
                "intent": "end",
                "messages": [AIMessage(content=fallback_response.message)],
            }
        except:
            return {
                "intent": "end",
                "messages": [
                    AIMessage(
                        content="I can help you list, confirm, or cancel appointments. What would you like to do?"
                    )
                ],
            }


def list_node(state: ChatbotState) -> Dict[str, Any]:
    """List appointments with LLM response"""

    user_data = state["user_data"]
    appointments = get_appointments.invoke({"patient_id": user_data["user_id"]})

    llm = ChatAnthropic(
        model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=0.3,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    if not appointments:
        system_prompt = "You are a healthcare assistant. The user has no scheduled appointments. Let them know this in a friendly way."
    else:
        apt_info = "\\n".join(
            [
                f"📅 {apt['type']} with Dr. {apt['doctor']}\\n   📍 {apt['date']} at {apt['time']}\\n   📊 Status: {apt['status'].title()}\\n"
                for apt in appointments
            ]
        )
        system_prompt = f"""You are a healthcare assistant. Present appointments clearly and professionally.

IMPORTANT formatting instructions:
- Use clear visual separation between each appointment
- Display ALL details: type, doctor, date, time, and status
- Keep formatting consistent throughout your response
- Make the list easy to read and understand

Appointment data to present:
{apt_info}

After listing the appointments, ask if they would like to confirm or cancel any specific appointment, mentioning they can reference by doctor name or appointment type."""

    try:
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Please show me my appointments."),
            ]
        )
        return {"available_appointments": appointments, "messages": [response]}
    except Exception as e:
        print(f"DEBUG: LLM error in list_node: {e}")
        if appointments:
            apt_text = "\\n".join(
                [
                    f"📅 {apt['type']} with Dr. {apt['doctor']}\\n   📍 {apt['date']} at {apt['time']}\\n   📊 Status: {apt['status'].title()}\\n"
                    for apt in appointments
                ]
            )
            return {
                "available_appointments": appointments,
                "messages": [
                    AIMessage(content=f"Here are your appointments:\\n{apt_text}")
                ],
            }
        else:
            # Generate "no appointments" response using LLM
            no_apt_llm = llm.with_structured_output(GeneralResponse)
            no_apt_response = no_apt_llm.invoke(
                [
                    SystemMessage(
                        content="You are a healthcare assistant. The user has no scheduled appointments. Let them know this in a friendly way and offer to help them schedule one."
                    )
                ]
            )
            return {"messages": [AIMessage(content=no_apt_response.message)]}


def confirm_node(state: ChatbotState) -> Dict[str, Any]:
    """Confirm appointments - uses shared memory and conversation context"""

    # Use appointments from shared state (should be available from previous list_node or fetch fresh)
    appointments = state.get("available_appointments", [])
    if not appointments:
        # If not in state, get from database using user data from shared state
        user_data = state.get("user_data", {})
        if user_data.get("user_id"):
            appointments = get_appointments.invoke({"patient_id": user_data["user_id"]})

    if not appointments:
        # Generate "no appointments to confirm" response using LLM
        llm = ChatAnthropic(
            model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
            temperature=0.1,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        no_confirm_llm = llm.with_structured_output(GeneralResponse)
        no_confirm_response = no_confirm_llm.invoke(
            [
                SystemMessage(
                    content="You are a healthcare assistant. The user doesn't have any appointments to confirm. Let them know this politely and offer to help them schedule an appointment."
                )
            ]
        )
        return {"messages": [AIMessage(content=no_confirm_response.message)]}

    # Use full conversation history from shared state
    messages = state.get("messages", [])

    llm = ChatAnthropic(
        model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=0.1,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Configure LLM with structured output
    llm_with_structured_output = llm.with_structured_output(ConfirmationDecision)

    # Provide appointments context to Claude
    apt_info = "\\n".join(
        [
            f"ID {apt['id']}: {apt['type']} with {apt['doctor']} on {apt['date']} at {apt['time']} (Status: {apt['status']})"
            for apt in appointments
        ]
    )

    system_prompt = f"""You are a healthcare appointment confirmation assistant. Based on the conversation history, determine if the user wants to confirm a specific appointment and which one.

Available appointments:
{apt_info}

Your task:
1. Analyze the conversation to understand which appointment they want to confirm
2. If you can identify a specific appointment, set confirm_appointment to true and provide the appointment_id
3. If unclear, set confirm_appointment to false and ask for clarification in the message

Provide a natural, helpful message in all cases."""

    try:
        # Pass full conversation context so Claude can understand the request in context
        conversation = [SystemMessage(content=system_prompt)] + messages[
            -6:
        ]  # Include recent conversation
        decision = llm_with_structured_output.invoke(conversation)

        if decision.confirm_appointment and decision.appointment_id:
            # Find the appointment in shared state
            apt_to_confirm = next(
                (apt for apt in appointments if apt["id"] == decision.appointment_id),
                None,
            )

            if apt_to_confirm and apt_to_confirm["status"] != "confirmed":
                # Actually confirm the appointment in database
                update_appointment_status.invoke(
                    {"appointment_id": decision.appointment_id, "status": "confirmed"}
                )

                # Update the appointment in shared state for future nodes
                updated_appointments = []
                for apt in appointments:
                    if apt["id"] == decision.appointment_id:
                        apt_copy = apt.copy()
                        apt_copy["status"] = "confirmed"
                        updated_appointments.append(apt_copy)
                    else:
                        updated_appointments.append(apt)

                # Generate confirmation using Claude with conversation context
                confirm_prompt = f"""You are a healthcare assistant. You have successfully confirmed the user's {apt_to_confirm['type']} appointment with {apt_to_confirm['doctor']} on {apt_to_confirm['date']} at {apt_to_confirm['time']}. 
                
Provide a friendly confirmation message."""

                try:
                    confirm_response = llm.invoke(
                        [
                            SystemMessage(content=confirm_prompt),
                            HumanMessage(content="Please confirm the confirmation."),
                        ]
                    )
                    return {
                        "messages": [confirm_response],
                        "available_appointments": updated_appointments,  # Update shared state
                    }
                except Exception:
                    return {
                        "messages": [
                            AIMessage(
                                content=f"✅ Confirmed: {apt_to_confirm['type']} with {apt_to_confirm['doctor']} on {apt_to_confirm['date']}"
                            )
                        ],
                        "available_appointments": updated_appointments,
                    }
            elif apt_to_confirm and apt_to_confirm["status"] == "confirmed":
                return {
                    "messages": [
                        AIMessage(
                            content=decision.message
                            + " This appointment is already confirmed."
                        )
                    ]
                }
            else:
                return {
                    "messages": [
                        AIMessage(
                            content="Sorry, I couldn't find that appointment to confirm."
                        )
                    ]
                }
        else:
            # Claude couldn't identify which appointment to confirm
            return {"messages": [AIMessage(content=decision.message)]}

    except Exception as e:
        print(f"DEBUG: LLM error in confirm_node: {e}")
        return {
            "messages": [
                AIMessage(
                    content="I'm having trouble processing your confirmation request. Could you please specify which appointment you'd like to confirm?"
                )
            ]
        }


def cancel_node(state: ChatbotState) -> Dict[str, Any]:
    """Cancel appointments - uses shared memory and conversation context"""

    # Use appointments from shared state (should be available from previous list_node or fetch fresh)
    appointments = state.get("available_appointments", [])
    if not appointments:
        # If not in state, get from database using user data from shared state
        user_data = state.get("user_data", {})
        if user_data.get("user_id"):
            appointments = get_appointments.invoke({"patient_id": user_data["user_id"]})

    if not appointments:
        # Generate "no appointments to cancel" response using LLM
        llm = ChatAnthropic(
            model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
            temperature=0.1,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        no_cancel_llm = llm.with_structured_output(GeneralResponse)
        no_cancel_response = no_cancel_llm.invoke(
            [
                SystemMessage(
                    content="You are a healthcare assistant. The user doesn't have any appointments to cancel. Let them know this politely and offer to help them schedule an appointment."
                )
            ]
        )
        return {"messages": [AIMessage(content=no_cancel_response.message)]}

    # Use full conversation history from shared state
    messages = state.get("messages", [])

    llm = ChatAnthropic(
        model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=0.1,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Configure LLM with structured output
    llm_with_structured_output = llm.with_structured_output(CancellationDecision)

    # Provide appointments context to Claude
    apt_info = "\\n".join(
        [
            f"ID {apt['id']}: {apt['type']} with {apt['doctor']} on {apt['date']} at {apt['time']} (Status: {apt['status']})"
            for apt in appointments
        ]
    )

    system_prompt = f"""You are a healthcare appointment cancellation assistant. Based on the conversation history, determine if the user wants to cancel a specific appointment and which one.

Available appointments:
{apt_info}

Your task:
1. Analyze the conversation to understand which appointment they want to cancel
2. If you can identify a specific appointment, set cancel_appointment to true and provide the appointment_id
3. If unclear, set cancel_appointment to false and ask for clarification in the message

Provide a natural, helpful message in all cases."""

    try:
        # Pass full conversation context so Claude can understand the request in context
        conversation = [SystemMessage(content=system_prompt)] + messages[
            -6:
        ]  # Include recent conversation
        decision = llm_with_structured_output.invoke(conversation)

        if decision.cancel_appointment and decision.appointment_id:
            # Find the appointment in shared state
            apt_to_cancel = next(
                (apt for apt in appointments if apt["id"] == decision.appointment_id),
                None,
            )

            if apt_to_cancel and apt_to_cancel["status"] != "cancelled":
                # Actually cancel the appointment in database
                update_appointment_status.invoke(
                    {"appointment_id": decision.appointment_id, "status": "cancelled"}
                )

                # Update the appointment in shared state for future nodes
                updated_appointments = []
                for apt in appointments:
                    if apt["id"] == decision.appointment_id:
                        apt_copy = apt.copy()
                        apt_copy["status"] = "cancelled"
                        updated_appointments.append(apt_copy)
                    else:
                        updated_appointments.append(apt)

                # Generate confirmation using Claude with conversation context
                confirm_prompt = f"""You are a healthcare assistant. You have successfully cancelled the user's {apt_to_cancel['type']} appointment with {apt_to_cancel['doctor']} on {apt_to_cancel['date']} at {apt_to_cancel['time']}. 
                
Provide a friendly confirmation message."""

                try:
                    confirm_response = llm.invoke(
                        [
                            SystemMessage(content=confirm_prompt),
                            HumanMessage(content="Please confirm the cancellation."),
                        ]
                    )
                    return {
                        "messages": [confirm_response],
                        "available_appointments": updated_appointments,  # Update shared state
                    }
                except Exception:
                    return {
                        "messages": [
                            AIMessage(
                                content=f"✅ Your {apt_to_cancel['type']} appointment with {apt_to_cancel['doctor']} on {apt_to_cancel['date']} has been successfully cancelled."
                            )
                        ],
                        "available_appointments": updated_appointments,  # Update shared state
                    }
            elif apt_to_cancel and apt_to_cancel["status"] == "cancelled":
                # Generate "already cancelled" response using LLM
                already_cancelled_llm = llm.with_structured_output(GeneralResponse)
                already_cancelled_response = already_cancelled_llm.invoke(
                    [
                        SystemMessage(
                            content="You are a healthcare assistant. The user wants to cancel an appointment that is already cancelled. Let them know this politely."
                        )
                    ]
                )
                return {
                    "messages": [AIMessage(content=already_cancelled_response.message)]
                }
            else:
                # Generate "appointment not found" response using LLM
                not_found_llm = llm.with_structured_output(GeneralResponse)
                not_found_response = not_found_llm.invoke(
                    [
                        SystemMessage(
                            content="You are a healthcare assistant. You couldn't find the appointment the user wants to cancel. Ask them to check and try again politely."
                        )
                    ]
                )
                return {"messages": [AIMessage(content=not_found_response.message)]}
        else:
            # No specific cancellation identified, return Claude's response asking for clarification
            return {"messages": [AIMessage(content=decision.message)]}

    except Exception as e:
        print(f"DEBUG: LLM error in cancel_node: {e}")
        # Generate fallback using LLM
        try:
            fallback_llm = llm.with_structured_output(GeneralResponse)
            fallback_response = fallback_llm.invoke(
                [
                    SystemMessage(
                        content="You are a healthcare assistant experiencing technical difficulties with cancellation. Ask the user which appointment they'd like to cancel."
                    )
                ]
            )
            return {"messages": [AIMessage(content=fallback_response.message)]}
        except:
            return {
                "messages": [
                    AIMessage(
                        content="I can help you cancel an appointment. Which one would you like to cancel?"
                    )
                ]
            }
