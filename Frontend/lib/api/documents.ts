import { apiFetch } from "./client";
import type { Document } from "@/types/document";

export async function getDocuments(): Promise<Document[]> {
  return apiFetch<Document[]>("/documents/");
}
