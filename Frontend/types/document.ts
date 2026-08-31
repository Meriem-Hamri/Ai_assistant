export interface Document {
  id: string;
  filename: string;
  type: string;
  page_count: number;
  size: number;
  created_at: string;
  status: string;

  title: string | null;
  category: string | null;
  year: number | null;
  person: string | null;
  department: string | null;
  document_type: string | null;
  tags: string[];
}
