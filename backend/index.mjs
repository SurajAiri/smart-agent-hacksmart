import "dotenv/config";
import express from "express";
import cors from "cors";
import { responseFormatter } from "./src/middlewares/response.middlewares.mjs";
import connectDB from "./src/utils/database.mjs";

// Import routes
import roomRoutes from "./src/routes/room.routes.mjs";
import webhookRoutes from "./src/routes/webhook.routes.mjs";
import aiAgentRoutes from "./src/routes/ai-agent.routes.mjs";

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB
connectDB();

// middlewares
app.use(cors());
app.use(express.json());
app.use(responseFormatter);

// Health check
app.get("/", (req, res) => {
  res.sendResponse(200, {
    message: "Health Check for 'smart-agent-backend' APIs.",
  });
});

// Config endpoint - expose non-secret config to frontend
app.get("/api/config", (req, res) => {
  res.sendResponse(200, {
    livekitUrl: process.env.LIVEKIT_URL,
  });
});

// API Routes
app.use("/api/rooms", roomRoutes);
app.use("/api/ai-agent", aiAgentRoutes);

// Webhook Routes (note: webhook routes have their own body parser)
app.use("/webhooks", webhookRoutes);

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Room API: http://localhost:${PORT}/api/rooms`);
  console.log(`AI Agent API: http://localhost:${PORT}/api/ai-agent`);
  console.log(`Webhooks: http://localhost:${PORT}/webhooks/livekit`);
});
