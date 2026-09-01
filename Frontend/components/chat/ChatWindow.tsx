"use client";
import { useEffect } from "react";
import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";
import { PromptAttachments } from "./PromptAttachments";
import { useChat } from "@/hooks/useChat";
import type { Conversation } from "@/types/conversation";
import type { Document } from "@/types/document";

interface ChatWindowProps { selectedConversationId: string | null; selectedDocumentIds: string[]; selectedDocuments: Document[]; availableDocuments: Document[]; onRemoveDocument: (documentId: string) => void; onConversationCreated: (conversation: Conversation) => void; onDocumentContextRestored: (documentIds: string[]) => void; onGeneratingChange: (isGenerating: boolean) => void; }

export function ChatWindow({ selectedConversationId, selectedDocumentIds, selectedDocuments, availableDocuments, onRemoveDocument, onConversationCreated, onDocumentContextRestored, onGeneratingChange }: ChatWindowProps) {
  const { messages, isLoadingHistory, isGenerating, error, sendMessage } = useChat(selectedConversationId, onConversationCreated);
  useEffect(() => {
    if (
      selectedConversationId === null ||
      isLoadingHistory ||
      isGenerating ||
      error
    ) {
      return;
    }

    const lastUserMessage = messages.findLast(
      (message) => message.role === "user"
    );
    onDocumentContextRestored([...(lastUserMessage?.document_ids ?? [])]);
  }, [
    error,
    isGenerating,
    isLoadingHistory,
    messages,
    onDocumentContextRestored,
    selectedConversationId,
  ]);
  const contextName = selectedDocuments.length === 0
    ? "Tous les documents"
    : selectedDocuments.length === 1
      ? selectedDocuments[0].filename
      : `${selectedDocuments.length} documents`;
  const handleSend = async (question: string) => {
    const submittedDocumentIds = [...selectedDocumentIds];
    onGeneratingChange(true);
    try {
      await sendMessage(question, submittedDocumentIds);
    } finally {
      onGeneratingChange(false);
    }
  };
  return <section className="chat-window" aria-label="Chat documentaire">
    <header className="chat-header"><div className="chat-context" title={contextName}><span className="scope-indicator" aria-hidden="true" /><span>Contexte : {contextName}</span></div></header>
    {isLoadingHistory ? (
      <div className="chat-history-loading" role="status">Chargement de la conversation...</div>
    ) : (
      <MessageList messages={messages} documents={availableDocuments} isGenerating={isGenerating} selectedDocumentName={contextName} />
    )}
    {error && <p className="chat-error" role="alert">{error}</p>}
    <div className="composer-area">
      <PromptAttachments
        documents={selectedDocuments}
        disabled={isGenerating}
        onRemoveDocument={onRemoveDocument}
      />
      <ChatInput disabled={isLoadingHistory} isGenerating={isGenerating} onSend={handleSend} />
    </div>
  </section>;
}
