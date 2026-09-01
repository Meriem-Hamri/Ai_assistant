"use client";
import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";
import { useChat } from "@/hooks/useChat";

interface ChatWindowProps { selectedConversationId: string | null; selectedDocumentId: string | null; selectedDocumentName?: string | null; onGeneratingChange: (isGenerating: boolean) => void; }

export function ChatWindow({ selectedConversationId, selectedDocumentId, selectedDocumentName, onGeneratingChange }: ChatWindowProps) {
  const { messages, isLoadingHistory, isGenerating, error, sendMessage } = useChat(selectedConversationId);
  const contextName = selectedDocumentName ?? "Tous les documents";
  const handleSend = async (question: string) => {
    onGeneratingChange(true);
    try {
      await sendMessage(question, selectedDocumentId);
    } finally {
      onGeneratingChange(false);
    }
  };
  return <section className="chat-window" aria-label="Chat documentaire">
    <header className="chat-header"><div className="chat-context" title={contextName}><span className="scope-indicator" aria-hidden="true" /><span>Contexte : {contextName}</span></div></header>
    {isLoadingHistory ? (
      <div className="chat-history-loading" role="status">Chargement de la conversation...</div>
    ) : (
      <MessageList messages={messages} isGenerating={isGenerating} selectedDocumentName={contextName} />
    )}
    {error && <p className="chat-error" role="alert">{error}</p>}
    <ChatInput disabled={selectedConversationId === null || isLoadingHistory} isGenerating={isGenerating} onSend={handleSend} />
  </section>;
}
