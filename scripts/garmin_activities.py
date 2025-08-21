#!/usr/bin/env python3
"""
Garmin Connect Activities Display Script

This script fetches and displays your Garmin Connect activities in a table format.
It requires your Garmin Connect username and password to authenticate.

Usage:
    python scripts/garmin_activities.py --days 7 --table
    python scripts/garmin_activities.py --activity-id 12345678901 --details
"""

import argparse
import logging
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.my_logging import MY_Logger
from utils.garmin_client import GarminActivitiesFetcher, ActivityFormatter

# Set up logging
log = MY_Logger(log_level=logging.WARNING).get_logger()
log.propagate = False

# Set up environment variables
load_dotenv(verbose=False)  # Set verbose=False to suppress loading messages


def main(args):
    """
    Main function to fetch and display Garmin activities.
    
    Args:
        args: Command line arguments
    """
    log.info('Starting Garmin Connect Activities Script')
    
    # Initialize Garmin client and formatter
    garmin_client = GarminActivitiesFetcher()
    formatter = ActivityFormatter()
    
    # Authenticate with Garmin Connect
    if not garmin_client.authenticate():
        return
    
    try:
        if args.activity_id:
            # Get details for a specific activity
            activity = garmin_client.get_activity_details(args.activity_id)
            if activity:
                formatter.display_activity_details(activity)
            else:
                log.error(f"Could not fetch activity {args.activity_id}")
        else:
            # Get list of activities
            activities = garmin_client.get_activities(args.days, args.activity_type)
            
            if activities:
                if args.table:
                    # Display as table
                    table = formatter.format_activities_table(activities, detailed=args.detailed)
                    print("\n" + table)
                    
                    # Calculate total distance
                    total_distance_meters = sum(activity.get('distance', 0) for activity in activities)
                    total_distance_miles = total_distance_meters / 1609.344
                    
                    print(f"\n  Total distance: {total_distance_miles:.2f} miles")
                    print(f"Total activities: {len(activities)}")
                else:
                    # Display as simple list
                    formatter.display_activities_list(activities, show_ids=args.show_ids)
            else:
                print("No activities found for the specified criteria.")
    
    except KeyboardInterrupt:
        log.info("Script interrupted by user")
    except Exception as e:
        log.error(f"Unexpected error: {e}")
    finally:
        # Clean token removal (optional - tokens remain valid for future use)
        # Uncomment the next line if you want to remove tokens on exit
        # garmin_client.logout()
        pass


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Fetch and display Garmin Connect activities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/garmin_activities.py --days 7 --table
  python scripts/garmin_activities.py --days 14 --table --detailed
  python scripts/garmin_activities.py --activity-type running --days 30
  python scripts/garmin_activities.py --activity-id 12345678901
        """
    )
    
    parser.add_argument('-d', '--days', type=int, default=7,
                      help='Number of days to look back for activities (default: 7)')
    
    parser.add_argument('-t', '--table', action='store_true',
                      help='Display activities in table format')
    
    parser.add_argument('--detailed', action='store_true',
                      help='Include detailed information in table (use with --table)')
    
    parser.add_argument('--activity-type', type=str,
                      help='Filter by activity type (e.g., running, cycling, swimming)')
    
    parser.add_argument('--activity-id', type=str,
                      help='Get detailed information for a specific activity ID')
    
    parser.add_argument('--show-ids', action='store_true',
                      help='Show activity IDs in the list')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging level based on verbose flag
    if args.verbose:
        log = MY_Logger(log_level=logging.INFO).get_logger()
        log.propagate = False
    
    log.info(f'{"="*20} Starting Script: {os.path.basename(__file__)} {"="*20}')
    
    main(args)
