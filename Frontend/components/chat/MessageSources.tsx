import type { ChatSource } from "@/types/source";
import { SourceItem } from "./SourceItem";

interface MessageSourcesProps {
  sources: ChatSource[];
}

export function MessageSources({ sources }: MessageSourcesProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <section className="message-sources" aria-label="Sources de la réponse">
      <h3 className="message-sources-header">
        Sources{sources.length > 1 ? ` · ${sources.length}` : ""}
      </h3>
      <ol className="source-list">
        {sources.map((source, index) => (
          <SourceItem
            key={`${source.document_id}-${source.chunk_id}-${index}`}
            source={source}
          />
        ))}
      </ol>
    </section>
  );
}
