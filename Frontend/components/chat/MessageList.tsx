"use client";

import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import type { ChatMessage } from "@/types/chat";
import type { Document } from "@/types/document";
import type { ViewerState } from "@/types/viewer";

interface MessageListProps { messages: ChatMessage[]; documents: Document[]; isGenerating: boolean; selectedDocumentName: string; onOpenSource: (viewer: ViewerState) => void; }

export function MessageList({ messages, documents, isGenerating, selectedDocumentName, onOpenSource }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, isGenerating]);

  if (messages.length === 0 && !isGenerating) {
    return (
      <div className="message-list chat-empty-state">
        <div className="welcome-mark" aria-hidden="true">A</div>
        <h2>Assistant AI</h2>
        <p>Posez une question sur vos documents.</p>
        <div className="active-scope"><span className="scope-indicator" aria-hidden="true" /><span>{selectedDocumentName}</span></div>
      </div>
    );
  }

  return (
    <div className="message-list" aria-live="polite" aria-relevant="additions">
      <div className="message-list-inner">
        {messages.map((message) => <MessageBubble key={message.id} message={message} documents={documents} onOpenSource={onOpenSource} />)}
        {isGenerating && <div className="chat-generating" role="status"><span className="generating-dot" aria-hidden="true" />L’assistant analyse les documents et prépare sa réponse…</div>}
        <div ref={endRef} aria-hidden="true" />
      </div>
    </div>
  );
}
