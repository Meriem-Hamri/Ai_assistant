import fitz #PyMuPDF
from pathlib import Path
from app.models.document import Document,DocumentPage

def extract_text_from_pdf(filePath:str)->Document:
    """
    Raises:
        FileNotFoundError:Si le fichier n'existe pas
        ValueError:Si le fichier n'est pas un pdf 
    """
    path=Path(filePath)

    if not path.exists():
        raise FileNotFoundError(f"Le fichier '{filePath}' est introuvable . ")
    
    try:
        pdf=fitz.open(path)
        document=Document(
            filename=path.name
        )
        for i,page in enumerate(pdf,start=1):
            page_text=page.get_text().strip()
            document.pages.append(
                DocumentPage(
                    page_number=i,
                    text=page_text
                )
            )
        document.metadata["type"] = "pdf"
        document.metadata["page_count"] = len(pdf)
        
        pdf.close()
        return document
        
    except Exception as e:
        raise ValueError("Impossible de lire le PDF : "f"{e}")