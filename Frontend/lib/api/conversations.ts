import { apiFetch } from "./client";
import type {
  Conversation,
  ConversationMessage,
} from "@/types/conversation";

export async function getConversations(): Promise<Conversation[]> {
  return apiFetch<Conversation[]>("/conversations/");
}

export async function getConversationMessages(
  conversationId: string
): Promise<ConversationMessage[]> {
  return apiFetch<ConversationMessage[]>(
    `/conversations/${encodeURIComponent(conversationId)}/messages`
  );
}
