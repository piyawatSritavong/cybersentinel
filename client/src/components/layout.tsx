import { Link, useLocation } from "wouter";
import {
  Shield, LayoutDashboard, AlertTriangle, Users, Wrench,
  Clock, Activity, Terminal, Globe, ChevronLeft, ChevronRight
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/alerts", label: "Alert Feed", icon: AlertTriangle },
  { path: "/agents", label: "Agent Squads", icon: Users },
  { path: "/skills", label: "Skills", icon: Wrench },
  { path: "/cron", label: "Cron Jobs", icon: Clock },
  { path: "/nodes", label: "Nodes", icon: Activity },
  { path: "/gateways", label: "Gateways", icon: Globe },
  { path: "/terminal", label: "Terminal", icon: Terminal },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-background">
      <aside
        data-testid="sidebar"
        className={`${collapsed ? "w-16" : "w-56"} flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-200`}
      >
        <div className="flex items-center gap-2 px-4 h-14 border-b border-sidebar-border">
          <Shield className="h-6 w-6 text-primary shrink-0" />
          {!collapsed && (
            <span className="text-sm font-bold text-sidebar-foreground tracking-wide truncate">
              CYBER SENTINEL
            </span>
          )}
        </div>

        <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location === item.path;
            return (
              <Link key={item.path} href={item.path}>
                <div
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, "-")}`}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm cursor-pointer transition-colors
                    ${isActive
                      ? "bg-sidebar-accent text-primary font-medium"
                      : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                    }`}
                >
                  <item.icon className={`h-4 w-4 shrink-0 ${isActive ? "text-primary" : ""}`} />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </div>
              </Link>
            );
          })}
        </nav>

        <button
          data-testid="toggle-sidebar"
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center h-10 border-t border-sidebar-border text-sidebar-foreground hover:text-primary transition-colors"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
