import type { Document } from "@/types/document";

interface MessageAttachmentsProps {
  documentIds: string[];
  documents: Document[];
}

export function MessageAttachments({
  documentIds,
  documents,
}: MessageAttachmentsProps) {
  if (documentIds.length === 0) {
    return (
      <div className="message-attachments message-attachments-all">
        <span className="scope-indicator" aria-hidden="true" />
        <span>Tous les documents</span>
      </div>
    );
  }

  const documentsById = new Map(
    documents.map((document) => [document.id, document])
  );

  return (
    <div className="message-attachments" aria-label="Documents joints au message">
      {documentIds.map((documentId) => {
        const document = documentsById.get(documentId);

        return (
          <div className="message-attachment" key={documentId}>
            <svg
              className="message-attachment-icon"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path d="M5.75 2.75h5.5l3 3v11.5h-8.5a1.5 1.5 0 0 1-1.5-1.5V4.25a1.5 1.5 0 0 1 1.5-1.5Z" />
              <path d="M11.25 2.75v3h3M7.25 9.25h4.5M7.25 12.25h4.5" />
            </svg>
            <span className="message-attachment-copy">
              <strong title={document?.filename ?? "Document indisponible"}>
                {document?.filename ?? "Document indisponible"}
              </strong>
              {document && <span>{document.document_type ?? document.type}</span>}
            </span>
          </div>
        );
      })}
    </div>
  );
}
