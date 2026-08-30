import type { ReactNode } from "react";

interface SidebarProps {
  children: ReactNode;
}

export function Sidebar({
  children,
}: SidebarProps) {
  return (
    <div className="sidebar-inner">
      <header className="sidebar-header">
        <span className="brand-mark" aria-hidden="true">A</span>
        <h1 className="sidebar-title">Assistant AI</h1>
      </header>

      {children}
    </div>
  );
}
