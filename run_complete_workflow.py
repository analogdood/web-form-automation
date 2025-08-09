#!/usr/bin/env python3
"""
CLI runner for the Complete Toto Automation workflow (focused version)

Usage examples:
  - Run with CSV and auto round from filename (fallback to latest):
      pwsh> python run_complete_workflow.py --csv sample_data.csv --auto-round

  - Run with explicit round:
      pwsh> python run_complete_workflow.py --csv path\to\bets.csv --round 1558

  - Headless mode:
      pwsh> python run_complete_workflow.py --csv sample_data.csv --auto-round --headless

  - Headless + 最後に可視ブラウザで表示:
      pwsh> python run_complete_workflow.py --csv sample_data.csv --auto-round --headless --show-end

  - ログイン情報の指定（自動ログイン）:
      pwsh> python run_complete_workflow.py --csv sample_data.csv --auto-round --username 00000931526 --password goodguyg
"""

from __future__ import annotations
import argparse
import logging
import re
from pathlib import Path
import sys
import time

from complete_toto_automation import CompleteTotoAutomation


def extract_round_from_filename(csv_path: str) -> str | None:
    name = Path(csv_path).stem
    m = re.search(r"(\d{4,5})", name)
    return m.group(1) if m else None


def configure_logging(verbose: bool = False) -> None:
    ts = time.strftime("%Y%m%d_%H%M%S")
    log_file = Path("logs") / f"complete_workflow_{ts}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Complete Toto Automation workflow (focused runner)",
    )
    parser.add_argument("--csv", required=True, help="Path to CSV file with betting data")
    parser.add_argument("--round", dest="round_number", help="Round number to select (e.g., 1558)")
    parser.add_argument("--auto-round", action="store_true", help="Try to extract round from CSV filename (fallback to latest)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--timeout", type=int, default=15, help="Driver timeout seconds (default: 15)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--show-end", action="store_true", help="After finish, open the final page in a visible browser (restores session)")
    parser.add_argument("--username", help="Username for site login (optional)")
    parser.add_argument("--password", help="Password for site login (optional)")

    args = parser.parse_args(argv)

    configure_logging(verbose=args.verbose)

    csv_path = args.csv
    if not Path(csv_path).exists():
        print(f"CSV not found: {csv_path}")
        return 1

    round_number: str | None = args.round_number
    if args.auto_round and not round_number:
        rn = extract_round_from_filename(csv_path)
        if rn:
            logging.info(f"CSV filename suggests round: 第{rn}回 (auto)")
            round_number = rn
        else:
            logging.info("No round digits found in filename. Will use latest automatically.")

    logging.info("Starting Complete Toto Automation (focused runner)...")
    automation = CompleteTotoAutomation(
        headless=args.headless,
        timeout=args.timeout,
        keep_browser_open=not args.show_end,  # if we plan to show-end, we'll spin up a new visible window
        show_end=args.show_end,
        username=args.username,
        password=args.password,
    )
    ok = automation.execute_complete_workflow(csv_path, round_number)

    if ok:
        logging.info("Workflow finished successfully.")
        return 0
    else:
        logging.error("Workflow failed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
