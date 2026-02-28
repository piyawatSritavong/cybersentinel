import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Shield, Swords, GitMerge, Loader2, Play } from "lucide-react";
import { useState } from "react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface AgentResult {
  agent: string;
  result: string;
  status: string;
}

const squads = [
  {
    id: "blue",
    name: "Blue Team",
    subtitle: "Defensive Operations",
    icon: Shield,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    capabilities: ["Log Analysis & Forensics", "Auto-Remediation (ISO 27001/NIST)", "Incident Response Playbooks", "PII Vault Management"],
  },
  {
    id: "red",
    name: "Red Team",
    subtitle: "Offensive Operations",
    icon: Swords,
    color: "text-red-500",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    capabilities: ["Vulnerability Scanning", "Exploit Simulation", "Attack Surface Mapping", "Penetration Testing"],
  },
  {
    id: "purple",
    name: "Purple Team",
    subtitle: "Orchestration",
    icon: GitMerge,
    color: "text-purple-500",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    capabilities: ["Blue-Red Feedback Loop", "Defense Hardening", "Gap Analysis", "Continuous Improvement"],
  },
];

export default function AgentSquads() {
  const { toast } = useToast();
  const [selectedSquad, setSelectedSquad] = useState("blue");
  const [taskInput, setTaskInput] = useState("");

  const runAgentMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/sentinel/agents/run", {
        squad: selectedSquad,
        task: taskInput,
      });
      return res.json();
    },
    onSuccess: (data: AgentResult) => {
      toast({ title: `${data.agent} Complete`, description: data.status });
    },
    onError: (err: Error) => {
      toast({ title: "Agent Error", description: err.message, variant: "destructive" });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="text-page-title" className="text-2xl font-bold">Agent Squads</h1>
        <p className="text-muted-foreground text-sm mt-1">Blue, Red, and Purple team agents for comprehensive security</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {squads.map((squad) => (
          <Card key={squad.id} data-testid={`card-squad-${squad.id}`} className={`border-border ${selectedSquad === squad.id ? `ring-1 ring-offset-1 ring-offset-background ${squad.border.replace("border-", "ring-")}` : ""}`}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className={`${squad.bg} p-2 rounded-lg`}>
                  <squad.icon className={`h-5 w-5 ${squad.color}`} />
                </div>
                <div>
                  <h3 className="text-sm font-medium">{squad.name}</h3>
                  <p className="text-xs text-muted-foreground">{squad.subtitle}</p>
                </div>
                <Badge className={`ml-auto ${squad.bg} ${squad.color} border-transparent text-xs`}>Active</Badge>
              </div>
              <div className="space-y-1.5">
                {squad.capabilities.map((cap) => (
                  <div key={cap} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className={`h-1 w-1 rounded-full ${squad.color.replace("text-", "bg-")}`} />
                    {cap}
                  </div>
                ))}
              </div>
              <Button
                data-testid={`button-select-${squad.id}`}
                variant={selectedSquad === squad.id ? "default" : "secondary"}
                className="w-full mt-3"
                size="sm"
                onClick={() => setSelectedSquad(squad.id)}
              >
                {selectedSquad === squad.id ? "Selected" : "Select"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-border">
        <CardContent className="p-4 space-y-3">
          <h3 className="text-sm font-medium">Run Agent Task</h3>
          <div className="flex gap-3">
            <Select value={selectedSquad} onValueChange={setSelectedSquad}>
              <SelectTrigger data-testid="select-squad" className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="blue">Blue Team</SelectItem>
                <SelectItem value="red">Red Team</SelectItem>
                <SelectItem value="purple">Purple Team</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Textarea
            data-testid="input-agent-task"
            placeholder="Describe the task... (e.g., 'Analyze subnet 10.0.0.0/24 for lateral movement patterns')"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            rows={3}
          />
          <Button
            data-testid="button-run-agent"
            onClick={() => runAgentMutation.mutate()}
            disabled={!taskInput || runAgentMutation.isPending}
          >
            {runAgentMutation.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
            Run {squads.find(s => s.id === selectedSquad)?.name}
          </Button>

          {runAgentMutation.data && (
            <div className="mt-3 p-3 rounded-md bg-muted/50 border border-border">
              <p className="text-xs text-muted-foreground mb-1">Result from {runAgentMutation.data.agent}</p>
              <pre data-testid="text-agent-result" className="text-sm whitespace-pre-wrap font-mono">{runAgentMutation.data.result}</pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
