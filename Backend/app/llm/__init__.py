from ollama import chat

from app.llm.base import BaseLLM
from app.llm.config import LLMConfig


class QwenClient(BaseLLM):
    """
    Client permettant de communiquer avec Qwen
    via Ollama.
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        """
        Initialise le client Qwen.

        Args:
            config: Configuration du LLM.
                   Une configuration par défaut est utilisée
                   si aucune configuration n'est fournie.
        """

        self._config = config or LLMConfig()

    def generate(self, prompt: str) -> str:
        """
        Génère une réponse à partir d'un prompt.

        Args:
            prompt: Prompt envoyé à Qwen.

        Returns:
            Réponse générée par Qwen.

        Raises:
            ValueError: Si le prompt est vide.
        """

        if not prompt or not prompt.strip():
            raise ValueError(
                "Le prompt ne peut pas être vide."
            )

        response = chat(
            model=self._config.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt.strip(),
                },
            ],
            think=self._config.think,
            options={
                "temperature": self._config.temperature,
                "num_predict": self._config.max_tokens,
                "top_p": self._config.top_p,
                "top_k": self._config.top_k,
                "repeat_penalty": self._config.repeat_penalty,
            },
        )

        content = response.message.content

        # Défense de compatibilité pour les anciennes versions d'Ollama qui
        # peuvent inclure une trace malgré think=False. Ce nettoyage ne sert
        # qu'à protéger le contenu retourné; la limite num_predict borne le
        # coût de cette régression côté serveur.
        if "</think>" in content:
            content = content.split("</think>", 1)[1]

        return content.strip()





# from ollama import chat

# def ask_qwen(question:str)->str:
#     """
#     ask qwen and he returns a response
#     """

#     response = chat(
#         model="qwen3:4b",
#         messages=[
#             {
#                 "role":"user",
#                 "content":question
#             }
#         ]
#     )

#     return response.message.content

