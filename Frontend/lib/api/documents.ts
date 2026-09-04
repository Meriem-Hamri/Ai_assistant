import { apiFetch, getApiUrl } from "./client";
import type { Document, DocumentMetadataOptions, DocumentUploadMetadata, OcrLanguage } from "@/types/document";

export async function getDocuments(): Promise<Document[]> {
  return apiFetch<Document[]>("/documents/");
}

export async function uploadDocument(
  file: File,
  ocrLanguage: OcrLanguage = "fr",
  metadata: DocumentUploadMetadata = {},
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("ocr_language", ocrLanguage);
  for (const field of ["title", "category", "department", "document_type"] as const) {
    const value = metadata[field]?.trim();
    if (value) formData.append(field, value);
  }
  if (metadata.year) formData.append("year", String(metadata.year));
  for (const tag of metadata.tags ?? []) formData.append("tags", tag);

  return apiFetch<Document>("/documents/", {
    method: "POST",
    body: formData,
  });
}

export async function getDocumentMetadataOptions(): Promise<DocumentMetadataOptions> {
  return apiFetch<DocumentMetadataOptions>("/documents/metadata-options");
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
