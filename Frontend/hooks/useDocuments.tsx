"use client";

import { useCallback, useEffect, useRef, useState } from "react";

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
  const requestInFlightRef = useRef<Promise<void> | null>(null);
  const refreshRequestedRef = useRef(false);
  const isMountedRef = useRef(false);

  const refreshDocuments = useCallback(async () => {
    if (requestInFlightRef.current) {
      refreshRequestedRef.current = true;
      return requestInFlightRef.current;
    }

    const request = (async () => {
      do {
        refreshRequestedRef.current = false;

        try {
          if (isMountedRef.current) {
            setError(null);
          }

          const data = await getDocuments();

          if (isMountedRef.current) {
            setDocuments(data);
          }
        } catch (err) {
          if (isMountedRef.current) {
            setError(
              err instanceof Error
                ? err.message
                : "Impossible de charger les documents."
            );
          }
        } finally {
          if (isMountedRef.current) {
            setLoading(false);
          }
        }
      } while (refreshRequestedRef.current && isMountedRef.current);
    })();

    requestInFlightRef.current = request;

    try {
      await request;
    } finally {
      if (requestInFlightRef.current === request) {
        requestInFlightRef.current = null;
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    void refreshDocuments();

    return () => {
      isMountedRef.current = false;
    };
  }, [refreshDocuments]);

  useEffect(() => {
    const hasPendingDocuments = documents.some(
      (document) =>
        document.status === "queued" || document.status === "processing"
    );

    if (!hasPendingDocuments) {
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      await refreshDocuments();

      if (!cancelled) {
        timer = setTimeout(poll, 3000);
      }
    };

    timer = setTimeout(poll, 3000);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [documents, refreshDocuments]);

  return {
    documents,
    loading,
    error,
    refreshDocuments,
  };
}
