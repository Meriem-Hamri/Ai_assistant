"use client";

import { ChangeEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { getDocumentMetadataOptions, uploadDocument } from "@/lib/api/documents";
import { assessMetadataValue, FALLBACK_METADATA_OPTIONS, FUZZY_STRONG_THRESHOLD, normalizeMetadataValue } from "@/lib/documentMetadata";
import type { DocumentMetadataOptions, MetadataField, OcrLanguage } from "@/types/document";

interface DocumentUploadProps {
  onUploaded: () => Promise<void>;
  variant?: "sidebar" | "workspace";
}

const FIELD_LABELS: Record<MetadataField, string> = {
  category: "Catégorie",
  department: "Département",
  document_type: "Type de document",
};

interface ReferenceFieldProps {
  field: MetadataField;
  value: string;
  options: string[];
  acceptedCustom?: string;
  onChange: (value: string) => void;
  onAcceptCustom: (normalized: string) => void;
}

function ReferenceField({ field, value, options, acceptedCustom, onChange, onAcceptCustom }: ReferenceFieldProps) {
  const assessment = assessMetadataValue(value, options, acceptedCustom);
  const listId = `${field}-options`;
  return (
    <div className="metadata-field">
      <label htmlFor={`metadata-${field}`}>{FIELD_LABELS[field]}</label>
      <input id={`metadata-${field}`} list={listId} value={value} placeholder={`Choisir ou saisir ${field === "document_type" ? "un type" : "une valeur"}`} onChange={(event) => onChange(event.target.value)} />
      <datalist id={listId}>{options.map((option) => <option key={option} value={option} />)}</datalist>
      {assessment.kind === "suggestion" && (
        <div className={`metadata-assistance ${assessment.score >= FUZZY_STRONG_THRESHOLD ? "strong" : ""}`}>
          <span>Voulez-vous dire « {assessment.suggestion} » ?</span>
          <div><button type="button" onClick={() => onChange(assessment.suggestion)}>Utiliser {assessment.suggestion}</button><button type="button" onClick={() => onAcceptCustom(normalizeMetadataValue(assessment.value))}>Conserver ma saisie</button></div>
        </div>
      )}
      {assessment.kind === "new" && (
        <div className="metadata-assistance new-value">
          <span>« {assessment.value} » n’existe pas encore. Créer cette nouvelle valeur ?</span>
          <div><button type="button" onClick={() => onAcceptCustom(normalizeMetadataValue(assessment.value))}>Créer</button><button type="button" onClick={() => onChange("")}>Annuler</button></div>
        </div>
      )}
      {assessment.kind === "accepted" && <span className="metadata-confirmed">Nouvelle valeur confirmée</span>}
    </div>
  );
}

export function DocumentUpload({ onUploaded, variant = "sidebar" }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ocrLanguage, setOcrLanguage] = useState<OcrLanguage>("fr");
  const [title, setTitle] = useState("");
  const [year, setYear] = useState("");
  const [referenceValues, setReferenceValues] = useState<Record<MetadataField, string>>({ category: "", department: "", document_type: "" });
  const [acceptedCustom, setAcceptedCustom] = useState<Partial<Record<MetadataField, string>>>({});
  const [tagInput, setTagInput] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [options, setOptions] = useState<DocumentMetadataOptions>(FALLBACK_METADATA_OPTIONS);

  useEffect(() => {
    if (!file) return;
    let cancelled = false;
    void getDocumentMetadataOptions().then((data) => { if (!cancelled) setOptions(data); }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [file]);

  useEffect(() => {
    if (!file) return;
    const closeOnEscape = (event: globalThis.KeyboardEvent) => { if (event.key === "Escape" && !uploading) setFile(null); };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [file, uploading]);

  const assessments = useMemo(() => Object.fromEntries((Object.keys(referenceValues) as MetadataField[]).map((field) => [field, assessMetadataValue(referenceValues[field], options[field], acceptedCustom[field])])) as Record<MetadataField, ReturnType<typeof assessMetadataValue>>, [acceptedCustom, options, referenceValues]);

  function resetForm() {
    setFile(null); setTitle(""); setYear(""); setTags([]); setTagInput(""); setReferenceValues({ category: "", department: "", document_type: "" }); setAcceptedCustom({}); setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    setFile(selectedFile);
    setError(null);
  }

  function updateReference(field: MetadataField, value: string) {
    setReferenceValues((current) => ({ ...current, [field]: value }));
    setAcceptedCustom((current) => ({ ...current, [field]: undefined }));
  }

  function addTag() {
    const cleaned = tagInput.trim().replace(/\s+/g, " ");
    if (cleaned && !tags.some((tag) => normalizeMetadataValue(tag) === normalizeMetadataValue(cleaned))) setTags((current) => [...current, cleaned]);
    setTagInput("");
  }

  function handleTagKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") { event.preventDefault(); addTag(); }
  }

  async function handleSubmit() {
    if (!file) return;
    if (Object.values(assessments).some((assessment) => assessment.kind === "suggestion" || assessment.kind === "new")) {
      setError("Validez les suggestions ou les nouvelles valeurs avant l’import.");
      return;
    }
    const parsedYear = year ? Number(year) : undefined;
    if (parsedYear !== undefined && (!Number.isInteger(parsedYear) || parsedYear < 1000 || parsedYear > 9999)) {
      setError("L’année doit comporter quatre chiffres.");
      return;
    }
    try {
      setUploading(true); setError(null);
      const pendingTag = tagInput.trim().replace(/\s+/g, " ");
      const submittedTags = pendingTag && !tags.some((tag) => normalizeMetadataValue(tag) === normalizeMetadataValue(pendingTag)) ? [...tags, pendingTag] : tags;
      await uploadDocument(file, ocrLanguage, {
        title,
        category: assessments.category.value,
        department: assessments.department.value,
        document_type: assessments.document_type.value,
        year: parsedYear,
        tags: submittedTags,
      });
      await onUploaded();
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d’importer le document.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className={`document-upload document-upload-${variant}`}>
      <input ref={inputRef} type="file" accept=".pdf,.docx,.png,.jpg,.jpeg" aria-label="Sélectionner un document à importer" hidden disabled={uploading} onChange={handleFileChange} />
      <button type="button" className="upload-button" disabled={uploading} onClick={() => inputRef.current?.click()}>{uploading ? "Import en cours…" : "+ Importer"}</button>

      {file && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !uploading) resetForm(); }}>
          <section className="import-modal" role="dialog" aria-modal="true" aria-labelledby="import-modal-title">
            <header><div><p>Import documentaire</p><h2 id="import-modal-title">Ajouter un document</h2></div><button type="button" className="modal-close" aria-label="Fermer" disabled={uploading} onClick={resetForm}>×</button></header>
            <div className="selected-file"><span aria-hidden="true"><svg viewBox="0 0 20 20"><path d="M5.75 2.75h5.5l3 3v11.5h-8.5a1.5 1.5 0 0 1-1.5-1.5V4.25a1.5 1.5 0 0 1 1.5-1.5Z"/><path d="M11.25 2.75v3h3"/></svg></span><div><strong>{file.name}</strong><small>{(file.size / (1024 * 1024)).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} Mo</small></div><button type="button" disabled={uploading} onClick={() => inputRef.current?.click()}>Changer</button></div>
            <div className="import-form">
              <div className="metadata-field"><label htmlFor="metadata-title">Titre <span>facultatif</span></label><input id="metadata-title" value={title} placeholder="Titre affiché dans la bibliothèque" onChange={(event) => setTitle(event.target.value)} /></div>
              {(Object.keys(referenceValues) as MetadataField[]).map((field) => <ReferenceField key={field} field={field} value={referenceValues[field]} options={options[field]} acceptedCustom={acceptedCustom[field]} onChange={(value) => updateReference(field, value)} onAcceptCustom={(normalized) => setAcceptedCustom((current) => ({ ...current, [field]: normalized }))} />)}
              <div className="metadata-field"><label htmlFor="metadata-tags">Tags <span>facultatif</span></label><div className="tag-editor">{tags.map((tag) => <span key={normalizeMetadataValue(tag)}>{tag}<button type="button" aria-label={`Retirer ${tag}`} onClick={() => setTags((current) => current.filter((value) => value !== tag))}>×</button></span>)}<input id="metadata-tags" value={tagInput} placeholder={tags.length ? "+ ajouter" : "Saisir un tag puis Entrée"} onChange={(event) => setTagInput(event.target.value)} onKeyDown={handleTagKeyDown} onBlur={addTag} /></div></div>
              <details className="additional-information"><summary>Informations supplémentaires</summary><div><label htmlFor="metadata-year">Année <span>facultatif</span></label><input id="metadata-year" inputMode="numeric" maxLength={4} value={year} placeholder="2026" onChange={(event) => setYear(event.target.value.replace(/\D/g, ""))} /><label htmlFor="ocr-language">Langue du document</label><select id="ocr-language" value={ocrLanguage} onChange={(event) => setOcrLanguage(event.target.value as OcrLanguage)}><option value="fr">Français</option><option value="ar">Arabe</option><option value="mixed">Arabe + Français</option></select></div></details>
            </div>
            {error && <p className="modal-error" role="alert">{error}</p>}
            <footer><p>Les champs vides pourront être complétés automatiquement pendant le traitement.</p><div><button type="button" className="secondary-button" disabled={uploading} onClick={resetForm}>Annuler</button><button type="button" className="primary-button" disabled={uploading} onClick={() => void handleSubmit()}>{uploading ? "Import en cours…" : "Importer"}</button></div></footer>
          </section>
        </div>
      )}
    </div>
  );
}
