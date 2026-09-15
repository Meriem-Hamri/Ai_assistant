"use client";

import { useMemo, useRef, useState } from "react";
import { DocumentFilters, type DocumentFilterValues } from "@/components/documents/DocumentFilters";
import { mergeDocumentOptions, normalizeMetadataValue } from "@/lib/documentMetadata";
import type { Document } from "@/types/document";

interface DocumentContextPickerProps {
  documents: Document[];
  selectedDocumentIds: string[];
  disabled: boolean;
  onToggleDocument: (documentId: string) => void;
  onSelectDocuments: (documentIds: string[], label?: string | null) => void;
}

const EMPTY_FILTERS: DocumentFilterValues = { category: "", department: "", document_type: "", year: "" };

export function DocumentContextPicker({ documents, selectedDocumentIds, disabled, onToggleDocument, onSelectDocuments }: DocumentContextPickerProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<DocumentFilterValues>(EMPTY_FILTERS);
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const filterOptions = useMemo(() => ({
    category: mergeDocumentOptions(documents, "category", []),
    department: mergeDocumentOptions(documents, "department", []),
    document_type: mergeDocumentOptions(documents, "document_type", []),
    year: [...new Set(documents.map((document) => document.year).filter((year): year is number => year !== null))].sort((a, b) => b - a),
  }), [documents]);
  const readyDocuments = useMemo(() => {
    const normalizedQuery = normalizeMetadataValue(query);
    return documents.filter((document) => document.status === "ready"
      && (!normalizedQuery || [document.filename, document.title].filter((value): value is string => Boolean(value)).some((value) => normalizeMetadataValue(value).includes(normalizedQuery)))
      && (!filters.category || normalizeMetadataValue(document.category ?? "") === normalizeMetadataValue(filters.category))
      && (!filters.department || normalizeMetadataValue(document.department ?? "") === normalizeMetadataValue(filters.department))
      && (!filters.document_type || normalizeMetadataValue(document.document_type ?? "") === normalizeMetadataValue(filters.document_type))
      && (!filters.year || document.year === Number(filters.year)));
  }, [documents, filters, query]);
  const label = selectedDocumentIds.length === 0
    ? "Tous les documents"
    : selectedDocumentIds.length === 1
      ? documents.find((document) => document.id === selectedDocumentIds[0])?.filename ?? "1 document"
      : `${selectedDocumentIds.length} documents`;
  const filteredSelectionLabel = useMemo(() => {
    const parts = [filters.category, filters.department, filters.document_type, filters.year].filter(Boolean);
    if (parts.length === 0 && query.trim()) parts.push(`Recherche : ${query.trim()}`);
    return `${parts.join(" · ") || "Résultats"} · ${readyDocuments.length} document${readyDocuments.length > 1 ? "s" : ""}`;
  }, [filters, query, readyDocuments.length]);

  return <details ref={detailsRef} className="context-picker" open={open} onToggle={(event) => setOpen(event.currentTarget.open)}>
    <summary className="context-picker-trigger" aria-label={`Choisir le contexte documentaire, actuellement ${label}`}><span className="scope-indicator" aria-hidden="true" /><span>Contexte : {label}</span><span aria-hidden="true">⌄</span></summary>
    <div className="context-picker-panel">
      <header><strong>Contexte documentaire</strong><button type="button" aria-label="Fermer" onClick={() => { if (detailsRef.current) detailsRef.current.open = false; }}>×</button></header>
      <p>{selectedDocumentIds.length === 0 ? "Toutes les sources prêtes seront interrogées." : "Seuls les documents cochés seront interrogés."}</p>
      <input type="search" value={query} placeholder="Rechercher un document…" aria-label="Rechercher un document prêt" onChange={(event) => setQuery(event.target.value)} />
      <DocumentFilters options={filterOptions} values={filters} onChange={setFilters} />
      <button className="context-select-results" type="button" disabled={disabled || readyDocuments.length === 0} onClick={() => onSelectDocuments(readyDocuments.map((document) => document.id), filteredSelectionLabel)}>Sélectionner tous les résultats<span>{readyDocuments.length}</span></button>
      <div className="context-document-list">
        {readyDocuments.map((document) => <label key={document.id}><input type="checkbox" checked={selectedDocumentIds.includes(document.id)} disabled={disabled} onChange={() => onToggleDocument(document.id)} /><span><strong>{document.title || document.filename}</strong>{document.title && <small>{document.filename}</small>}</span></label>)}
        {readyDocuments.length === 0 && <span className="context-empty">Aucun document prêt ne correspond.</span>}
      </div>
      <button className="context-reset" type="button" disabled={disabled || selectedDocumentIds.length === 0} onClick={() => onSelectDocuments([], null)}>Utiliser tous les documents</button>
    </div>
  </details>;
}
