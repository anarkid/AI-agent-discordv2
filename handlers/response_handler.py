import aiohttp
import logging

logger = logging.getLogger("response_handler")

class ResponseHandler:
    def __init__(self, api_url='http://localhost:11434/api/generate', model_name='deepseek-r1:latest'):
        self.api_url = api_url
        self.model_name = model_name

    async def generate(self, prompt):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as resp:
                    if resp.status != 200:
                        return f"❌ Error {resp.status}: Could not reach DeepSeek."
                    data = await resp.json()
                    return data.get("response", "🤖 No response from model.")
        except Exception as e:
            logger.error(f"[DeepSeek Error] {e}")
            return f"❌ Error contacting DeepSeek: {e}"
