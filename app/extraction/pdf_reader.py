import fitz  # PyMuPDF

from pathlib import Path

from app.models.document import Document, DocumentPage
from app.extraction.ocr_reader import extract_text_from_image


def extract_text_from_pdf(file_path: str) -> Document:
    """
    Extrait le texte d'un PDF.

    Le texte peut provenir :
    - du texte natif du PDF ;
    - de l'OCR des images présentes dans le PDF.

    Les deux sources sont fusionnées afin de gérer
    également les PDF mixtes.

    Raises:
        FileNotFoundError:
            Si le fichier n'existe pas.
        ValueError:
            Si le PDF ne peut pas être lu.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Le fichier '{file_path}' est introuvable."
        )

    try:
        pdf = fitz.open(path)

        document = Document(
            filename=path.name
        )

        for page_number, page in enumerate(pdf, start=1):

            # --------------------------------------------------
            # 1. Extraction du texte natif
            # --------------------------------------------------

            native_text = page.get_text().strip()

            extracted_parts = []

            if native_text:
                extracted_parts.append(native_text)

            # --------------------------------------------------
            # 2. Extraction des images de la page
            # --------------------------------------------------

            images = page.get_images(full=True)

            for image_index, image_info in enumerate(images):

                xref = image_info[0]

                image_data = pdf.extract_image(xref)

                image_bytes = image_data["image"]
                image_ext = image_data["ext"]

                image_path = (
                    path.parent
                    / f".ocr_{path.stem}_"
                    f"{page_number}_{image_index}.{image_ext}"
                )

                try:
                    image_path.write_bytes(image_bytes)

                    ocr_text = extract_text_from_image(
                        str(image_path)
                    )

                    if ocr_text:
                        extracted_parts.append(ocr_text)

                finally:
                    if image_path.exists():
                        image_path.unlink()

            # --------------------------------------------------
            # 3. Fusion du texte
            # --------------------------------------------------

            page_text = "\n\n".join(extracted_parts).strip()

            document.pages.append(
                DocumentPage(
                    page_number=page_number,
                    text=page_text,
                )
            )

        document.metadata["type"] = "pdf"
        document.metadata["page_count"] = len(pdf)

        pdf.close()

        return document

    except Exception as exc:
        raise ValueError(
            f"Impossible de lire le PDF : {exc}"
        ) from exc