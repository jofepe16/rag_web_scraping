from langchain_ollama import ChatOllama

from app.domain.ports import GeneratorPort


class OllamaGeneratorAdapter(GeneratorPort):
    def __init__(self, base_url: str, model: str, timeout: float = 600) -> None:
        self.client = ChatOllama(
            base_url=base_url.rstrip("/"),
            model=model,
            temperature=0.1,
            keep_alive="30m",
            client_kwargs={"timeout": timeout},
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.ainvoke(prompt)
        answer = response.content.strip() if isinstance(response.content, str) else ""
        if not answer:
            raise RuntimeError("Ollama returned an empty response")
        return answer
