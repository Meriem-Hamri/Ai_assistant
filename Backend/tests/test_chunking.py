from app.chunking.natural_chunker import NaturalChunker
from app.models.document import (
    Document,
    DocumentPage,
)


def test_single_paragraph():
    """
    Un document contenant un seul paragraphe
    doit produire un seul chunk.
    """

    document = Document(
        filename="document.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text="Ceci est un paragraphe suffisamment long pour devenir un chunk."
            )
        ],
    )

    chunker = NaturalChunker(
        min_chunk_size=20,
        max_chunk_size=500,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) == 1

def test_multiple_paragraphs():
    """
    Deux paragraphes assez grands
    doivent produire deux chunks.
    """

    text = (
        "Premier paragraphe très long afin de dépasser "
        "la taille minimale.\n\n"
        "Deuxième paragraphe lui aussi suffisamment grand."
    )

    document = Document(
        filename="document.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text=text,
            )
        ],
    )

    chunker = NaturalChunker(
        min_chunk_size=20,
        max_chunk_size=500,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) == 2

def test_merge_small_paragraphs():
    """
    Deux petits paragraphes doivent être fusionnés.
    """

    text = (
        "Petit.\n\n"
        "Encore petit."
    )

    document = Document(
        filename="doc.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text=text,
            )
        ],
    )

    chunker = NaturalChunker(
        min_chunk_size=100,
        max_chunk_size=500,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) == 1

def test_split_large_paragraph():
    """
    Un paragraphe trop long
    doit être découpé.
    """

    text = ("mot " * 500)

    document = Document(
        filename="doc.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text=text,
            )
        ],
    )

    chunker = NaturalChunker(
        min_chunk_size=20,
        max_chunk_size=200,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) > 1

def test_chunk_metadata():
    """
    Chaque chunk doit conserver
    les métadonnées du document.
    """

    document = Document(
        filename="manuel.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text="Texte suffisamment long pour créer un chunk."
            )
        ],
    )

    chunker = NaturalChunker(
        min_chunk_size=20,
        max_chunk_size=500,
    )

    chunk = chunker.chunk(document)[0]

    assert chunk.document_id == document.id
    assert chunk.document_name == "manuel.pdf"
    assert chunk.page_number == 1

def test_empty_document():
    """
    Un document vide
    ne produit aucun chunk.
    """

    document = Document(
        filename="vide.pdf",
        pages=[],
    )

    chunker = NaturalChunker()

    chunks = chunker.chunk(document)

    assert chunks == []

def test_chunk_index():
    """
    Les chunks doivent avoir
    un index croissant.
    """

    text = (
        "Premier paragraphe très long.\n\n"
        "Deuxième paragraphe très long.\n\n"
        "Troisième paragraphe très long."
    )

    document = Document(
        filename="doc.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text=text,
            )
        ],
    )

    chunker = NaturalChunker(
        min_chunk_size=20,
        max_chunk_size=500,
    )

    chunks = chunker.chunk(document)

    for index, chunk in enumerate(chunks):
        assert chunk.chunk_index == index


def test_arabic_paragraphs_are_preserved_and_respect_max_size():
    text = ("هذه فقرة عربية تحتوي على معلومات مهمة دون فقدان الكلمات " * 12).strip()
    document = Document(
        filename="arabic.pdf",
        pages=[DocumentPage(page_number=1, text=text)],
    )

    chunks = NaturalChunker(min_chunk_size=40, max_chunk_size=120).chunk(document)

    assert chunks
    assert all(0 < len(chunk.text) <= 120 for chunk in chunks)
    assert "هذه فقرة عربية" in " ".join(chunk.text for chunk in chunks)


def test_arabic_question_mark_is_used_as_sentence_boundary():
    first = "هل هذه هي الفقرة الأولى؟"
    second = "هذه هي الفقرة الثانية وتحتوي على تفاصيل إضافية."
    document = Document(
        filename="arabic.pdf",
        pages=[DocumentPage(page_number=1, text=f"{first} {second}")],
    )

    chunks = NaturalChunker(min_chunk_size=1, max_chunk_size=len(second)).chunk(document)

    assert [chunk.text for chunk in chunks] == [first, second]
