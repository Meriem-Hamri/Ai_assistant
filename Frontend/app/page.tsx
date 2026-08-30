"use client";

import { useEffect, useState } from "react";
import { getDocuments } from "@/lib/api/documents";
import type { Document } from "@/types/document";

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDocuments()
      .then(setDocuments)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erreur inconnue");
      });
  }, []);

  return (
    <main>
      <h1>Assistant AI</h1>

      {error && <p>Erreur : {error}</p>}

      <pre>{JSON.stringify(documents, null, 2)}</pre>
    </main>
  );
}
