#!/usr/bin/env python3
"""
GORUCK Workout Scraper Script

This script scrapes all workouts from the GORUCK workouts blog and saves each as a Markdown file in the specified directory, using a format similar to the provided 'Grin and Bear It' example.

Usage:
    python scripts/goruck_wod_scraper.py
"""

import os
import sys
import logging
import time
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Output directory for notes
OUTPUT_DIR = os.path.expanduser('~/Documents/cignaNotes/journal/goruck_wod/')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("goruck_wod_scraper")

def get_page1_workouts():
    """Get workouts from pages 1 and 2 with proper timeouts and retries."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    all_workouts = []
    
    # Get both page 1 and page 2
    for page_num in [1]:
    # for page_num in [4,5,6]:
        if page_num == 1:
            url = "https://www.goruck.com/blogs/workouts"
        else:
            url = f"https://www.goruck.com/blogs/workouts?page={page_num}"
        
        max_retries = 3
        page_workouts = []
        
        for attempt in range(max_retries):
            try:
                log.info(f"Fetching page {page_num} of GORUCK workouts (attempt {attempt + 1}/{max_retries})...")
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                workout_links = soup.find_all('a', href=re.compile(r'/blogs/workouts/'))
                
                seen_urls = set()
                
                for link in workout_links:
                    href = link.get('href')
                    if href and '/blogs/workouts/' in href and not href.endswith('/blogs/workouts'):
                        # Skip tag pages and other non-workout URLs
                        if '/tagged/' in href or '/pages/' in href or '?' in href:
                            continue
                            
                        if href in seen_urls:
                            continue
                        seen_urls.add(href)
                        
                        # Build full URL
                        workout_url = href if href.startswith('http') else 'https://www.goruck.com' + href
                        
                        # Extract workout name from URL
                        url_parts = href.split('/')
                        if len(url_parts) > 0:
                            slug = url_parts[-1]
                            workout_name = slug.replace('-', ' ').title()
                        else:
                            workout_name = "Unknown Workout"
                        
                        page_workouts.append({
                            'name': workout_name,
                            'url': workout_url
                        })
                
                log.info(f"Found {len(page_workouts)} workouts on page {page_num}")
                break  # Success, exit retry loop
                
            except Exception as e:
                log.warning(f"Page {page_num} attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Progressive delay: 5s, 10s, 15s
                    log.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    log.error(f"All {max_retries} attempts failed for page {page_num}")
        
        # Add this page's workouts to the total
        all_workouts.extend(page_workouts)
        
        # Add delay between pages
        if page_num == 1 and page_workouts:
            log.info("Waiting 3 seconds before fetching page 2...")
            time.sleep(3)
    
    # Remove duplicates (in case same workout appears on multiple pages)
    unique_workouts = []
    seen_urls = set()
    for workout in all_workouts:
        if workout['url'] not in seen_urls:
            unique_workouts.append(workout)
            seen_urls.add(workout['url'])
    
    log.info(f"Found {len(unique_workouts)} total unique workouts across pages 1-2")
    return unique_workouts

def get_workout_details(workout_url):
    """Get detailed information about a specific workout."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        log.info(f"Fetching details for: {workout_url}")
        response = requests.get(workout_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('h1')
        title_text = title.get_text().strip() if title else "Unknown Workout"
        
        # Look for YouTube link
        youtube_link = None
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://youtu\.be/[\w-]+'
        ]
        
        page_text = str(soup)
        for pattern in youtube_patterns:
            match = re.search(pattern, page_text)
            if match:
                found_link = match.group(0)
                if 'youtube.com/goruck' not in found_link.lower():
                    youtube_link = found_link
                    break
        
        # Extract workout content
        content_div = soup.find('div', class_=['rte', 'blog-content', 'article-content'])
        if not content_div:
            content_div = soup.find('article')
        
        workout_details = []
        if content_div:
            paragraphs = content_div.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 10:
                    workout_details.append(text)
        
        # Try to extract date from content or URL
        date = extract_date(workout_details, workout_url)
        
        return {
            'title': title_text,
            'url': workout_url,
            'youtube_url': youtube_link,
            'details': workout_details,
            'date': date
        }
        
    except Exception as e:
        log.error(f"Error fetching workout details for {workout_url}: {e}")
        return None

def extract_date(details, url):
    """Extract date from workout details or URL."""
    # Try to find date in content first
    content = ' '.join(details).lower()
    
    # Look for date patterns in content
    month_names = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
        'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    # Pattern 1: "8.19.2025" format
    date_pattern1 = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
    match = re.search(date_pattern1, content)
    if match:
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"
    
    # Pattern 2: "august 19, 2025" or "aug 19, 2025" format
    for month_name, month_num in month_names.items():
        pattern = rf'{month_name}\s+(\d{{1,2}}),?\s+(\d{{4}})'
        match = re.search(pattern, content)
        if match:
            day = match.group(1).zfill(2)
            year = match.group(2)
            return f"{year}-{month_num}-{day}"
    
    # Pattern 3: Try to extract from URL like "aug25", "sep24"
    url_lower = url.lower()
    for month_abbr, month_num in month_names.items():
        if len(month_abbr) == 3:  # Only 3-letter abbreviations
            pattern = rf'{month_abbr}(\d{{2}})'
            match = re.search(pattern, url_lower)
            if match:
                year_suffix = match.group(1)
                full_year = f"20{year_suffix}"
                # Try to get day from content or default to 1st
                day = "01"
                # Look for day number near the month in content
                day_pattern = rf'{month_abbr}\w*\s*(\d{{1,2}})'
                day_match = re.search(day_pattern, content)
                if day_match:
                    day = day_match.group(1).zfill(2)
                return f"{full_year}-{month_num}-{day}"
    
    # Pattern 4: Look for YYYY-MM-DD format anywhere
    iso_pattern = r'(\d{4})-(\d{2})-(\d{2})'
    match = re.search(iso_pattern, content)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    
    # If no date found, return Unknown so we can identify these files
    return 'Unknown'

def sanitize_filename(s):
    """Sanitize string for use as a filename."""
    # Split filename and extension
    if s.endswith('.md'):
        name = s[:-3]
        ext = '.md'
    else:
        name = s
        ext = ''
    
    # Sanitize the name part only
    clean_name = ''.join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
    
    # Return with extension
    return clean_name + ext

def make_markdown(workout):
    """Generate markdown content for a workout dict."""
    # Extract fields
    title = workout.get('title', 'GORUCK WOD')
    date = workout.get('date', 'Unknown')
    url = workout.get('url', '')
    video = workout.get('youtube_url', '')
    details = workout.get('details', [])
    rx = ''  # Could try to extract from details if needed
    completed = False
    # Try to get a short title for filename
    short_title = title.split(':')[0].replace(' ', '-').upper()
    # YAML frontmatter
    frontmatter = f"""---
note subject: {title.replace('"','')}
creation date: {date}
type: goruck_wod
sort_title: {short_title}
post_date: {date}
post_url: {url}
post_video: {video}
rx: {rx}
completed: {str(completed).lower()}
aliases: [ \"{title.upper()}\" ]
---
"""
    # Workout notes (first paragraph or two)
    notes = ''
    if details:
        notes = '\n'.join(details[:2])
    # Video callout
    video_callout = ''
    if video:
        video_callout = f'> [!example]- Video Recap\n> <iframe width="360" height="600" src="{video}" frameborder="0" allowfullscreen></iframe>\n'
    # Workout section (try to find a list in details)
    workout_section = '\n'.join(details[2:]) if len(details) > 2 else ''
    # Compose markdown
    md = f"{frontmatter}\n> [!abstract]- Workout Notes\n> \n> {notes}\n\n{video_callout}\n## Workout\n{workout_section}\n"
    return md

def main():
    log.info("Fetching GORUCK workouts from pages 1-2...")
    
    # Get workouts from pages 1 and 2
    try:
        workouts = get_page1_workouts()  # Now gets both pages 1 and 2
    except Exception as e:
        log.error(f"Error fetching workout list: {e}")
        return
    
    log.info(f"Found {len(workouts)} workouts to process")
    
    processed = 0
    errors = 0
    
    for i, w in enumerate(workouts):
        try:
            log.info(f"Processing workout {i+1}/{len(workouts)}: {w.get('name', 'Unknown')}")
            
            # Add delay between requests to be nice to the server
            if i > 0:
                time.sleep(2)  # 2 second delay between requests
            
            details = get_workout_details(w['url'])
            if not details:
                log.warning(f"Could not fetch details for {w['url']}")
                errors += 1
                continue
            
            # Compose filename: YYYY-MM-DD_SHORT-TITLE.md
            title = details.get('title', 'GORUCK WOD')
            date = details.get('date', 'Unknown')
            short_title = title.split(':')[0].replace(' ', '-').upper()
            if date != 'Unknown':
                filename = f"{date}_{short_title}.md"
            else:
                filename = f"{short_title}.md"
            filename = sanitize_filename(filename)
            out_path = os.path.join(OUTPUT_DIR, filename)
            
            # Skip if file already exists
            if os.path.exists(out_path):
                log.info(f"File already exists, skipping: {filename}")
                continue
            
            # Write markdown
            md = make_markdown(details)
            with open(out_path, 'w') as f:
                f.write(md)
            log.info(f"Wrote {out_path}")
            processed += 1
            
        except Exception as e:
            log.error(f"Error processing workout {w.get('url', 'unknown')}: {e}")
            errors += 1
            continue
    
    log.info(f"Processing complete! Successfully processed: {processed}, Errors: {errors}")

if __name__ == "__main__":
    main()
