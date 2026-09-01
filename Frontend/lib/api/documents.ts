import { apiFetch, getApiUrl } from "./client";
import type { Document, OcrLanguage } from "@/types/document";

export async function getDocuments(): Promise<Document[]> {
  return apiFetch<Document[]>("/documents/");
}

export async function uploadDocument(
  file: File,
  ocrLanguage: OcrLanguage = "fr"
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("ocr_language", ocrLanguage);

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

interface DocumentFileUrlOptions {
  documentName?: string;
  pageNumber?: number | null;
}

export function getDocumentFileUrl(
  documentId: string,
  options?: DocumentFileUrlOptions
): string {
  const fileUrl = getApiUrl(
    `/documents/${encodeURIComponent(documentId)}/file`
  );
  const pageNumber = options?.pageNumber;
  const isPdf = options?.documentName?.toLowerCase().endsWith(".pdf");

  if (isPdf && pageNumber !== null && pageNumber !== undefined) {
    return `${fileUrl}#page=${pageNumber}`;
  }

  return fileUrl;
}
