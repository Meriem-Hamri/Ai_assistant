import type { Document } from "@/types/document";

function formatFileSize(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return null;
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  return `${(bytes / (1024 * 1024)).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} Mo`;
}

export function DocumentMetadata({ document }: { document: Document }) {
  const parsedDate = document.created_at ? new Date(document.created_at) : null;
  const date = parsedDate && !Number.isNaN(parsedDate.getTime()) ? new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "short", year: "numeric" }).format(parsedDate) : null;
  const details = [document.category, document.department, document.document_type, document.year?.toString(), date, document.page_count > 0 ? `${document.page_count} p.` : null, formatFileSize(document.size)].filter((value): value is string => Boolean(value));

  return <span className="document-metadata">{details.map((detail) => <span key={detail}>{detail}</span>)}{document.tags?.length > 0 && <span className="document-tags">{document.tags.map((tag) => <span key={tag}>#{tag}</span>)}</span>}</span>;
}
