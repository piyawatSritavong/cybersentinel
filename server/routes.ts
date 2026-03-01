import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import pg from "pg";

const SENTINEL_API = "http://localhost:8000";
let _cachedApiKey: string | null = null;

function getApiKey(): string {
  if (!_cachedApiKey) {
    _cachedApiKey = process.env.APP_API_KEY ?? "";
  }
  return _cachedApiKey;
}

function refreshApiKey(): void {
  _cachedApiKey = null;
}

async function proxyToSentinel(path: string, method: string = "GET", body?: any) {
  const headers: Record<string, string> = {
    "X-API-KEY": getApiKey(),
    "Content-Type": "application/json",
  };

  const opts: RequestInit = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${SENTINEL_API}${path}`, opts);
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Sentinel API error ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {

  app.get("/api/sentinel/health", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/health");
      res.json(data);
    } catch {
      res.json({
        status: "offline",
        version: "1.0.0",
        architecture: "AI-Native Agentic",
        agents: [],
        tools: [],
        learning_mode: false,
        queue_workers: 0,
      });
    }
  });

  app.get("/api/sentinel/stats", async (_req: Request, res: Response) => {
    const stats = storage.getStats();
    res.json(stats);
  });

  app.get("/api/sentinel/alerts", async (_req: Request, res: Response) => {
    const alerts = storage.getAlerts();
    res.json(alerts);
  });

  app.post("/api/sentinel/ingest", async (req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/ingest", "POST", req.body);

      storage.addAlert({
        alert_id: req.body.alert_id || `ALERT-${Date.now()}`,
        verdict: data.status === "queued" ? "Pending" : (data.verdict || "Unknown"),
        risk_level: data.risk_level || "Medium",
        source: req.body.source || "custom",
        summary: data.message || "Alert submitted",
        timestamp: new Date().toISOString(),
        task_id: data.task_id,
      });

      res.json(data);
    } catch (err: any) {
      storage.addAlert({
        alert_id: req.body.alert_id || `ALERT-${Date.now()}`,
        verdict: "Error",
        risk_level: "Unknown",
        source: req.body.source || "custom",
        summary: `Submission error: ${err.message}`,
        timestamp: new Date().toISOString(),
      });
      res.status(500).json({ error: err.message });
    }
  });

  app.post("/api/sentinel/agents/run", async (req: Request, res: Response) => {
    try {
      const { squad, task } = req.body;
      const data = await proxyToSentinel("/v1/agents/run", "POST", { squad, task });
      res.json(data);
    } catch (err: any) {
      res.json({
        agent: req.body.squad || "unknown",
        result: `Agent unavailable: ${err.message}. The CyberSentinel backend may not be running.`,
        status: "error",
      });
    }
  });

  app.get("/api/sentinel/skills", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/skills");
      res.json(data);
    } catch {
      res.json([]);
    }
  });

  app.post("/api/sentinel/skills/generate", async (req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/skills/generate", "POST", req.body);
      res.json(data);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/sentinel/cron", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/cron");
      res.json(data);
    } catch {
      const jobs = storage.getCronJobs();
      res.json(jobs);
    }
  });

  app.post("/api/sentinel/cron", async (req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/cron", "POST", req.body);
      res.json(data);
    } catch {
      const job = storage.addCronJob(req.body);
      res.json(job);
    }
  });

  app.patch("/api/sentinel/cron/:id/toggle", async (req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel(`/v1/cron/${req.params.id}/toggle`, "PATCH", {});
      res.json(data);
    } catch {
      const job = storage.toggleCronJob(req.params.id);
      res.json(job || { error: "Job not found" });
    }
  });

  app.delete("/api/sentinel/cron/:id", async (req: Request, res: Response) => {
    try {
      await proxyToSentinel(`/v1/cron/${req.params.id}`, "DELETE", {});
    } catch {
      storage.deleteCronJob(req.params.id);
    }
    res.json({ status: "deleted" });
  });

  app.get("/api/sentinel/nodes", async (_req: Request, res: Response) => {
    const nodes = storage.getNodes();
    res.json(nodes);
  });

  app.get("/api/sentinel/infra", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/infra/status");
      res.json(data);
    } catch {
      res.json({
        provider: "REPLIT",
        database: "Replit Managed PostgreSQL",
        storage: "data",
        db_connected: false,
      });
    }
  });

  app.get("/api/sentinel/health/pro", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/health/pro");
      res.json(data);
    } catch {
      res.json({
        status: "offline",
        version: "1.0.0",
        uptime_seconds: 0,
        memory_usage_mb: 0,
        queue_depth: 0,
        worker_count: 0,
        agents_responsive: false,
        gateways: [],
      });
    }
  });

  app.get("/api/sentinel/gateways", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/gateways/status");
      res.json(data);
    } catch {
      const gateways = storage.getGateways();
      res.json({
        total_gateways: gateways.length,
        connected: gateways.filter(g => g.status === "connected").length,
        gateways: gateways.map(g => ({
          name: g.name,
          type: g.type,
          connected: g.status === "connected",
        })),
        broadcast_count: 0,
      });
    }
  });

  app.post("/api/sentinel/gateways/test", async (req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/gateways/test", "POST", req.body);
      res.json(data);
    } catch (err: any) {
      res.json({
        status: "error",
        message: `Gateway test failed: ${err.message}. The CyberSentinel backend may not be running.`,
      });
    }
  });

  app.get("/api/settings", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/settings");
      res.json(data);
    } catch {
      res.json({
        ai_models: {},
        social_gateways: {},
        integrations: {},
        security: {},
        system: {},
      });
    }
  });

  app.post("/api/settings", async (req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/settings", "POST", req.body);
      res.json(data);
    } catch (err: any) {
      res.json({ status: "error", message: err.message });
    }
  });

  app.get("/api/settings/onboarding", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/settings/onboarding");
      res.json(data);
    } catch {
      try {
        const dbUrl = process.env.DATABASE_URL;
        if (dbUrl) {
          const pool = new pg.Pool({ connectionString: dbUrl });
          await pool.query(`
            CREATE TABLE IF NOT EXISTS onboarding_state (
              id SERIAL PRIMARY KEY,
              completed BOOLEAN DEFAULT FALSE,
              completed_at TIMESTAMP,
              steps_completed TEXT[] DEFAULT '{}'
            )
          `);
          const result = await pool.query("SELECT completed, steps_completed FROM onboarding_state ORDER BY id DESC LIMIT 1");
          await pool.end();
          if (result.rows.length > 0) {
            res.json({ completed: result.rows[0].completed, steps_completed: result.rows[0].steps_completed || [] });
            return;
          }
        }
      } catch {}
      res.json({ completed: false, steps_completed: [] });
    }
  });

  app.post("/api/settings/onboarding/complete", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/settings/onboarding/complete", "POST", {});
      res.json(data);
    } catch {
      try {
        const dbUrl = process.env.DATABASE_URL;
        if (dbUrl) {
          const pool = new pg.Pool({ connectionString: dbUrl });
          await pool.query(`
            CREATE TABLE IF NOT EXISTS onboarding_state (
              id SERIAL PRIMARY KEY,
              completed BOOLEAN DEFAULT FALSE,
              completed_at TIMESTAMP,
              steps_completed TEXT[] DEFAULT '{}'
            )
          `);
          await pool.query(
            "INSERT INTO onboarding_state (completed, completed_at, steps_completed) VALUES (true, CURRENT_TIMESTAMP, $1)",
            [["welcome", "ai_model", "integrations", "complete"]]
          );
          await pool.end();
          res.json({ status: "completed" });
          return;
        }
      } catch {}
      res.json({ status: "error", message: "Backend unavailable and no database fallback" });
    }
  });

  app.get("/api/providers/models", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/providers/models");
      res.json(data);
    } catch {
      res.json([
        { name: "groq", display_name: "Groq", configured: false, status: "offline" },
        { name: "openai", display_name: "OpenAI", configured: false, status: "not_configured" },
        { name: "anthropic", display_name: "Anthropic", configured: false, status: "not_configured" },
        { name: "ollama", display_name: "Ollama", configured: false, status: "not_configured" },
      ]);
    }
  });

  app.get("/api/providers/integrations", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/providers/integrations");
      res.json(data);
    } catch {
      res.json([
        { name: "splunk", display_name: "Splunk SIEM", category: "siem", configured: false },
        { name: "jira", display_name: "Jira", category: "ticketing", configured: false },
        { name: "virustotal", display_name: "VirusTotal", category: "threat_intel", configured: false },
        { name: "clickup", display_name: "ClickUp", category: "ticketing", configured: false },
        { name: "notion", display_name: "Notion", category: "documentation", configured: false },
        { name: "hybrid_analysis", display_name: "Hybrid Analysis", category: "threat_intel", configured: false },
      ]);
    }
  });

  app.post("/api/providers/integrations/test", async (req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/providers/integrations/test", "POST", req.body);
      res.json(data);
    } catch (err: any) {
      res.json({ success: false, message: err.message });
    }
  });

  app.get("/api/providers/social", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/providers/social");
      res.json(data);
    } catch {
      res.json([
        { name: "line", display_name: "Line", configured: false, status: "not_configured" },
        { name: "whatsapp", display_name: "WhatsApp", configured: false, status: "not_configured" },
      ]);
    }
  });

  app.post("/api/settings/api-key/rotate", async (_req: Request, res: Response) => {
    try {
      const data = await proxyToSentinel("/v1/settings/api-key/rotate", "POST", {});
      refreshApiKey();
      res.json(data);
    } catch (err: any) {
      res.json({ status: "error", message: err.message });
    }
  });

  app.post("/api/sentinel/terminal", async (req: Request, res: Response) => {
    const { command } = req.body;

    if (command === "/status") {
      try {
        const health = await proxyToSentinel("/health");
        res.json({ output: JSON.stringify(health, null, 2) });
      } catch {
        res.json({ output: "CyberSentinel backend is offline." });
      }
      return;
    }

    if (command.startsWith("/analyze ")) {
      const alertId = command.replace("/analyze ", "").trim();
      res.json({ output: `Queuing analysis for alert: ${alertId}. Use the Alert Feed to submit full alert data.` });
      return;
    }

    if (command.startsWith("/scan ")) {
      const target = command.replace("/scan ", "").trim();
      try {
        const data = await proxyToSentinel("/v1/agents/run", "POST", {
          squad: "red",
          task: `Security scan on target: ${target}`,
        });
        res.json({ output: data.result || JSON.stringify(data) });
      } catch (err: any) {
        res.json({ output: `Scan failed: ${err.message}` });
      }
      return;
    }

    try {
      const data = await proxyToSentinel("/v1/agents/run", "POST", {
        squad: "blue",
        task: command,
      });
      res.json({ output: data.result || JSON.stringify(data) });
    } catch (err: any) {
      res.json({ output: `Processing error: ${err.message}. Is the CyberSentinel backend running?` });
    }
  });

  return httpServer;
}
