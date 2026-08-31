import { apiFetch } from "./client";
import type { ChatRequest, ChatResponse } from "@/types/chat";

export function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}
