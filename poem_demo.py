from chatgptdb.key_value_store import KeyValueStore
from chatgptdb.auth import OpenAPIAuth
from typing import Any, List
import asyncio
from loguru import logger

def print_assert(value: Any, *expected_values: List[Any]):
    print(value)
    ok = False
    for expected in expected_values:
        if expected == value:
            ok = True
            break
    if not ok and len(expected_values) > 0:
        logger.error(f"Invalid response!")
        for expected in expected_values:
            logger.error(f" | Expected: {expected}")
        assert False
    return value


async def main():
    auth = OpenAPIAuth(session_token="YOUR TOKEN GOES HERE")
    kv = KeyValueStore(auth)
    await kv.start()

    await kv.save("x", 42)
    await kv.save("a", 19)
    await kv.save("x", 99)
    print(await kv.query("write me a short poem, two sentences long"))
    print(await kv.all())

if __name__ == "__main__":
    asyncio.run(main())

