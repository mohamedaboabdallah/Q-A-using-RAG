import os
import io
import chardet
from PyPDF2 import PdfReader
import docx

def read_txt_from_bytes(file_bytes):
    """Read text from bytes with automatic encoding detection."""
    detected = chardet.detect(file_bytes)
    encoding = detected['encoding'] or 'utf-8'
    text = file_bytes.decode(encoding, errors='ignore')
    return text.splitlines()

def extract_text(file_bytes, filename):
    """Extract text lines from file bytes depending on file type."""
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.txt':
        return read_txt_from_bytes(file_bytes)

    elif ext == '.pdf':
        reader = PdfReader(io.BytesIO(file_bytes))
        return [page.extract_text() for page in reader.pages if page.extract_text()]

    elif ext == '.docx':
        doc = docx.Document(io.BytesIO(file_bytes))
        return [para.text for para in doc.paragraphs if para.text.strip()]

    else:
        raise ValueError(f"Unsupported file type: {ext}")
