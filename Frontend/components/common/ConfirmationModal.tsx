"use client";

import { useEffect } from "react";

interface ConfirmationModalProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  submitting: boolean;
  error?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmationModal({ open, title, description, confirmLabel = "Supprimer", submitting, error, onCancel, onConfirm }: ConfirmationModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape" && !submitting) onCancel(); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onCancel, open, submitting]);
  if (!open) return null;

  return <div className="modal-backdrop confirm-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !submitting) onCancel(); }}>
    <section className="confirmation-modal" role="alertdialog" aria-modal="true" aria-labelledby="confirmation-title" aria-describedby="confirmation-description">
      <span className="confirmation-icon" aria-hidden="true">!</span>
      <h2 id="confirmation-title">{title}</h2>
      <p id="confirmation-description">{description}</p>
      {error && <p className="confirmation-error" role="alert">{error}</p>}
      <footer><button type="button" className="secondary-button" disabled={submitting} onClick={onCancel}>Annuler</button><button type="button" className="danger-button" disabled={submitting} onClick={onConfirm}>{submitting ? "Suppression…" : confirmLabel}</button></footer>
    </section>
  </div>;
}
