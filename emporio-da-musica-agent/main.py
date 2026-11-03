from src.agent import chat_with_agent


def main():
    print("=" * 55)
    print("EMPORIO DA MUSICA - AI CUSTOMER SERVICE")
    print("=" * 55)
    print("\nAssistant is ready!")
    print("Type 'exit' to close the application.\n")

    while True:
        user_message = input("Customer: ").strip()

        if user_message.lower() in ["exit", "quit", "bye"]:
            print("\nAssistant: Thank you for contacting us!")
            break

        if not user_message:
            continue

        try:
            answer = chat_with_agent(user_message)
            print("\nAssistant:")
            print(answer)
            print()

        except Exception as error:
            print("\nAssistant: Sorry, an error occurred.")
            print(f"Technical details: {error}\n")


if __name__ == "__main__":
    main()