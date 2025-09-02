# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a healthcare appointment management chatbot built with LangGraph and FastAPI. It features conversational AI that helps patients manage appointments through natural language interactions with user verification, appointment management, and session persistence.

## Development Commands

### Dependencies
- Uses `uv` package manager (Python 3.11+)
- Install dependencies: `uv sync`
- Install dev dependencies: Already included in sync

### Running the Application
- **API Server**: `uv run uvicorn app.api:app --reload` (serves on http://localhost:8000)
- **CLI Chat**: `uv run python main.py` 
- **Generate Diagram**: `uv run python main.py diagram`

### Code Quality Tools
- **Format**: `uv run black .` (88 char line length)
- **Sort imports**: `uv run isort .` 
- **Lint**: `uv run ruff check .`
- **Type check**: Not configured (no mypy/pyright in dependencies)

### Testing
- Test framework: `pytest` (in dev dependencies)
- Run tests: `uv run pytest`

## Architecture

### Core Components
- **LangGraph Workflow**: Stateful conversation flow in `graph/` module
- **FastAPI API**: RESTful endpoints in `app/api.py`
- **In-Memory SQLite**: Database with sample data in `app/database.py`
- **State Management**: InMemorySaver for session persistence
- **AI Model**: Claude Sonnet via Anthropic API

### Directory Structure
```
graph/          # LangGraph workflow implementation
├── models.py   # Pydantic models & ChatbotState
├── nodes.py    # All node functions for conversation flow
├── routing.py  # Conditional routing logic + auth bypass
└── builder.py  # Graph construction and compilation

app/            # Application logic
├── database.py # SQLite setup with sample patient data
├── tools.py    # LangChain tools for appointment operations
└── api.py      # FastAPI endpoints and schemas

main.py         # CLI entry point (chat/diagram generation)
index.html      # Vanilla JS frontend interface
```

### Conversation Flow
1. **Introduction** → Collects user data (name, phone, DOB)
2. **Authentication** → Verifies against database
3. **Chatbot** → Intent detection using Claude
4. **Actions** → List/Confirm/Cancel appointments via tools
5. **Smart Re-routing** → Returns to chatbot for continued conversation

### Key Features
- **Auth Bypass**: Returning users skip intro/auth steps
- **Sample Data**: Pre-loaded patients (John Smith, Maria Garcia) with appointments
- **Dynamic Dates**: Appointments generated relative to current date
- **Session State**: Maintains conversation context across messages

## Environment Setup

Required environment variables in `.env`:
- `ANTHROPIC_API_KEY`: Claude API key
- `DEFAULT_MODEL`: Claude model (defaults to claude-3-7-sonnet-latest)

## Testing Data

### Test Patients
- **John Smith**: Phone `555-010-1001`, DOB `1985-03-15`
- **Maria Garcia**: Phone `555-010-2001`, DOB `1990-07-22`

Use these exact values for authentication testing. Each patient has pre-loaded appointments that can be listed, confirmed, or cancelled.