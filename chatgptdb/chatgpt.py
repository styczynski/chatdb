from .messages import ModelResponse
from typing import Optional, Dict
from .auth import InvalidTokenError, OpenAPIAuth
import requests
import json
import uuid
import aiohttp
import asyncio
from loguru import logger

DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    'Connection': 'keep-alive', 
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://chat.openai.com',
    'Referer': 'https://chat.openai.com/chat',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

class Chatbot:
    auth: OpenAPIAuth
    conversation_id: str
    parent_id: str
    headers: dict

    def __init__(self, auth: OpenAPIAuth, conversation_id: Optional[str] = None):
        self.auth = auth
        self.conversation_id = conversation_id
        self.parent_id = self.generate_uuid()
        self.refresh_headers()

    async def reset_chat(self):
        self.conversation_id = None
        self.parent_id = self.generate_uuid()
        
    def refresh_headers(self):
        self.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + (self.auth.authorization_header or ""),
            "Content-Type": "application/json"
        }

    def generate_uuid(self):
        uid = str(uuid.uuid4())
        return uid
        
    async def get_chat_response(self, prompt) -> ModelResponse:
        data = {
            "action":"next",
            "messages":[
                {"id":str(self.generate_uuid()),
                "role":"user",
                "content":{"content_type":"text","parts":[prompt]}
            }],
            "conversation_id":self.conversation_id,
            "parent_message_id":self.parent_id,
            "model":"text-davinci-002-render"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post("https://chat.openai.com/backend-api/conversation", headers={**DEFAULT_HEADERS, **self.headers}, data=json.dumps(data)) as response:
                logger.debug("Send HTTP ChatGPT request")
                response_text = await response.text()
                if "Your authentication token has expired" in response_text:
                    raise InvalidTokenError()
                if ("Rate limit reached for" in response_text) or ("We're working to restore all services as soon as possible. Please check back soon" in response_text):
                    # Dumb way to do a request retry
                    await asyncio.sleep(5)
                    return await self.get_chat_response(prompt)
                try:
                    response = response_text.splitlines()[-4]
                except:
                    print(response_text)
                    return ValueError("Error: Response is not a text/event-stream")
                try:
                    response = response[6:]
                except:
                    print(response_text)
                    return ValueError("Response is not in the correct format")
                response = json.loads(response)
                self.parent_id = response["message"]["id"]
                self.conversation_id = response["conversation_id"]
                message = response["message"]["content"]["parts"][0]
                logger.debug(f"Got ChatGTP response: {message}")
                return ModelResponse(
                    message=message,
                    conversation_id=self.conversation_id,
                    parent_id=self.parent_id
                )

    async def refresh_session(self):
        logger.debug("Refresh ChatGPT session token...")
        cookies = {
            "__Secure-next-auth.session-token": self.auth.session_token,
        }
        async with aiohttp.ClientSession(cookies=cookies, headers=DEFAULT_HEADERS) as s:
            async with s.get("https://chat.openai.com/api/auth/session") as r:
                try:
                    response = await r.json()
                    cookies = s.cookie_jar.filter_cookies("https://chat.openai.com")
                    self.auth.session_token = cookies["__Secure-next-auth.session-token"]
                    self.auth.authorization_header = response["accessToken"]
                    self.refresh_headers()
                    logger.debug("Completed ChatGPT session token refresh")
                except Exception as e:
                    print("Error refreshing session")  
                    print(response.text)
