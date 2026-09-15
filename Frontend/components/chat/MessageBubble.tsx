import type { ChatMessage } from "@/types/chat";
import type { Document } from "@/types/document";
import { MessageAttachments } from "./MessageAttachments";
import { MessageSources } from "./MessageSources";
import type { ViewerState } from "@/types/viewer";

interface MessageBubbleProps {
  message: ChatMessage;
  documents: Document[];
  onOpenSource: (viewer: ViewerState) => void;
}

export function MessageBubble({ message, documents, onOpenSource }: MessageBubbleProps) {
  const isUser = message.role === "user";
  return (
    <article className={`message-row ${isUser ? "message-user" : "message-assistant"}`}>
      <div className="message-content">
        <span className="visually-hidden">{isUser ? "Vous" : "Assistant"} : </span>
        {message.content}
        {isUser && (
          <MessageAttachments
            documentIds={message.document_ids}
            documents={documents}
          />
        )}
        {!isUser && <MessageSources sources={message.sources ?? []} onOpenSource={onOpenSource} />}
      </div>
    </article>
  );
}
