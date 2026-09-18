import os
import glob
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings

def run_ingestion():
    """
    Ingests all markdown documents in the knowledge base directory,
    generates embeddings using Gemini, and saves them in the Chroma vector database.
    """
    print("[Ingestion Pipeline] Starting document ingestion...")
    
    if not settings.GEMINI_API_KEY:
        print("[Ingestion Pipeline] WARNING: GEMINI_API_KEY is not set. Ingestion skipped (requires API key).")
        return False
        
    knowledge_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base"))
    md_files = glob.glob(os.path.join(knowledge_dir, "*.md"))
    
    if not md_files:
        print(f"[Ingestion Pipeline] No markdown files found in {knowledge_dir}")
        return False
        
    raw_docs = []
    for file_path in md_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Extract title from the first `# ` header
            title = os.path.basename(file_path).replace(".md", "").replace("_", " ").title()
            for line in content.split("\n"):
                if line.startswith("# "):
                    title = line.replace("# ", "").strip()
                    break
                    
            raw_docs.append({
                "id": f"doc_{os.path.basename(file_path).replace('.md', '')}",
                "title": title,
                "content": content,
                "filename": os.path.basename(file_path)
            })
            print(f"[Ingestion Pipeline] Loaded: {title} ({os.path.basename(file_path)})")
        except Exception as e:
            print(f"[Ingestion Pipeline] Error reading {file_path}: {e}")

    if not raw_docs:
        print("[Ingestion Pipeline] No valid documents to ingest.")
        return False

    try:
        # Initialize Google GenAI Embeddings (Gemini)
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GEMINI_API_KEY
        )
        
        # Initialize Chroma persistent store
        vectorstore = Chroma(
            collection_name="parkiq_knowledge",
            embedding_function=embeddings,
            persist_directory=settings.CHROMA_DB_DIR
        )
        
        # Clear existing collection items to ensure clean ingestion
        print("[Ingestion Pipeline] Cleaning old vectors from Chroma database...")
        existing = vectorstore.get()
        if existing and existing.get("ids"):
            vectorstore.delete(ids=existing["ids"])
            
        # Split documents into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        langchain_docs = []
        
        for doc in raw_docs:
            chunks = splitter.split_text(doc["content"])
            for i, chunk in enumerate(chunks):
                langchain_docs.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": doc["filename"],
                        "title": doc["title"],
                        "chunk_id": i
                    }
                ))
                
        if langchain_docs:
            # Load chunks into Chroma
            vectorstore.add_documents(langchain_docs)
            print(f"[Ingestion Pipeline] SUCCESS: Ingested {len(langchain_docs)} chunks from {len(raw_docs)} documents.")
            return True
        else:
            print("[Ingestion Pipeline] No chunks created.")
            return False
            
    except Exception as e:
        print(f"[Ingestion Pipeline] CRITICAL: Ingestion failed: {e}")
        return False

if __name__ == "__main__":
    run_ingestion()
