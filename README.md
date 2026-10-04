# Weather & Search Agent – Backend

A LangGraph agent that answers **current weather** questions (OpenWeather) and
**any other question** via web search (Tavily). Chats are stored in MongoDB and
work like ChatGPT: create, list, open, rename, delete, ask follow-ups, edit a
question, and regenerate an answer.

## Structure

```
backend/
├── .env                      # your API keys (fill this in)
├── requirements.txt
└── src/
    ├── main.py               # FastAPI app
    ├── config.py             # loads settings from .env
    ├── agent/
    │   ├── models.py         # Gemini / Groq / xAI Grok with automatic fallback
    │   ├── guardrails.py     # input + output guardrails
    │   ├── tools.py          # OpenWeather + Tavily tools
    │   ├── nodes.py          # graph state, nodes, routing
    │   └── agent.py          # builds the LangGraph graph, run_agent()
    ├── database/
    │   ├── connection.py     # MongoDB connection + indexes
    │   ├── schemas.py        # chat/message schemas, request/response models
    │   └── chat_repository.py# CRUD for chats & messages
    └── api/
        └── chat_routes.py    # /api/chats endpoints
```

## Agent graph

```
START → input_guardrail ─(blocked)→ END
              │
              ▼
            agent ⇄ tools
              │
              ▼
       output_guardrail → END
```

## Setup

1. Fill in the keys in `.env` (at least one of `GOOGLE_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`,
   plus `OPENWEATHER_API_KEY` and `TAVILY_API_KEY`). `PRIMARY_LLM_PROVIDER` is tried first;
   if it fails, the other configured providers are used automatically.
2. Start MongoDB (local `mongodb://localhost:27017` or set `MONGODB_URI` to an Atlas URI).
3. Install and run (from the `backend` folder):

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on Mac/Linux)
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Open http://localhost:8000/docs to try the API.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/api/health` | Shows which models/tools are configured |
| POST | `/api/chats` | New chat (`{"message": "..."}` also answers the first question) |
| GET | `/api/chats` | List chats, newest first |
| GET | `/api/chats/{chat_id}` | Open a chat with all messages |
| PATCH | `/api/chats/{chat_id}` | Rename (`{"title": "..."}`) |
| DELETE | `/api/chats/{chat_id}` | Delete a chat |
| DELETE | `/api/chats` | Delete all chats |
| POST | `/api/chats/{chat_id}/messages` | Ask a follow-up question (`{"message": "..."}`) |
| PUT | `/api/chats/{chat_id}/messages/{message_id}` | Edit a question; later messages are replaced with a new answer |
| POST | `/api/chats/{chat_id}/regenerate` | Regenerate the last answer |
| DELETE | `/api/chats/{chat_id}/messages/{message_id}` | Delete one message |
