# Driver Test Frontend

A simple HTML test page to verify the Smart Agent voice call flow.

## What It Does

1. Creates a room via the backend API
2. Connects to LiveKit as a "driver" participant
3. Enables microphone
4. Spawns the AI agent to join the call
5. Receives audio from the AI agent

## How to Test

### 1. Start the services

**Terminal 1 - Backend (Node.js):**
```bash
cd backend
pnpm install  # or npm install
pnpm dev      # or npm run dev
```

**Terminal 2 - AI Agent (Python):**
```bash
cd ai-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure API keys!
python3 -m uvicorn src.main:app --reload --port 8000
```

### 2. Configure `.env` files

**backend/.env:**
```
LIVEKIT_URL=wss://your-livekit-instance.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
MONGODB_URI=mongodb://localhost:27017/smart-agent
AI_AGENT_URL=http://localhost:8000
```

**ai-agent/.env:**
```
LIVEKIT_URL=wss://your-livekit-instance.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
DEEPGRAM_API_KEY=your_key
GROQ_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
BACKEND_URL=http://localhost:3000
```

### 3. Open the test page

Open `driver/test.html` in your browser (or serve it locally).

1. Update the LiveKit URL to match your instance
2. Click "Start Call"
3. Grant microphone permission
4. The AI agent should join and greet you
5. Speak to test the conversation

## Troubleshooting

- **CORS errors**: Make sure the backend has CORS enabled
- **AI agent not joining**: Check the Python agent logs
- **No audio**: Check browser permissions and LiveKit connection
