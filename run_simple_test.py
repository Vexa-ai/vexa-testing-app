#!/usr/bin/env python3
"""Script to run a simple test scenario."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

from src.synthetic import (
    SyntheticMeeting,
    SyntheticDataGenerator,
    Speaker
)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run a simple test scenario."""
    # Create output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Create a simple 5-minute meeting with 2 users and 2 speakers
    logger.info("Generating simple test scenario...")
    
    meeting = SyntheticMeeting(
        duration_minutes=5,
        num_users=2,  # Two participants/clients
        chunk_duration_sec=1.0,
        speaker_update_interval_sec=0.5,
        start_time=datetime.now()
    )
    
    # Generate the test data
    generator = SyntheticDataGenerator('api_calls.json')
    
    scenario_config = {
        'meetings': [meeting],
        'output_file': str(output_dir / "simple_test.json")
    }
    
    output_file = generator.generate_test_scenario(scenario_config)
    logger.info(f"Generated test data saved to {output_file}")
    
    # Print summary
    logger.info("Test Scenario Summary:")
    logger.info(f"Meeting ID: {meeting.meeting_id}")
    logger.info(f"Duration: {meeting.duration_minutes} minutes")
    logger.info(f"Number of users: {meeting.num_users}")
    if meeting.speakers:
        logger.info(f"Number of speakers: {len(meeting.speakers)}")
        for speaker in meeting.speakers:
            total_speaking_time = sum(
                end - start 
                for start, end in speaker.speaking_patterns
            )
            logger.info(f"  - {speaker.name}: {total_speaking_time:.1f} seconds of speaking time")
    
    # Now we can run this test using the replay module
    from src.replay import ApiReplay
    
    logger.info("Starting replay of generated test data...")
    replay = ApiReplay(output_file)
    await replay.replay_calls()
    
    logger.info("Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 