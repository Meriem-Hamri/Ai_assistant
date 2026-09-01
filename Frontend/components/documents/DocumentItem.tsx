
"use client";

import { useState } from "react";

import type { Document } from "@/types/document";

import {
  deleteDocument,
  getDocumentFileUrl,
} from "@/lib/api/documents";

const statusLabels = {
  queued: "En attente",
  processing: "Traitement...",
  ready: "Prêt",
  error: "Échec du traitement",
} as const;

interface DocumentItemProps {
  document: Document;
  isSelected: boolean;
  contextSelectionDisabled: boolean;
  onSelect: () => void;
  onDeleted: () => Promise<void>;
}

export function DocumentItem({
  document,
  isSelected,
  contextSelectionDisabled,
  onSelect,
  onDeleted,
}: DocumentItemProps) {
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const isReady = document.status === "ready";
  const canDelete =
    document.status === "ready" || document.status === "error";

  function handleOpen() {
    window.open(
      getDocumentFileUrl(document.id),
      "_blank",
      "noopener,noreferrer"
    );
  }

  async function handleDelete() {
    if (!canDelete || (contextSelectionDisabled && isSelected)) {
      return;
    }

    const confirmed = window.confirm(
      `Supprimer "${document.filename}" ?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);
      setDeleteError(null);
      await deleteDocument(document.id);
      await onDeleted();
    } catch (error) {
      setDeleteError(
        error instanceof Error
          ? error.message
          : "Impossible de supprimer le document."
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div
      className={`document-entry document-item ${
        isSelected ? "selected" : ""
      }`}
    >
      <button
        type="button"
        onClick={onSelect}
        aria-pressed={isSelected}
        aria-disabled={!isReady || contextSelectionDisabled}
        className="document-main-button"
        title={
          isReady
            ? document.filename
            : `${document.filename} — ${statusLabels[document.status]}`
        }
        disabled={!isReady || contextSelectionDisabled}
      >
        <svg
          className="document-icon"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path d="M5.75 2.75h5.5l3 3v11.5h-8.5a1.5 1.5 0 0 1-1.5-1.5V4.25a1.5 1.5 0 0 1 1.5-1.5Z" />
          <path d="M11.25 2.75v3h3M7.25 9.25h4.5M7.25 12.25h4.5" />
        </svg>

        <span className="document-filename">
          {document.filename}
        </span>
      </button>

      <details className="document-menu">
        <summary
          className="document-menu-button"
          aria-label={`Actions pour ${document.filename}`}
          title="Actions du document"
        >
          <span aria-hidden="true">⋯</span>
        </summary>
        <div className="document-action-menu">
          <button
            type="button"
            onClick={handleOpen}
            className="document-action-button"
            disabled={deleting}
          >
            Ouvrir
          </button>

          <button
            type="button"
            onClick={() => void handleDelete()}
            className="document-action-button document-delete-button"
            title={
              canDelete && !(contextSelectionDisabled && isSelected)
                ? "Supprimer le document"
                : contextSelectionDisabled && isSelected
                  ? "Suppression indisponible pendant la génération"
                  : "Suppression indisponible pendant le traitement"
            }
            disabled={
              deleting || !canDelete || (contextSelectionDisabled && isSelected)
            }
          >
            {deleting ? "Suppression..." : "Supprimer"}
          </button>
        </div>
      </details>

      {deleteError && (
        <p className="delete-error" role="status">
          Suppression impossible : {deleteError}
        </p>
      )}
    </div>
  );
}
