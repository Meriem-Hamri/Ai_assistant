import { getDocumentFileUrl } from "@/lib/api/documents";
import type { ChatSource } from "@/types/source";

interface SourceItemProps {
  source: ChatSource;
}

export function SourceItem({ source }: SourceItemProps) {
  const href = getDocumentFileUrl(source.document_id, {
    documentName: source.document_name,
    pageNumber: source.page_number,
  });

  return (
    <li>
      <a
        className="source-item"
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Ouvrir ${source.document_name}${
          source.page_number !== null ? `, page ${source.page_number}` : ""
        } dans un nouvel onglet`}
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
      </a>
    </li>
  );
}
