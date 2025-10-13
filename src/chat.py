from search import search_prompt

def main():
    run = search_prompt()

    if not run:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return

    print("Faça sua pergunta (digite 'sair' para encerrar):")
    while True:
        try:
            question = input("PERGUNTA: ")
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando...")
            break

        if not question:
            continue

        if question.strip().lower() in {"sair", "exit", "quit"}:
            print("Encerrando...")
            break

        answer = run(question)
        print(f"RESPOSTA: {answer}\n")

if __name__ == "__main__":
    main()