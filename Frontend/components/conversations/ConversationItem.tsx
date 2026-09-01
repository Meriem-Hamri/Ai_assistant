import type { Conversation } from "@/types/conversation";

interface ConversationItemProps {
  conversation: Conversation;
  selected: boolean;
  disabled: boolean;
  onSelect: (conversationId: string) => void;
}

export function ConversationItem({
  conversation,
  selected,
  disabled,
  onSelect,
}: ConversationItemProps) {
  return (
    <button
      className={`conversation-item${selected ? " selected" : ""}`}
      type="button"
      title={conversation.title}
      aria-pressed={selected}
      disabled={disabled}
      onClick={() => onSelect(conversation.id)}
    >
      {conversation.title}
    </button>
  );
}
