"use client";

import { useEffect, useState } from "react";

import { getDocuments } from "@/lib/api/documents";
import type { Document } from "@/types/document";

interface UseDocumentsResult {
  documents: Document[];
  loading: boolean;
  error: string | null;
}

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocuments() {
      try {
        setLoading(true);
        setError(null);

        const data = await getDocuments();
        setDocuments(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Impossible de charger les documents."
        );
      } finally {
        setLoading(false);
      }
    }

    loadDocuments();
  }, []);

  return {
    documents,
    loading,
    error,
  };
}