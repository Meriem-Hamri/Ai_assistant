import type { Conversation } from "@/types/conversation";

interface ConversationItemProps {
  conversation: Conversation;
}

export function ConversationItem({
  conversation,
}: ConversationItemProps) {
  return (
    <div className="conversation-item" title={conversation.title}>
      {conversation.title}
    </div>
  );
}
