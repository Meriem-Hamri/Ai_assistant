export interface ChatSource {
  document_id: string;
  document_name: string;
  page_number: number | null;
  chunk_id: string;
  excerpt: string;
  distance: number;
}
