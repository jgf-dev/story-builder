import os
import pathlib
import re

from bs4 import BeautifulSoup

from . import db
from .cache import safe_print
from .network import fetch_page


def _parse_html_story(response_text: str) -> tuple[str, str, str]:
	title = ""
	author = ""
	story_text = ""

	soup = BeautifulSoup(response_text, "html.parser")

	# Try to find title in title tag
	title_tag = soup.find("title")
	if title_tag:
		title = title_tag.get_text(strip=True)

	# Try to find author in h5 or similar tags (often <h5>By Author Name</h5>)
	for h_tag in soup.find_all(["h4", "h5", "h6"]):
		text = h_tag.get_text(strip=True)
		if text.lower().startswith("by ") or "by" in text.lower():
			author = text
			break

	# Extract paragraph text
	paragraphs = []
	body_tag = soup.find("body")
	target_container = body_tag or soup

	for p in target_container.find_all("p"):
		p_text = p.get_text(strip=True)
		if p_text:
			paragraphs.append(p_text)

	# If no paragraphs found, extract all text
	if not paragraphs:
		story_text = soup.get_text()
	else:
		story_text = "\n\n".join(paragraphs)

	return title, author, story_text


def _parse_text_story(raw_text: str):
	title = ""
	author = ""
	story_text = raw_text

	# Try to parse headers (Subject, From)
	subject_match = re.search(
		r"^Subject:\s*(.*)$",
		raw_text,
		re.IGNORECASE | re.MULTILINE,
	)
	if subject_match:
		title = subject_match.group(1).strip()

	from_match = re.search(r"^From:\s*(.*)$", raw_text, re.IGNORECASE | re.MULTILINE)
	if from_match:
		author = from_match.group(1).strip()

	return title, author, story_text


def _format_header(title, author, story_date, story_url) -> str:
	header = "=" * 80 + "\n"
	header += f"Title: {title or 'Unknown'}\n"
	header += f"Author: {author or 'Unknown'}\n"
	header += f"Publication Date: {story_date}\n"
	header += f"URL: {story_url}\n"
	header += "=" * 80 + "\n\n"
	return header


def save_story(story_url, output_path, story_date, delay) -> bool:
	"""
	Downloads the story from story_url and saves it to output_path.
	If the response is HTML, extracts plain text from body paragraphs.
	Prepends basic metadata (Title, Author, Date, URL) to the saved file.
	"""
	safe_print(f"Downloading story from {story_url}...")
	response = fetch_page(story_url, delay=delay)
	if not response:
		return False

	content_type = response.headers.get("Content-Type", "")

	if (
		"text/html" in content_type
		or response.text.strip().startswith("<!DOCTYPE")
		or response.text.strip().startswith("<html")
	):
		title, author, story_text = _parse_html_story(response.text)
	else:
		title, author, story_text = _parse_text_story(response.text)

	# Format metadata header
	header = _format_header(title, author, story_date, story_url)

	# Save to file ONLY if database is NOT enabled
	if db.get_conn() is None:
		pathlib.Path(os.path.dirname(output_path)).mkdir(exist_ok=True, parents=True)
		pathlib.Path(output_path).write_text(header + story_text, encoding="utf-8")
		safe_print(f"Saved story to {output_path}")

	# Insert into SQLite database
	if db.get_conn() is not None:
		db.insert_story(
			output_path=output_path,
			title=title or "Unknown",
			author=author or "Unknown",
			story_date=story_date,
			url=story_url,
			content=story_text,
		)

	return True


def _is_already_downloaded(idx_str, url, output_paths, story_date) -> bool:
	if db.get_conn() is not None:
		# Check if all paths exist in the database
		all_exist = True
		for path in output_paths:
			if not db.story_exists(path, story_date):
				all_exist = False
				break
		if all_exist:
			safe_print(f"[{idx_str}] Skipping target (already in database): {url}")
			return True
	else:
		# Check if all paths exist on disk
		all_exist = True
		for path in output_paths:
			if not pathlib.Path(path).exists():
				all_exist = False
				break
		if all_exist:
			safe_print(f"[{idx_str}] Skipping target (already exists on disk): {url}")
			return True
	return False


def _replicate_story(primary_path, output_paths, story_date) -> None:
	if len(output_paths) <= 1:
		return

	if db.get_conn() is None:
		import shutil

		for extra_path in output_paths[1:]:
			safe_print(f"Copying already downloaded story to: {extra_path}")
			pathlib.Path(os.path.dirname(extra_path)).mkdir(exist_ok=True, parents=True)
			try:
				shutil.copy2(primary_path, extra_path)
			except Exception as e:
				safe_print(
					f"Warning: Failed to copy {primary_path} to {extra_path}: {e}",
				)
	else:
		# Retrieve from database and insert for duplicates
		story_data = db.get_story(primary_path, story_date)
		if story_data:
			for extra_path in output_paths[1:]:
				db.insert_story(
					output_path=extra_path,
					title=story_data["title"],
					author=story_data["author"],
					story_date=story_data["story_date"],
					url=story_data["url"],
					content=story_data["content"],
				)


def download_single_target(idx_str, url, output_paths, story_date, delay, force: bool = False) -> bool:
<<<<<<< HEAD
	"""
	Downloads a single target story and handles duplicate copy replication.
	Returns True if successful, False otherwise.
	"""
	if not force and _is_already_downloaded(idx_str, url, output_paths, story_date):
		return True
=======
    """
    Downloads a single target story and handles duplicate copy replication.
    Returns True if successful, False otherwise.
    """
    if not force and _is_already_downloaded(idx_str, url, output_paths, story_date):
        return True
>>>>>>> origin/main

	safe_print(f"\n[{idx_str}] Downloading target...")
	primary_path = output_paths[0]
	success = save_story(url, primary_path, story_date, delay=delay)
	if success:
		# If the story appears in multiple subcategories, copy or insert them
		_replicate_story(primary_path, output_paths, story_date)
	return success
