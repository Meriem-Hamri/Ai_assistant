import { DocumentItem } from "./DocumentItem";

import type { Document } from "@/types/document";

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  selectedDocumentId: string | null;
  onSelectDocument: (documentId: string | null) => void;
}

export function DocumentList({
  documents,
  loading,
  error,
  selectedDocumentId,
  onSelectDocument,
}: DocumentListProps) {
  if (loading) {
    return <p>Chargement des documents...</p>;
  }

  if (error) {
    return <p>Impossible de charger les documents : {error}</p>;
  }

  return (
    <section>
      <h2>Documents</h2>

      <button
        type="button"
        onClick={() => onSelectDocument(null)}
        aria-pressed={selectedDocumentId === null}
      >
        Tous les documents
      </button>

      {documents.length === 0 ? (
        <p>Aucun document disponible.</p>
      ) : (
        <div>
          {documents.map((document) => (
            <DocumentItem
              key={document.id}
              document={document}
              isSelected={selectedDocumentId === document.id}
              onSelect={() => onSelectDocument(document.id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}