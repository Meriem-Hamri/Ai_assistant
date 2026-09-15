import type { Document, DocumentMetadataOptions, MetadataField } from "@/types/document";

export const FUZZY_STRONG_THRESHOLD = 0.84;
export const FUZZY_POSSIBLE_THRESHOLD = 0.72;

export const FALLBACK_METADATA_OPTIONS: DocumentMetadataOptions = {
  category: ["Finance", "Ressources humaines", "Informatique", "Juridique", "Commercial", "Marketing", "Formation", "Administration", "Opérations"],
  department: ["Direction générale", "Finance", "Ressources humaines", "Informatique", "Commercial", "Marketing", "Juridique", "Opérations"],
  document_type: ["Rapport", "Contrat", "Procédure", "Guide", "Facture", "Présentation", "CV", "Note", "Politique"],
};

export function cleanMetadataValue(value: string) {
  return value.trim().replace(/\s+/g, " ");
}

export function normalizeMetadataValue(value: string) {
  return cleanMetadataValue(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("fr");
}

export function levenshteinSimilarity(left: string, right: string) {
  const a = normalizeMetadataValue(left);
  const b = normalizeMetadataValue(right);
  if (a === b) return 1;
  if (!a.length || !b.length) return 0;
  const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i += 1) {
    let diagonal = previous[0];
    previous[0] = i;
    for (let j = 1; j <= b.length; j += 1) {
      const old = previous[j];
      previous[j] = Math.min(previous[j] + 1, previous[j - 1] + 1, diagonal + (a[i - 1] === b[j - 1] ? 0 : 1));
      diagonal = old;
    }
  }
  return 1 - previous[b.length] / Math.max(a.length, b.length);
}

export function assessMetadataValue(value: string, options: string[], acceptedCustomValue?: string) {
  const cleaned = cleanMetadataValue(value);
  const key = normalizeMetadataValue(cleaned);
  if (!key) return { kind: "empty" as const, value: "" };
  const exact = options.find((option) => normalizeMetadataValue(option) === key);
  if (exact) return { kind: "exact" as const, value: exact };
  if (acceptedCustomValue === key) return { kind: "accepted" as const, value: cleaned };
  const ranked = options.map((option) => ({ option, score: levenshteinSimilarity(cleaned, option) })).sort((a, b) => b.score - a.score || a.option.localeCompare(b.option, "fr"));
  const best = ranked[0];
  if (best && best.score >= FUZZY_POSSIBLE_THRESHOLD) return { kind: "suggestion" as const, value: cleaned, suggestion: best.option, score: best.score };
  return { kind: "new" as const, value: cleaned };
}

export function mergeDocumentOptions(documents: Document[], field: MetadataField, fallback: string[]) {
  const result: string[] = [];
  const seen = new Set<string>();
  for (const value of [...documents.map((document) => document[field]), ...fallback]) {
    if (typeof value !== "string") continue;
    const cleaned = cleanMetadataValue(value);
    const key = normalizeMetadataValue(cleaned);
    if (cleaned && !seen.has(key)) { seen.add(key); result.push(cleaned); }
  }
  return result;
}
