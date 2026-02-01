# Agent Dashboard

Real-time handoff management dashboard for QuickRide support agents.

## Features

- **Real-time Queue**: View pending handoffs sorted by priority
- **Context Brief**: Get full conversation context before accepting calls
- **WebSocket Updates**: Live updates when new handoffs arrive
- **Sentiment Tracking**: See user sentiment throughout the conversation
- **Suggested Actions**: AI-generated recommendations for agents

## Getting Started

### Prerequisites

- Node.js 18+
- Python backend running on port 8000

### Installation

```bash
cd agent-dashboard
npm install
```

### Development

```bash
npm run dev
```

Dashboard will be available at [http://localhost:3001](http://localhost:3001)

### Build for Production

```bash
npm run build
npm start
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Dashboard (Next.js)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────────────────┐   │
│  │   Queue Panel   │  │          Context Brief              │   │
│  │                 │  │                                     │   │
│  │  - Priority     │  │  - Driver Info                     │   │
│  │  - Trigger      │  │  - Sentiment & Confidence          │   │
│  │  - Wait Time    │  │  - Summary                         │   │
│  │  - Accept Btn   │  │  - Suggested Actions               │   │
│  │                 │  │  - Conversation History            │   │
│  │                 │  │  - Bot Actions                     │   │
│  └─────────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API + WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Python AI Agent Backend (FastAPI)                 │
├─────────────────────────────────────────────────────────────────┤
│  /api/handoff/queue          - Get pending handoffs             │
│  /api/handoff/queue/stats    - Queue statistics                 │
│  /api/handoff/alert/{id}     - Alert details                    │
│  /api/handoff/assign         - Assign agent                     │
│  /api/handoff/start/{id}     - Start call                       │
│  /api/handoff/complete       - Complete handoff                 │
│  /api/handoff/dashboard/{id} - WebSocket for real-time updates  │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/handoff/queue` | GET | Get all pending handoff alerts |
| `/api/handoff/queue/stats` | GET | Get queue statistics |
| `/api/handoff/alert/{id}` | GET | Get detailed alert info |
| `/api/handoff/alert/{id}/brief` | GET | Get micro-brief for agent |
| `/api/handoff/assign` | POST | Assign agent to handoff |
| `/api/handoff/start/{id}` | POST | Start handoff call |
| `/api/handoff/complete` | POST | Mark handoff as completed |
| `/api/handoff/dashboard/{agent_id}` | WS | Real-time updates |

## WebSocket Events

### Received from Server

| Type | Description |
|------|-------------|
| `queue_sync` | Initial queue state on connect |
| `new_alert` | New handoff added to queue |
| `assignment_confirmed` | Agent assigned to handoff |
| `pong` | Keep-alive response |
| `error` | Error message |

### Sent to Server

| Type | Description |
|------|-------------|
| `ping` | Keep-alive ping |
| `accept` | Accept a handoff alert |
