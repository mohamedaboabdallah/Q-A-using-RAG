import os
import chardet
from PyPDF2 import PdfReader
import docx

def read_txt(file_path):
    """Read text file with automatic encoding detection."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']

    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        return f.read().splitlines()

def extract_text(file_path):
    """Extract text lines depending on file type."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        return read_txt(file_path)
    elif ext == '.pdf':
        reader = PdfReader(file_path)
        return [page.extract_text() for page in reader.pages if page.extract_text()]
    elif ext == '.docx':
        doc = docx.Document(file_path)
        return [para.text for para in doc.paragraphs if para.text.strip()]
    else:
        raise ValueError(f"Unsupported file type: {ext}")