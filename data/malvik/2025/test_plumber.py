import pdfplumber

def extract_text_from_pdf(path="malvik01-2025.pdf"):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

print(extract_text_from_pdf())
