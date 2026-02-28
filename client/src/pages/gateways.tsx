import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Globe, MessageCircle, Hash, Send, Wifi, WifiOff, Zap } from "lucide-react";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface GatewayInfo {
  name: string;
  type: string;
  connected: boolean;
  last_activity?: string;
}

interface GatewayStatusData {
  gateways: GatewayInfo[];
  total_gateways?: number;
  total?: number;
  connected: number;
  broadcast_count?: number;
}

const gatewayIcons: Record<string, typeof Globe> = {
  telegram: Send,
  discord: MessageCircle,
  slack: Hash,
};

const gatewayColors: Record<string, { dot: string; bg: string }> = {
  telegram: { dot: "bg-blue-500", bg: "bg-blue-500/10" },
  discord: { dot: "bg-indigo-500", bg: "bg-indigo-500/10" },
  slack: { dot: "bg-amber-500", bg: "bg-amber-500/10" },
};

export default function Gateways() {
  const { toast } = useToast();

  const { data: gatewayStatus, isLoading } = useQuery<GatewayStatusData>({
    queryKey: ["/api/sentinel/gateways"],
    refetchInterval: 10000,
  });

  const testMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/sentinel/gateways/test");
      return await res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/sentinel/gateways"] });
      toast({
        title: "Connectivity Test Complete",
        description: "All gateway connections have been tested.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Test Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const gateways = gatewayStatus?.gateways ?? [];

  const defaultGateways: GatewayInfo[] = [
    { name: "Telegram", type: "telegram", connected: false },
    { name: "Discord", type: "discord", connected: false },
    { name: "Slack", type: "slack", connected: false },
  ];

  const displayGateways = gateways.length > 0 ? gateways : defaultGateways;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 data-testid="text-page-title" className="text-2xl font-bold">Social Gateways</h1>
          <p className="text-muted-foreground text-sm mt-1">Multi-channel notification and HITL feedback management</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" data-testid="text-gateway-count">
            {gatewayStatus?.connected ?? 0}/{gatewayStatus?.total_gateways ?? gatewayStatus?.total ?? displayGateways.length} Connected
          </Badge>
          <Button
            data-testid="button-test-connectivity"
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
          >
            <Zap className="h-4 w-4 mr-1" />
            {testMutation.isPending ? "Testing..." : "Test Connectivity"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {displayGateways.map((gw) => {
          const Icon = gatewayIcons[gw.type] ?? Globe;
          const colors = gatewayColors[gw.type] ?? { dot: "bg-muted-foreground", bg: "bg-muted/50" };

          return (
            <Card key={gw.type} className="border-border" data-testid={`card-gateway-${gw.type}`}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between gap-2 mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`${colors.bg} p-2.5 rounded-lg`}>
                      <Icon className="h-5 w-5 text-foreground" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{gw.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">{gw.type} Gateway</p>
                    </div>
                  </div>
                  {gw.connected ? (
                    <Badge data-testid={`status-gateway-${gw.type}`} className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                      <Wifi className="h-3 w-3 mr-1" />
                      Connected
                    </Badge>
                  ) : (
                    <Badge data-testid={`status-gateway-${gw.type}`} variant="secondary">
                      <WifiOff className="h-3 w-3 mr-1" />
                      Offline
                    </Badge>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="p-2.5 rounded-md bg-muted/50">
                    <p className="text-xs text-muted-foreground">Status</p>
                    <p className="text-sm font-medium mt-0.5" data-testid={`text-status-${gw.type}`}>
                      {gw.connected ? "Active & Receiving" : "Not Configured"}
                    </p>
                  </div>
                  {gw.last_activity && (
                    <div className="p-2.5 rounded-md bg-muted/50">
                      <p className="text-xs text-muted-foreground">Last Activity</p>
                      <p className="text-sm font-medium mt-0.5">{gw.last_activity}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="border-border">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Globe className="h-4 w-4 text-primary" />
            Gateway Configuration
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { label: "Alert Broadcasting", value: "Critical alerts pushed to all connected channels" },
              { label: "HITL Feedback", value: "Human-in-the-loop replies routed to Purple Team" },
              { label: "Supported Commands", value: "/status, /analyze, /squad_stats" },
              { label: "Extensibility", value: "Plugin-based gateway architecture" },
            ].map((item) => (
              <div key={item.label} className="p-2.5 rounded-md bg-muted/50" data-testid={`text-config-${item.label.toLowerCase().replace(/\s/g, "-")}`}>
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="text-sm font-medium mt-0.5">{item.value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-border">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <MessageCircle className="h-4 w-4 text-primary" />
            Recent Notifications
          </h3>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading notification history...</p>
          ) : (
            <div className="space-y-2">
              <div className="p-3 rounded-md bg-muted/50 text-center">
                <p className="text-sm text-muted-foreground" data-testid="text-no-notifications">
                  No recent notifications. Alerts will appear here when gateways are active.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
