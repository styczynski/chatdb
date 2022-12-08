from pydantic.dataclasses import dataclass
from typing import Optional

@dataclass
class OpenAPIAuth:
    session_token: str
    authorization_header: Optional[str] = None

class InvalidTokenError(ValueError):
    def __init__(self) -> None:
        super().__init__("Provided authorization token was invalid.")