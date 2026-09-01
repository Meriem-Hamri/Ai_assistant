
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
  onSelect: () => void;
  onDeleted: () => Promise<void>;
}

export function DocumentItem({
  document,
  isSelected,
  onSelect,
  onDeleted,
}: DocumentItemProps) {
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const isReady = document.status === "ready";
  const canDelete =
    document.status === "ready" || document.status === "error";

  const metadata = [
    document.category,
    document.document_type,
    document.year?.toString(),
  ].filter(Boolean);

  function handleOpen() {
    window.open(
      getDocumentFileUrl(document.id),
      "_blank",
      "noopener,noreferrer"
    );
  }

  async function handleDelete() {
    if (!canDelete) {
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
        className="document-main-button"
        title={
          isReady
            ? document.filename
            : `${document.filename} — ${statusLabels[document.status]}`
        }
        disabled={!isReady}
      >
        <svg
          className="document-icon"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path d="M5.75 2.75h5.5l3 3v11.5h-8.5a1.5 1.5 0 0 1-1.5-1.5V4.25a1.5 1.5 0 0 1 1.5-1.5Z" />
          <path d="M11.25 2.75v3h3M7.25 9.25h4.5M7.25 12.25h4.5" />
        </svg>

        <span className="document-copy">
          <strong className="document-filename">
            {document.filename}
          </strong>

          {document.title && (
            <span className="document-title">
              {document.title}
            </span>
          )}

          {metadata.length > 0 && (
            <span className="document-metadata">
              {metadata.join(" • ")}
            </span>
          )}

          <span
            className={`document-status document-status-${document.status}`}
          >
            {statusLabels[document.status]}
          </span>
        </span>
      </button>

      <div className="document-actions">
        <button
          type="button"
          onClick={handleOpen}
          className="document-action-button"
          title="Ouvrir le document"
          disabled={deleting}
        >
          Ouvrir
        </button>

        <button
          type="button"
          onClick={() => void handleDelete()}
          className="document-action-button document-delete-button"
          title={
            canDelete
              ? "Supprimer le document"
              : "Suppression indisponible pendant le traitement"
          }
          disabled={deleting || !canDelete}
        >
          {deleting ? "Suppression..." : "Supprimer"}
        </button>
      </div>

      {deleteError && (
        <p className="delete-error" role="status">
          Suppression impossible : {deleteError}
        </p>
      )}
    </div>
  );
}
