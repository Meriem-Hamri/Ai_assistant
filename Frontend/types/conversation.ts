import type { ChatSource } from "./source";

export interface Conversation {
  id: string;
  title: string;
  active_document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[];
  created_at: string;
}
