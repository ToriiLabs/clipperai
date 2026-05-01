# app/rag.py
from pypdf import PdfReader
import os
from .vector_memory import VectorMemory   # ← fixed

vector_memory = VectorMemory()

def process_document(file_path: str, filename: str):
    try:
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            text = "".join(page.extract_text() or "" for page in reader.pages)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        for chunk in chunks:
            vector_memory.add_memory(chunk, {"source": filename, "type": "document"})

        return f"✅ Processed {filename} — {len(chunks)} clips added to memory."
    except Exception as e:
        return f"❌ Error processing document: {str(e)}"
