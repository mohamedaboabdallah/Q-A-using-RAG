"""
Text Extraction Utility Module for RAG Applications.

This module provides functions to extract plain text content from
uploaded files in various formats. It supports text files (.txt),
PDF documents (.pdf), and Microsoft Word documents (.docx).

All functions operate on in-memory file bytes rather than file paths,
making them suitable for web applications where files are uploaded
via HTTP requests.

Features
--------
- Automatic encoding detection for `.txt` files using `chardet`
- PDF text extraction using `PyPDF2`
- Word document text extraction using `python-docx`
- Unified interface that returns extracted content as a list of strings

Functions
---------
- read_txt_from_bytes(file_bytes):
    Reads text from raw bytes of a `.txt` file, detecting encoding automatically.

- extract_text(file_bytes, filename):
    Determines file type from its extension and extracts text lines accordingly.

Usage
-----
This module is intended to be used by the file upload route in a Flask
application before storing the extracted text in ChromaDB or another
vector database for Retrieval-Augmented Generation (RAG) pipelines.
"""

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
    if ext == '.pdf':
        reader = PdfReader(io.BytesIO(file_bytes))
        return [page.extract_text() for page in reader.pages if page.extract_text()]
    if ext == '.docx':
        doc = docx.Document(io.BytesIO(file_bytes))
        return [para.text for para in doc.paragraphs if para.text.strip()]
    raise ValueError(f"Unsupported file type: {ext}")
