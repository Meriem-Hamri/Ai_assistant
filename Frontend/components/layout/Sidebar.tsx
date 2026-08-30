import type { ReactNode } from "react";

interface SidebarProps {
  children: ReactNode;
}

export function Sidebar({
  children,
}: SidebarProps) {
  return (
    <div>
      <h1>Assistant AI</h1>

      {children}
    </div>
  );
}