
import ollama


MODEL_NAME = "qwen2.5:3b"


def ask_ai(message: str) -> str:
    """
    Sends a message to the local Qwen model
    and returns its response.
    """

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the virtual customer service assistant "
                        "of Empório da Música, a musical instrument store "
                        "located in Campo Grande, Brazil. "
                        "You represent the store and must speak as part "
                        "of its customer service team. "
                        "Always respond in English. "
                        "Be polite, friendly, professional and helpful. "
                        "Never claim to be a human employee. "
                        "Do not invent product prices, stock quantities "
                        "or order information."
                    )
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        return response["message"]["content"]

    except Exception as error:
        return f"Error connecting to the AI model: {error}"


if __name__ == "__main__":
    print("EMPORIO DA MUSICA - AI ASSISTANT")
    print("=" * 40)

    question = input("You: ")

    answer = ask_ai(question)

    print("\nAssistant:")
    print(answer)
