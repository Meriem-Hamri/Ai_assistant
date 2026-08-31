"use client";

import { useCallback, useEffect, useState } from "react";

import { getDocuments } from "@/lib/api/documents";
import type { Document } from "@/types/document";

interface UseDocumentsResult {
  documents: Document[];
  loading: boolean;
  error: string | null;
  refreshDocuments: () => Promise<void>;
}

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshDocuments = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    void refreshDocuments();
  }, [refreshDocuments]);

  return {
    documents,
    loading,
    error,
    refreshDocuments,
  };
}