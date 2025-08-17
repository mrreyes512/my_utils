#!/bin/bash

#date +"> Date: %Y-%m-%d"
/opt/homebrew/bin/icalbuddy -b "> - [ ] " -ea -nc -iep datetime,title -eed -po datetime,title -ps "| |" eventsToday
