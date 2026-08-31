import { apiFetch, getApiUrl } from "./client";
import type { Document } from "@/types/document";

export async function getDocuments(): Promise<Document[]> {
  return apiFetch<Document[]>("/documents/");
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<Document>("/documents/", {
    method: "POST",
    body: formData,
  });
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiFetch<void>(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

export function getDocumentFileUrl(documentId: string): string {
  return getApiUrl(`/documents/${documentId}/file`);
}