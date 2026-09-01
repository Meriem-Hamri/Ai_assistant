"use client";

import { ChangeEvent, useRef, useState } from "react";

import { uploadDocument } from "@/lib/api/documents";
import type { OcrLanguage } from "@/types/document";

interface DocumentUploadProps {
  onUploaded: () => Promise<void>;
}

export function DocumentUpload({
  onUploaded,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ocrLanguage, setOcrLanguage] = useState<OcrLanguage>("fr");

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

      await uploadDocument(file, ocrLanguage);
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
      <label className="upload-language-label" htmlFor="ocr-language">
        Langue du document
      </label>
      <select
        id="ocr-language"
        className="upload-language-select"
        value={ocrLanguage}
        disabled={uploading}
        onChange={(event) => setOcrLanguage(event.target.value as OcrLanguage)}
      >
        <option value="fr">Français</option>
        <option value="ar">Arabe</option>
        <option value="mixed">Arabe + Français</option>
      </select>
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
          ? "Import en cours..."
          : "+ Importer"}
      </button>

      {error && (
        <p className="upload-error">
          {error}
        </p>
      )}
    </div>
  );
}
