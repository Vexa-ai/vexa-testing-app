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

async def register_test_user():
    """Register a new user and update the credentials file."""
    try:
        credentials_manager = UserCredentialsManager()
        
        # Check if credentials already exist
        existing_credentials = credentials_manager.load_credentials()
        if existing_credentials:
            logger.info("Existing credentials found:")
            logger.info(f"User ID: {existing_credentials['user_id']}")
            logger.info(f"Email: {existing_credentials['email']}")
            
            # Ask user if they want to overwrite
            response = input("Credentials already exist. Do you want to create a new user? (y/n): ")
            if response.lower() != 'y':
                logger.info("Registration cancelled. Using existing credentials.")
                return True
            logger.info("Creating new user and overwriting existing credentials...")
        
        # Create new credentials
        credentials = await credentials_manager.auth_flow.register_user(
            engine_url=config.ENGINE_URL,
            engine_token=config.ENGINE_TOKEN
        )
        
        # Save the new credentials
        credentials_manager.auth_flow.save_credentials(credentials)
        
        logger.info("New user registered successfully:")
        logger.info(f"User ID: {credentials['user_id']}")
        logger.info(f"Email: {credentials['email']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register new user: {e}")
        return False

def main():
    print("=== User Registration Tool ===")
    print(f"Engine URL: {config.ENGINE_URL}")
    
    if not config.ENGINE_TOKEN:
        logger.error("ENGINE_TOKEN environment variable is not set. Please set it before running this script.")
        exit(1)
    
    success = asyncio.run(register_test_user())
    exit(0 if success else 1)

if __name__ == '__main__':
    main() 