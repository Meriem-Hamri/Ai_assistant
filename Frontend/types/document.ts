export type DocumentStatus =
  | "queued"
  | "processing"
  | "ready"
  | "error";

export type OcrLanguage = "fr" | "ar" | "mixed";

export type MetadataField = "category" | "department" | "document_type";

export interface DocumentMetadataOptions {
  category: string[];
  department: string[];
  document_type: string[];
}

export interface DocumentUploadMetadata {
  title?: string;
  category?: string;
  department?: string;
  document_type?: string;
  year?: number;
  tags?: string[];
}

export interface Document {
  id: string;
  filename: string;
  type: string;
  page_count: number;
  size: number;
  created_at: string;
  status: DocumentStatus;

  title: string | null;
  category: string | null;
  year: number | null;
  person: string | null;
  department: string | null;
  document_type: string | null;
  tags: string[];
  ocr_language: OcrLanguage;
}
