import type { Document } from "@/types/document";

interface DocumentItemProps { document: Document; isSelected: boolean; onSelect: () => void; }

export function DocumentItem({ document, isSelected, onSelect }: DocumentItemProps) {
  const metadata = [document.category, document.document_type, document.year?.toString()].filter(Boolean);

  return (
    <button type="button" onClick={onSelect} aria-pressed={isSelected} className="document-entry document-item" title={document.filename}>
      <svg className="document-icon" viewBox="0 0 20 20" aria-hidden="true"><path d="M5.75 2.75h5.5l3 3v11.5h-8.5a1.5 1.5 0 0 1-1.5-1.5V4.25a1.5 1.5 0 0 1 1.5-1.5Z" /><path d="M11.25 2.75v3h3M7.25 9.25h4.5M7.25 12.25h4.5" /></svg>
      <span className="document-copy">
        <strong className="document-filename">{document.filename}</strong>
        {document.title && <span className="document-title">{document.title}</span>}
        {metadata.length > 0 && <span className="document-metadata">{metadata.join(" • ")}</span>}
      </span>
    </button>
  );
}
