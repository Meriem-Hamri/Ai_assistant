import { ConversationItem } from "./ConversationItem";
import type { Conversation } from "@/types/conversation";

interface ConversationListProps {
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
  selectedConversationId: string | null;
  disabled: boolean;
  onSelectConversation: (conversationId: string) => void;
}

export function ConversationList({
  conversations,
  loading,
  error,
  selectedConversationId,
  disabled,
  onSelectConversation,
}: ConversationListProps) {
  return (
    <section
      className="conversation-library"
      aria-labelledby="conversations-heading"
    >
      <h2 className="sidebar-section-title" id="conversations-heading">
        Conversations
      </h2>

      {loading ? (
        <p className="sidebar-status">Chargement des conversations...</p>
      ) : error ? (
        <p className="sidebar-status sidebar-status-error" role="status">
          {error}
        </p>
      ) : conversations.length === 0 ? (
        <p className="sidebar-status">Aucune conversation</p>
      ) : (
        <div className="conversation-list">
          {conversations.map((conversation) => (
            <ConversationItem
              key={conversation.id}
              conversation={conversation}
              selected={conversation.id === selectedConversationId}
              disabled={disabled}
              onSelect={onSelectConversation}
            />
          ))}
        </div>
      )}
    </section>
  );
}
