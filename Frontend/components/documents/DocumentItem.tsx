"use client";

import { DocumentMetadata } from "./DocumentMetadata";
import type { Document } from "@/types/document";

const statusLabels = { queued: "En attente", processing: "Traitement", ready: "Prêt", error: "Échec" } as const;

interface DocumentItemProps {
  document: Document;
  selectionMode: boolean;
  selected: boolean;
  onToggleSelection: () => void;
  onOpen: () => void;
  onRequestDelete: () => void;
  deletionDisabled?: boolean;
}

export function DocumentItem({ document, selectionMode, selected, onToggleSelection, onOpen, onRequestDelete, deletionDisabled = false }: DocumentItemProps) {
  const canDelete = (document.status === "ready" || document.status === "error") && !deletionDisabled;
  return (
    <article className={`document-entry document-item document-item-workspace ${selected ? "management-selected" : ""}`} role="listitem">
      {selectionMode && <label className="document-selection-check" title={canDelete ? "Sélectionner" : "Indisponible pendant le traitement"}><input type="checkbox" checked={selected} disabled={!canDelete} onChange={onToggleSelection} /><span aria-hidden="true" /></label>}
      <button type="button" onClick={selectionMode ? onToggleSelection : onOpen} className="document-main-button" disabled={selectionMode && !canDelete} title={selectionMode ? `Sélectionner ${document.filename}` : `Ouvrir ${document.filename}`}>
        <span className="document-icon-wrap" aria-hidden="true"><svg className="document-icon" viewBox="0 0 20 20"><path d="M5.75 2.75h5.5l3 3v11.5h-8.5a1.5 1.5 0 0 1-1.5-1.5V4.25a1.5 1.5 0 0 1 1.5-1.5Z"/><path d="M11.25 2.75v3h3M7.25 9.25h4.5M7.25 12.25h4.5"/></svg></span>
        <span className="document-primary-copy"><strong>{document.title || document.filename}</strong>{document.title && <span>{document.filename}</span>}<DocumentMetadata document={document} /></span>
      </button>
      <span className={`status-badge status-${document.status}`}><span aria-hidden="true" />{statusLabels[document.status]}</span>
      {!selectionMode && <details className="document-menu"><summary className="document-menu-button" aria-label={`Actions pour ${document.filename}`} title="Actions du document"><span aria-hidden="true">⋯</span></summary><div className="document-action-menu"><button type="button" onClick={onOpen} className="document-action-button">Ouvrir</button><button type="button" onClick={onRequestDelete} className="document-action-button document-delete-button" disabled={!canDelete}>Supprimer</button></div></details>}
    </article>
  );
}
