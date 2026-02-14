import uuid
import threading
from typing import List, Dict, Optional

# Simple in-memory conversation store. Not persistent across restarts.
_STORE: Dict[str, List[Dict[str, str]]] = {}
_LOCK = threading.Lock()

# Maximum stored messages per conversation (pair of messages counted separately)
MAX_MESSAGES = 60
MAX_STORE_CHARS = 1000

def _trim(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(messages) <= MAX_MESSAGES:
        return messages
    return messages[-MAX_MESSAGES:]

def get_or_create_conversation(conversation_id: Optional[str]) -> str:
    if conversation_id:
        with _LOCK:
            if conversation_id not in _STORE:
                _STORE[conversation_id] = []
        return conversation_id

    new_id = str(uuid.uuid4())
    with _LOCK:
        _STORE[new_id] = []
    return new_id

def get_history(conversation_id: Optional[str]) -> (str, List[Dict[str, str]]):
    cid = get_or_create_conversation(conversation_id)
    with _LOCK:
        # return a shallow copy for safety
        return cid, list(_STORE.get(cid, []))

def append_user_message(conversation_id: str, content: str) -> None:
    if len(content) > MAX_STORE_CHARS:
        content = content[:MAX_STORE_CHARS] + "..."
    with _LOCK:
        _STORE.setdefault(conversation_id, []).append({"role": "user", "content": content})
        _STORE[conversation_id] = _trim(_STORE[conversation_id])

def append_assistant_message(conversation_id: str, content: str) -> None:
    if len(content) > MAX_STORE_CHARS:
        content = content[:MAX_STORE_CHARS] + "..."
    with _LOCK:
        _STORE.setdefault(conversation_id, []).append({"role": "assistant", "content": content})
        _STORE[conversation_id] = _trim(_STORE[conversation_id])
