import type { ChatMessage } from "@/types/chat";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <article className={`message-row ${isUser ? "message-user" : "message-assistant"}`}>
      <div className="message-content">
        <span className="visually-hidden">{isUser ? "Vous" : "Assistant"} : </span>
        {message.content}
      </div>
    </article>
  );
}
