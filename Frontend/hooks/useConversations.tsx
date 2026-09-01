"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getConversations } from "@/lib/api/conversations";
import type { Conversation } from "@/types/conversation";

interface UseConversationsResult {
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
  refreshConversations: () => Promise<void>;
}

export function useConversations(): UseConversationsResult {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(false);

  const refreshConversations = useCallback(async () => {
    try {
      const data = await getConversations();

      if (isMountedRef.current) {
        setConversations(data);
        setError(null);
      }
    } catch {
      if (isMountedRef.current) {
        setError("Impossible de charger les conversations.");
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    void refreshConversations();

    return () => {
      isMountedRef.current = false;
    };
  }, [refreshConversations]);

  return {
    conversations,
    loading,
    error,
    refreshConversations,
  };
}
