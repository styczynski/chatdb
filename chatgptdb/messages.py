from pydantic.dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ModelResponse:
    message: str
    conversation_id: str
    parent_id: str