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
import pendulum
import os
import sys
import subprocess
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.my_logging import MY_Logger
from garminconnect import Garmin
from tabulate import tabulate

# Set up logging
log = MY_Logger(log_level=logging.WARNING).get_logger()
log.propagate = False

# Set up environment variables
load_dotenv()


class GarminActivitiesFetcher:
    """Class to handle Garmin Connect API interactions."""
    
    def __init__(self):
        self.client = None
        
    def authenticate(self):
        """
        Authenticate with Garmin Connect using credentials from environment variables.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Get credentials from environment variables
            email = os.environ.get("GARMIN_EMAIL")
            password = os.environ.get("GARMIN_PASSWORD")
            
            if not email or not password:
                log.error("Garmin credentials not found. Please set GARMIN_EMAIL and GARMIN_PASSWORD environment variables.")
                log.info("Add these to your .env file:")
                log.info("GARMIN_EMAIL=your_email@example.com")
                log.info("GARMIN_PASSWORD=your_password")
                return False
            
            log.info("Authenticating with Garmin Connect...")
            self.client = Garmin(email, password)
            self.client.login()
            log.info("Successfully authenticated with Garmin Connect")
            
            return True
            
        except Exception as e:
            log.error(f"Failed to authenticate with Garmin Connect: {e}")
            return False

    def get_activities(self, days=7, activity_type=None):
        """
        Fetch activities from Garmin Connect.
        
        Args:
            days (int): Number of days to look back
            activity_type (str): Filter by activity type (optional)
        
        Returns:
            list: List of activity dictionaries
        """
        try:
            if not self.client:
                log.error("Not authenticated with Garmin Connect")
                return []
            
            # Calculate start date
            start_date = pendulum.now().subtract(days=days).to_date_string()
            end_date = pendulum.now().to_date_string()
            
            log.info(f"Fetching activities from {start_date} to {end_date}")
            
            # Get activities for the date range
            activities = self.client.get_activities_by_date(start_date, end_date)
            
            if activity_type:
                # Filter by activity type if specified
                activities = [a for a in activities if a.get('activityType', {}).get('typeKey', '').lower() == activity_type.lower()]
                log.info(f"Found {len(activities)} {activity_type} activities")
            else:
                log.info(f"Found {len(activities)} activities")
            
            return activities
            
        except Exception as e:
            log.error(f"Error fetching activities: {e}")
            return []

    def get_activity_details(self, activity_id):
        """
        Get detailed information about a specific activity.
        
        Args:
            activity_id (str): Activity ID
        
        Returns:
            dict: Detailed activity information
        """
        try:
            if not self.client:
                log.error("Not authenticated with Garmin Connect")
                return None
                
            log.info(f"Fetching details for activity {activity_id}")
            activity = self.client.get_activity(activity_id)
            return activity
            
        except Exception as e:
            log.error(f"Error fetching activity details: {e}")
            return None

    def logout(self):
        """Clean logout from Garmin Connect."""
        try:
            if self.client:
                self.client.logout()
                log.info("Logged out from Garmin Connect")
        except Exception as e:
            log.warning(f"Error during logout: {e}")


class ActivityFormatter:
    """Class to handle formatting and display of activities."""
    
    @staticmethod
    def parse_datetime(start_time):
        """Parse datetime string and return formatted date and time."""
        if not start_time:
            return 'Unknown', ''
        
        try:
            dt = pendulum.parse(start_time)
            date_str = dt.format('YYYY-MM-DD')
            time_str = dt.format('HH:mm')
            return date_str, time_str
        except Exception:
            date_str = start_time[:10] if len(start_time) >= 10 else start_time
            time_str = start_time[11:16] if len(start_time) >= 16 else ''
            return date_str, time_str

    @staticmethod
    def format_duration(duration_seconds):
        """Format duration from seconds to readable string."""
        if not duration_seconds:
            return ''
        
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @staticmethod
    def format_distance(distance_meters):
        """Format distance from meters to miles."""
        if not distance_meters:
            return ''
        
        distance_miles = distance_meters / 1609.344  # Convert meters to miles
        return f"{distance_miles:.2f} mi"

    @staticmethod
    def format_speed(avg_speed):
        """Format speed from m/s to mph."""
        if not avg_speed:
            return ''
        
        avg_speed_mph = avg_speed * 2.237  # Convert m/s to mph
        return f"{avg_speed_mph:.1f} mph"

    @staticmethod
    def format_pace(avg_speed, distance_meters, duration_seconds):
        """Format pace in minutes per mile."""
        if not avg_speed or not distance_meters or not duration_seconds:
            return ''
        
        # Calculate pace as minutes per mile
        distance_miles = distance_meters / 1609.344
        duration_minutes = duration_seconds / 60
        
        if distance_miles > 0:
            pace_min_per_mile = duration_minutes / distance_miles
            minutes = int(pace_min_per_mile)
            seconds = int((pace_min_per_mile - minutes) * 60)
            return f"{minutes}:{seconds:02d}/mi"
        
        return ''

    def format_activities_table(self, activities, detailed=False):
        """
        Format activities data into a readable table.
        
        Args:
            activities (list): List of activity dictionaries
            detailed (bool): Whether to include detailed information
        
        Returns:
            str: Formatted table string
        """
        if not activities:
            return "No activities found."
        
        # Prepare data for table
        table_data = []
        
        for activity in activities:
            # Extract basic information
            date_str, time_str = self.parse_datetime(activity.get('startTimeLocal', ''))
            activity_name = activity.get('activityName', 'Untitled')
            activity_type = activity.get('activityType', {}).get('typeKey', 'Unknown')
            duration_str = self.format_duration(activity.get('duration', 0))
            distance_str = self.format_distance(activity.get('distance', 0))
            
            # Basic row
            row = [date_str, time_str, activity_name, activity_type, duration_str, distance_str]
            
            if detailed:
                # Add more detailed information
                calories = activity.get('calories', '')
                avg_speed = activity.get('averageSpeed', 0)
                pace_str = self.format_pace(avg_speed, activity.get('distance', 0), activity.get('duration', 0))
                speed_str = self.format_speed(avg_speed)
                activity_id = activity.get('activityId', '')
                
                row.extend([
                    str(calories) if calories else '',
                    pace_str,
                    speed_str,
                    str(activity_id) if activity_id else ''
                ])
            
            table_data.append(row)
        
        # Define headers
        headers = ['Date', 'Time', 'Activity', 'Type', 'Duration', 'Distance']
        if detailed:
            headers.extend(['Calories', 'Pace', 'Avg Speed', 'Activity ID'])
        
        # Create table
        table_str = tabulate(table_data, headers=headers, tablefmt='presto')
        
        return table_str

    def display_activity_details(self, activity):
        """
        Display detailed information about a single activity.
        
        Args:
            activity (dict): Activity details dictionary
        """
        if not activity:
            log.error("No activity details to display")
            return
        
        # Extract the actual activity data from summaryDTO if it exists
        activity_data = activity.get('summaryDTO', activity)
        
        print("\n" + "="*60)
        print("ACTIVITY DETAILS")
        print("="*60)
        
        # Basic information
        print(f"Name: {activity.get('activityName', 'Untitled')}")
        
        # Get activity type from nested structure
        activity_type_dto = activity.get('activityTypeDTO', {})
        activity_type = activity_type_dto.get('typeKey', 'Unknown')
        print(f"Type: {activity_type}")
        
        # Activity ID for reference
        activity_id = activity.get('activityId')
        if activity_id:
            print(f"Activity ID: {activity_id}")
        
        # Location
        location = activity.get('locationName')
        if location:
            print(f"Location: {location}")
        
        # Description
        description = activity.get('description')
        if description:
            print(f"Description: {description}")
        
        # Date and time from summaryDTO
        start_time = activity_data.get('startTimeLocal', '') or activity_data.get('startTimeGMT', '')
        if start_time:
            try:
                dt = pendulum.parse(start_time)
                print(f"Date: {dt.format('YYYY-MM-DD dddd')}")
                print(f"Start Time: {dt.format('HH:mm:ss')}")
            except Exception:
                print(f"Start Time: {start_time}")
        
        # Duration and distance
        self._print_duration_distance(activity_data)
        
        # Performance metrics
        self._print_performance_metrics(activity_data)
        
        # Pace information
        self._print_pace_info(activity_data)
        
        # Elevation and training effects
        try:
            self._print_elevation_training(activity_data)
        except Exception as e:
            print(f"Error in elevation section: {e}")
        
        # Additional metrics
        try:
            self._print_additional_metrics(activity_data)
        except Exception as e:
            print(f"Error in additional metrics section: {e}")
        
        print("="*60)

    def _print_duration_distance(self, activity):
        """Print duration and distance information."""
        # Try multiple possible field names for duration
        duration_seconds = (activity.get('duration') or 
                          activity.get('elapsedDuration') or 
                          activity.get('movingDuration') or 0)
        
        if duration_seconds and duration_seconds > 0:
            duration_seconds = int(duration_seconds)  # Ensure it's an integer
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            print(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Moving duration if different
        moving_duration = activity.get('movingDuration')
        if moving_duration and moving_duration != duration_seconds and moving_duration > 0:
            moving_duration = int(moving_duration)
            hours = moving_duration // 3600
            minutes = (moving_duration % 3600) // 60
            seconds = moving_duration % 60
            print(f"Moving Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Try multiple possible field names for distance
        distance_meters = (activity.get('distance') or 
                         activity.get('totalDistance') or 0)
        
        if distance_meters and distance_meters > 0:
            distance_miles = distance_meters / 1609.344  # Convert meters to miles
            print(f"Distance: {distance_miles:.2f} mi")

    def _print_performance_metrics(self, activity):
        """Print performance metrics."""
        calories = activity.get('calories')
        if calories:
            print(f"Calories: {int(float(calories))}")
        
        avg_hr = activity.get('averageHR')
        max_hr = activity.get('maxHR')
        min_hr = activity.get('minHR')
        if avg_hr:
            print(f"Average Heart Rate: {int(float(avg_hr))} bpm")
        if max_hr:
            print(f"Maximum Heart Rate: {int(float(max_hr))} bpm")
        if min_hr:
            print(f"Minimum Heart Rate: {int(float(min_hr))} bpm")
        
        # Use the available speed fields
        avg_speed = activity.get('averageSpeed', 0) or activity.get('averageMovingSpeed', 0)
        if avg_speed:
            avg_speed = float(avg_speed)
            avg_speed_mph = avg_speed * 2.237  # Convert m/s to mph
            print(f"Average Speed: {avg_speed_mph:.2f} mph")
        
        max_speed = activity.get('maxSpeed', 0)
        if max_speed:
            max_speed = float(max_speed)
            max_speed_mph = max_speed * 2.237  # Convert m/s to mph
            print(f"Maximum Speed: {max_speed_mph:.2f} mph")

    def _print_pace_info(self, activity):
        """Print pace information."""
        avg_speed = activity.get('averageSpeed', 0)
        distance_meters = activity.get('distance', 0)
        duration_seconds = activity.get('duration', 0)
        
        if avg_speed and distance_meters and duration_seconds:
            pace_str = self.format_pace(avg_speed, distance_meters, duration_seconds)
            if pace_str:
                print(f"Average Pace: {pace_str}")
        
        # Moving time vs elapsed time
        moving_duration = activity.get('movingDuration')
        if moving_duration and moving_duration != duration_seconds:
            hours = moving_duration // 3600
            minutes = (moving_duration % 3600) // 60
            seconds = moving_duration % 60
            print(f"Moving Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            if distance_meters:
                distance_miles = distance_meters / 1609.344
                moving_pace_min_per_mile = (moving_duration / 60) / distance_miles
                minutes = int(moving_pace_min_per_mile)
                seconds = int((moving_pace_min_per_mile - minutes) * 60)
                print(f"Moving Pace: {minutes}:{seconds:02d}/mi")

    def _print_elevation_training(self, activity):
        """Print elevation and training effect information."""
        elevation_gain = activity.get('elevationGain')
        elevation_loss = activity.get('elevationLoss')
        if elevation_gain:
            elevation_gain = float(elevation_gain)
            print(f"Elevation Gain: {elevation_gain:.0f} m ({elevation_gain * 3.28084:.0f} ft)")
        if elevation_loss:
            elevation_loss = float(elevation_loss)
            print(f"Elevation Loss: {elevation_loss:.0f} m ({elevation_loss * 3.28084:.0f} ft)")
        
        min_elevation = activity.get('minElevation')
        max_elevation = activity.get('maxElevation')
        if min_elevation is not None:
            min_elevation = float(min_elevation)
            print(f"Min Elevation: {min_elevation:.0f} m ({min_elevation * 3.28084:.0f} ft)")
        if max_elevation is not None:
            max_elevation = float(max_elevation)
            print(f"Max Elevation: {max_elevation:.0f} m ({max_elevation * 3.28084:.0f} ft)")
        
        # Training effects (look for different field names)
        aerobic_effect = (activity.get('aerobicTrainingEffect') or 
                         activity.get('aerobicTrainingEffectMessage'))
        anaerobic_effect = (activity.get('anaerobicTrainingEffect') or 
                           activity.get('anaerobicTrainingEffectMessage'))
        if aerobic_effect:
            print(f"Aerobic Training Effect: {aerobic_effect}")
        if anaerobic_effect:
            print(f"Anaerobic Training Effect: {anaerobic_effect}")
        
        training_effect_label = activity.get('trainingEffectLabel')
        if training_effect_label:
            print(f"Training Effect: {training_effect_label}")

    def _print_additional_metrics(self, activity):
        """Print additional activity metrics."""
        print()  # Add some spacing
        
        # Steps (for activities that track them)
        steps = activity.get('steps')
        if steps:
            print(f"Steps: {int(float(steps)):,}")
        
        # Cadence information (look for available field names)
        avg_running_cadence = (activity.get('avgRunningCadenceInStepsPerMinute') or 
                              activity.get('averageRunCadence'))
        max_running_cadence = (activity.get('maxRunningCadenceInStepsPerMinute') or 
                              activity.get('maxRunCadence'))
        if avg_running_cadence:
            print(f"Average Cadence: {int(float(avg_running_cadence))} steps/min")
        if max_running_cadence:
            print(f"Maximum Cadence: {int(float(max_running_cadence))} steps/min")
        
        # GPS coordinates
        start_latitude = activity.get('startLatitude')
        start_longitude = activity.get('startLongitude')
        end_latitude = activity.get('endLatitude')
        end_longitude = activity.get('endLongitude')
        
        if start_latitude and start_longitude:
            print(f"Start Location: {float(start_latitude):.6f}, {float(start_longitude):.6f}")
        if end_latitude and end_longitude:
            print(f"End Location: {float(end_latitude):.6f}, {float(end_longitude):.6f}")
        
        # Special metrics for rucking
        begin_pack_weight = activity.get('beginPackWeight')
        if begin_pack_weight:
            # Convert from grams to pounds
            weight_lbs = float(begin_pack_weight) / 453.592
            print(f"Pack Weight: {weight_lbs:.1f} lbs")
        
        # Intensity minutes
        moderate_intensity = activity.get('moderateIntensityMinutes')
        vigorous_intensity = activity.get('vigorousIntensityMinutes')
        if moderate_intensity:
            print(f"Moderate Intensity Minutes: {int(float(moderate_intensity))}")
        if vigorous_intensity:
            print(f"Vigorous Intensity Minutes: {int(float(vigorous_intensity))}")
        
        # Body battery and other metrics
        body_battery_diff = activity.get('differenceBodyBattery')
        if body_battery_diff:
            print(f"Body Battery Change: {int(float(body_battery_diff))}")
        
        water_estimated = activity.get('waterEstimated')
        if water_estimated:
            print(f"Water Loss Estimate: {float(water_estimated):.1f} L")
        
        bmr_calories = activity.get('bmrCalories')
        if bmr_calories:
            print(f"BMR Calories: {int(float(bmr_calories))}")
        
        # Workout feel and RPE
        workout_feel = activity.get('directWorkoutFeel')
        workout_rpe = activity.get('directWorkoutRpe')
        if workout_feel:
            print(f"Workout Feel: {workout_feel}")
        if workout_rpe:
            print(f"Workout RPE: {workout_rpe}")

    def display_activities_list(self, activities, show_ids=False):
        """
        Display activities as a simple list.
        
        Args:
            activities (list): List of activity dictionaries
            show_ids (bool): Whether to show activity IDs
        """
        print(f"\nFound {len(activities)} activities:")
        for i, activity in enumerate(activities, 1):
            name = activity.get('activityName', 'Untitled')
            activity_type = activity.get('activityType', {}).get('typeKey', 'Unknown')
            start_time = activity.get('startTimeLocal', '')
            
            date_str, _ = self.parse_datetime(start_time)
            
            print(f"{i:2d}. {name} ({activity_type}) - {date_str}")
            
            # Show activity ID for reference
            activity_id = activity.get('activityId')
            if activity_id and show_ids:
                print(f"    ID: {activity_id}")


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
                    print(f"\nTotal activities: {len(activities)}")
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
        # Clean logout
        garmin_client.logout()


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
