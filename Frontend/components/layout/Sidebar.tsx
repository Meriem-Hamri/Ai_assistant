import type { ReactNode } from "react";

interface SidebarProps {
  children: ReactNode;
  onClose: () => void;
}

export function Sidebar({
  children,
  onClose,
}: SidebarProps) {
  return (
    <div className="sidebar-inner">
      <header className="sidebar-header">
        <span className="brand-mark" aria-hidden="true">A</span>
        <h1 className="sidebar-title">Assistant AI</h1>
        <button
          className="close-sidebar-button"
          type="button"
          title="Fermer la barre latérale"
          aria-label="Fermer la barre latérale"
          aria-controls="app-sidebar"
          aria-expanded="true"
          onClick={onClose}
        >
          <svg
            className="sidebar-toggle-icon"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
          >
            <rect x="2.75" y="3.25" width="14.5" height="13.5" rx="2" />
            <path d="M7.25 3.75v12.5" />
          </svg>
        </button>
      </header>

      {children}
    </div>
  );
}
