# imports -------------------------
import keyboard
import yaml
from fsrs import Scheduler, Card, Rating, State

# from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from pathlib import Path
import argparse

# consts -------------------------

REMEMBER_TAG = "#remember"
STORE_KEY = 'remember'

# utils -------------------------

def get_default_timezone():
    # return datetime.now().astimezone().tzinfo
    return timezone.utc

def extract_front_matter(content: str) -> tuple:
    if content.startswith("---"):
        start_content_i = 3 
        end_content_i = content.find('---', start_content_i)
        if end_content_i != -1:
            return (0, start_content_i, end_content_i, end_content_i+3)
    return (0, 0, 0, 0)

def get_remember_rating_terminal():
    while True:
        print("how was that? [E]asy [G]ood [H]ard: ", end="", flush=True)
        key = keyboard.read_key()     # blocks until a key is pressed
        match key:
            case 'E' | 'e': return Rating.Easy
            case 'G' | 'g': return Rating.Good
            case 'H' | 'h': return Rating.Hard
            case _: 
                print(f"\n invalid input '{key}', please try again.")

def replace_slice(s: str, start: int, stop: int, new: str) -> str:
    return s[:start] + new + s[stop:]

def unix_from_datatime(dt: datetime) -> float:
    return int(dt.timestamp())

def unix_to_datetime(ts) -> datetime:
    if ts is None:
        return None
    else:
        return datetime.fromtimestamp(ts, tz=get_default_timezone())

# main -------------------------

def job(root: Path):
    scheduler = Scheduler() #. Initialize the FSRS scheduler with default parameters

    for fpath_abs in args.root.rglob("*.md"): # for all markdown file
        fpath_rel = fpath_abs.relative_to(args.root)
        curr_content = fpath_abs.read_text(encoding="utf-8")
        
        if REMEMBER_TAG in curr_content: # check if the corresponding tag exists

            try: # capture and report if any error occurd while processing this file
                tz = get_default_timezone()
                now = datetime.now(tz) # the `fsrs` package works with UTC
                start_i, content_start_i, content_end_i, end_i = extract_front_matter(curr_content)
                frontmatter_exists= end_i != 0
                frontmatter = yaml.safe_load(curr_content[content_start_i:content_end_i]) or {}
                old_data : dict= frontmatter.get(STORE_KEY, {})

                STATE_KEY = 'state'
                DUE_KEY = 'due'
                LAST_REVIEW_KEY = 'last_review'

                old_state= State(old_data.get(STATE_KEY, int(State.Learning)))
                old_due= unix_to_datetime(old_data.get(DUE_KEY))
                old_last_review= unix_to_datetime(old_data.get(LAST_REVIEW_KEY))

                if old_due is None or now >= old_due:
                    old_card = Card(
                        card_id= fpath_rel,
                        step= None,
                        stability= None,
                        difficulty = None,
                        due= old_due,
                        state = old_state,
                        last_review= old_last_review)

                    print("\n>>", fpath_rel)
                    rating = get_remember_rating_terminal()
                    new_card, review_log = scheduler.review_card(old_card, rating)
                    new_data = {
                        STATE_KEY: int(new_card.state),
                        DUE_KEY: unix_from_datatime(new_card.due),
                        LAST_REVIEW_KEY: unix_from_datatime(new_card.last_review),
                    }

                    print(f"\nuntil next: {new_card.due - now}")

                    new_frontmatter = yaml.safe_dump({**frontmatter, STORE_KEY: new_data})
                    replacement = f"---\n{new_frontmatter}---" + ("" if frontmatter_exists else "\n\n")
                    new_content = replace_slice(curr_content, start_i, end_i, replacement)
                    fpath_abs.write_text(new_content, encoding="utf-8")

                else:
                    pass
            except:
                print(f"error for {fpath_abs}")
                raise
        else: # ignore other notes
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Spaced Repetition System for your markdown files (.md) tagged with {REMEMBER_TAG}. stores information in front matter as '{STORE_KEY}' object")
    parser.add_argument("root", type=Path, help="Root directory to scan")
    args = parser.parse_args()

    job(args.root)
