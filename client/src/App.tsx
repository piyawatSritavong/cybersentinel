import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
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
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/alerts" component={AlertFeed} />
        <Route path="/agents" component={AgentSquads} />
        <Route path="/skills" component={Skills} />
        <Route path="/cron" component={CronJobs} />
        <Route path="/nodes" component={Nodes} />
        <Route path="/gateways" component={Gateways} />
        <Route path="/terminal" component={TerminalPage} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
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
