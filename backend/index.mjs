import "dotenv/config";
import express from "express";
import { responseFormatter } from "./src/middlewares/response.middlewares.mjs";
import connectDB from "./src/utils/database.mjs";

// Import routes
import roomRoutes from "./src/routes/room.routes.mjs";
import webhookRoutes from "./src/routes/webhook.routes.mjs";

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB
connectDB();

// middlewares
app.use(express.json());
app.use(responseFormatter);

// Health check
app.get("/", (req, res) => {
  res.sendResponse(200, {
    message: "Health Check for 'smart-agent-backend' APIs.",
  });
});

// API Routes
app.use("/api/rooms", roomRoutes);

// Webhook Routes (note: webhook routes have their own body parser)
app.use("/webhooks", webhookRoutes);

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Room API: http://localhost:${PORT}/api/rooms`);
  console.log(`Webhooks: http://localhost:${PORT}/webhooks/livekit`);
});
