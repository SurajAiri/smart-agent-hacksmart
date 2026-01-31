# Smart Agent AI

This is the Python AI agent that handles voice conversations using Pipecat and LiveKit.

## Responsibilities

- Connect to LiveKit rooms as an AI participant
- Handle voice pipeline: ASR → LLM → TTS
- Manage turn-taking in conversations
- Send events back to Node.js backend

## Project Structure

```
ai-agent/
├── src/
│   ├── main.py              # FastAPI entry point
│   ├── api/
│   │   └── routes.py        # /bot/join, /bot/leave endpoints
│   ├── bot/
│   │   ├── manager.py       # Manages multiple bot instances
│   │   └── agent.py         # Pipecat voice pipeline
│   ├── events/
│   │   └── callback.py      # Send events to Node.js
│   └── config/
│       └── settings.py      # Environment configuration
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy and configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Run the server:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bot/join` | POST | Join a LiveKit room |
| `/api/bot/leave` | POST | Leave a room |
| `/api/bot/status/{room}` | GET | Get bot status |
| `/api/bot/list` | GET | List active bots |
| `/health` | GET | Health check |

## Environment Variables

See `.env.example` for all required configuration.