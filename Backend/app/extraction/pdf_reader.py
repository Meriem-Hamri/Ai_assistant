import fitz  # PyMuPDF

from pathlib import Path

from app.models.document import Document, DocumentPage
from app.extraction.ocr_language import DEFAULT_OCR_LANGUAGE, OcrLanguage
from app.extraction.ocr_router import extract_text_from_image


def _ocr_dpi(ocr_language: OcrLanguage) -> int:
    """Augmente uniquement la résolution du chemin Paddle français."""

    return 250 if ocr_language == "fr" else 200


def extract_text_from_pdf(
    file_path: str,
    ocr_language: OcrLanguage = DEFAULT_OCR_LANGUAGE,
) -> Document:
    """
    Extrait le texte d'un PDF.

    - Texte natif : extrait directement avec PyMuPDF.
    - Pages contenant des images : OCR de la page entière.
    - Les deux sources sont fusionnées pour gérer les PDF mixtes.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Le fichier '{file_path}' est introuvable."
        )

    pdf = None

    try:
        pdf = fitz.open(path)

        document = Document(
            filename=path.name
        )

        total_pages = len(pdf)

        for page_number, page in enumerate(
            pdf,
            start=1,
        ):
            print(
                f"[PDF] Traitement page "
                f"{page_number}/{total_pages}"
            )

            extracted_parts = []

            # ==================================================
            # 1. TEXTE NATIF
            # ==================================================

            native_text = page.get_text().strip()

            if native_text:
                extracted_parts.append(
                    native_text
                )

            # ==================================================
            # 2. OCR SI LA PAGE CONTIENT DES IMAGES
            # ==================================================

            images = page.get_images(
                full=True
            )

            if images:
                print(
                    f"[PDF] Page {page_number}: "
                    f"{len(images)} image(s) détectée(s)"
                )

                # Rendre toute la page en image.
                # Cela permet de traiter correctement
                # les pages mixtes texte + images.
                pixmap = page.get_pixmap(
                    dpi=_ocr_dpi(ocr_language)
                )

                ocr_image_path = (
                    path.parent
                    / (
                        f".ocr_page_"
                        f"{path.stem}_"
                        f"{page_number}.png"
                    )
                )

                try:
                    pixmap.save(
                        str(ocr_image_path)
                    )

                    print(
                        f"[OCR] Page "
                        f"{page_number}/{total_pages}"
                    )

                    try:
                        # ocr_document = (
                        #     extract_text_from_image(
                        #         str(ocr_image_path)
                        #     )
                        # )

                        # if (
                        #     ocr_document.pages
                        #     and
                        #     ocr_document.pages[0].text.strip()
                        # ):
                        #     extracted_parts.append(
                        #         ocr_document.pages[0].text.strip()
                        #     )
                        ocr_text = extract_text_from_image(
                            str(ocr_image_path),
                            ocr_language,
                        )

                        if ocr_text:
                            extracted_parts.append(ocr_text)

                    except Exception as ocr_exc:
                        # Une erreur OCR sur une page
                        # ne doit pas arrêter tout le PDF.
                        print(
                            f"[OCR] Échec page "
                            f"{page_number}: "
                            f"{ocr_exc}"
                        )

                finally:
                    if ocr_image_path.exists():
                        ocr_image_path.unlink()

            # ==================================================
            # 3. FUSION
            # ==================================================

            page_text = "\n\n".join(
                extracted_parts
            ).strip()

            document.pages.append(
                DocumentPage(
                    page_number=page_number,
                    text=page_text,
                )
            )

        document.metadata["type"] = "pdf"
        document.metadata["page_count"] = len(
            document.pages
        )

        return document

    except Exception as exc:
        raise ValueError(
            f"Impossible de lire le PDF : {exc}"
        ) from exc

    finally:
        if pdf is not None:
            pdf.close()
