import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Wrench, Plus, Loader2, Code, Zap } from "lucide-react";
import { useState } from "react";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface Skill {
  name: string;
  description: string;
  file: string;
  status: string;
}

export default function Skills() {
  const { toast } = useToast();
  const [skillName, setSkillName] = useState("");
  const [skillDescription, setSkillDescription] = useState("");

  const { data: skills, isLoading } = useQuery<Skill[]>({
    queryKey: ["/api/sentinel/skills"],
    refetchInterval: 10000,
  });

  const generateSkillMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/sentinel/skills/generate", {
        name: skillName,
        description: skillDescription,
      });
      return res.json();
    },
    onSuccess: () => {
      toast({ title: "Skill Generated", description: `${skillName} has been created and hot-loaded` });
      setSkillName("");
      setSkillDescription("");
      queryClient.invalidateQueries({ queryKey: ["/api/sentinel/skills"] });
    },
    onError: (err: Error) => {
      toast({ title: "Generation Failed", description: err.message, variant: "destructive" });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="text-page-title" className="text-2xl font-bold">Dynamic Skills</h1>
        <p className="text-muted-foreground text-sm mt-1">Self-evolving tool ecosystem - the AI can write its own skills</p>
      </div>

      <Card className="border-border">
        <CardContent className="p-4 space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            Generate New Skill
          </h3>
          <p className="text-xs text-muted-foreground">
            Describe a capability and the AI will generate a new skill, save it, and hot-reload it without restart.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input
              data-testid="input-skill-name"
              placeholder="Skill name (e.g., dns_resolver)"
              value={skillName}
              onChange={(e) => setSkillName(e.target.value)}
            />
          </div>
          <Textarea
            data-testid="input-skill-description"
            placeholder="Describe what this skill should do... (e.g., 'Resolve DNS records for a given domain and check against known malicious DNS servers')"
            value={skillDescription}
            onChange={(e) => setSkillDescription(e.target.value)}
            rows={3}
          />
          <Button
            data-testid="button-generate-skill"
            onClick={() => generateSkillMutation.mutate()}
            disabled={!skillName || !skillDescription || generateSkillMutation.isPending}
          >
            {generateSkillMutation.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Plus className="h-4 w-4 mr-2" />}
            Generate & Hot-Load Skill
          </Button>
        </CardContent>
      </Card>

      <Card className="border-border">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Wrench className="h-4 w-4 text-primary" />
            Loaded Skills
          </h3>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !skills?.length ? (
            <p className="text-sm text-muted-foreground py-8 text-center">No skills loaded. Generate one above.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {skills.map((skill) => (
                <div
                  key={skill.name}
                  data-testid={`skill-card-${skill.name}`}
                  className="flex items-start gap-3 p-3 rounded-md bg-muted/30"
                >
                  <Code className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{skill.name}</span>
                      <Badge variant="secondary" className="text-xs">{skill.status}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{skill.description}</p>
                    <p className="text-xs text-muted-foreground font-mono mt-1">{skill.file}</p>
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
