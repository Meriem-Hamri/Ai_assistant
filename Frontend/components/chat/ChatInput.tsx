"use client";
import { FormEvent, KeyboardEvent, useLayoutEffect, useRef, useState } from "react";

interface ChatInputProps { isGenerating: boolean; disabled?: boolean; onSend: (question: string) => Promise<void>; }

export function ChatInput({ isGenerating, disabled = false, onSend }: ChatInputProps) {
  const [question, setQuestion] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const canSend = question.trim().length > 0 && !isGenerating && !disabled;

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const previousScrollTop = textarea.scrollTop;
    const caretIsAtEnd = textarea.selectionEnd === textarea.value.length;
    const maxHeight = Number.parseFloat(getComputedStyle(textarea).maxHeight);

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
    textarea.scrollTop = caretIsAtEnd ? textarea.scrollHeight : previousScrollTop;
  }, [question]);

  const submit = async () => { if (!canSend) return; const value = question.trim(); setQuestion(""); await onSend(value); };
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); void submit(); };
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(); } };

  return <div className="chat-input-container">
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <label className="visually-hidden" htmlFor="chat-question">Votre question</label>
      <textarea ref={textareaRef} id="chat-question" className="chat-input" value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={handleKeyDown} placeholder="Posez une question sur vos documents" rows={1} disabled={isGenerating || disabled} />
      <button className="send-button" type="submit" disabled={!canSend} aria-label="Envoyer la question"><span aria-hidden="true">↑</span></button>
    </form>
    <p className="chat-input-hint">Entrée pour envoyer · Maj + Entrée pour une nouvelle ligne</p>
  </div>;
}
