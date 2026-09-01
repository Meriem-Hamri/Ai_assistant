"use client";

import { useEffect, useState } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { ConversationList } from "@/components/conversations/ConversationList";
import { DocumentList } from "@/components/documents/DocumentList";
import { DocumentUpload } from "@/components/documents/DocumentUpload";
import { AppShell } from "@/components/layout/AppShell";
import { Sidebar } from "@/components/layout/Sidebar";
import { useConversations } from "@/hooks/useConversations";
import { useDocuments } from "@/hooks/useDocuments";

export default function Home() {
  const { documents, loading, error, refreshDocuments } = useDocuments();
  const {
    conversations,
    loading: conversationsLoading,
    error: conversationsError,
  } = useConversations();
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const selectedDocument = documents.find(
    (document) =>
      document.id === selectedDocumentId && document.status === "ready"
  );
  const validSelectedDocumentId = selectedDocument?.id ?? null;

  useEffect(() => {
    if (
      !loading &&
      selectedDocumentId !== null &&
      !documents.some(
        (document) =>
          document.id === selectedDocumentId && document.status === "ready"
      )
    ) {
      setSelectedDocumentId(null);
    }
  }, [documents, loading, selectedDocumentId]);

  return (
    <AppShell
      sidebar={
        <Sidebar>
          <ConversationList
            conversations={conversations}
            loading={conversationsLoading}
            error={conversationsError}
          />
          <DocumentUpload onUploaded={refreshDocuments} />
          <DocumentList documents={documents} loading={loading} error={error} selectedDocumentId={validSelectedDocumentId} onSelectDocument={setSelectedDocumentId} onDocumentsChanged={refreshDocuments} />
        </Sidebar>
      }
    >
      <ChatWindow selectedDocumentId={validSelectedDocumentId} selectedDocumentName={selectedDocument?.filename} />
    </AppShell>
  );
}
