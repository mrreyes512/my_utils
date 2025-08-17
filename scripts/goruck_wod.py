#!/usr/bin/env python3

import argparse
import logging
import pendulum
import os, sys
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path to import utils modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.my_logging import MY_Logger
from utils.goruck_scraper import get_daily_workout, get_workout_list, create_workout_dataframe
from utils.notify import MY_CiscoWebex
from utils.gns_llm import GNS_LLM

# Set up logging
log = MY_Logger(log_level=logging.WARNING).get_logger()
log.propagate = False

# Set up environment variables
load_dotenv()

now = pendulum.now().format('YYYY-MM-DD')

def print_workout(workout_data):
    """
    Pretty prints the workout data.
    
    Args:
        workout_data (dict): Workout data dictionary
    """
    if not workout_data:
        print("No workout data available.")
        return
    
    print("=" * 50)
    print(f"GORUCK WORKOUT: {workout_data['title']}")
    print(f"Date: {workout_data['date']}")
    print(f"URL: {workout_data['url']}")
    if workout_data.get('youtube_url'):
        print(f"YouTube: {workout_data['youtube_url']}")
    print("=" * 50)
    
    if workout_data['details']:
        for detail in workout_data['details']:
            print(detail)
    else:
        print("No workout details available.")
    
    print("=" * 50)

def format_workout_for_webex(workout_data):
    """
    Formats workout data for WebEx message (markdown format).
    
    Args:
        workout_data (dict): Workout data dictionary
        
    Returns:
        str: Formatted markdown message for WebEx
    """
    if not workout_data:
        return "**No workout data available.**"
    
    message = f"## GORUCK WORKOUT: {workout_data['title']}\n\n"
    message += f"**Date:** {workout_data['date']}\n\n"
    message += f"**URL:** {workout_data['url']}\n\n"
    
    if workout_data.get('youtube_url'):
        message += f"**YouTube:** {workout_data['youtube_url']}\n\n"
    
    if workout_data['details']:
        message += "**Workout Details:**\n\n"
        for detail in workout_data['details']:
            message += f"- {detail}\n"
    else:
        message += "**No workout details available.**\n"
    
    return message

def send_webex_message(message, recipient=None):
    """
    Sends a message via WebEx.
    
    Args:
        message (str): The message to send
        recipient (str): WebEx recipient (email, room name, or room ID)
    """
    try:
        # Get WebEx access token from environment
        webex_token = os.getenv('WEBEX_TOKEN')
        if not webex_token:
            log.error("WEBEX_TOKEN not found in environment variables")
            print("WebEx access token not configured. Cannot send message.")
            return False
            
        # Initialize WebEx client
        webex = MY_CiscoWebex(access_token=webex_token)
        
        # Default email
        default_email = 'mark.reyes@evernorth.com'
        
        # Use default recipient if none provided
        if not recipient:
            recipient = os.getenv('WEBEX_DEFAULT_RECIPIENT', default_email)
            log.info(f"No recipient specified, using default: {recipient}")
        
        # Send to the specified recipient
        message_sent = webex.api.messages.create(
            toPersonEmail=recipient if "@" in recipient else None,
            roomId=recipient if recipient.startswith("Y2lzY29zcGFyazovL3VzL1JPT00") else None,
            markdown=message
        )
        print(f"✅ Message sent to {recipient}")
        print(f"   Message ID: {message_sent.id}")
        
        # If recipient is not your email, also send a copy to you
        if recipient != default_email and not recipient.startswith("Y2lzY29zcGFyazovL3VzL1JPT00"):
            copy_message = webex.api.messages.create(
                toPersonEmail=default_email,
                markdown=f"**Copy of message sent to {recipient}:**\n\n{message}"
            )
            print(f"✅ Copy sent to {default_email}")
            print(f"   Copy Message ID: {copy_message.id}")
        
        return True
        
    except Exception as e:
        log.error(f"Failed to send WebEx message: {e}")
        print(f"❌ Failed to send WebEx message: {e}")
        return False

def get_gordon_ramsay_motivation(workout_data):
    """
    Get Gordon Ramsay-style motivation for a workout using the LLM.
    
    Args:
        workout_data (dict): Workout data from GORUCK scraper
        
    Returns:
        str: Gordon Ramsay-style motivational workout instructions
    """
    try:
        # Check for required environment variables
        environment_url = os.getenv('AI_COE_ENV_URL')
        project_name = os.getenv('AI_COE_PROJECT_NAME')
        api_key = os.getenv('AI_COE_TOKEN')
        
        if not environment_url:
            return "❌ AI_COE_ENV_URL not found in environment variables. Please set it in your .env file."
        if not project_name:
            return "❌ AI_COE_PROJECT_NAME not found in environment variables. Please set it in your .env file."
        if not api_key:
            return "❌ AI_COE_TOKEN not found in environment variables. Please set it in your .env file."
        
        log.info(f"Initializing GNS_LLM with environment: {environment_url}, project: {project_name}")
        
        # Initialize the LLM
        llm = GNS_LLM(
            environment_url=environment_url,
            projectname=project_name,
            api_key=api_key
        )
        
        # Set the Gordon Ramsay trainer prompt
        prompt_file = os.path.join(os.path.dirname(__file__), "..", "prompts", "gordon_ramsay_personal_trainer.txt")
        if not os.path.exists(prompt_file):
            return f"❌ Gordon Ramsay prompt file not found at: {prompt_file}"
        
        llm.set_prompt(prompt_file)
        
        # Prepare the workout context
        workout_context = f"""
        Here are today's workout details:
        
        Workout: {workout_data['title']}
        Date: {workout_data['date']}
        URL: {workout_data['url']}
        
        Workout Details:
        """
        
        if workout_data['details']:
            for detail in workout_data['details']:
                workout_context += f"- {detail}\n"
        else:
            workout_context += "- No specific details provided\n"
        
        # Set the context
        llm.set_context(workout_context)
        
        # Ask Gordon to motivate us!
        question = "Gordon, I need you to yell these workout instructions at me and motivate me to crush this workout! Give me your best motivational training session!"
        
        # Use the AI COE engine from environment variables
        model = os.getenv('AI_COE_ENGINE', 'ai-coe-gpt4o:analyze')
        log.info(f"Using model: {model}")
        
        response = llm.ask_question(question, model=model)
        return response
        
    except Exception as e:
        log.error(f"Error getting Gordon Ramsay motivation: {e}")
        return f"❌ Error getting Gordon Ramsay motivation: {e}\n\nPlease check your environment variables:\n- AI_COE_ENV_URL\n- AI_COE_PROJECT_NAME\n- AI_COE_TOKEN"

def display_workout_list(args):
    """
    Handles the display of workout lists in short or long format.
    
    Args:
        args: Parsed command line arguments
    """
    # Determine format based on number of -l flags
    short_format = (args.l == 1)  # -l = short, -ll = long
    list_type = "short" if short_format else "long"
    
    log.info(f"Creating {list_type} workout list for the last {args.days} days")
    df = create_workout_dataframe(days=args.days, include_youtube=args.youtube, short_format=short_format)
    
    if df.empty:
        print("No workouts found for the specified time period.")
    else:
        format_label = "Short" if short_format else "Long"
        print(f"\nGORUCK Workouts - {format_label} Format ({args.days} days):")
        print("=" * 60)
        
        # Display as a formatted table
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        if short_format:
            pd.set_option('display.max_colwidth', 30)  # Shorter for compact view
            # Custom formatting for short format with left-aligned names
            print(f"{'date':<12} {'name':<30}")
            for _, row in df.iterrows():
                print(f"{row['date']:<12} {row['name']:<30}")
        else:
            pd.set_option('display.max_colwidth', 50)  # Longer for full URLs
            # Custom formatting for long format with left-aligned columns
            if args.youtube:
                print(f"{'date':<12} {'name':<30} {'blog_link':<50} {'youtube_link':<50}")
                for _, row in df.iterrows():
                    youtube_link = row.get('youtube_link', '') or ''  # Handle None values
                    print(f"{row['date']:<12} {row['name']:<30} {row['blog_link']:<50} {youtube_link:<50}")
            else:
                print(f"{'date':<12} {'name':<30} {'blog_link':<50}")
                for _, row in df.iterrows():
                    print(f"{row['date']:<12} {row['name']:<30} {row['blog_link']:<50}")
        
        # Optionally save to CSV
        if args.save:
            format_suffix = "short" if short_format else "long"
            filename = f"goruck_workouts_{format_suffix}_{pendulum.now().format('YYYY-MM-DD')}.csv"
            df.to_csv(filename, index=False)
            print(f"\nDataFrame saved to: {filename}")

def main(args):
    log.info('Welcome to the main function')
    
    if args.l > 0:
        display_workout_list(args)
    else:
        log.info(f"Getting daily workout for: {args.date}")
        
        # Get the daily workout
        try:
            workout = get_daily_workout(args.date)
        except Exception as e:
            log.error(f"Error fetching workout for {args.date}: {e}")
            workout = None
        
        # If no workout found for today, try yesterday
        if not workout:
            try:
                yesterday_date = pendulum.parse(args.date).subtract(days=1).to_date_string()
                log.info(f"No workout found for {args.date}, trying previous day: {yesterday_date}")
                print(f"No workout found for {args.date}, trying previous day: {yesterday_date}")
                workout = get_daily_workout(yesterday_date)
                
                if workout:
                    print(f"📅 Using previous day's workout ({yesterday_date})")
            except Exception as e:
                log.error(f"Error fetching fallback workout: {e}")
                workout = None
        
        if workout:
            # Always show the workout header
            print("=" * 50)
            print(f"GORUCK WORKOUT: {workout['title']}")
            print(f"Date: {workout['date']}")
            print(f"URL: {workout['url']}")
            if workout.get('youtube_url'):
                print(f"YouTube: {workout['youtube_url']}")
            print("=" * 50)
            
            # Get Gordon Ramsay motivation if requested
            if args.gordon:
                print("🔥 GORDON RAMSAY PERSONAL TRAINER SESSION 🔥")
                print("-"*45)
                gordon_motivation = get_gordon_ramsay_motivation(workout)
                print(gordon_motivation)
                print("="*50)
                log.info("Gordon Ramsay motivation session completed")
                
                # Send Gordon's motivation to WebEx if requested
                if args.webex:
                    webex_message = f"## 🔥 GORDON RAMSAY PERSONAL TRAINER SESSION 🔥\n\n{gordon_motivation}"
                    send_webex_message(webex_message, args.recipient)
            else:
                # Show regular workout details
                if workout['details']:
                    for detail in workout['details']:
                        print(detail)
                else:
                    print("No workout details available.")
                print("=" * 50)
                log.info("Workout downloaded and displayed successfully")
                
                # Send regular workout to WebEx if requested
                if args.webex:
                    webex_message = format_workout_for_webex(workout)
                    send_webex_message(webex_message, args.recipient)
        else:
            log.error("Failed to download workout")
            print("Could not retrieve today's workout. Please try again later.")

if __name__ == "__main__":

    date = pendulum.now().to_date_string()

    parser = argparse.ArgumentParser(description="Download daily GORUCK workout or create workout list")
    parser.add_argument('-d', '--date', type=str, default=date, 
                       help=f"Date in YYYY-MM-DD format (default: {date})")
    parser.add_argument('-v', action='store_true', help="Enable verbose logging")
    parser.add_argument('-l', action='count', default=0,
                       help="Create workout list: -l for short format, -ll for long format")
    parser.add_argument('--days', type=int, default=7,
                       help="Number of days to look back for workouts (default: 7)")
    parser.add_argument('--youtube', action='store_true',
                       help="Include YouTube links in long list (slower)")
    parser.add_argument('--save', action='store_true',
                       help="Save DataFrame to CSV file")
    parser.add_argument('--webex', action='store_true',
                       help="Send workout to WebEx")
    parser.add_argument('--recipient', type=str,
                       help="WebEx recipient (email, room name, or room ID)")
    parser.add_argument('--gordon', action='store_true',
                       help="Get Gordon Ramsay-style motivational workout instructions using LLM")
    parser.add_argument('--fallback', action='store_true',
                       help="Try previous day if no workout found for specified date (default: enabled)")
    args = parser.parse_args()

    if args.v:
        log = MY_Logger(log_level=logging.INFO).get_logger()
    log.info(f'{ "="*20 } Starting Script: { os.path.basename(__file__) } { "="*20 }')

    main(args)
