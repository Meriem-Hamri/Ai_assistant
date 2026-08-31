"use client";

import { useEffect, useState } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";
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
    if (!loading && selectedDocumentId !== null && !documents.some((document) => document.id === selectedDocumentId)) {
      setSelectedDocumentId(null);
    }
  }, [documents, loading, selectedDocumentId]);

  return (
    <AppShell
      sidebar={
        <Sidebar>
          <DocumentUpload onUploaded={refreshDocuments} />
          <DocumentList documents={documents} loading={loading} error={error} selectedDocumentId={selectedDocumentId} onSelectDocument={setSelectedDocumentId} onDocumentsChanged={refreshDocuments} />
        </Sidebar>
      }
    >
      <ChatWindow selectedDocumentId={selectedDocumentId} selectedDocumentName={selectedDocument?.filename} />
    </AppShell>
  );
}
