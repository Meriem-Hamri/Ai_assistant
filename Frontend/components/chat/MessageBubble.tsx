import type { ChatMessage } from "@/types/chat";
import { MessageSources } from "./MessageSources";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <article className={`message-row ${isUser ? "message-user" : "message-assistant"}`}>
      <div className="message-content">
        <span className="visually-hidden">{isUser ? "Vous" : "Assistant"} : </span>
        {message.content}
        {!isUser && <MessageSources sources={message.sources ?? []} />}
      </div>
    </article>
  );
}
