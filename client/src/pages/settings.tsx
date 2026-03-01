import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Brain, Globe, Puzzle, ShieldCheck, Save, Loader2, Eye, EyeOff,
  RefreshCw, CheckCircle, XCircle, Send, MessageCircle, Hash,
  Search, FileText, Bug, Zap, RotateCcw
} from "lucide-react";
import { useState } from "react";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface ProviderInfo {
  name: string;
  display_name: string;
  configured: boolean;
  status: string;
}

interface IntegrationInfo {
  name: string;
  display_name: string;
  category: string;
  configured: boolean;
}

interface SocialInfo {
  name: string;
  display_name: string;
  configured: boolean;
  status: string;
}

const modelIcons: Record<string, typeof Brain> = {
  groq: Zap,
  openai: Brain,
  anthropic: Brain,
  ollama: Brain,
};

const integrationIcons: Record<string, typeof Puzzle> = {
  splunk: Search,
  jira: Bug,
  virustotal: ShieldCheck,
  clickup: CheckCircle,
  notion: FileText,
  hybrid_analysis: Search,
};

const socialIcons: Record<string, typeof Globe> = {
  telegram: Send,
  discord: MessageCircle,
  slack: Hash,
  line: MessageCircle,
  whatsapp: MessageCircle,
};

interface SettingField {
  category: string;
  key: string;
  label: string;
  encrypted?: boolean;
}

const modelFields: Record<string, SettingField[]> = {
  groq: [
    { category: "ai_models", key: "groq_api_key", label: "Groq API Key", encrypted: true },
  ],
  openai: [
    { category: "ai_models", key: "openai_api_key", label: "OpenAI API Key", encrypted: true },
  ],
  anthropic: [
    { category: "ai_models", key: "anthropic_api_key", label: "Anthropic API Key", encrypted: true },
  ],
  ollama: [
    { category: "ai_models", key: "ollama_base_url", label: "Ollama Base URL" },
  ],
};

const integrationFields: Record<string, SettingField[]> = {
  splunk: [
    { category: "integrations", key: "splunk_host", label: "Splunk Host" },
    { category: "integrations", key: "splunk_token", label: "Splunk Token", encrypted: true },
  ],
  jira: [
    { category: "integrations", key: "jira_url", label: "Jira URL" },
    { category: "integrations", key: "jira_email", label: "Jira Email" },
    { category: "integrations", key: "jira_api_token", label: "Jira API Token", encrypted: true },
  ],
  virustotal: [
    { category: "integrations", key: "virustotal_api_key", label: "VirusTotal API Key", encrypted: true },
  ],
};

const gatewayFields: Record<string, SettingField[]> = {
  telegram: [
    { category: "social_gateways", key: "telegram_bot_token", label: "Bot Token", encrypted: true },
    { category: "social_gateways", key: "telegram_chat_id", label: "Chat ID" },
  ],
  discord: [
    { category: "social_gateways", key: "discord_bot_token", label: "Bot Token", encrypted: true },
    { category: "social_gateways", key: "discord_channel_id", label: "Channel ID" },
  ],
  slack: [
    { category: "social_gateways", key: "slack_bot_token", label: "Bot Token", encrypted: true },
    { category: "social_gateways", key: "slack_channel", label: "Channel" },
  ],
};

function SettingInput({
  field,
  onSave,
  isSaving,
}: {
  field: SettingField;
  onSave: (category: string, key: string, value: string, encrypted: boolean) => void;
  isSaving: boolean;
}) {
  const [value, setValue] = useState("");
  const [visible, setVisible] = useState(false);

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1">
        <label className="text-xs text-muted-foreground mb-1 block">{field.label}</label>
        <div className="flex items-center gap-1">
          <Input
            data-testid={`input-${field.key}`}
            type={field.encrypted && !visible ? "password" : "text"}
            placeholder={field.encrypted ? "****" : `Enter ${field.label}`}
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
          {field.encrypted && (
            <Button
              size="icon"
              variant="ghost"
              data-testid={`button-toggle-${field.key}`}
              onClick={() => setVisible(!visible)}
            >
              {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </div>
      <div className="pt-5">
        <Button
          size="icon"
          data-testid={`button-save-${field.key}`}
          onClick={() => onSave(field.category, field.key, value, !!field.encrypted)}
          disabled={!value || isSaving}
        >
          {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}

function ProviderCard({
  provider,
  fields,
  icon: Icon,
  comingSoon,
  onSave,
  isSaving,
}: {
  provider: ProviderInfo;
  fields?: SettingField[];
  icon: typeof Brain;
  comingSoon?: boolean;
  onSave: (category: string, key: string, value: string, encrypted: boolean) => void;
  isSaving: boolean;
}) {
  return (
    <Card data-testid={`card-provider-${provider.name}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-3">
            <div className="bg-muted/50 p-2.5 rounded-lg">
              <Icon className="h-5 w-5 text-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium">{provider.display_name}</p>
              <p className="text-xs text-muted-foreground">{provider.name} provider</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {comingSoon ? (
              <Badge variant="secondary" data-testid={`status-provider-${provider.name}`}>Coming Soon</Badge>
            ) : provider.configured ? (
              <Badge data-testid={`status-provider-${provider.name}`} className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                <CheckCircle className="h-3 w-3 mr-1" />
                Active
              </Badge>
            ) : (
              <Badge variant="secondary" data-testid={`status-provider-${provider.name}`}>
                <XCircle className="h-3 w-3 mr-1" />
                Not Configured
              </Badge>
            )}
          </div>
        </div>
        {!comingSoon && fields && (
          <div className="space-y-3 mt-3">
            {fields.map((field) => (
              <SettingInput key={field.key} field={field} onSave={onSave} isSaving={isSaving} />
            ))}
          </div>
        )}
        {comingSoon && (
          <p className="text-xs text-muted-foreground mt-2">
            This provider will be available in a future update.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default function Settings() {
  const { toast } = useToast();

  const { data: providers, isLoading: providersLoading } = useQuery<ProviderInfo[]>({
    queryKey: ["/api/providers/models"],
  });

  const { data: integrations, isLoading: integrationsLoading } = useQuery<IntegrationInfo[]>({
    queryKey: ["/api/providers/integrations"],
  });

  const { data: socials } = useQuery<SocialInfo[]>({
    queryKey: ["/api/providers/social"],
  });

  const { data: gatewayStatus } = useQuery<{
    gateways: { name: string; type: string; connected: boolean }[];
  }>({
    queryKey: ["/api/sentinel/gateways"],
  });

  const saveMutation = useMutation({
    mutationFn: async ({
      category,
      key,
      value,
      encrypted,
    }: {
      category: string;
      key: string;
      value: string;
      encrypted: boolean;
    }) => {
      const res = await apiRequest("POST", "/api/settings", {
        category,
        key,
        value,
        encrypted,
      });
      return res.json();
    },
    onSuccess: () => {
      toast({ title: "Setting Saved", description: "Configuration updated successfully." });
      queryClient.invalidateQueries({ queryKey: ["/api/settings"] });
      queryClient.invalidateQueries({ queryKey: ["/api/providers/models"] });
      queryClient.invalidateQueries({ queryKey: ["/api/providers/integrations"] });
      queryClient.invalidateQueries({ queryKey: ["/api/providers/social"] });
    },
    onError: (err: Error) => {
      toast({ title: "Save Failed", description: err.message, variant: "destructive" });
    },
  });

  const rotateMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/settings/api-key/rotate");
      return res.json();
    },
    onSuccess: () => {
      toast({ title: "API Key Rotated", description: "A new API key has been generated." });
      queryClient.invalidateQueries({ queryKey: ["/api/settings"] });
    },
    onError: (err: Error) => {
      toast({ title: "Rotation Failed", description: err.message, variant: "destructive" });
    },
  });

  const testMutation = useMutation({
    mutationFn: async (name: string) => {
      const res = await apiRequest("POST", "/api/providers/integrations/test", { name });
      return res.json();
    },
    onSuccess: (data: { success: boolean; message?: string }) => {
      toast({
        title: data.success ? "Connection Successful" : "Connection Failed",
        description: data.message || (data.success ? "Integration is reachable." : "Could not connect."),
        variant: data.success ? "default" : "destructive",
      });
    },
    onError: (err: Error) => {
      toast({ title: "Test Failed", description: err.message, variant: "destructive" });
    },
  });

  const handleSave = (category: string, key: string, value: string, encrypted: boolean) => {
    saveMutation.mutate({ category, key, value, encrypted });
  };

  const allGateways = [
    ...(gatewayStatus?.gateways ?? [
      { name: "Telegram", type: "telegram", connected: false },
      { name: "Discord", type: "discord", connected: false },
      { name: "Slack", type: "slack", connected: false },
    ]),
    ...(socials ?? []).filter(s => !["telegram", "discord", "slack"].includes(s.name)).map(s => ({
      name: s.display_name,
      type: s.name,
      connected: s.configured,
    })),
  ];

  const comingSoonProviders = ["openai", "anthropic", "ollama"];
  const comingSoonIntegrations = ["clickup", "notion", "hybrid_analysis"];

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="text-page-title" className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">Configure integrations, providers, and security settings</p>
      </div>

      <Tabs defaultValue="ai_models" data-testid="tabs-settings">
        <TabsList className="flex flex-wrap gap-1">
          <TabsTrigger value="ai_models" data-testid="tab-ai-models">
            <Brain className="h-4 w-4 mr-1" />
            AI Models
          </TabsTrigger>
          <TabsTrigger value="social_gateways" data-testid="tab-social-gateways">
            <Globe className="h-4 w-4 mr-1" />
            Social Gateways
          </TabsTrigger>
          <TabsTrigger value="integrations" data-testid="tab-integrations">
            <Puzzle className="h-4 w-4 mr-1" />
            Integrations
          </TabsTrigger>
          <TabsTrigger value="security" data-testid="tab-security">
            <ShieldCheck className="h-4 w-4 mr-1" />
            Security
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ai_models" className="mt-4">
          {providersLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(providers ?? []).map((p) => (
                <ProviderCard
                  key={p.name}
                  provider={p}
                  fields={modelFields[p.name]}
                  icon={modelIcons[p.name] ?? Brain}
                  comingSoon={comingSoonProviders.includes(p.name)}
                  onSave={handleSave}
                  isSaving={saveMutation.isPending}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="social_gateways" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {allGateways.map((gw) => {
              const Icon = socialIcons[gw.type] ?? Globe;
              const fields = gatewayFields[gw.type];
              const isComingSoon = !fields;

              return (
                <Card key={gw.type} data-testid={`card-gateway-${gw.type}`}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <div className="flex items-center gap-3">
                        <div className="bg-muted/50 p-2.5 rounded-lg">
                          <Icon className="h-5 w-5 text-foreground" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{gw.name}</p>
                          <p className="text-xs text-muted-foreground">{gw.type} gateway</p>
                        </div>
                      </div>
                      {isComingSoon ? (
                        <Badge variant="secondary" data-testid={`status-gateway-settings-${gw.type}`}>Coming Soon</Badge>
                      ) : gw.connected ? (
                        <Badge data-testid={`status-gateway-settings-${gw.type}`} className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Connected
                        </Badge>
                      ) : (
                        <Badge variant="secondary" data-testid={`status-gateway-settings-${gw.type}`}>
                          <XCircle className="h-3 w-3 mr-1" />
                          Offline
                        </Badge>
                      )}
                    </div>
                    {fields ? (
                      <div className="space-y-3 mt-3">
                        {fields.map((field) => (
                          <SettingInput key={field.key} field={field} onSave={handleSave} isSaving={saveMutation.isPending} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground mt-2">
                        This gateway will be available in a future update.
                      </p>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="integrations" className="mt-4">
          {integrationsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(integrations ?? []).map((integ) => {
                const Icon = integrationIcons[integ.name] ?? Puzzle;
                const fields = integrationFields[integ.name];
                const isComingSoon = comingSoonIntegrations.includes(integ.name);

                return (
                  <Card key={integ.name} data-testid={`card-integration-${integ.name}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <div className="flex items-center gap-3">
                          <div className="bg-muted/50 p-2.5 rounded-lg">
                            <Icon className="h-5 w-5 text-foreground" />
                          </div>
                          <div>
                            <p className="text-sm font-medium">{integ.display_name}</p>
                            <p className="text-xs text-muted-foreground">{integ.category}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {isComingSoon ? (
                            <Badge variant="secondary" data-testid={`status-integration-${integ.name}`}>Coming Soon</Badge>
                          ) : integ.configured ? (
                            <Badge data-testid={`status-integration-${integ.name}`} className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Active
                            </Badge>
                          ) : (
                            <Badge variant="secondary" data-testid={`status-integration-${integ.name}`}>
                              <XCircle className="h-3 w-3 mr-1" />
                              Not Configured
                            </Badge>
                          )}
                        </div>
                      </div>
                      {!isComingSoon && fields ? (
                        <div className="space-y-3 mt-3">
                          {fields.map((field) => (
                            <SettingInput key={field.key} field={field} onSave={handleSave} isSaving={saveMutation.isPending} />
                          ))}
                          <Button
                            variant="outline"
                            data-testid={`button-test-${integ.name}`}
                            onClick={() => testMutation.mutate(integ.name)}
                            disabled={testMutation.isPending}
                          >
                            {testMutation.isPending ? (
                              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                            ) : (
                              <RefreshCw className="h-4 w-4 mr-1" />
                            )}
                            Test Connection
                          </Button>
                        </div>
                      ) : isComingSoon ? (
                        <p className="text-xs text-muted-foreground mt-2">
                          This integration will be available in a future update.
                        </p>
                      ) : null}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="security" className="mt-4">
          <Card data-testid="card-security-api-key">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-muted/50 p-2.5 rounded-lg">
                  <ShieldCheck className="h-5 w-5 text-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium">APP API Key</p>
                  <p className="text-xs text-muted-foreground">
                    Used to authenticate requests to the CyberSentinel backend
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  data-testid="input-api-key-display"
                  type="password"
                  value="****************************"
                  readOnly
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  data-testid="button-rotate-api-key"
                  onClick={() => rotateMutation.mutate()}
                  disabled={rotateMutation.isPending}
                >
                  {rotateMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <RotateCcw className="h-4 w-4 mr-1" />
                  )}
                  Rotate Key
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Rotating the key will invalidate the current key. All services will need to be restarted.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}