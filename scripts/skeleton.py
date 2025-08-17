import argparse
import logging
import pendulum
import os, sys
from dotenv import load_dotenv

from utils.my_logging import MY_Logger

# Set up logging
log = MY_Logger(log_level=logging.WARNING).get_logger()
log.propagate = False

# Set up environment variables
load_dotenv()
base_url = os.environ["BASIC_URI"]
username = os.environ["BASIC_USER"]
password = os.environ["BASIC_PASS"]

now = pendulum.now().format('YYYY-MM-DD')

def main(args):
    log.info(f'Welcome to the main function')
    log.info(f"Getting daily tasks for: {args.date}")

if __name__ == "__main__":

    date = pendulum.now().to_date_string()

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--date', type=str, default=date)
    parser.add_argument('-v', action='store_true')
    args = parser.parse_args()

    if args.v:
        log = MY_Logger(log_level=logging.INFO).get_logger()
    log.info(f'{ "="*20 } Starting Script: { os.path.basename(__file__) } { "="*20 }')

    main(args)
