import os
import re
from typing import List
from datetime import datetime
from app.schema import DocumentMetadata

class Chunk:
    def __init__(self, text: str, metadata: DocumentMetadata):
        self.text = text
        self.metadata = metadata

def load_and_chunk_docs(docs_dir: str) -> List[Chunk]:
    chunks = []
    if not os.path.exists(docs_dir):
        return chunks
        
    for filename in os.listdir(docs_dir):
        if not filename.endswith(".md"): continue
        
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split document by markdown subheadings (H2)
        sections = re.split(r'\n## ', content)
        
        for i, section in enumerate(sections):
            text = section.strip()
            if not text: continue
            
            if i > 0:
                text = "## " + text
                heading = text.split("\n")[0].replace("## ", "").strip()
            else:
                heading = "Introduction"
                
            meta = DocumentMetadata(
                source_name=filename,
                section_heading=heading,
                last_updated=datetime.now().strftime("%Y-%m-%d"),
                doc_type="FAQ" if "faq" in filename.lower() else "POLICY"
            )
            chunks.append(Chunk(text=text, metadata=meta))
            
    return chunks