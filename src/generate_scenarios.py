"""Script to generate various test scenarios using the synthetic data generator."""

import argparse
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timedelta

from .synthetic import (
    create_concurrent_meetings_scenario,
    create_extended_meeting_scenario,
    SyntheticMeeting,
    SyntheticDataGenerator
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_basic_scenarios(output_dir: Path):
    """Generate basic test scenarios."""
    # Concurrent meetings
    logger.info("Generating concurrent meetings scenario...")
    concurrent_file = output_dir / "concurrent_meetings.json"
    create_concurrent_meetings_scenario(
        base_duration_minutes=30,
        num_meetings=3,
        users_per_meeting=2,
        output_file=str(concurrent_file)
    )
    
    # Extended meeting with gap
    logger.info("Generating extended meeting scenario...")
    extended_file = output_dir / "extended_meeting.json"
    create_extended_meeting_scenario(
        duration_hours=24,
        num_users=2,
        gap_hours=12,
        output_file=str(extended_file)
    )
    
def generate_edge_cases(output_dir: Path):
    """Generate edge case scenarios."""
    generator = SyntheticDataGenerator('api_calls.json')
    
    # 1. Meeting with long silence
    logger.info("Generating meeting with silence periods...")
    silence_meeting = SyntheticMeeting(
        duration_minutes=60,
        num_users=2,
        chunk_duration_sec=2.0,  # Longer chunks for silence
        speaker_update_interval_sec=2.0
    )
    scenario_config = {
        'meetings': [silence_meeting],
        'output_file': str(output_dir / "meeting_with_silence.json")
    }
    generator.generate_test_scenario(scenario_config)
    
    # 2. Meeting with rapid speaker switches
    logger.info("Generating meeting with rapid speaker switches...")
    rapid_switch_meeting = SyntheticMeeting(
        duration_minutes=30,
        num_users=4,  # More users for more switches
        chunk_duration_sec=0.5,  # Shorter chunks
        speaker_update_interval_sec=0.2  # Frequent speaker updates
    )
    scenario_config = {
        'meetings': [rapid_switch_meeting],
        'output_file': str(output_dir / "rapid_speaker_switches.json")
    }
    generator.generate_test_scenario(scenario_config)
    
    # 3. Multi-day meeting with multiple breaks
    logger.info("Generating multi-day meeting...")
    day1 = SyntheticMeeting(
        duration_minutes=480,  # 8 hours
        num_users=3,
        start_time=datetime.now()
    )
    day2 = SyntheticMeeting(
        duration_minutes=480,
        num_users=3,
        start_time=datetime.now() + timedelta(days=1),
        meeting_id=day1.meeting_id  # Same meeting continues
    )
    day3 = SyntheticMeeting(
        duration_minutes=480,
        num_users=3,
        start_time=datetime.now() + timedelta(days=2),
        meeting_id=day1.meeting_id
    )
    scenario_config = {
        'meetings': [day1, day2, day3],
        'output_file': str(output_dir / "multi_day_meeting.json")
    }
    generator.generate_test_scenario(scenario_config)

def generate_load_test(output_dir: Path):
    """Generate load test scenarios."""
    # Many concurrent short meetings
    logger.info("Generating load test with many concurrent meetings...")
    meetings = []
    start_time = datetime.now()
    
    for i in range(20):  # 20 concurrent meetings
        meeting = SyntheticMeeting(
            duration_minutes=15,  # Short meetings
            num_users=3,
            start_time=start_time + timedelta(minutes=i)  # Staggered starts
        )
        meetings.append(meeting)
    
    scenario_config = {
        'meetings': meetings,
        'output_file': str(output_dir / "load_test.json")
    }
    
    generator = SyntheticDataGenerator('api_calls.json')
    generator.generate_test_scenario(scenario_config)

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic test scenarios")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_data",
        help="Directory to store generated test data"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        choices=["basic", "edge", "load", "all"],
        default="all",
        help="Which scenarios to generate"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.scenarios in ["basic", "all"]:
        generate_basic_scenarios(output_dir)
    if args.scenarios in ["edge", "all"]:
        generate_edge_cases(output_dir)
    if args.scenarios in ["load", "all"]:
        generate_load_test(output_dir)
        
    logger.info(f"All requested scenarios generated in {output_dir}")

if __name__ == "__main__":
    main() 