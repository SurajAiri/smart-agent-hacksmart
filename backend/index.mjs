import "dotenv/config";
import express from "express";
import { responseFormatter } from "./src/middlewares/response.middlewares.mjs";
import connectDB from "./src/utils/database.mjs";
const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB
connectDB();

// middlewares
app.use(express.json());
app.use(responseFormatter);

app.get("/", (req, res) => {
  res.sendResponse(200, {
    message: "Health Check for 'smart-agent-backend' APIs.",
  });
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
