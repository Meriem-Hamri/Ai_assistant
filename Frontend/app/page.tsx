"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { ConversationList } from "@/components/conversations/ConversationList";
import { DocumentList } from "@/components/documents/DocumentList";
import { DocumentUpload } from "@/components/documents/DocumentUpload";
import { AppShell } from "@/components/layout/AppShell";
import { Sidebar } from "@/components/layout/Sidebar";
import { useConversations } from "@/hooks/useConversations";
import { useDocuments } from "@/hooks/useDocuments";
import type { Conversation } from "@/types/conversation";
import type { Document } from "@/types/document";

export default function Home() {
  const { documents, loading, error, refreshDocuments } = useDocuments();
  const {
    conversations,
    loading: conversationsLoading,
    error: conversationsError,
    refreshConversations,
  } = useConversations();
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [isChatGenerating, setIsChatGenerating] = useState(false);
  const selectedDocuments = selectedDocumentIds
    .map((documentId) => documents.find((document) => document.id === documentId))
    .filter(
      (document): document is Document => document?.status === "ready"
    );
  const validSelectedDocumentIds = selectedDocuments.map(
    (document) => document.id
  );

  const handleToggleDocument = useCallback((documentId: string) => {
    if (isChatGenerating) {
      return;
    }

    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((selectedId) => selectedId !== documentId)
        : [...current, documentId]
    );
  }, [isChatGenerating]);

  const handleClearDocumentSelection = useCallback(() => {
    if (isChatGenerating) {
      return;
    }

    setSelectedDocumentIds([]);
  }, [isChatGenerating]);

  const handleDocumentContextRestored = useCallback(
    (documentIds: string[]) => {
      if (isChatGenerating) {
        return;
      }

      setSelectedDocumentIds([...documentIds]);
    },
    [isChatGenerating]
  );

  const handleNewConversation = useCallback(() => {
    setSelectedConversationId(null);
    setSelectedDocumentIds([]);
  }, []);

  useEffect(() => {
    if (loading || isChatGenerating) {
      return;
    }

    const readyDocumentIds = new Set(
      documents
        .filter((document) => document.status === "ready")
        .map((document) => document.id)
    );

    setSelectedDocumentIds((current) => {
      const validIds = current.filter((documentId) =>
        readyDocumentIds.has(documentId)
      );

      return validIds.length === current.length ? current : validIds;
    });
  }, [documents, isChatGenerating, loading]);

  const handleConversationCreated = (conversation: Conversation) => {
    setSelectedConversationId(conversation.id);
    void refreshConversations();
  };

  return (
    <AppShell
      sidebar={
        <Sidebar>
          <ConversationList
            conversations={conversations}
            loading={conversationsLoading}
            error={conversationsError}
            selectedConversationId={selectedConversationId}
            disabled={isChatGenerating}
            onNewConversation={handleNewConversation}
            onSelectConversation={setSelectedConversationId}
          />
          <DocumentUpload onUploaded={refreshDocuments} />
          <DocumentList documents={documents} loading={loading} error={error} selectedDocumentIds={validSelectedDocumentIds} disabled={isChatGenerating} onToggleDocument={handleToggleDocument} onClearSelection={handleClearDocumentSelection} onDocumentsChanged={refreshDocuments} />
        </Sidebar>
      }
    >
      <ChatWindow selectedConversationId={selectedConversationId} selectedDocumentIds={validSelectedDocumentIds} selectedDocuments={selectedDocuments} availableDocuments={documents} onRemoveDocument={handleToggleDocument} onConversationCreated={handleConversationCreated} onDocumentContextRestored={handleDocumentContextRestored} onGeneratingChange={setIsChatGenerating} />
    </AppShell>
  );
}
