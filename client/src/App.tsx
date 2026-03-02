import { Switch, Route, useLocation, Redirect } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Layout from "@/components/layout";
import Dashboard from "@/pages/dashboard";
import AlertFeed from "@/pages/alerts";
import AgentSquads from "@/pages/agents";
import Skills from "@/pages/skills";
import CronJobs from "@/pages/cron-jobs";
import Nodes from "@/pages/nodes";
import TerminalPage from "@/pages/terminal";
import Gateways from "@/pages/gateways";
import Settings from "@/pages/settings";
import Onboarding from "@/pages/onboarding";
import NotFound from "@/pages/not-found";

function OnboardingGate({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();
  const { data, isLoading } = useQuery<{ completed: boolean }>({
    queryKey: ["/v1/settings/onboarding"],
    staleTime: 0,
  });

  if (isLoading) return null;

  const isDone = data?.completed === true || String(data?.completed) === "true";

  if (!isDone && location !== "/onboarding") {
    return <Redirect to="/onboarding" />;
  }

  if (isDone && location === "/onboarding") {
    return <Redirect to="/dashboard" />;
  }

  return <>{children}</>;
}

function Router() {
  return (
    <OnboardingGate>
      <Switch>
        <Route path="/onboarding" component={Onboarding} />
        <Route>
          {() => (
            <Layout>
              <Switch>
                <Route path="/dashboard" component={Dashboard} />
                <Route path="/alerts" component={AlertFeed} />
                <Route path="/agents" component={AgentSquads} />
                <Route path="/skills" component={Skills} />
                <Route path="/cron" component={CronJobs} />
                <Route path="/nodes" component={Nodes} />
                <Route path="/gateways" component={Gateways} />
                <Route path="/settings" component={Settings} />
                <Route path="/terminal" component={TerminalPage} />
                <Route component={NotFound} />
              </Switch>
            </Layout>
          )}
        </Route>
      </Switch>
    </OnboardingGate>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
