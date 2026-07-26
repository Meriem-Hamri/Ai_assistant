from ollama import chat

def ask_qwen(question:str)->str:
    """
    ask qwen and he returns a response
    """

    response = chat(
        model="qwen3:4b",
        messages=[
            {
                "role":"user",
                "content":question
            }
        ]
    )

    return response.message.content