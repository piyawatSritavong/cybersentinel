import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Activity, Server, Copy, Loader2, Wifi, WifiOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Node {
  id: string;
  name: string;
  type: string;
  status: string;
  last_heartbeat: string | null;
  alerts_processed: number;
  ip: string;
}

export default function Nodes() {
  const { toast } = useToast();

  const { data: nodes, isLoading } = useQuery<Node[]>({
    queryKey: ["/api/sentinel/nodes"],
    refetchInterval: 10000,
  });

  const installCommand = `curl -sSL https://cybersentinel.ai/install | bash -s -- --gateway $(window.location.origin)`;

  const copyInstallCommand = () => {
    navigator.clipboard.writeText(installCommand);
    toast({ title: "Copied", description: "Install command copied to clipboard" });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="text-page-title" className="text-2xl font-bold">Sensor Nodes</h1>
        <p className="text-muted-foreground text-sm mt-1">Deploy and manage distributed sensor nodes</p>
      </div>

      <Card className="border-border">
        <CardContent className="p-4 space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <Server className="h-4 w-4 text-primary" />
            Deploy New Sensor Node
          </h3>
          <p className="text-xs text-muted-foreground">
            Install a lightweight sensor on any machine with a single command. It will auto-register with this Gateway.
          </p>
          <div className="flex items-center gap-2">
            <code data-testid="text-install-command" className="flex-1 text-xs font-mono bg-muted/50 p-3 rounded-md border border-border overflow-x-auto">
              curl -sSL https://cybersentinel.ai/install | bash
            </code>
            <Button data-testid="button-copy-install" variant="secondary" size="sm" onClick={copyInstallCommand}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" />
            Connected Nodes
          </h3>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !nodes?.length ? (
            <div className="text-center py-8">
              <Server className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No nodes connected yet.</p>
              <p className="text-xs text-muted-foreground mt-1">Use the install command above to deploy a sensor node.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {nodes.map((node) => (
                <div
                  key={node.id}
                  data-testid={`node-card-${node.id}`}
                  className="flex items-center gap-3 p-3 rounded-md bg-muted/30 border border-border"
                >
                  {node.status === "online" ? (
                    <Wifi className="h-4 w-4 text-emerald-500 shrink-0" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-red-500 shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{node.name}</span>
                      <Badge variant="secondary" className="text-xs">{node.type}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 font-mono">{node.ip}</p>
                  </div>
                  <div className="text-right">
                    <Badge className={node.status === "online"
                      ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                      : "bg-red-500/10 text-red-500 border-red-500/20"
                    }>
                      {node.status}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">{node.alerts_processed} alerts</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
