"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api/chat";
import { getConversationMessages } from "@/lib/api/conversations";
import type { ChatMessage, ChatRequest } from "@/types/chat";
import type { ConversationMessage } from "@/types/conversation";

interface UseChatResult {
  messages: ChatMessage[];
  isLoadingHistory: boolean;
  isGenerating: boolean;
  error: string | null;
  sendMessage: (question: string, documentId: string | null) => Promise<void>;
}

function toChatMessages(messages: ConversationMessage[]): ChatMessage[] {
  return messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    sources: message.sources,
  }));
}

export function useChat(conversationId: string | null): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messagesConversationId, setMessagesConversationId] = useState<
    string | null
  >(null);
  const [isLoadingHistoryState, setIsLoadingHistoryState] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorConversationId, setErrorConversationId] = useState<string | null>(
    null
  );
  const activeConversationIdRef = useRef(conversationId);
  const historyRequestVersionRef = useRef(0);
  const requestInFlightRef = useRef(false);

  activeConversationIdRef.current = conversationId;

  useEffect(() => {
    const requestVersion = ++historyRequestVersionRef.current;

    if (conversationId === null) {
      setMessages([]);
      setMessagesConversationId(null);
      setError(null);
      setErrorConversationId(null);
      setIsLoadingHistoryState(false);
      return;
    }

    setMessages([]);
    setMessagesConversationId(null);
    setError(null);
    setErrorConversationId(null);
    setIsLoadingHistoryState(true);

    void getConversationMessages(conversationId)
      .then((history) => {
        if (
          historyRequestVersionRef.current !== requestVersion ||
          activeConversationIdRef.current !== conversationId
        ) {
          return;
        }

        setMessages(toChatMessages(history));
        setMessagesConversationId(conversationId);
      })
      .catch((historyError: unknown) => {
        if (
          historyRequestVersionRef.current !== requestVersion ||
          activeConversationIdRef.current !== conversationId
        ) {
          return;
        }

        console.error("Conversation history request failed", historyError);
        setMessages([]);
        setMessagesConversationId(conversationId);
        setError("Impossible de charger la conversation.");
        setErrorConversationId(conversationId);
      })
      .finally(() => {
        if (
          historyRequestVersionRef.current === requestVersion &&
          activeConversationIdRef.current === conversationId
        ) {
          setIsLoadingHistoryState(false);
        }
      });
  }, [conversationId]);

  const resynchronizeConversation = useCallback(
    async (targetConversationId: string): Promise<void> => {
      const updatesVisibleConversation =
        activeConversationIdRef.current === targetConversationId;
      const requestVersion = updatesVisibleConversation
        ? ++historyRequestVersionRef.current
        : null;
      const history = await getConversationMessages(targetConversationId);

      if (
        requestVersion === null ||
        historyRequestVersionRef.current !== requestVersion ||
        activeConversationIdRef.current !== targetConversationId
      ) {
        return;
      }

      setMessages(toChatMessages(history));
      setMessagesConversationId(targetConversationId);
    },
    []
  );

  const sendMessage = useCallback(
    async (question: string, documentId: string | null) => {
      const targetConversationId = conversationId;
      const trimmedQuestion = question.trim();
      if (
        targetConversationId === null ||
        !trimmedQuestion ||
        requestInFlightRef.current
      ) {
        return;
      }

      requestInFlightRef.current = true;
      ++historyRequestVersionRef.current;
      setIsLoadingHistoryState(false);
      setError(null);
      setErrorConversationId(null);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "user",
          content: trimmedQuestion,
        },
      ]);
      setMessagesConversationId(targetConversationId);
      setIsGenerating(true);

      const request: ChatRequest = {
        conversation_id: targetConversationId,
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
        await sendChatMessage(request);

        try {
          await resynchronizeConversation(targetConversationId);
        } catch (synchronizationError) {
          console.error(
            "Conversation resynchronization failed",
            synchronizationError
          );
          if (activeConversationIdRef.current === targetConversationId) {
            setError("Impossible de resynchroniser la conversation.");
            setErrorConversationId(targetConversationId);
          }
        }
      } catch (requestError) {
        console.error("Chat request failed", requestError);
        if (activeConversationIdRef.current === targetConversationId) {
          setError(
            "Impossible d’obtenir une réponse pour le moment. Veuillez réessayer."
          );
          setErrorConversationId(targetConversationId);
        }

        try {
          await resynchronizeConversation(targetConversationId);
        } catch (synchronizationError) {
          console.error(
            "Conversation resynchronization after chat error failed",
            synchronizationError
          );
        }
      } finally {
        requestInFlightRef.current = false;
        setIsGenerating(false);
      }
    },
    [conversationId, resynchronizeConversation]
  );

  const hasCurrentConversationMessages =
    messagesConversationId === conversationId;
  const isLoadingHistory =
    conversationId !== null &&
    (isLoadingHistoryState || !hasCurrentConversationMessages);
  return {
    messages: hasCurrentConversationMessages ? messages : [],
    isLoadingHistory,
    isGenerating,
    error: errorConversationId === conversationId ? error : null,
    sendMessage,
  };
}
