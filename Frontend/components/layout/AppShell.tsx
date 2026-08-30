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
    <div>
      <aside>
        {sidebar}
      </aside>

      <main>
        {children}
      </main>
    </div>
  );
}