# Desafio MBA - Ingestão e Busca Semântica (LangChain + Postgres/pgVector)

## Requisitos
- Python 3.10+
- Docker e Docker Compose
- Chave de API (uma das opções):
  - OpenAI (`OPENAI_API_KEY`) – embeddings: `text-embedding-3-small`, LLM: `gpt-5-nano`
  - Google (`GOOGLE_API_KEY`) – embeddings: `models/embedding-001`, LLM: `gemini-2.5-flash-lite`

## Ambiente
1. Crie e ative o virtualenv:
```bash
python -m venv venv
venv\\Scripts\\activate
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure variáveis de ambiente (crie um `.env` na raiz, baseado em `.env.example`):
```env
# Uma das duas chaves é obrigatória
OPENAI_API_KEY=...
# ou
# GOOGLE_API_KEY=...

# Postgres
PG_HOST=localhost
PG_PORT=5432
PG_DB=rag
PG_USER=postgres
PG_PASSWORD=postgres
PG_COLLECTION=documents

# PDF (opcional; padrão: ./document.pdf)
PDF_PATH=./document.pdf
```

## Subir banco de dados
```bash
docker compose up -d
```

## Ingestão do PDF
```bash
python src/ingest.py
```
– Divide em chunks de 1000 caracteres (overlap 150), gera embeddings e grava no Postgres com pgVector.

## Rodar o chat (CLI)
```bash
python src/chat.py
```

Exemplo:
```
Faça sua pergunta (digite 'sair' para encerrar):
PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de 10 milhões de reais.
```

Perguntas fora do contexto retornam:
```
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

## Estrutura
```
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py
│   ├── search.py
│   ├── chat.py
├── document.pdf
└── README.md
```

## Observações
- A seleção de provedor (OpenAI ou Google) é automática com base na variável definida.
- A tabela/collection definida em `PG_COLLECTION` será criada automaticamente caso não exista.