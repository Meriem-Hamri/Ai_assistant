"use client";

import { ChangeEvent, useRef, useState } from "react";

import { uploadDocument } from "@/lib/api/documents";

interface DocumentUploadProps {
  onUploaded: () => Promise<void>;
}

export function DocumentUpload({
  onUploaded,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    try {
      setUploading(true);
      setError(null);

      await uploadDocument(file);
      await onUploaded();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Impossible d'importer le document."
      );
    } finally {
      setUploading(false);

      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <div className="document-upload">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.png,.jpg,.jpeg"
        aria-label="Sélectionner un document à importer"
        hidden
        disabled={uploading}
        onChange={handleFileChange}
      />

      <button
        type="button"
        className="upload-button"
        disabled={uploading}
        onClick={() => inputRef.current?.click()}
      >
        {uploading
          ? "Analyse du document en cours..."
          : "+ Importer un document"}
      </button>

      {uploading && (
        <p className="upload-status">
          Extraction, analyse et indexation en cours. Cela peut prendre quelques minutes.
        </p>
      )}

      {error && (
        <p className="upload-error">
          {error}
        </p>
      )}
    </div>
  );
}
