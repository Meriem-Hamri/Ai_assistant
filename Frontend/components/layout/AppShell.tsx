import type { ReactNode } from "react";

interface AppShellProps {
  sidebar: ReactNode;
  children: ReactNode;
}

export function AppShell({
  sidebar,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        {sidebar}
      </aside>

      <main className="app-main">
        {children}
      </main>
    </div>
  );
}
