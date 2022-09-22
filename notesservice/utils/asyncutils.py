import asyncio


# Run a coroitine inside a sync function
def run_coroutine(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)
