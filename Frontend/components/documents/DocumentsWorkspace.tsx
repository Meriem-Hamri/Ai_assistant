"use client";

import { useMemo, useState } from "react";
import { ConfirmationModal } from "@/components/common/ConfirmationModal";
import { deleteDocument } from "@/lib/api/documents";
import { mergeDocumentOptions, normalizeMetadataValue } from "@/lib/documentMetadata";
import type { Document } from "@/types/document";
import type { ViewerState } from "@/types/viewer";
import { DocumentFilters, type DocumentFilterValues } from "./DocumentFilters";
import { DocumentItem } from "./DocumentItem";
import { DocumentUpload } from "./DocumentUpload";

const EMPTY_FILTERS: DocumentFilterValues = { category: "", department: "", document_type: "", year: "" };

interface DocumentsWorkspaceProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  protectedDocumentIds: string[];
  contextSelectionDisabled: boolean;
  onDocumentsChanged: () => Promise<void>;
  onOpenDocument: (viewer: ViewerState) => void;
  sidebarOpen: boolean;
  onOpenSidebar: () => void;
}

export function DocumentsWorkspace({ documents, loading, error, protectedDocumentIds, contextSelectionDisabled, onDocumentsChanged, onOpenDocument, sidebarOpen, onOpenSidebar }: DocumentsWorkspaceProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<DocumentFilterValues>(EMPTY_FILTERS);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [pendingDelete, setPendingDelete] = useState<Document[]>([]);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const filterOptions = useMemo(() => ({
    category: mergeDocumentOptions(documents, "category", []),
    department: mergeDocumentOptions(documents, "department", []),
    document_type: mergeDocumentOptions(documents, "document_type", []),
    year: [...new Set(documents.map((document) => document.year).filter((year): year is number => year !== null))].sort((a, b) => b - a),
  }), [documents]);
  const filteredDocuments = useMemo(() => {
    const query = normalizeMetadataValue(searchQuery);
    return documents.filter((document) => {
      const matchesSearch = !query || [document.filename, document.title].filter((value): value is string => Boolean(value)).some((value) => normalizeMetadataValue(value).includes(query));
      return matchesSearch
        && (!filters.category || normalizeMetadataValue(document.category ?? "") === normalizeMetadataValue(filters.category))
        && (!filters.department || normalizeMetadataValue(document.department ?? "") === normalizeMetadataValue(filters.department))
        && (!filters.document_type || normalizeMetadataValue(document.document_type ?? "") === normalizeMetadataValue(filters.document_type))
        && (!filters.year || document.year === Number(filters.year));
    });
  }, [documents, filters, searchQuery]);
  const canDelete = (document: Document) => (document.status === "ready" || document.status === "error") && !(contextSelectionDisabled && protectedDocumentIds.includes(document.id));
  const selectableResults = filteredDocuments.filter(canDelete);
  const allResultsSelected = selectableResults.length > 0 && selectableResults.every((document) => selectedIds.includes(document.id));

  function cancelSelection() { setSelectionMode(false); setSelectedIds([]); setNotice(null); }
  function toggleSelection(documentId: string) { setSelectedIds((current) => current.includes(documentId) ? current.filter((id) => id !== documentId) : [...current, documentId]); }
  function toggleAllResults() {
    const resultIds = selectableResults.map((document) => document.id);
    setSelectedIds((current) => allResultsSelected ? current.filter((id) => !resultIds.includes(id)) : [...new Set([...current, ...resultIds])]);
  }
  function requestDelete(targets: Document[]) { setDeleteError(null); setPendingDelete(targets); }
  async function confirmDelete() {
    if (deleting || pendingDelete.length === 0) return;
    setDeleting(true); setDeleteError(null); setNotice(null);
    const results = await Promise.allSettled(pendingDelete.map((document) => deleteDocument(document.id)));
    const failed = pendingDelete.filter((_, index) => results[index].status === "rejected");
    const deletedIds = pendingDelete.filter((_, index) => results[index].status === "fulfilled").map((document) => document.id);
    setSelectedIds((current) => current.filter((id) => !deletedIds.includes(id)));
    await onDocumentsChanged();
    setDeleting(false);
    if (failed.length > 0) {
      setPendingDelete(failed);
      setDeleteError(`${failed.length} document${failed.length > 1 ? "s n’ont" : " n’a"} pas pu être supprimé${failed.length > 1 ? "s" : ""}.`);
      if (deletedIds.length > 0) setNotice(`${deletedIds.length} document${deletedIds.length > 1 ? "s supprimés" : " supprimé"}.`);
    } else {
      setPendingDelete([]);
      setNotice(`${deletedIds.length} document${deletedIds.length > 1 ? "s supprimés" : " supprimé"}.`);
      if (selectionMode) { setSelectionMode(false); setSelectedIds([]); }
    }
  }

  return <section className="documents-workspace" aria-labelledby="library-title">
    <header className="workspace-header">
      <div className="workspace-heading-row">
        {!sidebarOpen && <button className="open-sidebar-button" type="button" title="Ouvrir la navigation" aria-label="Ouvrir la navigation" onClick={onOpenSidebar}><svg className="sidebar-toggle-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true"><rect x="2.75" y="3.25" width="14.5" height="13.5" rx="2"/><path d="M7.25 3.75v12.5"/></svg></button>}
        <div><p className="workspace-eyebrow">Espace documentaire</p><h2 id="library-title">Bibliothèque documentaire</h2><p>{documents.length} document{documents.length === 1 ? "" : "s"}</p></div>
      </div>
      <div className="library-tools"><div className="library-search-wrap"><svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.25"/><path d="m12.5 12.5 4 4"/></svg><label className="visually-hidden" htmlFor="library-search">Rechercher un document</label><input id="library-search" className="library-search" type="search" value={searchQuery} placeholder="Rechercher un document…" onChange={(event) => setSearchQuery(event.target.value)} /></div><div className="library-filter-actions"><DocumentFilters options={filterOptions} values={filters} onChange={setFilters} /><div className="library-header-actions"><button type="button" className="selection-mode-button" onClick={() => selectionMode ? cancelSelection() : setSelectionMode(true)}>{selectionMode ? "Annuler" : "Sélectionner"}</button><DocumentUpload variant="workspace" onUploaded={onDocumentsChanged} /></div></div></div>
      {selectionMode && selectedIds.length > 0 && <div className="selection-action-bar"><strong>{selectedIds.length} document{selectedIds.length > 1 ? "s sélectionnés" : " sélectionné"}</strong><div><button type="button" onClick={toggleAllResults}>{allResultsSelected ? "Désélectionner les résultats" : "Tout sélectionner"}</button><button type="button" className="bulk-delete-button" onClick={() => requestDelete(documents.filter((document) => selectedIds.includes(document.id)))}>Supprimer</button></div></div>}
    </header>
    <div className="library-content">
      {notice && <p className="library-notice" role="status">{notice}</p>}
      {loading ? <div className="library-state" role="status">Chargement de la bibliothèque…</div> : error && documents.length === 0 ? <div className="library-state library-state-error" role="alert">Impossible de charger les documents : {error}</div> : <>{error && <p className="library-inline-error" role="status">Actualisation impossible : {error}</p>}{documents.length === 0 ? <div className="library-state"><strong>Votre bibliothèque est vide</strong><span>Importez un premier document pour commencer.</span></div> : filteredDocuments.length === 0 ? <div className="library-state"><strong>Aucun résultat</strong><span>Aucun document ne correspond à la recherche et aux filtres actifs.</span></div> : <div className={`library-list ${selectionMode ? "selection-active" : ""}`} role="list" aria-label="Documents">{filteredDocuments.map((document) => <DocumentItem key={document.id} document={document} selectionMode={selectionMode} selected={selectedIds.includes(document.id)} deletionDisabled={!canDelete(document)} onToggleSelection={() => { if (canDelete(document)) toggleSelection(document.id); }} onOpen={() => onOpenDocument({ documentId: document.id, documentName: document.filename, pageNumber: null, excerpt: "" })} onRequestDelete={() => requestDelete([document])} />)}</div>}</>}
    </div>
    <ConfirmationModal open={pendingDelete.length > 0} title={pendingDelete.length === 1 ? "Supprimer le document ?" : `Supprimer ${pendingDelete.length} documents ?`} description={pendingDelete.length === 1 ? `${pendingDelete[0]?.filename} sera supprimé définitivement.` : "Les documents sélectionnés seront supprimés définitivement."} submitting={deleting} error={deleteError} onCancel={() => { setPendingDelete([]); setDeleteError(null); }} onConfirm={() => void confirmDelete()} />
  </section>;
}
