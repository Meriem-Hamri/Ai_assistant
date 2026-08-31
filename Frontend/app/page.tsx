"use client";

import { useEffect, useState } from "react";
import { DocumentList } from "@/components/documents/DocumentList";
import { DocumentUpload } from "@/components/documents/DocumentUpload";
import { AppShell } from "@/components/layout/AppShell";
import { Sidebar } from "@/components/layout/Sidebar";
import { useDocuments } from "@/hooks/useDocuments";

export default function Home() {
  const { documents, loading, error, refreshDocuments } = useDocuments();
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const selectedDocument = documents.find((document) => document.id === selectedDocumentId);

  useEffect(() => {
    if (
      !loading &&
      selectedDocumentId !== null &&
      !documents.some((document) => document.id === selectedDocumentId)
    ) {
      setSelectedDocumentId(null);
    }
  }, [documents, loading, selectedDocumentId]);

  return (
    <AppShell
      sidebar={
        <Sidebar>
          <DocumentUpload onUploaded={refreshDocuments} />
          <DocumentList
            documents={documents}
            loading={loading}
            error={error}
            selectedDocumentId={selectedDocumentId}
            onSelectDocument={setSelectedDocumentId}
            onDocumentsChanged={refreshDocuments}
          />
        </Sidebar>
      }
    >
      <section className="welcome-panel">
        <div className="welcome-mark" aria-hidden="true">A</div>
        <h2>Assistant AI</h2>
        <p>Posez des questions sur vos documents.</p>
        <div className="active-scope" aria-label="Périmètre documentaire actif">
          <span className="scope-indicator" aria-hidden="true" />
          <span>{selectedDocumentId === null ? "Tous les documents" : selectedDocument?.filename ?? selectedDocumentId}</span>
        </div>
      </section>
    </AppShell>
  );
}
