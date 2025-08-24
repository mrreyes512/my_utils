# Garmin Connect Activities Script

## Overview

The `garmin_activities.py` script allows you to fetch and display your Garmin Connect activities in a clean table format. It authenticates with your Garmin Connect account and can display activities with various filtering and formatting options.

## Features

- 🏃 **Activity Fetching**: Get activities from your Garmin Connect account for any date range
- 📊 **Table Display**: Clean, formatted table view of your activities
- 🔍 **Filtering**: Filter activities by type (running, cycling, swimming, etc.)
- 📈 **Detailed Metrics**: Optional display of performance metrics (heart rate, calories, speed, etc.)
- 🆔 **Activity Details**: Get detailed information for specific activities
- 🔒 **Secure Authentication**: Uses environment variables for credentials

## Setup

### 1. Install Dependencies

The script will automatically install required dependencies, but you can also install them manually:

```bash
pipenv install garminconnect tabulate
```

### 2. Configure Credentials

Add your Garmin Connect credentials to your `.env` file:

```bash
# Copy .env.template to .env first
cp .env.template .env

# Then edit .env and add:
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password_here
```

**Important**: Never commit your `.env` file to version control. Your credentials should be kept private.

## Usage Examples

### Basic Usage

Display the last 7 days of activities in a simple list:
```bash
python scripts/garmin_activities.py
```

### Table View

Display activities in a formatted table:
```bash
python scripts/garmin_activities.py --days 7 --table
```

### Detailed Table

Include performance metrics in the table:
```bash
python scripts/garmin_activities.py --days 14 --table --detailed
```

### Filter by Activity Type

Show only running activities from the past month:
```bash
python scripts/garmin_activities.py --activity-type running --days 30 --table
```

### Get Activity Details

Get detailed information about a specific activity:
```bash
python scripts/garmin_activities.py --activity-id 12345678901
```

### Show Activity IDs

Display activity IDs for reference:
```bash
python scripts/garmin_activities.py --days 7 --show-ids
```

### Verbose Logging

Enable detailed logging to see what the script is doing:
```bash
python scripts/garmin_activities.py --days 7 --table --verbose
```

## Output Examples

### Simple List View
```
Found 5 activities:
 1. Morning Run (running) - 2025-08-16
 2. Evening Bike Ride (cycling) - 2025-08-15
 3. Strength Training (strength_training) - 2025-08-14
 4. Swimming Workout (swimming) - 2025-08-13
 5. Long Run (running) - 2025-08-12
```

### Table View
```
┌────────────┬───────┬─────────────────┬─────────────────┬──────────┬──────────┐
│ Date       │ Time  │ Activity        │ Type            │ Duration │ Distance │
├────────────┼───────┼─────────────────┼─────────────────┼──────────┼──────────┤
│ 2025-08-16 │ 06:30 │ Morning Run     │ running         │ 45m      │ 8.2 km   │
│ 2025-08-15 │ 18:15 │ Evening Ride    │ cycling         │ 1h 20m   │ 25.4 km  │
│ 2025-08-14 │ 19:00 │ Strength        │ strength_train  │ 50m      │          │
└────────────┴───────┴─────────────────┴─────────────────┴──────────┴──────────┘
```

### Detailed Table View
```
┌────────────┬───────┬─────────────┬─────────┬──────────┬──────────┬──────────┬────────┬────────┬───────────┐
│ Date       │ Time  │ Activity    │ Type    │ Duration │ Distance │ Calories │ Avg HR │ Max HR │ Avg Speed │
├────────────┼───────┼─────────────┼─────────┼──────────┼──────────┼──────────┼────────┼────────┼───────────┤
│ 2025-08-16 │ 06:30 │ Morning Run │ running │ 45m      │ 8.2 km   │ 420      │ 155    │ 172    │ 10.9 km/h │
└────────────┴───────┴─────────────┴─────────┴──────────┴──────────┴──────────┴────────┴────────┴───────────┘
```

### Activity Details View
```
============================================================
ACTIVITY DETAILS
============================================================
Name: Morning 5K Run
Type: running
Date: 2025-08-16 Saturday
Start Time: 06:30:15
Duration: 00:28:45
Distance: 5.12 km
Calories: 285
Average Heart Rate: 152 bpm
Maximum Heart Rate: 168 bpm
Average Speed: 10.7 km/h
Elevation Gain: 45 m
Aerobic Training Effect: 3.2
============================================================
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-d, --days` | Number of days to look back (default: 7) |
| `-t, --table` | Display activities in table format |
| `--detailed` | Include detailed metrics (use with --table) |
| `--activity-type` | Filter by activity type (running, cycling, etc.) |
| `--activity-id` | Get details for a specific activity ID |
| `--show-ids` | Show activity IDs in list view |
| `-v, --verbose` | Enable detailed logging |

## Supported Activity Types

Common activity types you can filter by:
- `running`
- `cycling`
- `swimming`
- `strength_training`
- `cardio_training`
- `walking`
- `hiking`
- `yoga`
- `pilates`

## Troubleshooting

### Authentication Issues

If you get authentication errors:
1. Double-check your email and password in the `.env` file
2. Make sure your Garmin Connect account is accessible via web browser
3. Try logging into Garmin Connect manually to ensure your account isn't locked
4. Check if you have 2FA enabled (the script doesn't support 2FA yet)

### Missing Dependencies

If you get import errors:
```bash
pipenv install garminconnect tabulate pandas
```

### Connection Issues

If you get network or timeout errors:
- Check your internet connection
- Garmin Connect servers might be temporarily unavailable
- Try again after a few minutes

## Privacy and Security

- **Credentials**: Your Garmin Connect credentials are stored locally in the `.env` file
- **No Data Storage**: The script doesn't store your activity data permanently
- **API Usage**: Uses the unofficial `garminconnect` Python library
- **Rate Limiting**: Be respectful of Garmin's servers; don't run the script excessively

## Integration with Other Tools

This script follows the same patterns as other utilities in this repository:
- Uses the same logging framework (`MY_Logger`)
- Follows the same argument parsing conventions
- Can be easily integrated into cron jobs or automation workflows
- Compatible with the existing environment variable system

## Future Enhancements

Potential improvements for future versions:
- Export to CSV/JSON formats
- Integration with local databases
- Visualization charts and graphs
- Comparison between time periods
- Goal tracking and progress monitoring
- Integration with other fitness platforms

## Support

This script uses the community-maintained `garminconnect` library. If you encounter issues:
1. Check the script's verbose output (`--verbose` flag)
2. Verify your Garmin Connect credentials
3. Check the garminconnect library documentation for known issues
4. Consider Garmin Connect API changes that might affect functionality
