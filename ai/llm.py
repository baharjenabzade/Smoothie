import ollama


MODEL_NAME = "qwen3:4b"


def ask_ai(prompt: str) -> str:
    """
    Send a prompt to the local Ollama model.
    """

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

    except Exception as e:
        return f"AI_ERROR: {str(e)}"