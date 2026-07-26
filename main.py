from app.extraction.pdf_reader import extract_pdf_text

def main():
    text=extract_pdf_text("documents/img.pdf")
    print(text)

if __name__ == "__main__":
    main()