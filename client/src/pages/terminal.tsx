import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Terminal, Send, Loader2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { apiRequest } from "@/lib/queryClient";

interface LogEntry {
  type: "command" | "response" | "system";
  content: string;
  timestamp: string;
}

export default function TerminalPage() {
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([
    { type: "system", content: "CyberSentinel Sovereign Gateway v3.0 - Interactive Terminal", timestamp: new Date().toISOString() },
    { type: "system", content: "Type a command or natural language query. Examples:", timestamp: new Date().toISOString() },
    { type: "system", content: "  /status - System health check", timestamp: new Date().toISOString() },
    { type: "system", content: "  /analyze <alert_id> - Analyze a specific alert", timestamp: new Date().toISOString() },
    { type: "system", content: "  /scan <target> - Run a security scan", timestamp: new Date().toISOString() },
    { type: "system", content: "  Or type a natural language query for the AI to process", timestamp: new Date().toISOString() },
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [logs]);

  const handleSubmit = async () => {
    if (!input.trim() || isProcessing) return;

    const cmd = input.trim();
    setInput("");
    setLogs(prev => [...prev, { type: "command", content: cmd, timestamp: new Date().toISOString() }]);
    setIsProcessing(true);

    try {
      const res = await apiRequest("POST", "/api/sentinel/terminal", { command: cmd });
      const data = await res.json();
      setLogs(prev => [...prev, { type: "response", content: data.output, timestamp: new Date().toISOString() }]);
    } catch (err: any) {
      setLogs(prev => [...prev, { type: "response", content: `Error: ${err.message}`, timestamp: new Date().toISOString() }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="text-page-title" className="text-2xl font-bold">Live Terminal</h1>
        <p className="text-muted-foreground text-sm mt-1">AI-powered interactive command center</p>
      </div>

      <Card className="border-border">
        <CardContent className="p-0">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-muted/30">
            <Terminal className="h-4 w-4 text-primary" />
            <span className="text-xs font-mono text-muted-foreground">sentinel@sovereign-gateway</span>
            <Badge variant="secondary" className="text-xs ml-auto">
              {isProcessing ? "Processing..." : "Ready"}
            </Badge>
          </div>

          <div
            ref={scrollRef}
            data-testid="terminal-output"
            className="h-[500px] overflow-y-auto p-4 font-mono text-sm space-y-1"
          >
            {logs.map((log, idx) => (
              <div key={idx} className={`${
                log.type === "command" ? "text-primary" :
                log.type === "system" ? "text-muted-foreground" :
                "text-foreground"
              }`}>
                {log.type === "command" && <span className="text-emerald-500">$ </span>}
                {log.type === "response" && <span className="text-blue-500">{">"} </span>}
                {log.type === "system" && <span className="text-yellow-500">* </span>}
                <span className="whitespace-pre-wrap">{log.content}</span>
              </div>
            ))}
            {isProcessing && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Processing...</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 p-3 border-t border-border">
            <span className="text-primary font-mono text-sm">$</span>
            <Input
              data-testid="input-terminal"
              className="flex-1 font-mono text-sm border-0 bg-transparent shadow-none focus-visible:ring-0"
              placeholder="Type a command..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
            <Button data-testid="button-send-command" size="sm" onClick={handleSubmit} disabled={isProcessing}>
              <Send className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
