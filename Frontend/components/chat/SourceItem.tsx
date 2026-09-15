import type { ChatSource } from "@/types/source";
import type { ViewerState } from "@/types/viewer";

interface SourceItemProps {
  source: ChatSource;
  onOpenSource: (viewer: ViewerState) => void;
}

export function SourceItem({ source, onOpenSource }: SourceItemProps) {
  return (
    <li>
      <button
        type="button"
        className="source-item"
        onClick={() => onOpenSource({ documentId: source.document_id, documentName: source.document_name, pageNumber: source.page_number, excerpt: source.excerpt })}
        aria-label={`Ouvrir ${source.document_name}${
          source.page_number !== null ? `, page ${source.page_number}` : ""
        } dans le viewer`}
      >
        <span className="source-meta">
          <strong className="source-document">{source.document_name}</strong>
          {source.page_number !== null && (
            <span className="source-page">Page {source.page_number}</span>
          )}
        </span>
        {source.excerpt && (
          <span className="source-excerpt">{source.excerpt}</span>
        )}
      </button>
    </li>
  );
}
