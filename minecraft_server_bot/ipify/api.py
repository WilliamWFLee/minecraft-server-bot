import aiohttp
import backoff

API_URL = "https://api.ipify.org"
MAX_TRIES = 3


@backoff.on_exception(backoff.expo, Exception, max_tries=MAX_TRIES)
async def get_ip():
    async with aiohttp.ClientSession(API_URL) as session:
        response = await session.get("/")
        return await response.text()
