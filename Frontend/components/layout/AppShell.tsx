import type { ReactNode } from "react";

interface AppShellProps {
  sidebar: ReactNode;
  sidebarOpen: boolean;
  children: ReactNode;
}

export function AppShell({
  sidebar,
  sidebarOpen,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="app-sidebar" id="app-sidebar" hidden={!sidebarOpen}>
        {sidebar}
      </aside>

      <main className="app-main">
        {children}
      </main>
    </div>
  );
}
