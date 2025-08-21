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
import traceback
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
load_dotenv(verbose=False)  # Set verbose=False to suppress loading messages


class GarminActivitiesFetcher:
    """Class to handle Garmin Connect API interactions."""
    
    def __init__(self, tokenstore="~/.garminconnect"):
        self.client = None
        self.tokenstore = os.path.expanduser(tokenstore)
        
    def authenticate(self):
        """
        Authenticate with Garmin Connect using credentials from environment variables.
        Uses token-based authentication for better session management.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Try to login using existing tokens first
            log.info(f"Trying to login to Garmin Connect using token data from directory '{self.tokenstore}'...")
            
            try:
                self.client = Garmin()
                self.client.login(self.tokenstore)
                log.info("Successfully authenticated with Garmin Connect using stored tokens")
                return True
                
            except (FileNotFoundError, OSError):
                # Tokens not found or expired, need to login with credentials
                log.info("Login tokens not present or expired, login with credentials to generate new tokens...")
                
                # Get credentials from environment variables
                email = os.environ.get("GARMIN_EMAIL")
                password = os.environ.get("GARMIN_PASSWORD")
                
                if not email or not password:
                    log.error("Garmin credentials not found. Please set GARMIN_EMAIL and GARMIN_PASSWORD environment variables.")
                    log.info("Add these to your .env file:")
                    log.info("GARMIN_EMAIL=your_email@example.com")
                    log.info("GARMIN_PASSWORD=your_password")
                    return False
                
                # Login with credentials and save tokens
                self.client = Garmin(email=email, password=password)
                result = self.client.login()
                
                # Handle MFA if required
                if isinstance(result, tuple) and result[0] == "needs_mfa":
                    mfa_code = input("MFA one-time code: ")
                    self.client.resume_login(result[1], mfa_code)
                
                # Save tokens for future use
                self.client.garth.dump(self.tokenstore)
                log.info(f"OAuth tokens stored in '{self.tokenstore}' directory for future use")
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
        """
        Clear authentication tokens instead of calling deprecated logout.
        This removes the stored tokens to effectively 'logout'.
        """
        try:
            if os.path.exists(self.tokenstore):
                # Remove the token directory and all its contents
                for root, dirs, files in os.walk(self.tokenstore, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(self.tokenstore)
                log.info(f"Removed stored login tokens from: {self.tokenstore}")
            else:
                log.info("No stored tokens found to remove")
        except Exception as e:
            log.warning(f"Error removing tokens: {e}")


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
            activity_id = activity.get('activityId', '')
            
            # Calculate pace for both detailed and basic view
            avg_speed = activity.get('averageSpeed', 0)
            pace_str = self.format_pace(avg_speed, activity.get('distance', 0), activity.get('duration', 0))
            
            if detailed:
                # Detailed row: Date, Time, Activity, Type, Duration, Distance, Calories, Pace, Avg Speed, Activity ID
                calories = activity.get('calories', '')
                speed_str = self.format_speed(avg_speed)
                
                row = [
                    date_str, time_str, activity_name, activity_type, duration_str, distance_str,
                    str(calories) if calories else '', pace_str, speed_str, str(activity_id) if activity_id else ''
                ]
            else:
                # Basic row: Date, Time, Activity, Distance, Pace, Activity ID
                row = [date_str, time_str, activity_name, distance_str, pace_str, str(activity_id) if activity_id else '']
            
            table_data.append(row)
        
        # Define headers
        if detailed:
            headers = ['Date', 'Time', 'Activity', 'Type', 'Duration', 'Distance', 'Calories', 'Pace', 'Avg Speed', 'Activity ID']
        else:
            headers = ['Date', 'Time', 'Activity', 'Distance', 'Pace', 'Activity ID']
        
        # Create table
        table_str = tabulate(table_data, headers=headers, tablefmt='presto')
        
        return table_str

    def display_activity_details(self, activity):
        """
        Display detailed information about a single activity using sectioned tables.
        
        Args:
            activity (dict): Activity details dictionary
        """
        if not activity:
            log.error("No activity details to display")
            return
        
        # Extract the actual activity data from summaryDTO if it exists
        activity_data = activity.get('summaryDTO', activity)
        
        print("\n" + "="*80)
        print("ACTIVITY DETAILS")
        print("="*80)
        
        # Meta Information Table
        self._print_meta_table(activity, activity_data)
        
        # Performance Metrics Table  
        self._print_performance_table(activity_data)
        
        # Workout Details Table
        self._print_workout_table(activity_data)
        
        # Location & Environment Table
        self._print_location_table(activity_data)
        
        print("="*80)

    def _print_meta_table(self, activity, activity_data):
        """Print meta information table."""
        meta_data = []
        
        # Activity name and type
        activity_name = activity.get('activityName', 'Untitled')
        activity_type_dto = activity.get('activityTypeDTO', {})
        activity_type = activity_type_dto.get('typeKey', 'Unknown')
        activity_id = activity.get('activityId', '')
        
        meta_data.append(['Activity Name', activity_name])
        meta_data.append(['Activity Type', activity_type])
        if activity_id:
            meta_data.append(['Activity ID', str(activity_id)])
        
        # Date and time
        start_time = activity_data.get('startTimeLocal', '') or activity_data.get('startTimeGMT', '')
        if start_time:
            try:
                dt = pendulum.parse(start_time)
                meta_data.append(['Date', dt.format('YYYY-MM-DD dddd')])
                meta_data.append(['Start Time', dt.format('HH:mm:ss')])
            except Exception:
                meta_data.append(['Start Time', start_time])
        
        # Description
        description = activity.get('description')
        if description:
            meta_data.append(['Description', description])
        
        print("\n📊 META INFORMATION")
        print(tabulate(meta_data, headers=['Field', 'Value'], tablefmt='presto'))

    def _print_performance_table(self, activity_data):
        """Print performance metrics table."""
        perf_data = []
        
        # Duration
        duration_seconds = (activity_data.get('duration') or 
                          activity_data.get('elapsedDuration') or 
                          activity_data.get('movingDuration') or 0)
        
        if duration_seconds and duration_seconds > 0:
            duration_seconds = int(duration_seconds)
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            perf_data.append(['Duration', f"{hours:02d}:{minutes:02d}:{seconds:02d}"])
        
        # Moving duration if different
        moving_duration = activity_data.get('movingDuration')
        if moving_duration and moving_duration != duration_seconds and moving_duration > 0:
            moving_duration = int(moving_duration)
            hours = moving_duration // 3600
            minutes = (moving_duration % 3600) // 60
            seconds = moving_duration % 60
            perf_data.append(['Moving Time', f"{hours:02d}:{minutes:02d}:{seconds:02d}"])
        
        # Distance
        distance_meters = (activity_data.get('distance') or 
                         activity_data.get('totalDistance') or 0)
        
        if distance_meters and distance_meters > 0:
            distance_miles = distance_meters / 1609.344
            perf_data.append(['Distance', f"{distance_miles:.2f} mi"])
        
        # Steps
        steps = activity_data.get('steps')
        if steps and float(steps) > 0:
            perf_data.append(['Steps', f"{int(float(steps)):,}"])
        
        # Calories
        calories = activity_data.get('calories')
        if calories:
            perf_data.append(['Calories', str(int(float(calories)))])
        
        # Pace
        avg_speed = activity_data.get('averageSpeed', 0)
        if avg_speed and distance_meters and duration_seconds:
            pace_str = self.format_pace(avg_speed, distance_meters, duration_seconds)
            if pace_str:
                perf_data.append(['Average Pace', pace_str])
        
        # Speed
        avg_speed = activity_data.get('averageSpeed', 0) or activity_data.get('averageMovingSpeed', 0)
        if avg_speed:
            avg_speed = float(avg_speed)
            avg_speed_mph = avg_speed * 2.237
            perf_data.append(['Average Speed', f"{avg_speed_mph:.2f} mph"])
        
        max_speed = activity_data.get('maxSpeed', 0)
        if max_speed:
            max_speed = float(max_speed)
            max_speed_mph = max_speed * 2.237
            perf_data.append(['Maximum Speed', f"{max_speed_mph:.2f} mph"])
        
        if perf_data:
            print("\n🏃 PERFORMANCE METRICS")
            print(tabulate(perf_data, headers=['Metric', 'Value'], tablefmt='presto'))

    def _print_workout_table(self, activity_data):
        """Print workout details table."""
        workout_data = []
        
        # Heart rate metrics
        avg_hr = activity_data.get('averageHR')
        max_hr = activity_data.get('maxHR')
        min_hr = activity_data.get('minHR')
        if avg_hr:
            workout_data.append(['Average Heart Rate', f"{int(float(avg_hr))} bpm"])
        if max_hr:
            workout_data.append(['Maximum Heart Rate', f"{int(float(max_hr))} bpm"])
        if min_hr:
            workout_data.append(['Minimum Heart Rate', f"{int(float(min_hr))} bpm"])
        
        # Cadence
        avg_running_cadence = (activity_data.get('avgRunningCadenceInStepsPerMinute') or 
                              activity_data.get('averageRunCadence'))
        max_running_cadence = (activity_data.get('maxRunningCadenceInStepsPerMinute') or 
                              activity_data.get('maxRunCadence'))
        if avg_running_cadence and float(avg_running_cadence) > 0:
            workout_data.append(['Average Cadence', f"{int(float(avg_running_cadence))} steps/min"])
        if max_running_cadence and float(max_running_cadence) > 0:
            workout_data.append(['Maximum Cadence', f"{int(float(max_running_cadence))} steps/min"])
        
        # Elevation
        elevation_gain = activity_data.get('elevationGain')
        elevation_loss = activity_data.get('elevationLoss')
        if elevation_gain:
            elevation_gain = float(elevation_gain)
            workout_data.append(['Elevation Gain', f"{elevation_gain:.0f} m ({elevation_gain * 3.28084:.0f} ft)"])
        if elevation_loss:
            elevation_loss = float(elevation_loss)
            workout_data.append(['Elevation Loss', f"{elevation_loss:.0f} m ({elevation_loss * 3.28084:.0f} ft)"])
        
        min_elevation = activity_data.get('minElevation')
        max_elevation = activity_data.get('maxElevation')
        if min_elevation is not None:
            min_elevation = float(min_elevation)
            workout_data.append(['Min Elevation', f"{min_elevation:.0f} m ({min_elevation * 3.28084:.0f} ft)"])
        if max_elevation is not None:
            max_elevation = float(max_elevation)
            workout_data.append(['Max Elevation', f"{max_elevation:.0f} m ({max_elevation * 3.28084:.0f} ft)"])
        
        # Training effects
        aerobic_effect = (activity_data.get('aerobicTrainingEffect') or 
                         activity_data.get('aerobicTrainingEffectMessage'))
        anaerobic_effect = (activity_data.get('anaerobicTrainingEffect') or 
                           activity_data.get('anaerobicTrainingEffectMessage'))
        if aerobic_effect:
            workout_data.append(['Aerobic Training Effect', str(aerobic_effect)])
        if anaerobic_effect:
            workout_data.append(['Anaerobic Training Effect', str(anaerobic_effect)])
        
        training_effect_label = activity_data.get('trainingEffectLabel')
        if training_effect_label:
            workout_data.append(['Training Effect', str(training_effect_label)])
        
        # Intensity minutes
        moderate_intensity = activity_data.get('moderateIntensityMinutes')
        vigorous_intensity = activity_data.get('vigorousIntensityMinutes')
        if moderate_intensity and float(moderate_intensity) > 0:
            workout_data.append(['Moderate Intensity Minutes', str(int(float(moderate_intensity)))])
        if vigorous_intensity and float(vigorous_intensity) > 0:
            workout_data.append(['Vigorous Intensity Minutes', str(int(float(vigorous_intensity)))])
        
        # Special equipment metrics
        begin_pack_weight = activity_data.get('beginPackWeight')
        if begin_pack_weight:
            weight_lbs = float(begin_pack_weight) / 453.592
            workout_data.append(['Pack Weight', f"{weight_lbs:.1f} lbs"])
        
        # Body metrics
        body_battery_diff = activity_data.get('differenceBodyBattery')
        if body_battery_diff and abs(float(body_battery_diff)) > 0:
            workout_data.append(['Body Battery Change', str(int(float(body_battery_diff)))])
        
        water_estimated = activity_data.get('waterEstimated')
        if water_estimated and float(water_estimated) > 0:
            workout_data.append(['Water Loss Estimate', f"{float(water_estimated):.1f} L"])
        
        bmr_calories = activity_data.get('bmrCalories')
        if bmr_calories and float(bmr_calories) > 0:
            workout_data.append(['BMR Calories', str(int(float(bmr_calories)))])
        
        # Workout feel and RPE
        workout_feel = activity_data.get('directWorkoutFeel')
        workout_rpe = activity_data.get('directWorkoutRpe')
        if workout_feel:
            workout_data.append(['Workout Feel', str(workout_feel)])
        if workout_rpe:
            workout_data.append(['Workout RPE', str(workout_rpe)])
        
        if workout_data:
            print("\n💪 WORKOUT DETAILS")
            print(tabulate(workout_data, headers=['Metric', 'Value'], tablefmt='presto'))

    def _print_location_table(self, activity_data):
        """Print location and environment table."""
        location_data = []
        
        # GPS coordinates
        start_latitude = activity_data.get('startLatitude')
        start_longitude = activity_data.get('startLongitude')
        end_latitude = activity_data.get('endLatitude')
        end_longitude = activity_data.get('endLongitude')
        
        if start_latitude and start_longitude:
            location_data.append(['Start Location', f"{float(start_latitude):.6f}, {float(start_longitude):.6f}"])
        if end_latitude and end_longitude:
            location_data.append(['End Location', f"{float(end_latitude):.6f}, {float(end_longitude):.6f}"])
        
        if location_data:
            print("\n📍 LOCATION & ENVIRONMENT")
            print(tabulate(location_data, headers=['Field', 'Value'], tablefmt='presto'))

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
