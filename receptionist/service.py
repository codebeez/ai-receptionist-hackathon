from openai import AsyncOpenAI


class ReceptionistService:
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client

    async def handle_message(self, message: str):
        # TODO: Implement actual chatbot logic
        return f"I received your message: {message}. (Bot functionality coming soon!)"
