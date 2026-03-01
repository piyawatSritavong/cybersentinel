import { useState } from "react";
import { useLocation } from "wouter";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Shield, Zap, Puzzle, CheckCircle, ArrowRight, ArrowLeft,
  SkipForward, Loader2, Eye, EyeOff
} from "lucide-react";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

const TOTAL_STEPS = 4;

export default function Onboarding() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [groqKey, setGroqKey] = useState("");
  const [keyVisible, setKeyVisible] = useState(false);
  const [selectedIntegrations, setSelectedIntegrations] = useState<Record<string, boolean>>({
    splunk: false,
    jira: false,
    virustotal: false,
    telegram: false,
    discord: false,
    slack: false,
  });

  const saveKeyMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/settings", {
        category: "ai_models",
        key: "groq_api_key",
        value: groqKey,
        encrypted: true,
      });
      return res.json();
    },
    onSuccess: () => {
      toast({ title: "API Key Saved", description: "Groq API key configured successfully." });
      queryClient.invalidateQueries({ queryKey: ["/api/providers/models"] });
    },
    onError: (err: Error) => {
      toast({ title: "Save Failed", description: err.message, variant: "destructive" });
    },
  });

  const completeMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/settings/onboarding/complete");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/settings/onboarding"] });
      toast({ title: "Setup Complete", description: "Welcome to CyberSentinel!" });
      setLocation("/");
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const progress = (step / TOTAL_STEPS) * 100;

  const toggleIntegration = (name: string) => {
    setSelectedIntegrations((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const handleNext = () => {
    if (step === 2 && groqKey) {
      saveKeyMutation.mutate();
    }
    if (step < TOTAL_STEPS) {
      setStep(step + 1);
    }
  };

  const handleSkip = () => {
    if (step < TOTAL_STEPS) {
      setStep(step + 1);
    } else {
      completeMutation.mutate();
    }
  };

  const handleComplete = () => {
    completeMutation.mutate();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            <h1 data-testid="text-onboarding-title" className="text-2xl font-bold">CyberSentinel</h1>
          </div>
          <p className="text-sm text-muted-foreground">AI-Native Security Operations Platform</p>
        </div>

        <div className="h-2 w-full bg-muted rounded-full overflow-hidden" data-testid="progress-onboarding">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground text-center" data-testid="text-step-indicator">
          Step {step} of {TOTAL_STEPS}
        </p>

        {step === 1 && (
          <Card data-testid="card-step-welcome">
            <CardContent className="p-6 text-center space-y-4">
              <div className="bg-primary/10 p-4 rounded-lg inline-block mx-auto">
                <Shield className="h-12 w-12 text-primary" />
              </div>
              <h2 className="text-xl font-bold">Welcome to CyberSentinel</h2>
              <p className="text-sm text-muted-foreground">
                Let's get your AI-native autonomous SOC configured in just a few steps.
                You can always change these settings later.
              </p>
              <div className="grid grid-cols-3 gap-3 pt-2">
                {[
                  { icon: Zap, label: "AI Analysis" },
                  { icon: Shield, label: "Auto Defense" },
                  { icon: Puzzle, label: "Integrations" },
                ].map((item) => (
                  <div key={item.label} className="p-3 rounded-md bg-muted/50 text-center">
                    <item.icon className="h-5 w-5 mx-auto mb-1 text-primary" />
                    <p className="text-xs font-medium">{item.label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {step === 2 && (
          <Card data-testid="card-step-ai-model">
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="bg-primary/10 p-2.5 rounded-lg">
                  <Zap className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h2 className="text-lg font-bold">AI Model Setup</h2>
                  <p className="text-xs text-muted-foreground">Configure your primary AI provider</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium mb-1 block">Groq API Key</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Get your free API key from groq.com to enable AI-powered analysis.
                  </p>
                  <div className="flex items-center gap-1">
                    <Input
                      data-testid="input-onboarding-groq-key"
                      type={keyVisible ? "text" : "password"}
                      placeholder="gsk_..."
                      value={groqKey}
                      onChange={(e) => setGroqKey(e.target.value)}
                    />
                    <Button
                      size="icon"
                      variant="ghost"
                      data-testid="button-toggle-groq-key-visibility"
                      onClick={() => setKeyVisible(!keyVisible)}
                    >
                      {keyVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {step === 3 && (
          <Card data-testid="card-step-integrations">
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="bg-primary/10 p-2.5 rounded-lg">
                  <Puzzle className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h2 className="text-lg font-bold">Optional Integrations</h2>
                  <p className="text-xs text-muted-foreground">Select what you'd like to enable (configure later in Settings)</p>
                </div>
              </div>
              <div className="space-y-2">
                {[
                  { key: "splunk", label: "Splunk SIEM", desc: "Log ingestion and correlation" },
                  { key: "jira", label: "Jira Ticketing", desc: "Automated ticket creation" },
                  { key: "virustotal", label: "VirusTotal", desc: "Threat intelligence lookups" },
                  { key: "telegram", label: "Telegram Gateway", desc: "Alert notifications via Telegram" },
                  { key: "discord", label: "Discord Gateway", desc: "Alert notifications via Discord" },
                  { key: "slack", label: "Slack Gateway", desc: "Alert notifications via Slack" },
                ].map((item) => (
                  <div
                    key={item.key}
                    data-testid={`toggle-integration-${item.key}`}
                    className="flex items-center justify-between gap-3 p-3 rounded-md bg-muted/50"
                  >
                    <div>
                      <p className="text-sm font-medium">{item.label}</p>
                      <p className="text-xs text-muted-foreground">{item.desc}</p>
                    </div>
                    <Switch
                      data-testid={`switch-${item.key}`}
                      checked={selectedIntegrations[item.key] ?? false}
                      onCheckedChange={() => toggleIntegration(item.key)}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {step === 4 && (
          <Card data-testid="card-step-complete">
            <CardContent className="p-6 text-center space-y-4">
              <div className="bg-emerald-500/10 p-4 rounded-lg inline-block mx-auto">
                <CheckCircle className="h-12 w-12 text-emerald-500" />
              </div>
              <h2 className="text-xl font-bold">Setup Complete</h2>
              <p className="text-sm text-muted-foreground">
                CyberSentinel is ready to protect your infrastructure.
                You can configure additional integrations anytime from the Settings page.
              </p>
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 rounded-md bg-muted/50">
                  <p className="text-xs text-muted-foreground">AI Model</p>
                  <p className="text-sm font-medium mt-0.5">{groqKey ? "Groq (configured)" : "Not set"}</p>
                </div>
                <div className="p-3 rounded-md bg-muted/50">
                  <p className="text-xs text-muted-foreground">Integrations</p>
                  <p className="text-sm font-medium mt-0.5">
                    {Object.values(selectedIntegrations).filter(Boolean).length} selected
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="flex items-center justify-between gap-2">
          <div>
            {step > 1 && (
              <Button
                variant="outline"
                data-testid="button-back"
                onClick={() => setStep(step - 1)}
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              data-testid="button-skip"
              onClick={handleSkip}
            >
              <SkipForward className="h-4 w-4 mr-1" />
              Skip
            </Button>
            {step < TOTAL_STEPS ? (
              <Button data-testid="button-next" onClick={handleNext}>
                Next
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button
                data-testid="button-complete"
                onClick={handleComplete}
                disabled={completeMutation.isPending}
              >
                {completeMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-1" />
                )}
                Launch Dashboard
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}