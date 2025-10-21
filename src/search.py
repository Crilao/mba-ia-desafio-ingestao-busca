PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

import os
from typing import Optional
from dotenv import load_dotenv

from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI


def _get_embeddings():
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    if openai_key:
        return OpenAIEmbeddings(model="text-embedding-3-small")
    if google_key:
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    raise RuntimeError(
        "Nenhuma API Key encontrada. Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env"
    )


def _get_llm():
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    if openai_key:
        # As per spec: gpt-5-nano
        return ChatOpenAI(model="gpt-5-nano", temperature=0)
    if google_key:
        # As per spec: gemini-2.5-flash-lite
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
    raise RuntimeError(
        "Nenhuma API Key encontrada. Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env"
    )


def _get_vectorstore() -> PGVector:
    connection = (
        f"postgresql+psycopg://{os.getenv('PG_USER','postgres')}:{os.getenv('PG_PASSWORD','postgres')}@"
        f"{os.getenv('PG_HOST','localhost')}:{os.getenv('PG_PORT','5432')}/{os.getenv('PG_DB','rag')}"
    )
    collection = os.getenv("PG_COLLECTION", "documents")
    embeddings = _get_embeddings()
    return PGVector(
        connection=connection,
        collection_name=collection,
        embeddings=embeddings,
        distance_strategy=DistanceStrategy.COSINE,
        use_jsonb=True,
    )


def _build_prompt(context: str, question: str) -> str:
    return PROMPT_TEMPLATE.format(contexto=context, pergunta=question)


def search_prompt(question: Optional[str] = None):
    load_dotenv()
    try:
        vectorstore = _get_vectorstore()
        llm = _get_llm()
    except Exception as e:
        print(f"Erro de inicialização: {e}")
        return None

    def _run(q: str) -> str:
        # Retrieve top-k with scores
        results = vectorstore.similarity_search_with_score(q, k=10)
        if not results:
            return "Não tenho informações necessárias para responder sua pergunta."

        # Concatenate contexts
        chunks = []
        for doc, score in results:
            # Keep raw page_content; could append metadata if needed
            chunks.append(doc.page_content)
        context = "\n\n".join(chunks)

        prompt = _build_prompt(context, q)

        # Call LLM with the strict prompt
        try:
            completion = llm.invoke(prompt)
        except Exception:
            # fallback: return safe message
            return "Não tenho informações necessárias para responder sua pergunta."

        # completion may be an AIMessage; extract content
        content = getattr(completion, "content", None) or str(completion)
        return content.strip()

    # If a question was provided, run immediately, else return callable
    if question:
        return _run(question)
    return _run
