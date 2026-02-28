import { type User, type InsertUser } from "@shared/schema";
import { randomUUID } from "crypto";

interface AlertEntry {
  id: number;
  alert_id: string;
  verdict: string;
  risk_level: string;
  source: string;
  summary: string;
  timestamp: string;
  task_id?: string;
}

interface CronJobEntry {
  id: string;
  name: string;
  schedule: string;
  task: string;
  squad: string;
  enabled: boolean;
  last_run: string | null;
  next_run: string | null;
}

interface NodeEntry {
  id: string;
  name: string;
  type: string;
  status: string;
  last_heartbeat: string | null;
  alerts_processed: number;
  ip: string;
}

interface GatewayEntry {
  id: string;
  name: string;
  type: string;
  status: string;
  enabled: boolean;
  last_message: string | null;
  messages_sent: number;
}

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  getAlerts(): AlertEntry[];
  addAlert(alert: Omit<AlertEntry, "id">): AlertEntry;
  getStats(): {
    total_alerts: number;
    true_positives: number;
    false_positives: number;
    pending: number;
    active_cron_jobs: number;
    active_nodes: number;
    skills_loaded: number;
    active_gateways: number;
  };
  getCronJobs(): CronJobEntry[];
  addCronJob(job: Omit<CronJobEntry, "id" | "enabled" | "last_run" | "next_run">): CronJobEntry;
  toggleCronJob(id: string): CronJobEntry | null;
  deleteCronJob(id: string): void;
  getNodes(): NodeEntry[];
  getGateways(): GatewayEntry[];
  updateGatewayStatus(id: string, status: string): GatewayEntry | null;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private alerts: AlertEntry[];
  private cronJobs: CronJobEntry[];
  private nodes: NodeEntry[];
  private gateways: GatewayEntry[];
  private alertIdCounter: number;

  constructor() {
    this.users = new Map();
    this.alerts = [];
    this.cronJobs = [];
    this.alertIdCounter = 1;

    this.nodes = [
      {
        id: "node-gateway",
        name: "Sovereign Gateway",
        type: "gateway",
        status: "online",
        last_heartbeat: new Date().toISOString(),
        alerts_processed: 0,
        ip: "127.0.0.1",
      },
    ];

    this.gateways = [
      {
        id: "gw-telegram",
        name: "Telegram",
        type: "telegram",
        status: "disconnected",
        enabled: false,
        last_message: null,
        messages_sent: 0,
      },
      {
        id: "gw-discord",
        name: "Discord",
        type: "discord",
        status: "disconnected",
        enabled: false,
        last_message: null,
        messages_sent: 0,
      },
      {
        id: "gw-slack",
        name: "Slack",
        type: "slack",
        status: "disconnected",
        enabled: false,
        last_message: null,
        messages_sent: 0,
      },
    ];
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  getAlerts(): AlertEntry[] {
    return [...this.alerts].reverse();
  }

  addAlert(alert: Omit<AlertEntry, "id">): AlertEntry {
    const entry: AlertEntry = { ...alert, id: this.alertIdCounter++ };
    this.alerts.push(entry);
    if (this.alerts.length > 500) {
      this.alerts = this.alerts.slice(-500);
    }
    return entry;
  }

  getStats() {
    const tp = this.alerts.filter(a => a.verdict === "True Positive").length;
    const fp = this.alerts.filter(a => a.verdict === "False Positive").length;
    const pending = this.alerts.filter(a => a.verdict === "Pending" || a.verdict === "Unknown").length;
    return {
      total_alerts: this.alerts.length,
      true_positives: tp,
      false_positives: fp,
      pending,
      active_cron_jobs: this.cronJobs.filter(j => j.enabled).length,
      active_nodes: this.nodes.filter(n => n.status === "online").length,
      skills_loaded: 0,
      active_gateways: this.gateways.filter(g => g.status === "connected").length,
    };
  }

  getCronJobs(): CronJobEntry[] {
    return this.cronJobs;
  }

  addCronJob(job: Omit<CronJobEntry, "id" | "enabled" | "last_run" | "next_run">): CronJobEntry {
    const entry: CronJobEntry = {
      ...job,
      id: `cron-${randomUUID().slice(0, 8)}`,
      enabled: true,
      last_run: null,
      next_run: new Date(Date.now() + 3600000).toISOString(),
    };
    this.cronJobs.push(entry);
    return entry;
  }

  toggleCronJob(id: string): CronJobEntry | null {
    const job = this.cronJobs.find(j => j.id === id);
    if (job) {
      job.enabled = !job.enabled;
      return job;
    }
    return null;
  }

  deleteCronJob(id: string): void {
    this.cronJobs = this.cronJobs.filter(j => j.id !== id);
  }

  getNodes(): NodeEntry[] {
    return this.nodes;
  }

  getGateways(): GatewayEntry[] {
    return this.gateways;
  }

  updateGatewayStatus(id: string, status: string): GatewayEntry | null {
    const gw = this.gateways.find(g => g.id === id);
    if (gw) {
      gw.status = status;
      return gw;
    }
    return null;
  }
}

export const storage = new MemStorage();
