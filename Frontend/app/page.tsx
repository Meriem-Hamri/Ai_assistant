"use client";

import { useState } from "react";

import { DocumentList } from "@/components/documents/DocumentList";
import { AppShell } from "@/components/layout/AppShell";
import { Sidebar } from "@/components/layout/Sidebar";
import { useDocuments } from "@/hooks/useDocuments";

export default function Home() {
  const {
    documents,
    loading,
    error,
  } = useDocuments();

  const [
    selectedDocumentId,
    setSelectedDocumentId,
  ] = useState<string | null>(null);

  return (
    <AppShell
      sidebar={
        <Sidebar>
          <DocumentList
            documents={documents}
            loading={loading}
            error={error}
            selectedDocumentId={selectedDocumentId}
            onSelectDocument={setSelectedDocumentId}
          />
        </Sidebar>
      }
    >
      <section>
        <h2>Bienvenue</h2>

        {selectedDocumentId === null ? (
          <p>Tous les documents sont sélectionnés.</p>
        ) : (
          <p>
            Document sélectionné :{" "}
            {documents.find(
              (document) => document.id === selectedDocumentId
            )?.filename ?? selectedDocumentId}
          </p>
        )}
      </section>
    </AppShell>
  );
}