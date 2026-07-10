import argparse
import concurrent.futures
import datetime
import glob
import sys
import time
from pathlib import Path

from storybuilder.downloader.storage import upload_many


# Add project root to sys.path to enable absolute imports when run directly as a script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from storybuilder.downloader import db
from storybuilder.downloader import network
from storybuilder.downloader.cache import load_cache
from storybuilder.downloader.cache import safe_print
from storybuilder.downloader.cache import save_cache
from storybuilder.downloader.scraper import get_subcategories
from storybuilder.downloader.scraper import process_subcategory
from storybuilder.downloader.writer import download_single_target


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download stories from Nifty Archive based on date range and category.",
    )
    parser.add_argument(
        "--category",
        required=True,
        choices=["gay", "lesbian", "bisexual", "transgender", "bestiality"],
        help="High-level category to download stories from.",
    )
    parser.add_argument(
        "--start-date",
        default="1990-01-01",
        help="Start date of publication range (YYYY-MM-DD). Defaults to 1990-01-01.",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="End date of publication range (YYYY-MM-DD). Defaults to today's date.",
    )
    parser.add_argument(
        "--output-dir",
        default="stories/text",
        help="Directory to save downloaded stories. Defaults to 'nifty_stories'.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Delay in seconds between HTTP requests (default 1.0) to avoid overloading the server.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full scan of all pages in a subcategory, bypassing early-stop optimization.",
    )
    parser.add_argument(
        "--socks5-proxy",
        default="192.168.2.10:37459",
        help="SOCKS5 proxy server to route requests through (e.g. 127.0.0.1:1080).",
    )
    parser.add_argument(
        "--rotate-on-refusal",
        action="store_true",
        default=True,
        help="Enable IP rotation using windscribe-cli if requests are refused or fail.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum number of parallel download workers (default 1).",
    )
    parser.add_argument(
        "--max-scraping",
        type=int,
        default=5,
        help="Maximum number of parallel scraping workers (default 4).",
    )
    parser.add_argument(
        "--db",
        default="stories/db",
        help="SQLite database path or directory. Stories are inserted into partitioned databases under this path as they download. Set to empty string to disable.",
    )
    return parser.parse_args()


def _setup_network(args: argparse.Namespace) -> bool:
    if args.socks5_proxy:
        try:
            import socks  # noqa: F401
        except ImportError:
            print("Error: SOCKS proxy support requires the 'pysocks' package.")
            print("Please install it in your environment using:")
            print("  pip install pysocks")
            print("Or run this script using the project virtual environment:")
            print("  .venv/bin/python download_nifty_stories.py ...")
            return False

        proxy_url = args.socks5_proxy
        if not proxy_url.startswith("socks5"):
            proxy_url = f"socks5h://{proxy_url}"
        network.PROXIES = {"http": proxy_url, "https": proxy_url}
    if args.rotate_on_refusal:
        network.ENABLE_ROTATION = True
    return True


def _parse_dates(
    start_date_str: str, end_date_str: str | None,
) -> tuple[datetime.date | None, datetime.date | None]:
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"Error: Invalid start date format '{start_date_str}'. Use YYYY-MM-DD.")
        return None, None

    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid end date format '{end_date_str}'. Use YYYY-MM-DD.")
            return None, None
    else:
        end_date = datetime.date.today()

    return start_date, end_date


def _print_config(
    args: argparse.Namespace, start_date: datetime.date, end_date: datetime.date,
) -> None:
    print("Starting downloader...")
    if args.db:
        print(f"Database: {args.db}")
        db.init_db(args.db)
    print(f"Category: {args.category}")
    print(f"Publication date range: {start_date} to {end_date}")
    print(f"Output directory: {args.output_dir}")
    print(f"Inter-request delay: {args.delay} seconds")
    if args.socks5_proxy:
        print(f"SOCKS5 proxy: {args.socks5_proxy}")
    if args.rotate_on_refusal:
        print("Windscribe IP rotation on refusal/failure is ENABLED.")
    print(f"Parallel download workers: {args.max_workers}")
    print(f"Parallel scraping workers: {args.max_scraping}")
    if args.force:
        print("Chronological early-stop optimization is DISABLED.")


def _scrape_subcategories(
    subcategories: list[str],
    start_date: datetime.date,
    end_date: datetime.date,
    args: argparse.Namespace,
) -> dict[str, dict]:
    all_story_targets: dict[str, dict] = {}
    if args.max_scraping > 1:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.max_scraping,
        ) as executor:
            futures = [
                executor.submit(process_subcategory, sub, start_date, end_date, args)
                for sub in subcategories
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    sub_targets = future.result()
                    for target in sub_targets:
                        key = target["key"]
                        if key not in all_story_targets:
                            all_story_targets[key] = {
                                "url": target["url"],
                                "output_paths": [],
                                "date": target["date"],
                            }
                        all_story_targets[key]["output_paths"].append(
                            target["output_path"],
                        )
                except Exception as e:
                    safe_print(f"Error occurred in scraping worker thread: {e}")
    else:
        for sub in subcategories:
            sub_targets = process_subcategory(sub, start_date, end_date, args)
            for target in sub_targets:
                key = target["key"]
                if key not in all_story_targets:
                    all_story_targets[key] = {
                        "url": target["url"],
                        "output_paths": [],
                        "date": target["date"],
                    }
                all_story_targets[key]["output_paths"].append(target["output_path"])
    return all_story_targets


def _download_stories(
    all_story_targets: dict[str, dict], args: argparse.Namespace,
) -> int:
    total_downloads = len(all_story_targets)
    print("\n" + "=" * 50)
    print(f"Total unique stories/chapters to download: {total_downloads}")
    print("=" * 50)

    successful_downloads = 0

    if args.max_workers > 1:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.max_workers,
        ) as executor:
            futures = []
            for idx, (key, target) in enumerate(all_story_targets.items()):
                idx_str = f"{idx + 1}/{total_downloads}"
                future = executor.submit(
                    download_single_target,
                    idx_str,
                    target["url"],
                    target["output_paths"],
                    target["date"],
                    args.delay,
                    force=args.force,
                )
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    success = future.result()
                    if success:
                        successful_downloads += 1
                except Exception as e:
                    print(f"Error occurred in download worker thread: {e}")
    else:
        for idx, (key, target) in enumerate(all_story_targets.items()):
            idx_str = f"{idx + 1}/{total_downloads}"
            success = download_single_target(
                idx_str,
                target["url"],
                target["output_paths"],
                target["date"],
                args.delay,
                force=args.force,
            )
            if success:
                successful_downloads += 1
            time.sleep(args.delay)

    print("\n" + "=" * 50)
    print("Download completed successfully.")
    print(f"Successfully downloaded: {successful_downloads}/{total_downloads}")
    print("=" * 50)

    return successful_downloads


def _upload_to_gcs(db_path_str: str) -> None:
    db_path = Path(db_path_str)
    if db_path.is_dir():
        db_files = glob.glob(str(db_path / "*.db"))
        source_dir = str(db_path)
    else:
        db_files = [str(db_path)]
        source_dir = str(db_path.parent)

    print("Uploading to GCS...")
    upload_many("nifty-index", db_files, source_directory=source_dir)


def main():
    args = _parse_args()

    if not _setup_network(args):
        return

    start_date, end_date = _parse_dates(args.start_date, args.end_date)
    if start_date is None or end_date is None:
        return

    _print_config(args, start_date, end_date)

    subcategories = get_subcategories(args.category.lower(), args.delay)
    if not subcategories:
        print("No subcategories found. Exiting.")
        return

    load_cache(args.output_dir)

    try:
        all_story_targets = _scrape_subcategories(
            subcategories, start_date, end_date, args,
        )
    finally:
        save_cache(args.output_dir)

    _download_stories(all_story_targets, args)

    if args.db:
        db.optimize_fts()
        db.close_db()
        print(f"Stories saved to database: {args.db}")
        _upload_to_gcs(args.db)


if __name__ == "__main__":
    main()
