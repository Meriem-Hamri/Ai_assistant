import { apiFetch } from "./client";
import type { Conversation } from "@/types/conversation";

export async function getConversations(): Promise<Conversation[]> {
  return apiFetch<Conversation[]>("/conversations/");
}
