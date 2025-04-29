import express from "express";
import cors from "cors";
import bodyParser from "body-parser";
import path from "path";
import { fileURLToPath } from "url";
import { WebSocketServer, WebSocket } from "ws";
import dotenv from "dotenv";

// Define __dirname for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: ".env.local" });
const PORT = process.env.PORT || 3001;

// Create Express app
const app = express();

// Check if dist directory exists and handle accordingly
import fs from "fs";

const distPath = path.join(__dirname, "dist");
const distExists = fs.existsSync(distPath);

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Only serve static files if dist directory exists
if (distExists) {
  app.use(express.static(distPath));
} else {
  console.warn(
    "Warning: 'dist' directory not found. Static file serving disabled."
  );
  console.warn("You may need to build your frontend application first.");
}

// Add error handling middleware
app.use((err, req, res, next) => {
  console.error("Express error:", err);
  res.status(500).send("Server error");
});

// Create HTTP server
const server = app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});

// Create WebSocket server
const wss = new WebSocketServer({
  noServer: true,
});

// Handle WebSocket connections
wss.on("connection", (ws) => {
  console.log("Client connected");

  ws.on("close", () => {
    console.log("Client disconnected");
  });
});

// Upgrade HTTP server to handle WebSocket protocol
server.on("upgrade", (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit("connection", ws, request);
  });
});

// Webhook endpoint for spacecraft distance
app.post("/api/spacecraft-distance", (req, res) => {
  try {
    const { distance } = req.body;

    if (distance === undefined || isNaN(Number(distance))) {
      return res.status(400).json({ error: "Invalid distance value" });
    }

    console.log(`Received spacecraft distance: ${distance}`);

    // Broadcast to all connected WebSocket clients
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(
          JSON.stringify({
            type: "spacecraft-distance",
            payload: Number(distance),
          })
        );
      }
    });

    res
      .status(200)
      .json({ status: "success", message: "Distance data received" });
  } catch (error) {
    console.error("Error in spacecraft-distance endpoint:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

// Modify the SPA fallback routes to check if the dist directory exists
app.get("/", (req, res) => {
  if (distExists) {
    res.sendFile(path.join(distPath, "index.html"));
  } else {
    res
      .status(404)
      .send(
        "Frontend build files not found. Please build the frontend application."
      );
  }
});

// Then handle other routes as needed
app.get("/:path", (req, res) => {
  if (distExists) {
    res.sendFile(path.join(distPath, "index.html"));
  } else {
    res
      .status(404)
      .send(
        "Frontend build files not found. Please build the frontend application."
      );
  }
});
