import asyncio
import aiohttp
import logging
from src.replay import ApiReplay
from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiOperations:
    def __init__(self):
        self.base_url = config.STREAMQUEUE_URL.rstrip('/')
        # For tools and connections endpoints we need service token
        self.service_headers = {'Authorization': f'Bearer {config.SERVICE_TOKEN}'}
        # For extension endpoints we need user token
        self.user_headers = {'Authorization': f'Bearer {config.USER_TOKEN}'}

    async def flush_cache(self):
        """Flush Redis cache via API."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/tools/flush-cache"
            async with session.post(url, headers=self.service_headers) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Cache flush result: {result}")
                return result

    async def flush_admin_cache(self):
        """Flush Redis admin cache via API."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/tools/flush-admin-cache"
            async with session.post(url, headers=self.service_headers) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Admin cache flush result: {result}")
                return result

    async def add_user_token(self):
        """Add user token to Redis."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/users/add-token"
            data = {
                "token": config.USER_TOKEN,
                "user_id": "00000000-0000-4000-a000-000000000001",
                "enable_status": True
            }
            async with session.post(url, headers=self.service_headers, json=data) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Add token result: {result}")
                return result

async def main():
    """Main function to orchestrate all operations."""
    if not config.USER_TOKEN:
        raise ValueError("USER_TOKEN must be set in environment variables")
    if not config.SERVICE_TOKEN:
        raise ValueError("SERVICE_TOKEN must be set in environment variables")

    api = ApiOperations()
    
    # 1. Flush caches
    logger.info("Flushing caches...")
    await api.flush_cache()
    await api.flush_admin_cache()
    
    # 2. Add user token
    logger.info("Adding user token...")
    await api.add_user_token()
    
    # 3. Replay calls (this will also store data)
    logger.info("Starting replay...")
    replay = ApiReplay('api_calls.json')
    await replay.replay_calls()
    
    # Log final status
    logger.info("All operations completed successfully!")

if __name__ == '__main__':
    asyncio.run(main()) 