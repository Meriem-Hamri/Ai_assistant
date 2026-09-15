"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { ConversationList } from "@/components/conversations/ConversationList";
import { DocumentsWorkspace } from "@/components/documents/DocumentsWorkspace";
import { AppShell } from "@/components/layout/AppShell";
import { Sidebar } from "@/components/layout/Sidebar";
import { DocumentViewer } from "@/components/viewer/DocumentViewer";
import { useConversations } from "@/hooks/useConversations";
import { useDocuments } from "@/hooks/useDocuments";
import type { Conversation } from "@/types/conversation";
import type { Document } from "@/types/document";
import type { ViewerState } from "@/types/viewer";

export default function Home() {
  const { documents, loading, error, refreshDocuments } = useDocuments();
  const {
    conversations,
    loading: conversationsLoading,
    error: conversationsError,
    refreshConversations,
  } = useConversations();
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const selectedDocumentIdsRef = useRef<string[]>([]);
  selectedDocumentIdsRef.current = selectedDocumentIds;
  const [contextSelectionLabel, setContextSelectionLabel] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [isChatGenerating, setIsChatGenerating] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isConversationsOpen, setIsConversationsOpen] = useState(true);
  const [activeView, setActiveView] = useState<"assistant" | "documents">("assistant");
  const [viewer, setViewer] = useState<ViewerState | null>(null);
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

    setContextSelectionLabel(null);
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((selectedId) => selectedId !== documentId)
        : [...current, documentId]
    );
  }, [isChatGenerating]);

  const handleSelectDocumentContext = useCallback(
    (documentIds: string[], label: string | null = null) => {
      if (isChatGenerating) return;
      setSelectedDocumentIds([...documentIds]);
      setContextSelectionLabel(label);
    },
    [isChatGenerating]
  );

  const handleDocumentContextRestored = useCallback(
    (documentIds: string[]) => {
      if (isChatGenerating) {
        return;
      }
      const currentDocumentIds = selectedDocumentIdsRef.current;
      const unchanged =
        currentDocumentIds.length === documentIds.length &&
        currentDocumentIds.every(
          (documentId, index) => documentId === documentIds[index]
        );
      if (unchanged) return;
      setContextSelectionLabel(null);
      setSelectedDocumentIds([...documentIds]);
    },
    [isChatGenerating]
  );

  const handleNewConversation = useCallback(() => {
    setSelectedConversationId(null);
    setSelectedDocumentIds([]);
    setContextSelectionLabel(null);
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
      sidebarOpen={isSidebarOpen}
      sidebar={
        <Sidebar activeView={activeView} onNavigate={(view) => { setActiveView(view); setViewer(null); }} onClose={() => setIsSidebarOpen(false)}>
          <ConversationList conversations={conversations} loading={conversationsLoading} error={conversationsError} selectedConversationId={selectedConversationId} disabled={isChatGenerating} onNewConversation={handleNewConversation} onSelectConversation={setSelectedConversationId} isOpen={isConversationsOpen} onToggleOpen={() => setIsConversationsOpen((current) => !current)} onConversationsChanged={refreshConversations} />
        </Sidebar>
      }
    >
      <div className={`workspace-stage ${viewer ? "viewer-open" : ""}`}>
        <div className="assistant-workspace view-panel" hidden={activeView !== "assistant"}>
          <ChatWindow selectedConversationId={selectedConversationId} selectedDocumentIds={validSelectedDocumentIds} selectedDocuments={selectedDocuments} availableDocuments={documents} contextSelectionLabel={contextSelectionLabel} onToggleDocument={handleToggleDocument} onSelectDocumentContext={handleSelectDocumentContext} onConversationCreated={handleConversationCreated} onDocumentContextRestored={handleDocumentContextRestored} onGeneratingChange={setIsChatGenerating} onOpenSource={setViewer} sidebarOpen={isSidebarOpen} onOpenSidebar={() => setIsSidebarOpen(true)} />
        </div>
        <div className="documents-view view-panel" hidden={activeView !== "documents"}>
          <DocumentsWorkspace documents={documents} loading={loading} error={error} protectedDocumentIds={validSelectedDocumentIds} contextSelectionDisabled={isChatGenerating} onDocumentsChanged={refreshDocuments} onOpenDocument={setViewer} sidebarOpen={isSidebarOpen} onOpenSidebar={() => setIsSidebarOpen(true)} />
        </div>
        {viewer && <DocumentViewer viewer={viewer} onClose={() => setViewer(null)} />}
      </div>
    </AppShell>
  );
}
