import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Clock, Plus, Loader2, Trash2, Play, Pause } from "lucide-react";
import { useState } from "react";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface CronJob {
  id: string;
  name: string;
  schedule: string;
  task: string;
  squad: string;
  enabled: boolean;
  last_run: string | null;
  next_run: string | null;
}

export default function CronJobs() {
  const { toast } = useToast();
  const [jobName, setJobName] = useState("");
  const [schedule, setSchedule] = useState("every_6h");
  const [squad, setSquad] = useState("blue");
  const [task, setTask] = useState("");

  const { data: jobs, isLoading } = useQuery<CronJob[]>({
    queryKey: ["/api/sentinel/cron"],
    refetchInterval: 10000,
  });

  const createJobMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/sentinel/cron", {
        name: jobName,
        schedule,
        squad,
        task,
      });
      return res.json();
    },
    onSuccess: () => {
      toast({ title: "Cron Job Created", description: `${jobName} scheduled successfully` });
      setJobName("");
      setTask("");
      queryClient.invalidateQueries({ queryKey: ["/api/sentinel/cron"] });
    },
    onError: (err: Error) => {
      toast({ title: "Creation Failed", description: err.message, variant: "destructive" });
    },
  });

  const toggleJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      const res = await apiRequest("PATCH", `/api/sentinel/cron/${jobId}/toggle`, {});
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/sentinel/cron"] });
    },
  });

  const deleteJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await apiRequest("DELETE", `/api/sentinel/cron/${jobId}`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/sentinel/cron"] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 data-testid="text-page-title" className="text-2xl font-bold">Cron Jobs</h1>
        <p className="text-muted-foreground text-sm mt-1">Security scheduler for recurring automated tasks</p>
      </div>

      <Card className="border-border">
        <CardContent className="p-4 space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <Plus className="h-4 w-4 text-primary" />
            Create Cron Job
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Input
              data-testid="input-job-name"
              placeholder="Job name"
              value={jobName}
              onChange={(e) => setJobName(e.target.value)}
            />
            <Select value={schedule} onValueChange={setSchedule}>
              <SelectTrigger data-testid="select-schedule">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="every_1h">Every 1 hour</SelectItem>
                <SelectItem value="every_6h">Every 6 hours</SelectItem>
                <SelectItem value="every_12h">Every 12 hours</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
              </SelectContent>
            </Select>
            <Select value={squad} onValueChange={setSquad}>
              <SelectTrigger data-testid="select-squad">
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
            data-testid="input-job-task"
            placeholder="Task description... (e.g., 'Run Red Team scan on subnet 10.0.0.0/24 and update Blue Team filters')"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            rows={2}
          />
          <Button
            data-testid="button-create-job"
            onClick={() => createJobMutation.mutate()}
            disabled={!jobName || !task || createJobMutation.isPending}
          >
            {createJobMutation.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Clock className="h-4 w-4 mr-2" />}
            Schedule Job
          </Button>
        </CardContent>
      </Card>

      <Card className="border-border">
        <CardContent className="p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            Scheduled Jobs
          </h3>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : !jobs?.length ? (
            <p className="text-sm text-muted-foreground py-8 text-center">No cron jobs scheduled. Create one above.</p>
          ) : (
            <div className="space-y-2">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  data-testid={`cron-row-${job.id}`}
                  className="flex items-center gap-3 p-3 rounded-md bg-muted/30"
                >
                  <Switch
                    data-testid={`switch-job-${job.id}`}
                    checked={job.enabled}
                    onCheckedChange={() => toggleJobMutation.mutate(job.id)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{job.name}</span>
                      <Badge variant="secondary" className="text-xs">{job.schedule}</Badge>
                      <Badge variant="secondary" className="text-xs capitalize">{job.squad}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-0.5">{job.task}</p>
                  </div>
                  <Button
                    data-testid={`button-delete-${job.id}`}
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteJobMutation.mutate(job.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
