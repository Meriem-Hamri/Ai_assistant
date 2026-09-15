import { apiFetch } from "./client";
import type {
  Conversation,
  ConversationMessage,
} from "@/types/conversation";

export async function getConversations(): Promise<Conversation[]> {
  return apiFetch<Conversation[]>("/conversations/");
}

export async function createConversation(
  title: string
): Promise<Conversation> {
  return apiFetch<Conversation>("/conversations/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });
}

export async function getConversationMessages(
  conversationId: string
): Promise<ConversationMessage[]> {
  return apiFetch<ConversationMessage[]>(
    `/conversations/${encodeURIComponent(conversationId)}/messages`
  );
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiFetch<void>(`/conversations/${encodeURIComponent(conversationId)}`, { method: "DELETE" });
}
