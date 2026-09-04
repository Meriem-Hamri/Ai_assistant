import type { DocumentMetadataOptions } from "@/types/document";

export interface DocumentFilterValues {
  category: string;
  department: string;
  document_type: string;
  year: string;
}

interface DocumentFiltersProps {
  options: DocumentMetadataOptions & { year: number[] };
  values: DocumentFilterValues;
  onChange: (values: DocumentFilterValues) => void;
}

export function DocumentFilters({ options, values, onChange }: DocumentFiltersProps) {
  const filters = [
    ["category", "Catégorie", options.category],
    ["department", "Département", options.department],
    ["document_type", "Type", options.document_type],
    ["year", "Année", options.year.map(String)],
  ] as const;
  const activeCount = Object.values(values).filter(Boolean).length;

  return (
    <div className="document-filters" aria-label="Filtres documentaires">
      <span>Filtres{activeCount ? ` · ${activeCount}` : ""}</span>
      {filters.map(([field, label, fieldOptions]) => (
        <label key={field} className={values[field] ? "filter-active" : ""}>
          <span className="visually-hidden">{label}</span>
          <select value={values[field]} onChange={(event) => onChange({ ...values, [field]: event.target.value })}>
            <option value="">{label}</option>
            {fieldOptions.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
        </label>
      ))}
      {activeCount > 0 && <button className="clear-filters" type="button" onClick={() => onChange({ category: "", department: "", document_type: "", year: "" })}>Effacer</button>}
    </div>
  );
}
