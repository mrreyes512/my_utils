#!/bin/bash

# Script to install aliases for my_utils scripts into ~/.aliases
# Usage: ./scripts/install_aliases.sh

set -e

ALIASES_FILE="$HOME/.aliases_new"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS_DIR="$(dirname "$SCRIPT_DIR")"

# Check if Python virtual environment is available
if [ -f "$UTILS_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$UTILS_DIR/.venv/bin/python"
elif command -v pipenv &> /dev/null && [ -f "$UTILS_DIR/Pipfile" ]; then
    PYTHON_CMD="pipenv run python"
else
    PYTHON_CMD="python3"
fi

echo "Installing my_utils aliases to $ALIASES_FILE..."
echo "Using Python command: $PYTHON_CMD"
echo "Utils directory: $UTILS_DIR"

# Create aliases file if it doesn't exist
touch "$ALIASES_FILE"

# Add a section header for our aliases
echo "" >> "$ALIASES_FILE"
echo "# ============================================================================" >> "$ALIASES_FILE"
echo "# my_utils aliases - $(date)" >> "$ALIASES_FILE"
echo "# ============================================================================" >> "$ALIASES_FILE"

# GORUCK workout aliases
echo "" >> "$ALIASES_FILE"
echo "# GORUCK Workout aliases" >> "$ALIASES_FILE"
echo "alias goruck='cd $UTILS_DIR && $PYTHON_CMD scripts/goruck_wod.py'" >> "$ALIASES_FILE"
echo "alias goruck-gordon='cd $UTILS_DIR && $PYTHON_CMD scripts/goruck_wod.py --gordon'" >> "$ALIASES_FILE"
echo "alias goruck-list='cd $UTILS_DIR && $PYTHON_CMD scripts/goruck_wod.py -l'" >> "$ALIASES_FILE"
echo "alias goruck-week='cd $UTILS_DIR && $PYTHON_CMD scripts/goruck_wod.py -l --days 7'" >> "$ALIASES_FILE"

# Garmin Connect aliases
echo "" >> "$ALIASES_FILE"
echo "# Garmin Connect aliases" >> "$ALIASES_FILE"
echo "alias garmin='cd $UTILS_DIR && $PYTHON_CMD scripts/garmin_activities.py'" >> "$ALIASES_FILE"
echo "alias garmin-table='cd $UTILS_DIR && $PYTHON_CMD scripts/garmin_activities.py --table'" >> "$ALIASES_FILE"
echo "alias garmin-week='cd $UTILS_DIR && $PYTHON_CMD scripts/garmin_activities.py --days 7 --table'" >> "$ALIASES_FILE"
echo "alias garmin-detailed='cd $UTILS_DIR && $PYTHON_CMD scripts/garmin_activities.py --table --detailed'" >> "$ALIASES_FILE"
echo "alias garmin-running='cd $UTILS_DIR && $PYTHON_CMD scripts/garmin_activities.py --activity-type running --table'" >> "$ALIASES_FILE"
echo "alias garmin-cycling='cd $UTILS_DIR && $PYTHON_CMD scripts/garmin_activities.py --activity-type cycling --table'" >> "$ALIASES_FILE"

# TimeFlip aliases
echo "" >> "$ALIASES_FILE"
echo "# TimeFlip aliases" >> "$ALIASES_FILE"
echo "alias timeflip='cd $UTILS_DIR && $PYTHON_CMD scripts/timeflip.py'" >> "$ALIASES_FILE"
echo "alias timeflip-today='cd $UTILS_DIR && $PYTHON_CMD scripts/timeflip.py -d \$(date +%Y-%m-%d)'" >> "$ALIASES_FILE"
echo "alias timeflip-yesterday='cd $UTILS_DIR && $PYTHON_CMD scripts/timeflip.py -d \$(date -v-1d +%Y-%m-%d)'" >> "$ALIASES_FILE"

# Calendar aliases
echo "" >> "$ALIASES_FILE"
echo "# Calendar aliases" >> "$ALIASES_FILE"
echo "alias cal-today='cd $UTILS_DIR && ./scripts/ical.sh'" >> "$ALIASES_FILE"
echo "alias cal-tomorrow='cd $UTILS_DIR && ./scripts/ical.sh 1'" >> "$ALIASES_FILE"
echo "alias cal-week='cd $UTILS_DIR && for i in {0..6}; do echo \"== Day +\$i ==\"; ./scripts/ical.sh \$i; echo; done'" >> "$ALIASES_FILE"
echo "alias daily-cal='cd $UTILS_DIR && ./scripts/daily_calendar.sh'" >> "$ALIASES_FILE"

# Utility aliases
echo "" >> "$ALIASES_FILE"
echo "# my_utils utility aliases" >> "$ALIASES_FILE"
echo "alias my-utils='cd $UTILS_DIR'" >> "$ALIASES_FILE"
echo "alias my-logs='cd $HOME/logs && ls -la'" >> "$ALIASES_FILE"
echo "alias my-env='cd $UTILS_DIR && cat .env.template'" >> "$ALIASES_FILE"

# Combined workflow aliases
echo "" >> "$ALIASES_FILE"
echo "# Combined workflow aliases" >> "$ALIASES_FILE"
echo "alias morning-fitness='echo \"=== GORUCK Workout ===\"; goruck-gordon; echo; echo \"=== Recent Garmin Activities ===\"; garmin-table'" >> "$ALIASES_FILE"
echo "alias daily-summary='echo \"=== Today Calendar ===\"; cal-today; echo; echo \"=== TimeFlip Tasks ===\"; timeflip-today'" >> "$ALIASES_FILE"
echo "alias fitness-week='echo \"=== GORUCK Workouts ===\"; goruck-week; echo; echo \"=== Garmin Activities ===\"; garmin-week'" >> "$ALIASES_FILE"

echo "" >> "$ALIASES_FILE"
echo "# ============================================================================" >> "$ALIASES_FILE"

echo "✅ Aliases installed successfully!"
echo ""
echo "🔄 To reload your aliases, run:"
echo "   source $ALIASES_FILE"
echo ""
echo "📋 Available aliases:"
echo ""
echo "GORUCK Workouts:"
echo "  goruck            - Get today's workout"
echo "  goruck-gordon     - Get today's workout with Gordon Ramsay motivation"
echo "  goruck-list       - List recent workouts (short format)"
echo "  goruck-week       - List workouts from past week"
echo ""
echo "Garmin Connect:"
echo "  garmin            - Show recent activities (simple list)"
echo "  garmin-table      - Show activities in table format"
echo "  garmin-week       - Show week's activities in table"
echo "  garmin-detailed   - Show detailed activity metrics"
echo "  garmin-running    - Show only running activities"
echo "  garmin-cycling    - Show only cycling activities"
echo ""
echo "TimeFlip Tracking:"
echo "  timeflip          - Show TimeFlip tasks"
echo "  timeflip-today    - Show today's tasks"
echo "  timeflip-yesterday - Show yesterday's tasks"
echo ""
echo "Calendar:"
echo "  cal-today         - Show today's calendar"
echo "  cal-tomorrow      - Show tomorrow's calendar"
echo "  cal-week          - Show next 7 days"
echo "  daily-cal         - Daily calendar format"
echo ""
echo "Utilities:"
echo "  my-utils          - Navigate to utils directory"
echo "  my-logs           - View logs directory"
echo "  my-env            - Show environment template"
echo ""
echo "Workflows:"
echo "  morning-fitness   - GORUCK workout + Garmin activities"
echo "  daily-summary     - Calendar + TimeFlip tasks"
echo "  fitness-week      - Weekly fitness overview"
echo ""
echo "💡 Tip: Add 'source $ALIASES_FILE' to your ~/.zshrc to auto-load aliases"
