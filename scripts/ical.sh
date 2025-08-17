#!/bin/bash
# set -x

ical="/opt/homebrew/bin/icalbuddy"
format="- [ ] "
days_ahead="${1:-0}" # Defaulting to 0 if no $1 is discovered
desired_date=$(date -v+${days_ahead}d +%Y-%m-%d)
log_file=${desired_date}_calendar.txt
log_dir="/Users/c8q9cp/logs/calendar"

# echo -e $days_ahead
# echo -e $desired_date

#date +"%Y-%m-%d"
# $ical -b "$format" -tf "%H%M" -ps "|: |" -iep "datetime,title" -po "datetime,title" -ea -npn -nc eventsToday

get_ical () {
    $ical -b "$format" \
        -tf "%H%M" -df "%Y-%m-%d" \
        -ps "|: |" \
        -iep "datetime,title" \
        -po "datetime,title" \
        -ea -npn -nrd -nc \
        eventsFrom:$desired_date to:$desired_date
}

# Output if interactive terminal
#[[ $- =~ i ]] && echo -e "Date: $desired_date"
[ -z "$PS1" ] && echo -e "Events for: $desired_date"

get_ical | sed "s/$desired_date at //g" | tee $log_dir/$log_file
