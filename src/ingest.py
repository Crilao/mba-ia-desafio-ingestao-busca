import os
from dotenv import load_dotenv
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings


def _get_embeddings_model() -> object:
    """Select embeddings model based on available API keys.

    Prefers OpenAI if `OPENAI_API_KEY` is set; otherwise uses Gemini if `GOOGLE_API_KEY` is set.
    Raises RuntimeError if neither is configured.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    if openai_key:
        return OpenAIEmbeddings(model="text-embedding-3-small")

    if google_key:
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    raise RuntimeError(
        "Nenhuma API Key encontrada. Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env"
    )


def _get_pgvector() -> PGVector:
    """Create a PGVector instance using env vars.

    Required env:
      - PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD
      - PG_COLLECTION (table/collection name; default: documents)
    """
    connection = (
        f"postgresql+psycopg://{os.getenv('PG_USER','postgres')}:{os.getenv('PG_PASSWORD','postgres')}@"
        f"{os.getenv('PG_HOST','localhost')}:{os.getenv('PG_PORT','5432')}/{os.getenv('PG_DB','rag')}"
    )

    collection = os.getenv("PG_COLLECTION", "documents")

    embeddings = _get_embeddings_model()

    return PGVector(
        connection=connection,
        collection_name=collection,
        embeddings=embeddings,
        distance_strategy=DistanceStrategy.COSINE,
        use_jsonb=True,
    )


def ingest_pdf(pdf_path: Optional[str] = None) -> None:
    load_dotenv()

    pdf_path = pdf_path or os.getenv("PDF_PATH", os.path.join(os.getcwd(), "document.pdf"))

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF não encontrado em: {pdf_path}")

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
        separators=["\n\n", "\n", " ", ""],
    )
    doc_chunks = splitter.split_documents(documents)

    store = _get_pgvector()

    # Persist chunks into vector store
    store.add_documents(doc_chunks)

    print(f"Ingestão concluída. Chunks gravados: {len(doc_chunks)}")


if __name__ == "__main__":
    ingest_pdf()