"""Main CLI entry point for Healthcare Chatbot"""

from graph.builder import create_healthcare_chatbot
from langchain_core.messages import HumanMessage
import uuid
import sys


def generate_diagram():
    """Generate and save the chatbot workflow diagram"""
    print("🎨 Generating Healthcare Chatbot Diagram...")

    app = create_healthcare_chatbot()

    try:
        png_data = app.get_graph().draw_mermaid_png()

        with open("chatbot_diagram.png", "wb") as f:
            f.write(png_data)

        print("✅ Diagram saved as 'chatbot_diagram.png'")
        print("📊 Shows complete conversation flow with auth bypass feature")

    except Exception as e:
        print(f"❌ Error generating diagram: {e}")


def start_chat():
    """Start interactive chat session"""
    print("🏥 Healthcare Appointment Chatbot")
    print("=" * 50)

    app = create_healthcare_chatbot()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        response = app.invoke({"messages": [HumanMessage(content=user_input)]}, config)

        if response.get("messages"):
            print(f"Bot: {response['messages'][-1].content}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "diagram":
        generate_diagram()
    else:
        start_chat()
