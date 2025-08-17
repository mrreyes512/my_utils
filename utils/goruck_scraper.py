import logging
import pendulum
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup

# Get logger for this module
log = logging.getLogger(__name__)

def get_workout_list(days=7, max_pages=10):
    """
    Gets a list of recent workouts from GORUCK blog with automatic pagination.
    
    Args:
        days (int): Number of recent workouts to include (default: 7)
        max_pages (int): Maximum number of pages to check as safety limit (default: 10)
    
    Returns:
        list: List of workout dictionaries with basic info
    """
    try:
        log.info(f"Fetching recent GORUCK workouts (auto-pagination, max {max_pages} pages)")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        workouts = []
        seen_urls = set()
        
        # Check multiple pages automatically until we have enough workouts or no more pages
        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                workouts_url = "https://www.goruck.com/blogs/workouts"
            else:
                workouts_url = f"https://www.goruck.com/blogs/workouts?page={page_num}"
            
            log.info(f"Checking page {page_num}: {workouts_url}")
            
            response = requests.get(workouts_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Use the same logic as the working get_daily_workout function
            workout_links = soup.find_all('a', href=re.compile(r'/blogs/workouts/'))
            
            # Track if we found any new workouts on this page
            page_workouts_found = 0
            
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
                    
                    # Extract workout name from URL (simple approach)
                    url_parts = href.split('/')
                    if len(url_parts) > 0:
                        slug = url_parts[-1]
                        # Convert slug to title (e.g., "5k-ruck-aug25" -> "5K Ruck Aug25")
                        workout_name = slug.replace('-', ' ').title()
                    else:
                        workout_name = "Unknown Workout"
                    
                    workouts.append({
                        'date': 'Unknown',  # We'll set this to unknown for now
                        'formatted_date': 'Unknown',
                        'name': workout_name,
                        'url': workout_url,
                        'youtube_url': None
                    })
                    
                    page_workouts_found += 1
            
            log.info(f"Found {page_workouts_found} new workouts on page {page_num}")
            
            # Stop conditions:
            # 1. If we have enough workouts (with some buffer for filtering)
            # 2. If no new workouts found on this page
            if len(workouts) >= days * 2 or page_workouts_found == 0:
                if page_workouts_found == 0:
                    log.info(f"No new workouts found on page {page_num}, stopping pagination")
                else:
                    log.info(f"Found sufficient workouts ({len(workouts)}), stopping pagination")
                break
        
        log.info(f"Found {len(workouts)} total workout links across {page_num} pages")
        return workouts
        
    except requests.RequestException as e:
        log.error(f"Error fetching workout list: {e}")
        return []
    except Exception as e:
        log.error(f"Unexpected error in get_workout_list: {e}")
        return []

def get_daily_workout(date_str=None, max_pages=10):
    """
    Downloads the daily workout from GORUCK blog with pagination support.
    
    Args:
        date_str (str, optional): Date in YYYY-MM-DD format. If None, uses today's date.
        max_pages (int): Maximum number of pages to search (default: 10)
    
    Returns:
        dict: Dictionary containing workout details or None if not found
    """
    try:
        if date_str is None:
            date_str = pendulum.now().format('YYYY-MM-DD')
        
        log.info(f"Fetching GORUCK workout for date: {date_str}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Parse the target date
        target_date = pendulum.parse(date_str)
        formatted_date = target_date.format('MMMM D, YYYY')  # e.g., "August 14, 2025"
        
        # Search through multiple pages for the specific date
        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                workouts_url = "https://www.goruck.com/blogs/workouts"
            else:
                workouts_url = f"https://www.goruck.com/blogs/workouts?page={page_num}"
            
            log.info(f"Searching page {page_num} for workout on {date_str}")
            
            response = requests.get(workouts_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for workout links
            workout_links = soup.find_all('a', href=re.compile(r'/blogs/workouts/'))
            
            # Check each workout link for the target date
            for link in workout_links:
                href = link.get('href')
                if href and '/blogs/workouts/' in href and not href.endswith('/blogs/workouts'):
                    # Skip tag pages and other non-workout URLs
                    if '/tagged/' in href or '/pages/' in href or '?' in href:
                        continue
                    
                    # Build full URL
                    workout_url = href if href.startswith('http') else 'https://www.goruck.com' + href
                    
                    # Get the workout details to check the date
                    try:
                        workout_response = requests.get(workout_url, headers=headers)
                        workout_response.raise_for_status()
                        
                        workout_soup = BeautifulSoup(workout_response.content, 'html.parser')
                        
                        # Extract workout information
                        title = workout_soup.find('h1')
                        title_text = title.get_text().strip() if title else "Unknown Workout"
                        
                        # Extract workout content to get the date
                        workout_details = _extract_workout_content(workout_soup)
                        workout_data = {
                            'title': title_text,
                            'url': workout_url,
                            'details': workout_details,
                            'raw_content': '\n'.join(workout_details)
                        }
                        
                        # Extract date from this workout
                        extracted_date = _extract_date_from_workout(workout_data, workout_url)
                        
                        # Check if this is the workout we're looking for
                        if extracted_date == date_str:
                            log.info(f"Found workout for {date_str}: {title_text}")
                            
                            # Look for YouTube link
                            youtube_link = _extract_youtube_link(workout_soup)
                            
                            return {
                                'title': title_text,
                                'date': formatted_date,
                                'url': workout_url,
                                'youtube_url': youtube_link,
                                'details': workout_details,
                                'raw_content': '\n'.join(workout_details)
                            }
                            
                    except requests.RequestException as e:
                        log.warning(f"Error checking workout {workout_url}: {e}")
                        continue
            
            # If we've searched several pages without finding anything, break early
            if page_num >= 3 and page_num > max_pages // 2:
                log.info(f"Searched {page_num} pages without finding workout for {date_str}")
        
        # If we didn't find the specific date, try to find the most recent workout
        log.warning(f"Could not find workout for {date_str}, trying to get latest workout")
        
        # Get the first page again for latest workout
        response = requests.get("https://www.goruck.com/blogs/workouts", headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        workout_links = soup.find_all('a', href=re.compile(r'/blogs/workouts/'))
        
        return _get_latest_workout(workout_links)
        
    except requests.RequestException as e:
        log.error(f"Error fetching workout: {e}")
        return None
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        return None


def _extract_youtube_link(workout_soup):
    """
    Extracts YouTube link from workout page, prioritizing specific videos over general channel links.
    
    Args:
        workout_soup: BeautifulSoup object of the workout page
        
    Returns:
        str or None: YouTube URL if found, None otherwise
    """
    youtube_link = None
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',  # Prioritize embedded videos
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+'
    ]
    
    # Search for YouTube links in the entire page
    page_text = str(workout_soup)
    for pattern in youtube_patterns:
        match = re.search(pattern, page_text)
        if match:
            found_link = match.group(0)
            # Skip general channel links, prefer specific videos
            if 'youtube.com/goruck' not in found_link.lower():
                youtube_link = found_link
                break
    
    # Also check for YouTube links in anchor tags if no embed found
    if not youtube_link:
        youtube_anchors = workout_soup.find_all('a', href=re.compile(r'youtube\.com|youtu\.be'))
        for anchor in youtube_anchors:
            href = anchor.get('href')
            if href and 'youtube.com/goruck' not in href.lower():
                youtube_link = href
                break
    
    return youtube_link


def _extract_workout_content(workout_soup):
    """
    Extracts workout content from the page, avoiding duplicates and unwanted content.
    
    Args:
        workout_soup: BeautifulSoup object of the workout page
        
    Returns:
        list: List of workout detail strings
    """
    # Look for workout details in the content
    content_div = workout_soup.find('div', class_=['rte', 'blog-content', 'article-content'])
    if not content_div:
        content_div = workout_soup.find('article')
    
    workout_details = []
    seen_text = set()  # Track already seen text to avoid duplicates
    
    # Skip phrases that indicate non-workout content
    skip_phrases = ['share on', 'leave a comment', 'recent posts', 'facebook']
    
    if content_div:
        # First try to find direct paragraph elements
        paragraphs = content_div.find_all('p', recursive=False)
        if paragraphs:
            for p in paragraphs:
                text = p.get_text().strip()
                if (text and 
                    text not in seen_text and 
                    not any(skip in text.lower() for skip in skip_phrases)):
                    workout_details.append(text)
                    seen_text.add(text)
        else:
            # Fallback to div elements if no direct paragraphs
            for element in content_div.find_all(['div'], recursive=False):
                text = element.get_text().strip()
                if (text and 
                    text not in seen_text and 
                    len(text) > 5 and  # Avoid very short text snippets
                    not any(skip in text.lower() for skip in skip_phrases)):
                    workout_details.append(text)
                    seen_text.add(text)
    
    return workout_details


def _get_latest_workout(workout_links):
    """
    Gets the most recent workout when specific date is not found.
    
    Args:
        workout_links: List of workout links from the main page
        
    Returns:
        dict or None: Workout data dictionary or None if not found
    """
    # Get first workout link
    first_link = None
    for link in workout_links:
        href = link.get('href')
        if href and '/blogs/workouts/' in href and not href.endswith('/blogs/workouts'):
            first_link = href
            break
    
    if not first_link:
        return None
    
    if not first_link.startswith('http'):
        first_link = 'https://www.goruck.com' + first_link
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        workout_response = requests.get(first_link, headers=headers)
        workout_response.raise_for_status()
        
        workout_soup = BeautifulSoup(workout_response.content, 'html.parser')
        title = workout_soup.find('h1')
        title_text = title.get_text().strip() if title else "Latest Workout"
        
        # Extract YouTube link and content
        youtube_link = _extract_youtube_link(workout_soup)
        workout_details = _extract_workout_content(workout_soup)
        
        return {
            'title': title_text,
            'date': 'Latest Available',
            'url': first_link,
            'youtube_url': youtube_link,
            'details': workout_details,
            'raw_content': '\n'.join(workout_details)
        }
        
    except requests.RequestException as e:
        # log.error(f"Error fetching latest workout: {e}")
        return None


def create_workout_dataframe(days=7, include_youtube=False, short_format=False, max_pages=None):
    """
    Creates a pandas DataFrame with recent workout data, with automatic pagination.
    
    Args:
        days (int): Number of days to look back for workouts (default: 7)
        include_youtube (bool): Whether to fetch YouTube links (slower but more complete)
        short_format (bool): If True, creates simplified format without YouTube and with short blog links
        max_pages (int, optional): Maximum number of pages to check. If None, uses automatic detection.
    
    Returns:
        pandas.DataFrame: DataFrame with columns based on format
    """
    log.info("Creating workout DataFrame for recent workouts")
    
    # If max_pages not specified, use automatic pagination with a reasonable safety limit
    if max_pages is None:
        max_pages = 10  # Safety limit to prevent infinite loops
    
    # Get workout list with automatic pagination
    workout_list = get_workout_list(days, max_pages)
    
    workouts_data = []
    
    # Process each workout to get detailed information
    for workout in workout_list[:days]:  # Limit to requested number
        try:
            # Get detailed workout information
            detailed_workout = _get_workout_details(workout['url'])
            
            if detailed_workout:
                workout_name = detailed_workout.get('title', workout['name'])
                blog_url = workout['url']
                youtube_url = detailed_workout.get('youtube_url', '') if include_youtube else ''
                
                # Try to extract date from the workout content or URL
                workout_date = _extract_date_from_workout(detailed_workout, blog_url)
                
                # Extract slug from URL for short format
                if blog_url:
                    slug = blog_url.split('/')[-1] if '/' in blog_url else workout_name.lower().replace(' ', '-')
                else:
                    slug = workout_name.lower().replace(' ', '-').replace("'", "")
                
                workouts_data.append({
                    'date': workout_date,
                    'name': workout_name,
                    'blog_link': blog_url,
                    'short_blog_link': f'/{slug}',
                    'youtube_link': youtube_url
                })
                log.info(f"Added workout: {workout_name} ({workout_date})")
            else:
                log.warning(f"Could not get details for workout: {workout['url']}")
                
        except Exception as e:
            log.warning(f"Could not process workout {workout.get('url', 'unknown')}: {e}")
    
    log.info(f"Found {len(workouts_data)} workouts")
    
    # Create DataFrame based on format
    if short_format:
        # Short format: date, name only (no links)
        df_data = []
        for workout in workouts_data:
            df_data.append({
                'date': workout['date'],
                'name': workout['name']
            })
        df = pd.DataFrame(df_data)
        log.info(f"Created short format DataFrame with {len(df)} workouts")
    else:
        # Long format: date, name, blog_link (full), youtube_link
        df_data = []
        for workout in workouts_data:
            row = {
                'date': workout['date'],
                'name': workout['name'],
                'blog_link': workout['blog_link']
            }
            if include_youtube:
                row['youtube_link'] = workout['youtube_link']
            df_data.append(row)
        df = pd.DataFrame(df_data)
        log.info(f"Created long format DataFrame with {len(df)} workouts")
    
    return df


def _get_workout_details(workout_url):
    """
    Get detailed information about a specific workout.
    
    Args:
        workout_url (str): URL of the workout page
        
    Returns:
        dict or None: Workout details or None if failed
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(workout_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract workout information
        title = soup.find('h1')
        title_text = title.get_text().strip() if title else "Unknown Workout"
        
        # Look for YouTube link
        youtube_link = _extract_youtube_link(soup)
        
        # Look for workout details in the content
        workout_details = _extract_workout_content(soup)
        
        return {
            'title': title_text,
            'url': workout_url,
            'youtube_url': youtube_link,
            'details': workout_details,
            'raw_content': '\n'.join(workout_details)
        }
        
    except requests.RequestException as e:
        log.error(f"Error fetching workout details for {workout_url}: {e}")
        return None
    except Exception as e:
        log.error(f"Unexpected error getting workout details: {e}")
        return None


def _extract_date_from_workout(workout_data, workout_url):
    """
    Try to extract the date from workout data or URL.
    
    Args:
        workout_data (dict): Workout data dictionary
        workout_url (str): URL of the workout
        
    Returns:
        str: Date string in YYYY-MM-DD format or 'Unknown'
    """
    # First try to extract date from the workout content
    if workout_data and 'raw_content' in workout_data:
        content = workout_data['raw_content'].lower()
        
        # Look for date patterns in content like "august 14, 2025" or "aug 14, 2025"
        date_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # M.D.YYYY format like "8.12.2025"
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})'   # YYYY-MM-DD
        ]
        
        month_names = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
            'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    if '.' in pattern:  # M.D.YYYY pattern
                        month = groups[0].zfill(2)
                        day = groups[1].zfill(2)
                        year = groups[2]
                        return f"{year}-{month}-{day}"
                    elif groups[0] in month_names:  # Month name pattern
                        month = month_names[groups[0]]
                        day = groups[1].zfill(2)
                        year = groups[2]
                        return f"{year}-{month}-{day}"
                    elif '/' in pattern:  # MM/DD/YYYY pattern
                        month = groups[0].zfill(2)
                        day = groups[1].zfill(2)
                        year = groups[2]
                        return f"{year}-{month}-{day}"
                    elif '-' in pattern:  # YYYY-MM-DD pattern
                        return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
    
    # Try to extract date from URL patterns like "aug25", "sep24", etc.
    url_lower = workout_url.lower()
    
    # Common month abbreviations and their numbers
    months = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    # Look for patterns like "aug25", "sep24" in the URL
    for month_abbr, month_num in months.items():
        pattern = rf'{month_abbr}(\d{{2}})'
        match = re.search(pattern, url_lower)
        if match:
            year_suffix = match.group(1)
            # Assume 20XX for years
            full_year = f"20{year_suffix}"
            return f"{full_year}-{month_num}-01"  # Use first day of month as placeholder
    
    # Look for patterns like "2025-08-14" in the URL
    date_pattern = r'(\d{4})-(\d{2})-(\d{2})'
    match = re.search(date_pattern, url_lower)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    
    # If no date pattern found, return Unknown
    return 'Unknown'
