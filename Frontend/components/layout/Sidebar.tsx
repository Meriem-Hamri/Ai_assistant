import type { ReactNode } from "react";

interface SidebarProps {
  children: ReactNode;
  onClose: () => void;
  activeView: "assistant" | "documents";
  onNavigate: (view: "assistant" | "documents") => void;
}

export function Sidebar({
  children,
  onClose,
  activeView,
  onNavigate,
}: SidebarProps) {
  return (
    <div className="sidebar-inner">
      <header className="sidebar-header">
        <span className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none"><path d="M7 3.75h7l3 3v13.5H7a2 2 0 0 1-2-2V5.75a2 2 0 0 1 2-2Z"/><path d="M14 3.75v3h3M8.5 11h5M8.5 14.5h5"/></svg>
        </span>
        <div className="sidebar-brand-copy">
          <h1 className="sidebar-title">AssistantAI</h1>
          <span>Document intelligence</span>
        </div>
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

      <nav className="primary-navigation" aria-label="Navigation principale">
        <button className="primary-nav-item" type="button" aria-current={activeView === "assistant" ? "page" : undefined} onClick={() => onNavigate("assistant")}>
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4 4.5h12v8H8l-4 3v-11Z"/><path d="M7 8.5h6"/></svg>
          <span>Assistant</span>
        </button>
        <button className="primary-nav-item" type="button" aria-current={activeView === "documents" ? "page" : undefined} onClick={() => onNavigate("documents")}>
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M5 2.75h6l4 4v10.5H5a1.5 1.5 0 0 1-1.5-1.5V4.25A1.5 1.5 0 0 1 5 2.75Z"/><path d="M11 2.75v4h4M7 10h4.5M7 13h5.5"/></svg>
          <span>Documents</span>
        </button>
      </nav>

      <div className="sidebar-workspace-content">{children}</div>
      <p className="sidebar-footer">Espace documentaire interne</p>
    </div>
  );
}
