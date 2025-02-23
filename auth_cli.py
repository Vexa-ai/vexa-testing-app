import asyncio
import logging
import argparse
from user_credentials import UserCredentialsManager
from src.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def validate_credentials():
    """Validate existing credentials or create new ones."""
    try:
        credentials_manager = UserCredentialsManager()
        credentials = await credentials_manager.get_or_create_credentials(
            engine_url=config.ENGINE_URL,
            engine_token=config.ENGINE_TOKEN
        )
        
        logger.info("Credentials validated successfully:")
        logger.info(f"User ID: {credentials['user_id']}")
        logger.info(f"Email: {credentials['email']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to validate/create credentials: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Manage authentication credentials')
    parser.add_argument('--validate', action='store_true', help='Validate existing credentials or create new ones')
    
    args = parser.parse_args()
    
    if args.validate:
        success = asyncio.run(validate_credentials())
        exit(0 if success else 1)
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
    main() 