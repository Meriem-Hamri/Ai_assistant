import { ConversationItem } from "./ConversationItem";
import type { Conversation } from "@/types/conversation";
import { useState } from "react";
import { ConfirmationModal } from "@/components/common/ConfirmationModal";
import { deleteConversation } from "@/lib/api/conversations";

interface ConversationListProps {
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
  selectedConversationId: string | null;
  disabled: boolean;
  onNewConversation: () => void;
  onSelectConversation: (conversationId: string) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
  onConversationsChanged: () => Promise<void>;
}

export function ConversationList({
  conversations,
  loading,
  error,
  selectedConversationId,
  disabled,
  onNewConversation,
  onSelectConversation,
  isOpen,
  onToggleOpen,
  onConversationsChanged,
}: ConversationListProps) {
  const [pendingDelete, setPendingDelete] = useState<Conversation | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function confirmDelete() {
    if (!pendingDelete || deleting) return;
    try {
      setDeleting(true); setDeleteError(null);
      await deleteConversation(pendingDelete.id);
      if (pendingDelete.id === selectedConversationId) onNewConversation();
      await onConversationsChanged();
      setPendingDelete(null);
    } catch {
      setDeleteError("La conversation n’a pas pu être supprimée.");
    } finally {
      setDeleting(false);
    }
  }
  return (
    <section
      className="conversation-library"
      aria-labelledby="conversations-heading"
    >
      <h2 className="sidebar-section-title" id="conversations-heading">
        <button
          className="sidebar-section-toggle"
          type="button"
          aria-expanded={isOpen}
          aria-controls="conversations-panel"
          aria-label={`${isOpen ? "Replier" : "Ouvrir"} la section Conversations`}
          onClick={onToggleOpen}
        >
          <span aria-hidden="true">{isOpen ? "▼" : "▶"}</span>
          <span>Historique / Conversations</span>
        </button>
      </h2>
      <div className="sidebar-section-content" id="conversations-panel" hidden={!isOpen}>
        <button
          className="new-conversation-button"
          type="button"
          disabled={disabled}
          onClick={onNewConversation}
        >
          Nouveau chat
        </button>

        {loading ? (
          <p className="sidebar-status">Chargement des conversations...</p>
        ) : error ? (
          <p className="sidebar-status sidebar-status-error" role="status">
            {error}
          </p>
        ) : conversations.length === 0 ? (
          <p className="sidebar-status">Aucune conversation</p>
        ) : (
          <div className="conversation-list">
            {conversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                selected={conversation.id === selectedConversationId}
                disabled={disabled}
                onSelect={onSelectConversation}
                onRequestDelete={() => { setDeleteError(null); setPendingDelete(conversation); }}
              />
            ))}
          </div>
        )}
      </div>
      <ConfirmationModal open={pendingDelete !== null} title="Supprimer la conversation ?" description={`${pendingDelete?.title ?? "Cette conversation"} sera supprimée définitivement.`} submitting={deleting} error={deleteError} onCancel={() => { setPendingDelete(null); setDeleteError(null); }} onConfirm={() => void confirmDelete()} />
    </section>
  );
}
