"use client";
import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";
import { useChat } from "@/hooks/useChat";

interface ChatWindowProps { selectedDocumentId: string | null; selectedDocumentName?: string | null; }

export function ChatWindow({ selectedDocumentId, selectedDocumentName }: ChatWindowProps) {
  const { messages, isGenerating, error, sendMessage } = useChat();
  const contextName = selectedDocumentName ?? "Tous les documents";
  return <section className="chat-window" aria-label="Chat documentaire">
    <header className="chat-header"><div className="chat-context" title={contextName}><span className="scope-indicator" aria-hidden="true" /><span>Contexte : {contextName}</span></div></header>
    <MessageList messages={messages} isGenerating={isGenerating} selectedDocumentName={contextName} />
    {error && <p className="chat-error" role="alert">{error}</p>}
    <ChatInput isGenerating={isGenerating} onSend={(question) => sendMessage(question, selectedDocumentId)} />
  </section>;
}
