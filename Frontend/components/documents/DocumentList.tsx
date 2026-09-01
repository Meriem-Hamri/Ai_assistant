
import { useState } from "react";
import { DocumentItem } from "./DocumentItem";
import { DocumentUpload } from "./DocumentUpload";

import type { Document } from "@/types/document";

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  selectedDocumentIds: string[];
  disabled: boolean;
  onToggleDocument: (documentId: string) => void;
  onDocumentsChanged: () => Promise<void>;
  isOpen: boolean;
  onToggleOpen: () => void;
}

export function DocumentList({
  documents,
  loading,
  error,
  selectedDocumentIds,
  disabled,
  onToggleDocument,
  onDocumentsChanged,
  isOpen,
  onToggleOpen,
}: DocumentListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const normalizedQuery = searchQuery.trim().toLocaleLowerCase("fr");
  const filteredDocuments = normalizedQuery
    ? documents.filter((document) =>
        [document.filename, document.title]
          .filter(Boolean)
          .some((value) => value?.toLocaleLowerCase("fr").includes(normalizedQuery))
      )
    : documents;

  return (
    <section
      className="document-library"
      aria-labelledby="documents-heading"
    >
      <h2 className="sidebar-section-title" id="documents-heading">
        <button
          className="sidebar-section-toggle"
          type="button"
          aria-expanded={isOpen}
          aria-controls="documents-panel"
          aria-label={`${isOpen ? "Replier" : "Ouvrir"} la section Documents`}
          onClick={onToggleOpen}
        >
          <span aria-hidden="true">{isOpen ? "▼" : "▶"}</span>
          <span>Documents</span>
        </button>
      </h2>

      <div className="sidebar-section-content" id="documents-panel" hidden={!isOpen}>
        <DocumentUpload onUploaded={onDocumentsChanged} />

        <label className="visually-hidden" htmlFor="document-search">
          Rechercher un document
        </label>
        <input
          className="document-search"
          id="document-search"
          type="search"
          value={searchQuery}
          placeholder="Rechercher un document"
          onChange={(event) => setSearchQuery(event.target.value)}
        />

        {loading ? (
          <p className="sidebar-status">Chargement des documents...</p>
        ) : error && documents.length === 0 ? (
          <p className="sidebar-status sidebar-status-error" role="status">
            Impossible de charger les documents : {error}
          </p>
        ) : (
          <>
            {error && (
              <p className="sidebar-status sidebar-status-error" role="status">
                Actualisation impossible : {error}
              </p>
            )}

            {documents.length === 0 ? (
              <p className="sidebar-status">Aucun document disponible.</p>
            ) : filteredDocuments.length === 0 ? (
              <p className="sidebar-status">Aucun document ne correspond à la recherche.</p>
            ) : (
              <div className="document-list">
                {filteredDocuments.map((document) => (
                  <DocumentItem
                    key={document.id}
                    document={document}
                    isSelected={selectedDocumentIds.includes(document.id)}
                    contextSelectionDisabled={disabled}
                    onSelect={() => {
                      if (document.status === "ready") {
                        onToggleDocument(document.id);
                      }
                    }}
                    onDeleted={onDocumentsChanged}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
