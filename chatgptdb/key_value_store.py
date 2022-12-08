from typing import Any, Dict, List, Optional, Tuple
from .action_log import ActionLog
from .auth import OpenAPIAuth
from .messages import ModelResponse
from .chatgpt import Chatbot
import asyncio
import json
import ast
from loguru import logger

DEFAULT_INITIAL_PROMPT = """
I want you to act as a computer program.
I will type javascript commands and return the result.
I want you to reply with the value returned by execution of the code inside one code block.
Do not write explanations. Do not do anything, unless I tell you to do so.
I can invoke function "save" that stores single value in memory.
The function accepts key and value to be stored under this key.
Keys are strings and any value other than string should cause an error.
I can call "read" which returns value stored under the key.
I also can invoke "all" which returns a list with all values stored as a json.
I also can invoke "delete" which deletes a given key.
I can also invoke "filter" which accepts regex and returns list of values for keys that match that regex.
No other function other than those mentioned can be called.
If there is any error you should print it with line number and all the details.
When I need you to tell something in English I will do so by calling function query that accepts a natural language input.
For example query("sum all values") returns sum of all values. Output of each command should be a valid json.
My first command is all();
"""

class KeyValueStore:
    log: ActionLog
    log_started: bool
    chat: Chatbot
    initial_prompt: str
    reset_on_start: bool

    def __init__(self, auth: OpenAPIAuth, initial_prompt: Optional[str] = None, conversations_ids: Optional[Tuple[str, str]] = None) -> None:
        store_conversation_id, log_conversation_id = None, None
        self.reset_on_start = True
        if conversations_ids:
            store_conversation_id, log_conversation_id = conversations_ids
            self.reset_on_start = False
        self.chat = Chatbot(auth, conversation_id=store_conversation_id)
        self.log = ActionLog(auth, conversation_id=log_conversation_id)
        self.log_started = False
        self.initial_prompt = initial_prompt or DEFAULT_INITIAL_PROMPT

    async def start(self) -> None:
        logger.debug("Intiializing key-value store. Please wait..")
        if self.reset_on_start:
            await self.chat.reset_chat()    
        await self.chat.refresh_session()
        if self.reset_on_start:
            while True:
                await self.chat.get_chat_response(self.initial_prompt)
                logger.debug("Validaitng key-value store initial response. Please wait..")
                # Assert that after initial bot returns no results (stored values)
                resp = await self.chat.get_chat_response("all();")
                if not (resp.message == "{}" or resp.message == "[]"):
                    await self.chat.reset_chat()
                    await self.chat.refresh_session()
                    logger.debug("Retry creating the storage...")
                else:
                    break
        logger.debug("Key-value store is ready.")
        if not self.log_started:
            logger.debug("Storage requires transaction log. Starting it now.")
            await self.log.start(reset=self.reset_on_start)
            self.log_started = True

    def conversations_ids(self) -> Tuple[str, str]:
        return (self.chat.conversation_id, self.log.chat.conversation_id)

    def _format_answer(self, resp: ModelResponse, expect_list=False):
        if resp.message == "null":
            return None
        if expect_list and resp.message == "{}":
            return []
        try:
            answer = json.loads(resp.message)
        except json.decoder.JSONDecodeError:
            try:
                answer = ast.literal_eval(resp.message)
            except:
                answer = str(resp.message).strip()
        if expect_list:
            if isinstance(answer, list):
                return answer
            elif isinstance(answer, dict):
                return list(answer.keys())
            else:
                raise ValueError("Invalid value")
        return answer

    async def _execute_command(self, command: str, skip_log: bool = False) -> ModelResponse:
        if skip_log:
            return await self.chat.get_chat_response(command)
        if not self.log_started:
            logger.debug("Storage requires transaction log. Starting it now.")
            await self.log.start()
            self.log_started = True
        logger.debug("Executing query and appending it to transaction log.")
        result = await asyncio.gather(
            self.log.append(command),
            self.chat.get_chat_response(command),
        )
        logger.debug("Query was executed.")
        return result[1]

    async def all(self) -> Dict[Any, Any]:
        resp = await self._execute_command("all();")
        value = self._format_answer(resp, expect_list=False)
        if isinstance(value, list):
            if len(value) == 0:
                return dict()
            elif isinstance(value[0], dict):
                return dict(*[(list(item_dict.keys())[0], list(item_dict.values())[0]) for item_dict in value])
        return value

    async def filter(self, regex: str) -> List[Any]:
        resp = await self._execute_command(f'filter("{regex}")')
        return self._format_answer(resp, expect_list=True)

    async def read(self,  key: str) -> Any:
        resp = await self._execute_command(f'read("{key}")')
        return self._format_answer(resp, expect_list=False)
    
    async def save(self,  key: str, value: Any) -> Any:
        resp = await self._execute_command(f'save("{key}", {value})')
        return self._format_answer(resp, expect_list=False)
    
    async def delete(self,  key: str) -> Any:
        resp = await self._execute_command(f'delete("{key}")')
        return self._format_answer(resp, expect_list=False)

    async def query(self,  query: str) -> Any:
        resp = await self._execute_command(f'query("{query}")')
        return self._format_answer(resp, expect_list=False)
    
    async def undo(self, no_actions: int = 1) -> List[str]:
        logger.debug("Undo is a complex operation that reloads entire database from the start. Plase wait...")
        commands = await self.log.undo(no_actions=no_actions)
        await self.start()
        resp: Optional[ModelResponse] = None
        for command in commands:
            resp = await self._execute_command(command, skip_log=True)
        logger.debug("Undo operation was finished.")
        if resp:
            return self._format_answer(resp)
        return None

    async def get_log(self) -> List[str]:
        return await self.log.get()