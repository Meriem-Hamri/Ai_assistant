
import { DocumentItem } from "./DocumentItem";

import type { Document } from "@/types/document";

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  selectedDocumentId: string | null;
  onSelectDocument: (documentId: string | null) => void;
  onDocumentsChanged: () => Promise<void>;
}

export function DocumentList({
  documents,
  loading,
  error,
  selectedDocumentId,
  onSelectDocument,
  onDocumentsChanged,
}: DocumentListProps) {
  if (loading) {
    return (
      <p className="sidebar-status">
        Chargement des documents...
      </p>
    );
  }

  if (error && documents.length === 0) {
    return (
      <p className="sidebar-status sidebar-status-error">
        Impossible de charger les documents : {error}
      </p>
    );
  }

  return (
    <section
      className="document-library"
      aria-labelledby="documents-heading"
    >
      <h2
        className="sidebar-section-title"
        id="documents-heading"
      >
        Documents
      </h2>

      {error && (
        <p className="sidebar-status sidebar-status-error" role="status">
          Actualisation impossible : {error}
        </p>
      )}

      <button
        type="button"
        onClick={() => onSelectDocument(null)}
        aria-pressed={selectedDocumentId === null}
        className={`document-entry all-documents-entry ${
          selectedDocumentId === null ? "selected" : ""
        }`}
      >
        <svg
          className="document-icon"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path d="M4.75 3.75h7.5a2 2 0 0 1 2 2v10.5h-7.5a2 2 0 0 1-2-2V3.75Z" />
          <path d="M14.25 6.25h1a1 1 0 0 1 1 1v9h-7.5" />
        </svg>

        <span>Tous les documents</span>
      </button>

      {documents.length === 0 ? (
        <p className="sidebar-status">
          Aucun document disponible.
        </p>
      ) : (
        <div className="document-list">
          {documents.map((document) => (
            <DocumentItem
              key={document.id}
              document={document}
              isSelected={selectedDocumentId === document.id}
              onSelect={() => {
                if (document.status === "ready") {
                  onSelectDocument(document.id);
                }
              }}
              onDeleted={onDocumentsChanged}
            />
          ))}
        </div>
      )}
    </section>
  );
}
