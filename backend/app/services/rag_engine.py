import os
import glob
from typing import Dict, Any, List
from app.config import settings

# LangChain and Chroma imports
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# Ingestion runner
from app.services.ingest import run_ingestion

class ParkIQRAGEngine:
    """
    RAG (Retrieval-Augmented Generation) Knowledge Assistant for ParkIQ.
    Retrieves information from parking policies, maps, reservation rules, FAQs,
    and emergency guides to generate contextually grounded responses using LangChain,
    ChromaDB, and the Gemini API.
    """
    def __init__(self):
        self.vectorstore = None
        self.rag_chain = None
        self.fallback_documents = []
        self._init_knowledge_base()

    def _init_knowledge_base(self):
        """
        Initializes the vector store, triggers ingestion if empty, and builds
        the LangChain RAG retrieval chain.
        """
        # 1. Load documents for fallback & rule matching
        knowledge_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base"))
        md_files = glob.glob(os.path.join(knowledge_dir, "*.md"))
        
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
                
                doc_info = {
                    "id": f"doc_{os.path.basename(file_path).replace('.md', '')}",
                    "title": title,
                    "content": content,
                    "filename": os.path.basename(file_path)
                }
                raw_docs.append(doc_info)
                self.fallback_documents.append(doc_info)
            except Exception as e:
                print(f"[RAG Engine] Error loading doc for fallback {file_path}: {e}")

        # Static fallback if knowledge base dir is empty
        if not raw_docs:
            self.fallback_documents = [
                {
                    "id": "doc_rules_1",
                    "title": "General Parking Rules",
                    "content": "ParkIQ enforce a maximum speed limit of 10 km/h inside garages. Vehicles must park centered within marked lines. Overstaying past reserved duration incurs a $10/hour overstay fee."
                },
                {
                    "id": "doc_reservations_2",
                    "title": "Reservation & Cancellation Policy",
                    "content": "Reservations can be made up to 7 days in advance. Cancellations made 30 minutes prior to reservation start time receive a 100% refund. Late cancellations incur a 20% processing fee."
                },
                {
                    "id": "doc_qr_3",
                    "title": "AES-256 Encrypted QR Identity",
                    "content": "Every registered vehicle receives a unique AES-256 encrypted QR code in their mobile app wallet. Scanned QR codes contain no personal data. Staff scan the QR code at entry/exit gates for ticketless parking."
                },
                {
                    "id": "doc_ev_4",
                    "title": "EV Charging Guidelines",
                    "content": "EV charging stations are located on Level 1 and Level 2 (Slots EV-01 to EV-10). Charging rate is $0.25 per kWh in addition to base parking rates. Idle fees apply if connected after charging reaches 100%."
                },
                {
                    "id": "doc_emergency_5",
                    "title": "Emergency & Assistance",
                    "content": "For parking assistance, vehicle breakdown, or security emergencies, call ParkIQ Helpline at 1-800-PARKIQ-HELP or push the blue assistance button located at every elevator bank."
                }
            ]
            raw_docs = self.fallback_documents

        # 2. Setup LangChain vector database & RAG chain if Gemini API key is configured
        if settings.GEMINI_API_KEY:
            try:
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=settings.GEMINI_API_KEY
                )
                
                self.vectorstore = Chroma(
                    collection_name="parkiq_knowledge",
                    embedding_function=embeddings,
                    persist_directory=settings.CHROMA_DB_DIR
                )
                
                # Automatically run ingestion on startup if the vector database is empty
                existing = self.vectorstore.get()
                if not existing or not existing.get("ids"):
                    print("[RAG Engine] Vector store is empty. Invoking auto-ingestion...")
                    run_ingestion()
                
                # Initialize Gemini Chat Model
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.0
                )
                
                # Design prompt context grounding template
                system_prompt = (
                    "You are the ParkIQ Smart Parking Assistant.\n"
                    "Answer the user's question using ONLY the provided official parking knowledge context below.\n"
                    "If the answer cannot be found in the context, give a helpful general answer based on standard ParkIQ parking policies.\n\n"
                    "CONTEXT:\n{context}"
                )
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "{input}"),
                ])
                
                # Create LangChain Retrieval Chain
                question_answer_chain = create_stuff_documents_chain(llm, prompt)
                self.rag_chain = create_retrieval_chain(
                    self.vectorstore.as_retriever(search_kwargs={"k": 3}), 
                    question_answer_chain
                )
                print("[RAG Engine] LangChain RAG retrieval chain successfully constructed.")
            except Exception as e:
                print(f"[RAG Engine] Initialization failure: {e}. Defaulting to keyword search fallback.")
        else:
            print("[RAG Engine] GEMINI_API_KEY not configured. Running in keyword-matching fallback mode.")

    def query(self, user_question: str) -> Dict[str, Any]:
        """
        Executes query semantic retrieval and generates answer via LangChain RAG pipeline.
        Falls back to local keyword searching if Gemini key is missing or calls fail.
        """
        if self.rag_chain:
            try:
                response = self.rag_chain.invoke({"input": user_question})
                answer = response.get("answer", "")
                
                # Parse unique sources
                sources = []
                context_docs = response.get("context", [])
                for doc in context_docs:
                    title = doc.metadata.get("title")
                    if title and title not in sources:
                        sources.append(title)
                        
                return {
                    "question": user_question,
                    "answer": answer.strip(),
                    "sources": sources
                }
            except Exception as e:
                print(f"[RAG Engine] LangChain query failed: {e}. Executing keyword fallback.")

        # Fallback to local keyword scan
        relevant_context = []
        sources = []
        q_lower = user_question.lower()
        
        for doc in self.fallback_documents:
            # Check if any query word matches title or content
            if any(word in doc["content"].lower() or word in doc["title"].lower() for word in q_lower.split() if len(word) > 2):
                relevant_context.append(f"{doc['title']}:\n{doc['content']}")
                sources.append(doc["title"])
                
        if not relevant_context:
            # Safe default fallback
            default_doc = self.fallback_documents[0]
            relevant_context.append(f"{default_doc['title']}:\n{default_doc['content']}")
            sources.append(default_doc["title"])

        # Construct naive answer outputting the document chunks
        sources_str = ", ".join(set(sources))
        answer = f"Based on ParkIQ Policy ({sources_str}):\n\n"
        answer += "\n\n".join(relevant_context) + "\n\n"
        answer += "[Notice: System is running in fallback mode. Please configure GEMINI_API_KEY for conversational AI.]"
        
        return {
            "question": user_question,
            "answer": answer,
            "sources": list(set(sources))
        }

rag_engine = ParkIQRAGEngine()
