from typing import Any, Dict, List, Optional
from .auth import OpenAPIAuth
from .messages import ModelResponse
from .chatgpt import Chatbot
import json
from loguru import logger

DEFAULT_INITIAL_PROMPT = """
I want you to act as a computer program.
I will type javascript commands and you should remember all of them in order. Do not do anything.
After I type "SHOW" you should type exactly all the commands I told you, each command in new line.
After I type "UNDO" you should remove the specified number of last commands.
For example "UNDO 3" removes 3 last commands. Do not react to anything other than "SHOW" or "UNDO".
Do not write explanations.
If I type anything other than "SHOW" or "UNDO", respond with "OK". 
"""

class ActionLog:
    chat: Chatbot
    initial_prompt: str

    def __init__(self, auth: OpenAPIAuth, initial_prompt: Optional[str] = None, conversation_id: Optional[str] = None) -> None:
        self.chat = Chatbot(auth, conversation_id=conversation_id)
        self.initial_prompt = initial_prompt or DEFAULT_INITIAL_PROMPT

    async def start(self, reset: bool = True) -> None:
        logger.debug("Initializing the transaction log. Please wait...")
        if reset:
            await self.chat.reset_chat()
        await self.chat.refresh_session()
        if reset:
            while True:
                resp = await self.chat.get_chat_response(self.initial_prompt)
                if resp.message == "OK":
                    break
                else:
                    logger.debug("Retry creating the log...")
                    await self.chat.reset_chat()
                    await self.chat.refresh_session()
        logger.debug("Transaction log is ready.")

    def _format_answer(self, resp: ModelResponse) -> List[str]:
        if resp.message == "OK":
            return []
        else:
            return [entry.strip() for entry in resp.message.split("\n")]

    async def append(self, command: str):
        logger.debug("Appending new item to log")
        resp = await self.chat.get_chat_response(command)
        assert resp.message == "OK"

    async def undo(self, no_actions: int) -> List[Any]:
        logger.debug("Rewriting transaction log")
        resp = await self.chat.get_chat_response(f"UNDO {no_actions}")
        assert resp.message == "OK"
        return await self.get()

    async def get(self) -> List[Any]:
        logger.debug("Query the transation log")
        resp = await self.chat.get_chat_response(f'SHOW')
        return self._format_answer(resp)
