import type { Document } from "@/types/document";

interface DocumentItemProps {
  document: Document;
  isSelected: boolean;
  onSelect: () => void;
}

export function DocumentItem({
  document,
  isSelected,
  onSelect,
}: DocumentItemProps) {
  const metadata = [
    document.category,
    document.document_type,
    document.year?.toString(),
  ].filter(Boolean);

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
    >
      <div>
        <strong>{document.filename}</strong>
      </div>

      {document.title && (
        <div>
          {document.title}
        </div>
      )}

      {metadata.length > 0 && (
        <div>
          {metadata.join(" • ")}
        </div>
      )}
    </button>
  );
}