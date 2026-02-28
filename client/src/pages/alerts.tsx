import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertTriangle, Send, Loader2, CheckCircle, XCircle } from "lucide-react";
import { useState } from "react";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface Alert {
  id: number;
  alert_id: string;
  verdict: string;
  risk_level: string;
  source: string;
  summary: string;
  timestamp: string;
}

interface IngestResult {
  alert_id: string;
  task_id: string;
  status: string;
  message: string;
}

export default function AlertFeed() {
  const { toast } = useToast();
  const [alertId, setAlertId] = useState("");
  const [rawData, setRawData] = useState("");
  const [source, setSource] = useState("splunk");
  const [riskScore, setRiskScore] = useState("50");

  const { data: alerts, isLoading } = useQuery<Alert[]>({
    queryKey: ["/api/sentinel/alerts"],
    refetchInterval: 5000,
  });

  const ingestMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/sentinel/ingest", {
        alert_id: alertId || `ALERT-${Date.now()}`,
        description: "Manual submission from Gateway",
        raw_data: rawData,
        risk_score: parseInt(riskScore),
        source,
      });
      return res.json();
    },
    onSuccess: (data: IngestResult) => {
      toast({ title: "Alert Submitted", description: `Task: ${data.task_id} - ${data.status}` });
      setAlertId("");
      setRawData("");
      queryClient.invalidateQueries({ queryKey: ["/api/sentinel/alerts"] });
      queryClient.invalidateQueries({ queryKey: ["/api/sentinel/stats"] });
    },
    onError: (err: Error) => {
      toast({ title: "Submission Failed", description: err.message, variant: "destructive" });
    },
  });

  const getVerdictBadge = (verdict: string) => {
    if (verdict === "True Positive") return <Badge className="bg-red-500/10 text-red-500 border-red-500/20">{verdict}</Badge>;
    if (verdict === "False Positive") return <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">{verdict}</Badge>;
    if (verdict === "Duplicate") return <Badge variant="secondary">{verdict}</Badge>;
    return <Badge variant="secondary">{verdict}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="text-page-title" className="text-2xl font-bold">Alert Feed</h1>
        <p className="text-muted-foreground text-sm mt-1">Submit and monitor security alerts in real-time</p>
      </div>

      <Card className="border-border">
        <CardContent className="p-4 space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <Send className="h-4 w-4 text-primary" />
            Submit New Alert
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Input
              data-testid="input-alert-id"
              placeholder="Alert ID (auto-generated if empty)"
              value={alertId}
              onChange={(e) => setAlertId(e.target.value)}
            />
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger data-testid="select-source">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="splunk">Splunk</SelectItem>
                <SelectItem value="paloalto">Palo Alto</SelectItem>
                <SelectItem value="crowdstrike">CrowdStrike</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
            <Input
              data-testid="input-risk-score"
              type="number"
              placeholder="Risk Score (0-100)"
              value={riskScore}
              onChange={(e) => setRiskScore(e.target.value)}
            />
          </div>
          <Textarea
            data-testid="input-raw-data"
            placeholder="Paste raw log data here... (e.g., Failed SSH login from 10.0.0.50 to server-01 as root)"
            value={rawData}
            onChange={(e) => setRawData(e.target.value)}
            rows={3}
          />
          <Button
            data-testid="button-submit-alert"
            onClick={() => ingestMutation.mutate()}
            disabled={!rawData || ingestMutation.isPending}
            className="w-full md:w-auto"
          >
            {ingestMutation.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
            Submit to Analysis Queue
          </Button>
        </CardContent>
      </Card>

      <Card className="border-border">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-primary" />
            Recent Alerts
          </h3>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !alerts?.length ? (
            <p className="text-sm text-muted-foreground py-8 text-center">No alerts yet. Submit one above to begin analysis.</p>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert, idx) => (
                <div
                  key={alert.alert_id || idx}
                  data-testid={`alert-row-${alert.alert_id}`}
                  className="flex items-center gap-3 p-3 rounded-md bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                  {alert.verdict === "True Positive" ? (
                    <XCircle className="h-4 w-4 text-red-500 shrink-0" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{alert.alert_id}</span>
                      <Badge variant="secondary" className="text-xs">{alert.source}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-0.5">{alert.summary}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">{alert.risk_level}</Badge>
                    {getVerdictBadge(alert.verdict)}
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
