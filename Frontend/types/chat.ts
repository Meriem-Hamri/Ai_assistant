import type { ChatSource } from "./source";

export interface RagFilters {
  category: string | null;
  year: number | null;
  person: string | null;
  tags: string[];
  department: string | null;
  document_type: string | null;
}

export interface ChatRequest {
  conversation_id: string;
  question: string;
  document_ids: string[];
  category: string | null;
  year: number | null;
  person: string | null;
  tags: string[] | null;
  department: string | null;
  document_type: string | null;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  sources: ChatSource[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  document_ids: string[];
}
