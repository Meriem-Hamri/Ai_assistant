from app.chunking.base import BaseChunker
from app.chunking.utils import (
    split_into_paragraphs,
    clean_paragraphs,
    merge_small_paragraphs,
    split_large_paragraph,
)
from app.chunking.validator import is_too_large
from app.models.document import Document, Chunk


class NaturalChunker(BaseChunker):
    """
    Découpe un document en chunks en respectant autant que possible
    la structure naturelle du texte (paragraphes).

    Pipeline :

    - découpage en paragraphes
    - nettoyage
    - fusion des petits paragraphes
    - découpage des paragraphes trop longs
    - création des objets Chunk
    """

    def __init__(
        self,
        min_chunk_size: int = 200,
        max_chunk_size: int = 800,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:
        """
        Découpe un document complet en une liste de chunks.

        Args:
            document: document à découper.

        Returns:
            Liste des chunks créés.
        """

        chunks: list[Chunk] = []

        chunk_index = 0

        for page in document.pages:

            paragraphs = split_into_paragraphs(page.text)

            paragraphs = clean_paragraphs(paragraphs)

            paragraphs = merge_small_paragraphs(
                paragraphs,
                self.min_chunk_size,
            )

            current_position = 0

            for paragraph in paragraphs:

                if is_too_large(paragraph,self.max_chunk_size,):

                    pieces = split_large_paragraph(
                        paragraph,
                        self.max_chunk_size,
                    )

                else:

                    pieces = [paragraph]

                for piece in pieces:
                    if not piece.strip():
                       continue

                    start = current_position
                    end = start + len(piece)

                    chunks.append(
                        self._create_chunk(
                            text=piece,
                            document=document,
                            page_number=page.page_number,
                            chunk_index=chunk_index,
                            start_char=start,
                            end_char=end,
                        )
                    )

                    current_position = end 
                    chunk_index += 1

        return chunks

    def _create_chunk(
        self,
        text: str,
        document: Document,
        page_number: int,
        chunk_index: int,
        start_char: int,
        end_char: int,
    ) -> Chunk:
        """
        Crée un objet Chunk.

        Args:
            text: contenu du chunk.
            document: document d'origine.
            page_number: numéro de page.
            chunk_index: index global du chunk.
            start_char: position de début.
            end_char: position de fin.

        Returns:
            Instance de Chunk.
        """

        return Chunk(
            text=text,
            document_id=document.id,
            document_name=document.filename,
            page_number=page_number,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            metadata=dict(document.metadata),
        )
