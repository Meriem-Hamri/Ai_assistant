"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api/chat";
import {
  createConversation,
  getConversationMessages,
} from "@/lib/api/conversations";
import type { ChatMessage, ChatRequest } from "@/types/chat";
import type {
  Conversation,
  ConversationMessage,
} from "@/types/conversation";

interface UseChatResult {
  messages: ChatMessage[];
  isLoadingHistory: boolean;
  isGenerating: boolean;
  error: string | null;
  sendMessage: (question: string, documentIds: string[]) => Promise<void>;
}

function toChatMessages(messages: ConversationMessage[]): ChatMessage[] {
  return messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    sources: message.sources,
    document_ids: message.document_ids,
  }));
}

export function useChat(
  conversationId: string | null,
  onConversationCreated: (conversation: Conversation) => void
): UseChatResult {
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
  const createdConversationInFlightRef = useRef<string | null>(null);

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

    if (
      requestInFlightRef.current &&
      createdConversationInFlightRef.current === conversationId
    ) {
      setMessagesConversationId(conversationId);
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
    async (question: string, documentIds: string[]) => {
      const trimmedQuestion = question.trim();
      if (!trimmedQuestion || requestInFlightRef.current) {
        return;
      }
      const submittedDocumentIds = [...documentIds];

      requestInFlightRef.current = true;
      ++historyRequestVersionRef.current;
      setIsLoadingHistoryState(false);
      setError(null);
      setErrorConversationId(null);
      setIsGenerating(true);

      let targetConversationId = conversationId;

      try {
        if (targetConversationId === null) {
          let conversation: Conversation;
          try {
            conversation = await createConversation(trimmedQuestion);
          } catch (creationError) {
            console.error("Conversation creation failed", creationError);
            setError("Impossible de créer la conversation.");
            setErrorConversationId(null);
            return;
          }

          targetConversationId = conversation.id;
          createdConversationInFlightRef.current = targetConversationId;
          activeConversationIdRef.current = targetConversationId;
          setMessagesConversationId(targetConversationId);
          onConversationCreated(conversation);
        }

        if (targetConversationId === null) {
          return;
        }
        const resolvedConversationId = targetConversationId;

        setMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "user",
            content: trimmedQuestion,
            document_ids: submittedDocumentIds,
          },
        ]);
        setMessagesConversationId(resolvedConversationId);

        const request: ChatRequest = {
          conversation_id: resolvedConversationId,
          question: trimmedQuestion,
          document_ids: [...submittedDocumentIds],
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
            await resynchronizeConversation(resolvedConversationId);
          } catch (synchronizationError) {
            console.error(
              "Conversation resynchronization failed",
              synchronizationError
            );
            if (activeConversationIdRef.current === resolvedConversationId) {
              setError("Impossible de resynchroniser la conversation.");
              setErrorConversationId(resolvedConversationId);
            }
          }
        } catch (requestError) {
          console.error("Chat request failed", requestError);
          if (activeConversationIdRef.current === resolvedConversationId) {
            setError(
              "Impossible d’obtenir une réponse pour le moment. Veuillez réessayer."
            );
            setErrorConversationId(resolvedConversationId);
          }

          try {
            await resynchronizeConversation(resolvedConversationId);
          } catch (synchronizationError) {
            console.error(
              "Conversation resynchronization after chat error failed",
              synchronizationError
            );
          }
        }
      } finally {
        createdConversationInFlightRef.current = null;
        requestInFlightRef.current = false;
        setIsGenerating(false);
      }
    },
    [conversationId, onConversationCreated, resynchronizeConversation]
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
