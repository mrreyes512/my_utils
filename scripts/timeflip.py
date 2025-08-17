import argparse
import logging
import os, sys
import requests
import json
import pendulum

from dotenv import load_dotenv
from humanfriendly import format_timespan

log = logging.getLogger(__name__)
load_dotenv()

base_url = os.environ["TIMEFLIP_URI"]
username = os.environ["TIMEFLIP_USER"]
password = os.environ["TIMEFLIP_PASS"]

logging.basicConfig(
    format='%(asctime)s | %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
    )

def get_token():
    """
    Return Auth Token
    """
    log.info(f"Authenticating with username: {username}")

    url = f"{base_url}/api/auth/email/sign-in"
    
    payload = json.dumps({
        "email": username,
        "password": password
    })

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    log.info(f"Authenticated as: {response.json()['user']['fullName']}")

    return response.headers['Token']

def get_daily_tasks(token, date):
    """
    Get daily tasks
    """

    log.info(f"Getting daily tasks for: {date}")

    url = f"{base_url}/report/daily?beginDateStr={date}&endDateStr={date}&timeOrPaymentSorting=true"
    # parameters = 
    
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("POST", url, headers=headers).json()

    # print(json.dumps(response, indent=4))

    return response

def parse_daily_report(data):
    """
    Parse the daily tasks from api
    This round time to nearest 15 and will ignore things less than 15 mins
    """

    formated_msg = ""

    # There's got to be a better way to peel out the data needed, but this works...
    for week in data['weeks']:

        for day in week['days']:
            if day['inPeriod']:

                for task_info in day['tasksInfo']:

                    # print(json.dumps(task_info, indent=4))
                    task_name = task_info['task']['name']
                    time_seconds = task_info['totalTime']
                    human_time = format_timespan(time_seconds)

                    round_seconds = 900 * round(time_seconds/900) # Round to nearest 15 mins, 900s = 15min
                    round_time = format_timespan(round_seconds)
                    log.info(f"- Task: {task_name} - {human_time}")

                    # Ignore things with tag, sorry for neg logic...
                    if task_info['task']['tag'] != 'ignore':

                        # Ignore things below 15m(900s)
                        if task_info['totalTime'] > 900:

                            # print(json.dumps(task_info, indent=4))
                            formated_msg += f"- Task: {task_name} - {round_time}\n"

    return formated_msg

def main(date):
    log.info(f'Welcome to the main function')

    token = get_token()
    # print(token)

    # date = "2024-11-27"

    msg = ""
    while True:

        tasks = get_daily_tasks(token=token, date=date)
        text_report = parse_daily_report(tasks)

        if text_report == "":
            log.info(f"** No interesting tasks found for: {date}")
            msg += f"No tasks found for: **{date}**\n"
            date = pendulum.parse(date).subtract(days=1).to_date_string()
        else:
            msg += f"Tasks logged for **{date}**\n"
            msg += text_report
            break

    print(msg)

if __name__ == "__main__":

    log.info(f'{ "="*20 } Starting Script: { os.path.basename(__file__) } { "="*20 }')

    date = pendulum.now().to_date_string()

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--date', type=str, default=date)
    parser.add_argument('-v', action='store_true')
    args = parser.parse_args()

    if args.v:
        logging.getLogger().setLevel(logging.INFO)

    main(args.date)
