"use client";

import { useCallback, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api/chat";
import type { ChatMessage, ChatRequest } from "@/types/chat";

interface UseChatResult {
  messages: ChatMessage[];
  isGenerating: boolean;
  error: string | null;
  sendMessage: (question: string, documentId: string | null) => Promise<void>;
}

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestInFlight = useRef(false);

  const sendMessage = useCallback(async (question: string, documentId: string | null) => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || requestInFlight.current) return;

    requestInFlight.current = true;
    setError(null);
    setMessages((current) => [...current, {
      id: crypto.randomUUID(), role: "user", content: trimmedQuestion,
    }]);
    setIsGenerating(true);

    const request: ChatRequest = {
      question: trimmedQuestion,
      document_id: documentId,
      category: null,
      year: null,
      person: null,
      tags: null,
      department: null,
      document_type: null,
    };

    try {
      const response = await sendChatMessage(request);
      setMessages((current) => [...current, {
        id: crypto.randomUUID(), role: "assistant", content: response.answer, sources: response.sources,
      }]);
    } catch (requestError) {
      console.error("Chat request failed", requestError);
      setError("Impossible d’obtenir une réponse pour le moment. Veuillez réessayer.");
    } finally {
      requestInFlight.current = false;
      setIsGenerating(false);
    }
  }, []);

  return { messages, isGenerating, error, sendMessage };
}
