# My Utils

A collection of personal automation scripts and utilities to streamline daily workflows, fitness motivation, and productivity tracking.

## 📁 Project Structure

```
my_utils/
├── scripts/          # Standalone executable scripts
├── utils/            # Python utility modules and libraries
└── prompts/          # AI/LLM prompt files
```

## 🚀 Scripts Overview

### `scripts/`

- **`goruck_wod.py`** - Fetches daily GORUCK workouts with optional Gordon Ramsay-style AI motivation and WebEx notifications
- **`garmin_activities.py`** - Fetches and displays Garmin Connect activities in table format with authentication support
- **`timeflip.py`** - TimeFlip device integration for automated time tracking and logging
- **`daily_calendar.sh`** - Daily calendar processing and notifications
- **`ical.sh`** - iCal calendar synchronization and management
- **`test_gns_llm.py`** - Test script for LLM integrations
- **`skeleton.py`** - Template script for new Python utilities

### `utils/`

- **`gns_llm.py`** - LLM integration and prompt management
- **`goruck_scraper.py`** - Web scraping utilities for GORUCK workout data
- **`my_logging.py`** - Custom logging configuration
- **`notify.py`** - WebEx notification and messaging utilities

### `prompts/`

- **`gordon_ramsay_personal_trainer.txt`** - AI prompt for Gordon Ramsay-style fitness motivation

## ⚙️ Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd my_utils
   ```

2. **Install dependencies**
   ```bash
   pipenv install
   # or
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your actual credentials and tokens
   ```

4. **Set up crontab (optional)**
   ```bash
   cp crontab.template my_crontab.txt
   # Edit my_crontab.txt with your paths and preferences
   crontab my_crontab.txt
   ```

## 🕐 Automated Schedule (Crontab)

The repository includes automation for:

- **Calendar sync** - Every 5 minutes (multiple calendar sources)
- **Time tracking** - Daily at 23:55 (TimeFlip data collection)
- **Fitness motivation** - Weekdays at 8:30 AM (GORUCK workout with Gordon Ramsay motivation)
- **Team reports** - Weekly (individual productivity reports)
- **Weather updates** - Weekly weather reports

See `crontab.template` for the complete automation schedule.

## 🔧 Key Features

- **🏋️ Fitness Integration**: Automated GORUCK workout fetching with AI-powered motivational coaching
- **📅 Calendar Management**: Multi-source calendar synchronization and processing
- **⏰ Time Tracking**: Automated TimeFlip device data collection and logging
- **🤖 AI Integration**: LLM-powered content generation and motivation
- **📨 Notifications**: WebEx integration for automated messaging and alerts
- **📊 Reporting**: Automated productivity and team reporting

## 🛡️ Security

- Sensitive credentials are stored in `.env` (not committed to repo)
- Template files provided for easy setup without exposing personal data
- `.gitignore` configured to exclude sensitive files

## 📋 Usage Examples

### Get today's GORUCK workout with Gordon Ramsay motivation:
```bash
python scripts/goruck_wod.py --gordon --webex
```

### Generate workout list for the past week:
```bash
python scripts/goruck_wod.py -l --days 7
```

### Run TimeFlip data collection:
```bash
python scripts/timeflip.py -d 2025-08-17
```

### Display Garmin Connect activities in table format:
```bash
python scripts/garmin_activities.py --days 7 --table
```

### Get detailed Garmin activities with performance metrics:
```bash
python scripts/garmin_activities.py --days 14 --table --detailed
```

### Filter activities by type (e.g., running, cycling):
```bash
python scripts/garmin_activities.py --activity-type running --days 30
```
