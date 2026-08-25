import express from "express";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import { createServer as createViteServer } from "vite";

function runPythonAgent(payload: Record<string, any>): Promise<any> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(process.cwd(), "backend", "agent_cli.py");
    const py = spawn("python3", [scriptPath], {
      cwd: process.cwd(),
      env: { ...process.env },
    });

    let stdout = "";
    let stderr = "";

    py.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    py.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    py.on("close", (code) => {
      if (code !== 0 && !stdout.trim()) {
        return reject(new Error(stderr || `Python process exited with code ${code}`));
      }
      try {
        const parsed = JSON.parse(stdout.trim());
        resolve(parsed);
      } catch (err) {
        reject(new Error(`Failed to parse Python agent output: ${stdout}\nStderr: ${stderr}`));
      }
    });

    py.on("error", (err) => {
      reject(err);
    });

    py.stdin.write(JSON.stringify(payload));
    py.stdin.end();
  });
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Enable CORS for preview and cross-origin iframe embedding
  app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization");
    if (req.method === "OPTIONS") {
      return res.sendStatus(200);
    }
    next();
  });

  // Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // API 1: Chat endpoint - calls Python backend agent
  app.post("/api/chat", async (req, res) => {
    try {
      const { message, sessionId = "web-session-1" } = req.body;
      if (!message || typeof message !== "string") {
        return res.status(400).json({ error: "Missing 'message' field" });
      }

      const response = await runPythonAgent({
        action: "chat",
        message,
        session_id: sessionId,
      });

      res.json(response);
    } catch (err: any) {
      console.error("Python agent error:", err.message);
      res.status(500).json({
        error: "Agent execution failed",
        details: err.message,
      });
    }
  });

  // API 2: Knowledge Base listing
  app.get("/api/knowledge-base", (req, res) => {
    try {
      const kbDir = path.join(process.cwd(), "knowledge-base");
      if (!fs.existsSync(kbDir)) {
        return res.json({ documents: [] });
      }
      const files = fs.readdirSync(kbDir).filter((f) => f.endsWith(".md") && f.toLowerCase() !== "readme.md");
      const docs = files.map((filename) => {
        const raw = fs.readFileSync(path.join(kbDir, filename), "utf-8");
        let title = filename;
        let status = "active";
        let category = "general";
        let audience = "public";

        if (raw.startsWith("---")) {
          const parts = raw.split("---", 2);
          if (parts.length >= 2) {
            for (const line of parts[1].split("\n")) {
              const [k, ...v] = line.split(":");
              if (k && v.length) {
                const key = k.trim().toLowerCase();
                const val = v.join(":").trim().replace(/['"]/g, "");
                if (key === "title") title = val;
                if (key === "status") status = val;
                if (key === "category") category = val;
                if (key === "audience") audience = val;
              }
            }
          }
        }
        return {
          filename,
          title,
          status,
          category,
          audience,
          content: raw,
        };
      });
      res.json({ documents: docs });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API 3: Mock orders list
  app.get("/api/orders", (req, res) => {
    try {
      const ordersPath = path.join(process.cwd(), "data", "orders.json");
      if (!fs.existsSync(ordersPath)) {
        return res.json({ orders: [] });
      }
      const orders = JSON.parse(fs.readFileSync(ordersPath, "utf-8"));
      res.json({ orders });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API 4: Run Evaluation Suite
  app.post("/api/evaluate", async (req, res) => {
    try {
      const report = await runPythonAgent({ action: "evaluate" });
      res.json(report);
    } catch (err: any) {
      console.error("Evaluation execution error:", err.message);
      res.status(500).json({ error: "Evaluation failed", details: err.message });
    }
  });

  // API 5: Direct Order Lookup tester
  app.get("/api/order-lookup/:id", async (req, res) => {
    try {
      const orderId = req.params.id;
      const result = await runPythonAgent({
        action: "order_lookup",
        order_id: orderId,
      });
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Vite middleware for development vs static serve for production
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Aster & Row Support Agent running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
