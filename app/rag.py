from pypdf import PdfReader
import os
from .models import VectorMemory

vector_memory = VectorMemory()

def process_document(file_path: str, filename: str):
    """Extract text from PDF and add to memory"""
    try:
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        # Split into chunks and store
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        for chunk in chunks:
            vector_memory.add_memory(chunk, {"source": filename, "type": "document"})

        return f"✅ Processed {filename} — {len(chunks)} clips added to memory."
    except Exception as e:
        return f"❌ Error processing document: {str(e)}"
