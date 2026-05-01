# app/rag.py
from pypdf import PdfReader
from .vector_memory import VectorMemory   # ← Fixed import

vector_memory = VectorMemory()

def process_document(file_path: str, filename: str):
    try:
        if file_path.lower().endswith('.pdf'):
            reader = PdfReader(file_path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        chunks = [text[i:i+600] for i in range(0, len(text), 600)]
        for chunk in chunks:
            if chunk.strip():
                vector_memory.add_memory(chunk, {"source": filename})

        return f"✅ Processed {filename} — {len(chunks)} clips added to memory."
    except Exception as e:
        return f"❌ Error processing {filename}: {str(e)}"
