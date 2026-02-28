import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, AlertTriangle, CheckCircle, XCircle, Activity, Clock, Wrench, Users, Globe, Wifi, WifiOff } from "lucide-react";
import { Link } from "wouter";

interface HealthData {
  status: string;
  version: string;
  architecture: string;
  agents: string[];
  tools: string[];
  learning_mode: boolean;
  queue_workers: number;
}

interface StatsData {
  total_alerts: number;
  true_positives: number;
  false_positives: number;
  pending: number;
  active_cron_jobs: number;
  active_nodes: number;
  skills_loaded: number;
}

interface GatewayInfo {
  name: string;
  type: string;
  connected: boolean;
}

interface GatewayStatusData {
  gateways: GatewayInfo[];
  total_gateways?: number;
  total?: number;
  connected: number;
}

export default function Dashboard() {
  const { data: health, isLoading: healthLoading } = useQuery<HealthData>({
    queryKey: ["/api/sentinel/health"],
    refetchInterval: 10000,
  });

  const { data: stats, isLoading: statsLoading } = useQuery<StatsData>({
    queryKey: ["/api/sentinel/stats"],
    refetchInterval: 5000,
  });

  const { data: gatewayStatus } = useQuery<GatewayStatusData>({
    queryKey: ["/api/sentinel/gateways"],
    refetchInterval: 15000,
  });

  const metricCards = [
    {
      label: "Total Alerts",
      value: stats?.total_alerts ?? 0,
      icon: AlertTriangle,
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
    },
    {
      label: "True Positives",
      value: stats?.true_positives ?? 0,
      icon: XCircle,
      color: "text-red-500",
      bg: "bg-red-500/10",
    },
    {
      label: "False Positives",
      value: stats?.false_positives ?? 0,
      icon: CheckCircle,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      label: "In Queue",
      value: stats?.pending ?? 0,
      icon: Clock,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="text-page-title" className="text-2xl font-bold">Sovereign Gateway</h1>
          <p className="text-muted-foreground text-sm mt-1">AI-Native Autonomous Security Operations Center</p>
        </div>
        <div className="flex items-center gap-2">
          {healthLoading ? (
            <Badge variant="secondary">Connecting...</Badge>
          ) : health?.status === "healthy" ? (
            <Badge data-testid="status-system" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
              <Activity className="h-3 w-3 mr-1 animate-pulse-glow" />
              System Online
            </Badge>
          ) : (
            <Badge variant="destructive">Offline</Badge>
          )}
          <Badge variant="secondary" data-testid="text-version">v{health?.version ?? "..."}</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((m) => (
          <Card key={m.label} className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{m.label}</p>
                  <p data-testid={`text-metric-${m.label.toLowerCase().replace(/\s/g, "-")}`} className="text-2xl font-bold mt-1">
                    {statsLoading ? "..." : m.value}
                  </p>
                </div>
                <div className={`${m.bg} p-2.5 rounded-lg`}>
                  <m.icon className={`h-5 w-5 ${m.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-border">
          <CardContent className="p-4">
            <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
              <Users className="h-4 w-4 text-primary" />
              Agent Squads
            </h3>
            <div className="space-y-2">
              {[
                { name: "Blue Team (Defensive)", desc: "Log Analysis, Forensics, Auto-remediation", color: "bg-blue-500" },
                { name: "Red Team (Offensive)", desc: "Vulnerability Scanning, Exploit Simulation", color: "bg-red-500" },
                { name: "Purple Team (Orchestrator)", desc: "Blue-Red Feedback Loop, Defense Hardening", color: "bg-purple-500" },
              ].map((squad) => (
                <div key={squad.name} data-testid={`squad-${squad.name.split(" ")[0].toLowerCase()}`} className="flex items-center gap-3 p-2.5 rounded-md bg-muted/50">
                  <div className={`h-2.5 w-2.5 rounded-full ${squad.color} animate-pulse-glow`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{squad.name}</p>
                    <p className="text-xs text-muted-foreground truncate">{squad.desc}</p>
                  </div>
                  <Badge variant="secondary" className="text-xs">Active</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardContent className="p-4">
            <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
              <Wrench className="h-4 w-4 text-primary" />
              Loaded Tools
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {(health?.tools ?? []).map((tool) => (
                <Badge key={tool} variant="secondary" className="text-xs" data-testid={`tool-${tool}`}>
                  {tool}
                </Badge>
              ))}
              {!health?.tools?.length && (
                <p className="text-xs text-muted-foreground">Loading tools...</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border" data-testid="card-gateway-status">
        <CardContent className="p-4">
          <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Globe className="h-4 w-4 text-primary" />
              Social Gateways
            </h3>
            <Link href="/gateways">
              <Badge variant="secondary" className="cursor-pointer text-xs" data-testid="link-view-gateways">
                View All
              </Badge>
            </Link>
          </div>
          <div className="space-y-2">
            {(gatewayStatus?.gateways ?? [
              { name: "Telegram", type: "telegram", connected: false },
              { name: "Discord", type: "discord", connected: false },
              { name: "Slack", type: "slack", connected: false },
            ]).map((gw) => (
              <div key={gw.type} data-testid={`gateway-summary-${gw.type}`} className="flex items-center justify-between gap-2 p-2.5 rounded-md bg-muted/50">
                <div className="flex items-center gap-2">
                  {gw.connected ? (
                    <Wifi className="h-3.5 w-3.5 text-emerald-500" />
                  ) : (
                    <WifiOff className="h-3.5 w-3.5 text-muted-foreground" />
                  )}
                  <span className="text-sm font-medium">{gw.name}</span>
                </div>
                <Badge variant={gw.connected ? "default" : "secondary"} className={`text-xs ${gw.connected ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : ""}`}>
                  {gw.connected ? "Connected" : "Offline"}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-border">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            System Architecture
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Architecture", value: health?.architecture ?? "..." },
              { label: "Learning Mode", value: health?.learning_mode ? "Active" : "Disabled" },
              { label: "Queue Workers", value: String(health?.queue_workers ?? "...") },
              { label: "Agents", value: String(health?.agents?.length ?? 0) },
            ].map((item) => (
              <div key={item.label} className="p-2.5 rounded-md bg-muted/50">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p data-testid={`text-arch-${item.label.toLowerCase().replace(/\s/g, "-")}`} className="text-sm font-medium mt-0.5">{item.value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
