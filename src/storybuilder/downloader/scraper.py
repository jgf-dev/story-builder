import datetime
import os
import re
import threading
import time
import urllib.parse
from datetime import date

from bs4 import BeautifulSoup

from .cache import cache_lock, metadata_cache, safe_print
from .date_parser import parse_nifty_date
from .network import BASE_URL, fetch_page

# Thread synchronization structures for folder processing
seen_folders = set()
seen_folders_lock = threading.Lock()


def _extract_subcategories_from_html(soup: BeautifulSoup, url: str):
    subcategories = []

    # Nifty pages have lists of subcategories under list-group-item class
    items = soup.find_all("li", class_="list-group-item")
    for item in items:
        a_tag = item.find("a")
        if a_tag and "href" in a_tag.attrs:
            href = str(a_tag["href"])
            sub_url = urllib.parse.urljoin(url, href)
            sub_name = a_tag.get_text(strip=True)
            subcategories.append({"name": sub_name, "url": sub_url})

    # Fallback: if no list-group-item found, look for table links or paragraph links
    if not subcategories:
        safe_print("No list-group-item elements found. Searching all links...")
        for a_tag in soup.find_all("a"):
            href = str(a_tag.get("href") or "")
            if href and not href.startswith("http") and not href.startswith("/") and href.endswith("/"):
                sub_url = urllib.parse.urljoin(url, href)
                sub_name = a_tag.get_text(strip=True) or href.rstrip("/")
                subcategories.append({"name": sub_name, "url": sub_url})

    return subcategories


def _filter_subcategories(subcategories, category):
    # Filter out external links or parent directories
    filtered = []
    seen_urls = set()
    category_path = f"/nifty/{category}/"
    for sub in subcategories:
        parsed_sub = urllib.parse.urlparse(sub["url"])
        if category_path in parsed_sub.path and parsed_sub.path != category_path:
            # Normalize path
            norm_path = parsed_sub.path
            if not norm_path.endswith("/"):
                norm_path += "/"
            normalized_url = parsed_sub._replace(path=norm_path).geturl()

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                filtered.append({"name": sub["name"], "url": normalized_url})

    return filtered


def get_subcategories(category, delay):
    """
    Scrapes the category index page to find all subcategory folders.
    Returns a list of dicts: [{'name': 'Adult Friends', 'url': 'https://nifty.org/nifty/gay/adult-friends/'}]
    """
    url = urllib.parse.urljoin(BASE_URL, f"{category}/")
    safe_print(f"Fetching subcategories from {url}...")
    response = fetch_page(url, delay)
    if not response:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    subcategories = _extract_subcategories_from_html(soup, url)
    filtered = _filter_subcategories(subcategories, category)

    safe_print(f"Found {len(filtered)} subcategories for category '{category}'")
    for sub in filtered:
        safe_print(f"  - {sub['name']}: {sub['url']}")
    return filtered


def parse_listing_rows(soup: BeautifulSoup):
    """
    Parses listing rows from Nifty index pages.
    Handles both new 'div.ftr' style rows and old 'tr' style table rows.
    Returns a list of dicts: [{'size': '13K', 'date_str': 'Jun 6 08:55', 'name': 'title', 'href': 'url'}]
    """
    rows = []

    # 1. Handle div.ftr rows
    ftr_divs = soup.find_all("div", class_="ftr")
    for row in ftr_divs:
        cols = row.find_all("div", recursive=False)
        if len(cols) >= 3:
            size = cols[0].get_text(strip=True)
            date_str = cols[1].get_text(strip=True)
            a_tag = cols[2].find("a")
            if a_tag and "href" in a_tag.attrs:
                href = str(a_tag["href"])
                name = a_tag.get_text(strip=True)
                rows.append({"size": size, "date_str": date_str, "name": name, "href": href})

    # 2. Handle tr table rows (skip header row with th)
    tr_elements = soup.find_all("tr")
    for row in tr_elements:
        if row.find("th"):
            continue  # Skip header
        cols = row.find_all("td")
        if len(cols) >= 3:
            size = cols[0].get_text(strip=True)
            date_str = cols[1].get_text(strip=True)
            a_tag = cols[2].find("a")
            if a_tag and "href" in a_tag.attrs:
                href = str(a_tag["href"])
                name = a_tag.get_text(strip=True)
                rows.append({"size": size, "date_str": date_str, "name": name, "href": href})

    return rows


def _get_cached_subcategory(sub_url):
    cached_entry = None
    with cache_lock:
        cached_entry = metadata_cache.get(sub_url)

    cached_stories = []
    is_complete = False
    if cached_entry and isinstance(cached_entry, dict):
        cached_stories = cached_entry.get("stories", [])
        is_complete = cached_entry.get("complete", False)

    return cached_stories, is_complete


def _scrape_subcategory_pages(sub_url, start_date, delay, force_scan, use_cache, cached_lookup):

    scraped_stories = []
    current_url = sub_url
    page_num = 1
    reached_end = False

    while current_url:
        safe_print(f"Scanning subcategory page {page_num}: {current_url}")
        response = fetch_page(current_url, delay=delay)
        if not response:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        rows = parse_listing_rows(soup)

        if not rows:
            safe_print(f"No story listings found on page {page_num}")
            break

        stop_pagination = False

        for row in rows:
            size = row["size"]
            date_str = row["date_str"]
            name = row["name"]
            href = row["href"]

            # Skip parent directory link
            if name == "Parent Directory" or href == "../":
                continue

            story_date = parse_nifty_date(date_str)
            if not story_date:
                continue

            story_url = urllib.parse.urljoin(current_url, href)
            is_directory = size == "Dir" or href.endswith("/")

            # Check if this story is already in our cache (with the same URL and date)
            if use_cache and story_url in cached_lookup:
                cached_s = cached_lookup[story_url]
                if cached_s.get("date") == story_date.isoformat():
                    safe_print(f"Cache hit at story: {name} ({story_url}). Stopping scraper traversal.")
                    stop_pagination = True
                    break

            scraped_stories.append(
                {
                    "name": name,
                    "url": story_url,
                    "date": story_date.isoformat(),
                    "is_dir": is_directory,
                    "size": size,
                },
            )

            # Early-stop optimization: if the story date is older than start_date,
            # and it is NOT a directory (as directories can have stale index dates),
            # and we are NOT in force_scan, we can stop traversing pages.
            if not force_scan and not is_directory and story_date < start_date:
                safe_print(
                    f"Reached story with date {story_date} which is older than start_date {start_date}. Stopping traversal.",
                )
                stop_pagination = True
                break

        if stop_pagination:
            break

        # Find next page link (jscroll pagination link)
        next_tag = soup.find("a", class_="jscroll-next")
        if next_tag and "href" in next_tag.attrs:
            next_href = next_tag["href"]
            current_url = urllib.parse.urljoin(current_url, next_href)
            page_num += 1
            time.sleep(delay)
        else:
            current_url = None  # No more pages
            reached_end = True

    return scraped_stories, reached_end


def _merge_and_save_stories(sub_url, scraped_stories, cached_stories, is_complete, reached_end: bool):
    # Merge scraped stories with cached stories
    scraped_urls = {s["url"] for s in scraped_stories}
    remaining_cached = [s for s in cached_stories if s["url"] not in scraped_urls]
    merged_stories = scraped_stories + remaining_cached

    # Sort merged stories by date descending (latest first)
    def get_sort_key(s) -> date:
        try:
            return datetime.datetime.strptime(s["date"], "%Y-%m-%d").date()
        except Exception:
            return datetime.date.min

    merged_stories.sort(key=get_sort_key, reverse=True)

    # Save merged stories back to the cache dictionary
    with cache_lock:
        metadata_cache[sub_url] = {
            "last_updated": datetime.datetime.now().isoformat(),
            "complete": is_complete or reached_end,
            "stories": merged_stories,
        }

    return merged_stories


def _filter_stories_by_date(merged_stories, start_date, end_date):
    # Now filter and return only the stories that match the current date query!
    filtered_stories = []
    for s in merged_stories:
        try:
            s_date = datetime.date.fromisoformat(s["date"])
        except Exception as e:
            safe_print(f"Warning: Failed to parse date '{s.get('date')}' for story '{s.get('name')}': {e}")
            continue

        # Always process directories because their index listing date can be stale
        # or out of range even if they contain chapters in our range.
        in_range = True if s["is_dir"] else start_date <= s_date <= end_date

        if in_range:
            filtered_stories.append(
                {
                    "name": s["name"],
                    "url": s["url"],
                    "date": s_date,
                    "is_dir": s["is_dir"],
                },
            )

    return filtered_stories


def scrape_subcategory(sub_url, start_date, end_date, delay, force_scan=False):
    """
    Crawls a subcategory directory, handling pagination.
    Uses the local metadata cache to avoid crawling previously scraped pages.
    Returns all stories/directories in this subcategory that fall in the date range.
    """
    cached_stories, is_complete = _get_cached_subcategory(sub_url)

    # We only use cache-hit early-stop if we are not forcing a scan and the cache is marked complete.
    # This ensures that we do not stop traversing on a cache hit when the cache has gaps or is partial.
    use_cache = not force_scan and is_complete

    # Create a quick lookup for cached stories by URL
    cached_lookup = {s["url"]: s for s in cached_stories}

    scraped_stories, reached_end = _scrape_subcategory_pages(
        sub_url,
        start_date,
        delay,
        force_scan,
        use_cache,
        cached_lookup,
    )

    merged_stories = _merge_and_save_stories(sub_url, scraped_stories, cached_stories, is_complete, reached_end)

    return _filter_stories_by_date(merged_stories, start_date, end_date)


def _get_cached_chapters(folder_url, folder_date, start_date, end_date):
    """
    Checks the cache for a multi-chapter folder and returns the chapters if valid.
    Returns (chapters, has_matching) if cached, else (None, False).
    """
    cached_entry = None
    with cache_lock:
        cached_entry = metadata_cache.get(folder_url)

    if not (cached_entry and isinstance(cached_entry, dict)):
        return None, False

    cached_folder_date = cached_entry.get("folder_date")
    if cached_folder_date != folder_date.isoformat():
        return None, False

    safe_print(f"Cache hit for multi-chapter folder: {folder_url} (date: {cached_folder_date}). Using cached chapters.")
    cached_chapters = cached_entry.get("chapters", [])
    chapters = []
    has_matching_chapter = False

    for ch in cached_chapters:
        try:
            ch_date = datetime.datetime.strptime(ch["date"], "%Y-%m-%d").date()
        except Exception:
            continue
        chapters.append({"name": ch["name"], "url": ch["url"], "date": ch_date, "is_dir": False})
        if start_date <= ch_date <= end_date:
            has_matching_chapter = True

    return chapters, has_matching_chapter


def _fetch_and_parse_chapters(folder_url, start_date, end_date, delay):
    """
    Fetches and parses chapters from a multi-chapter folder URL.
    Returns (chapters, scraped_chapters, has_matching_chapter).
    """
    safe_print(f"Scraping multi-chapter folder: {folder_url}")
    response = fetch_page(folder_url, delay=delay)
    if not response:
        return [], [], False

    soup = BeautifulSoup(response.text, "html.parser")
    rows = parse_listing_rows(soup)
    scraped_chapters = []
    chapters = []
    has_matching_chapter = False

    for row in rows:
        size = row["size"]
        date_str = row["date_str"]
        name = row["name"]
        href = row["href"]

        if name == "Parent Directory" or href == "../" or size == "Dir" or href.endswith("/"):
            continue

        chapter_date = parse_nifty_date(date_str)
        if not chapter_date:
            continue

        chapter_url = urllib.parse.urljoin(folder_url, href)

        scraped_chapters.append({"name": name, "url": chapter_url, "date": chapter_date.isoformat()})
        chapters.append({"name": name, "url": chapter_url, "date": chapter_date, "is_dir": False})

        if start_date <= chapter_date <= end_date:
            has_matching_chapter = True

    return chapters, scraped_chapters, has_matching_chapter


def scrape_multi_chapter_folder(folder_url, folder_date, start_date, end_date, delay, force_scan=False):
    """
    Crawls a multi-chapter folder (represented by a 'Dir' entry).
    Uses caching based on folder_date to avoid fetching unless the folder changed.
    If at least one chapter falls within the date range [start_date, end_date],
    returns all chapters from this folder. Otherwise, returns an empty list.
    """
    if not force_scan:
        chapters, has_matching = _get_cached_chapters(folder_url, folder_date, start_date, end_date)
        if chapters is not None:
            if has_matching:
                safe_print(
                    f"Folder {folder_url} (cached) has at least one chapter in date range. Downloading all {len(chapters)} chapters.",
                )
                return chapters
            safe_print(f"Folder {folder_url} (cached) has no chapters in date range. Skipping all.")
            return []

    # If cache miss or outdated, fetch the page
    chapters, scraped_chapters, has_matching = _fetch_and_parse_chapters(folder_url, start_date, end_date, delay)

    if not chapters and not scraped_chapters:
        # Still save to cache so we don't re-fetch empty folders
        with cache_lock:
            metadata_cache[folder_url] = {
                "last_updated": datetime.datetime.now().isoformat(),
                "folder_date": folder_date.isoformat(),
                "chapters": scraped_chapters,
            }
        return []

    # Save to cache
    with cache_lock:
        metadata_cache[folder_url] = {
            "last_updated": datetime.datetime.now().isoformat(),
            "folder_date": folder_date.isoformat(),
            "chapters": scraped_chapters,
        }

    if has_matching:
        safe_print(
            f"Folder {folder_url} has at least one chapter in date range. Downloading all {len(chapters)} chapters.",
        )
        return chapters
    safe_print(f"Folder {folder_url} has no chapters in date range. Skipping all.")
    return []


def _process_directory_story(s, start_date, end_date, args, sub_folder):
    folder_url = s["url"]

    # Thread-safe check of seen_folders
    should_skip = False
    with seen_folders_lock:
        if folder_url in seen_folders:
            should_skip = True
        else:
            seen_folders.add(folder_url)

    if should_skip:
        safe_print(f"Skipping already scraped folder: {folder_url}")
        return []

    # Fetch multi-chapter story chapters
    chapters = scrape_multi_chapter_folder(
        folder_url,
        s["date"],
        start_date,
        end_date,
        delay=args.delay,
        force_scan=args.force,
    )

    targets = []
    for ch in chapters:
        story_slug = s["name"].lower().replace(" ", "-")
        story_slug = re.sub(r"[^\w\-]", "", story_slug)

        filename = ch["name"]
        if not filename.endswith(".txt") and not filename.endswith(".html"):
            filename += ".txt"

        output_path = os.path.join(args.output_dir, args.category, sub_folder, story_slug, filename)
        targets.append(
            {
                "key": (story_slug, filename),
                "url": ch["url"],
                "output_path": output_path,
                "date": ch["date"],
            },
        )
    return targets


def _process_single_story(s, args, sub_folder):
    filename = s["name"]
    if not filename.endswith(".txt") and not filename.endswith(".html"):
        filename += ".txt"

    output_path = os.path.join(args.output_dir, args.category, sub_folder, filename)
    return [
        {
            "key": (None, filename),
            "url": s["url"],
            "output_path": output_path,
            "date": s["date"],
        },
    ]


def process_subcategory(sub, start_date, end_date, args):
    """
    Crawls a single subcategory and all its multi-chapter folders,
    collecting metadata to prepare story targets for downloading.
    """
    sub_name = sub["name"]
    sub_url = sub["url"]
    safe_print("\n" + "=" * 50)
    safe_print(f"Crawling subcategory: {sub_name}")
    safe_print("=" * 50)

    stories = scrape_subcategory(sub_url, start_date, end_date, force_scan=args.force, delay=args.delay)
    safe_print(f"Found {len(stories)} stories in {sub_name} matching date criteria.")

    parsed_sub = urllib.parse.urlparse(sub_url)
    sub_folder = parsed_sub.path.rstrip("/").split("/")[-1]

    sub_targets = []

    for s in stories:
        if s["is_dir"]:
            sub_targets.extend(_process_directory_story(s, start_date, end_date, args, sub_folder))
        else:
            sub_targets.extend(_process_single_story(s, args, sub_folder))

    return sub_targets
