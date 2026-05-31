# app/rag.py
from pypdf import PdfReader
from docx import Document
import os
from .vector_memory import vector_memory

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path.lower())[1]
    if ext == '.pdf':
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == '.docx':
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)
    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        # fallback for unknown text files
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            raise ValueError(f"Unsupported file type: {ext}")

def process_document(file_path: str, filename: str):
    try:
        text = extract_text(file_path)
        if not text.strip():
            return f"No readable text in {filename}"

        # Smart overlapping chunks
        chunk_size = 800
        overlap = 200
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            if start >= len(text):
                break

        for i, chunk in enumerate(chunks):
            if chunk.strip():
                metadata = {"source": filename, "type": "document", "chunk": i}
                vector_memory.add_memory(chunk, metadata)

        return f"✅ Processed {filename} — {len(chunks)} semantic chunks added to vector database."
    except Exception as e:
        return f"❌ Error processing {filename}: {str(e)}"
