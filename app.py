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

def extract_front_matter(content: str) -> tuple:
    if content.startswith("---"):
        end_content_i = content.find('---', 3)
        if end_content_i != -1:
            return (0, end_content_i+3)
    return (0, 0)

def get_remember_rating_terminal():
    while True:
        print("how was that? [E]asy [G]ood [H]ard [I]gnore: ", end="", flush=True)
        key = keyboard.read_key()     # blocks until a key is pressed
        match key:
            case 'E' | 'e': return key, Rating.Easy
            case 'G' | 'g': return key, Rating.Good
            case 'H' | 'h': return key, Rating.Hard
            case 'I' | 'i': return key, None
            case _: 
                print(f"\n invalid input '{key}', please try again.")

def replace_slice(s: str, start: int, stop: int, new: str) -> str:
    return s[:start] + new + s[stop:]

def try_parse_float(s: str):
    try:
        return float(s)
    except: 
        return None

# main -------------------------

def job(root: Path):
    scheduler = Scheduler() #. Initialize the FSRS scheduler with default parameters

    for fpath_abs in args.root.rglob("*.md"): # for all markdown file
        fpath_rel = fpath_abs.relative_to(args.root)
        curr_content = fpath_abs.read_text(encoding="utf-8")
        
        if REMEMBER_TAG in curr_content: # check if the corresponding tag exists

            try: # capture and report if any error occurd while processing this file
                now = datetime.now(timezone.utc) # the `fsrs` package works with UTC
                start_i, end_i = extract_front_matter(curr_content)
                content_start_i, content_end_i = start_i+3, end_i-3
                frontmatter_exists= end_i != 0
                frontmatter = yaml.safe_load(curr_content[content_start_i:content_end_i] if frontmatter_exists else "") or {}
                old_data= frontmatter.get(STORE_KEY)
                old_card = Card.from_dict(old_data) if old_data else Card()
                
                if old_card.last_review  is None or now >= old_card.due:
                    late = now - old_card.due if old_card.due else 0

                    if late: print(f"\n[late: {late}]")
                    print(f">> {fpath_rel}")

                    label, rating = get_remember_rating_terminal()
                    print(label)
                    if rating is None: continue

                    new_card, review_log = scheduler.review_card(old_card, rating)

                    print(f"\nuntil next: {new_card.due - now}")
                    print("---------------------")

                    new_frontmatter = yaml.safe_dump({**frontmatter, STORE_KEY: new_card.to_dict()})
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
