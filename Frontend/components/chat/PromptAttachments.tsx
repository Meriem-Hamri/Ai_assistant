import type { Document } from "@/types/document";

interface PromptAttachmentsProps {
  documents: Document[];
  selectionLabel: string | null;
  disabled: boolean;
  onRemoveDocument: (documentId: string) => void;
  onClearSelection?: () => void;
}

export function PromptAttachments({
  documents,
  selectionLabel,
  disabled,
  onRemoveDocument,
}: PromptAttachmentsProps) {
  if (documents.length === 0) {
    return null;
  }

  if (selectionLabel || documents.length > 3) {
    const label = selectionLabel ?? `${documents.length} documents sélectionnés`;
    return (
      <details className="prompt-selection-group">
        <summary>
          <span className="prompt-selection-icon" aria-hidden="true">▤</span>
          <span><strong>Documents sélectionnés</strong><small>{label}</small></span>
          <span className="prompt-selection-chevron" aria-hidden="true">⌄</span>
        </summary>
        <div className="prompt-selection-details">
          <strong>Documents concernés</strong>
          <ul>{documents.map((document) => <li key={document.id}>✓ {document.filename}</li>)}</ul>
        </div>
      </details>
    );
  }

  return (
    <div className="prompt-attachments" aria-label="Documents joints au prompt">
      <div className="prompt-attachments-list">
        {documents.map((document) => (
          <div className="prompt-attachment" key={document.id}>
            <svg
              className="prompt-attachment-icon"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path d="M5.75 2.75h5.5l3 3v11.5h-8.5a1.5 1.5 0 0 1-1.5-1.5V4.25a1.5 1.5 0 0 1 1.5-1.5Z" />
              <path d="M11.25 2.75v3h3M7.25 9.25h4.5M7.25 12.25h4.5" />
            </svg>

            <span className="prompt-attachment-copy">
              <strong title={document.filename}>{document.filename}</strong>
              <span>{document.document_type ?? document.type}</span>
            </span>

            <button
              type="button"
              className="prompt-attachment-remove"
              onClick={() => onRemoveDocument(document.id)}
              disabled={disabled}
              aria-label={`Retirer ${document.filename} du contexte`}
              title={
                disabled
                  ? "Contexte verrouillé pendant la génération"
                  : "Retirer du contexte"
              }
            >
              <span aria-hidden="true">×</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
