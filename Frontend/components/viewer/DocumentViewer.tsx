"use client";

import { useEffect, useState } from "react";
import DOMPurify from "dompurify";
import * as mammoth from "mammoth";
import { getDocumentFileUrl } from "@/lib/api/documents";
import type { ViewerState } from "@/types/viewer";

interface DocumentViewerProps {
  viewer: ViewerState;
  onClose: () => void;
}

export function DocumentViewer({ viewer, onClose }: DocumentViewerProps) {
  const [docxHtml, setDocxHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const extension = viewer.documentName.split(".").pop()?.toLocaleLowerCase();
  const fileUrl = getDocumentFileUrl(viewer.documentId, { documentName: viewer.documentName, pageNumber: viewer.pageNumber });

  useEffect(() => {
    if (extension !== "docx") return;
    const controller = new AbortController();
    setLoading(true); setError(null); setDocxHtml("");
    void fetch(getDocumentFileUrl(viewer.documentId), { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.arrayBuffer(); })
      .then((arrayBuffer) => mammoth.convertToHtml({ arrayBuffer }))
      .then((result) => setDocxHtml(DOMPurify.sanitize(result.value)))
      .catch((cause) => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Lecture impossible."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [extension, viewer.documentId]);

  return <aside className="document-viewer" aria-label={`Aperçu de ${viewer.documentName}`}>
    <header><div><span>Aperçu documentaire</span><strong title={viewer.documentName}>{viewer.documentName}</strong>{extension === "pdf" && viewer.pageNumber !== null && <small>Page ciblée : {viewer.pageNumber}</small>}</div><button type="button" aria-label="Fermer le viewer" onClick={onClose}>×</button></header>
    <div className="viewer-content">
      {extension === "pdf" ? <iframe title={`Document ${viewer.documentName}`} src={fileUrl} /> : extension === "docx" ? loading ? <div className="viewer-state">Conversion du document…</div> : error ? <div className="viewer-state viewer-error">Impossible d’afficher ce DOCX : {error}</div> : <article className="docx-content" dangerouslySetInnerHTML={{ __html: docxHtml }} /> : <iframe title={`Document ${viewer.documentName}`} src={fileUrl} />}
    </div>
    <footer>{viewer.excerpt && <p>{viewer.excerpt}</p>}<a href={getDocumentFileUrl(viewer.documentId)} target="_blank" rel="noopener noreferrer">Télécharger / ouvrir le fichier</a></footer>
  </aside>;
}
