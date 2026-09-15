import type { Conversation } from "@/types/conversation";

interface ConversationItemProps {
  conversation: Conversation;
  selected: boolean;
  disabled: boolean;
  onSelect: (conversationId: string) => void;
  onRequestDelete: () => void;
}

export function ConversationItem({
  conversation,
  selected,
  disabled,
  onSelect,
  onRequestDelete,
}: ConversationItemProps) {
  return (
    <div className={`conversation-entry${selected ? " selected" : ""}`}>
      <button className="conversation-item" type="button" title={conversation.title} aria-pressed={selected} disabled={disabled} onClick={() => onSelect(conversation.id)}>{conversation.title}</button>
      <button className="conversation-delete" type="button" aria-label={`Supprimer ${conversation.title}`} title="Supprimer la conversation" disabled={disabled} onClick={onRequestDelete}>×</button>
    </div>
  );
}
