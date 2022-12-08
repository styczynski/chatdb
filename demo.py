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
    conversation_ids = None
    kv = KeyValueStore(auth, conversations_ids=conversation_ids)
    await kv.start()

    print_assert(await kv.save("a", 9))
    print_assert(await kv.all(), {'a': 9})
    print_assert(await kv.save("xx", 12))
    print_assert(await kv.save("xy", 42))
    print_assert(await kv.save("zz", 99))
    print_assert(await kv.all(), {'a': 9, 'xx': 12, 'xy': 42, 'zz': 99})
    print_assert(await kv.filter("x[x-y]"), ['xx', 'xy'], [12, 42], ["12", "42"])
    print_assert(await kv.delete("xy"))
    print_assert(await kv.all(), {'a': 9, 'xx': 12, 'zz': 99})
    print_assert(await kv.query("sum all the values"), {'sum': 120}, 120)
    
    # Optionally revert the actions using our commands log
    # await kv.undo(4)
    # print_assert(await kv.all(), {'a': 9, 'xx': 12, 'xy': 42, 'zz': 99})

if __name__ == "__main__":
    asyncio.run(main())

