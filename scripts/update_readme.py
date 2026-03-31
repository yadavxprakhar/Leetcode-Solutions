#!/usr/bin/env python3
"""
update_readme.py
────────────────
Scans the topics/ directory, counts problems by difficulty and topic,
then rewrites the stats sections in README.md between special markers.

Markers used:
  <!-- STATS:START --> ... <!-- STATS:END -->
  <!-- TOPICS:START --> ... <!-- TOPICS:END -->
  <!-- RECENT:START --> ... <!-- RECENT:END -->
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ─── Config ───────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
TOPICS_DIR = REPO_ROOT / "topics"
README_PATH = REPO_ROOT / "README.md"
INDEX_FILE = REPO_ROOT / "scripts" / "problem_index.json"

DIFFICULTY_EMOJI = {
    "easy":   "🟢 Easy",
    "medium": "🟡 Medium",
    "hard":   "🔴 Hard",
}

TOPIC_ORDER = [
    "arrays", "strings", "linked-list", "trees", "graphs",
    "dynamic-programming", "sliding-window", "two-pointers",
    "binary-search", "stack-queue", "backtracking", "greedy",
    "heap", "math"
]

# ─── Scan Problems ────────────────────────────────────────────────────────────

def load_index():
    """Load the problem index JSON for difficulty metadata."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return json.load(f)
    return {}

def scan_problems(index: dict):
    """Walk topics/ dir and build stats."""
    stats = {
        "total": 0,
        "easy": 0,
        "medium": 0,
        "hard": 0,
        "by_topic": defaultdict(lambda: {"total": 0, "easy": 0, "medium": 0, "hard": 0}),
        "recent": [],
    }

    if not TOPICS_DIR.exists():
        print(f"⚠️  topics/ directory not found at {TOPICS_DIR}")
        return stats

    for topic_dir in sorted(TOPICS_DIR.iterdir()):
        if not topic_dir.is_dir():
            continue
        topic = topic_dir.name

        for problem_dir in sorted(topic_dir.iterdir(), reverse=True):
            if not problem_dir.is_dir():
                continue

            # Parse problem number from folder name e.g. "1-two-sum" → "1"
            match = re.match(r'^(\d+)-(.+)$', problem_dir.name)
            if not match:
                continue

            problem_num = match.group(1)
            problem_slug = match.group(2)
            problem_key = f"{problem_num}-{problem_slug}"

            # Get difficulty from index, default to "medium"
            difficulty = index.get(problem_key, {}).get("difficulty", "medium").lower()
            display_name = index.get(problem_key, {}).get("title", problem_slug.replace("-", " ").title())
            
            # Get last modified time for "recent" sort
            java_files = list(problem_dir.glob("*.java"))
            mtime = max(f.stat().st_mtime for f in java_files) if java_files else 0

            stats["total"] += 1
            stats[difficulty] += 1
            stats["by_topic"][topic]["total"] += 1
            stats["by_topic"][topic][difficulty] += 1

            stats["recent"].append({
                "num": problem_num,
                "title": display_name,
                "difficulty": difficulty,
                "topic": topic,
                "path": f"./topics/{topic}/{problem_dir.name}/",
                "mtime": mtime,
            })

    # Sort recent by modification time, take top 10
    stats["recent"].sort(key=lambda x: x["mtime"], reverse=True)
    stats["recent"] = stats["recent"][:10]

    return stats

# ─── Generate Markdown Sections ───────────────────────────────────────────────

def make_stats_table(stats):
    return f"""| Metric | Count |
|--------|-------|
| 🟢 Easy | {stats['easy']} |
| 🟡 Medium | {stats['medium']} |
| 🔴 Hard | {stats['hard']} |
| 📦 **Total Solved** | **{stats['total']}** |"""


def make_topics_table(stats):
    rows = []
    by_topic = stats["by_topic"]
    
    for topic in TOPIC_ORDER:
        if topic not in by_topic:
            continue
        t = by_topic[topic]
        name = topic.replace("-", " ").title()
        rows.append(f"| {name} | {t['total']} | {t['easy']} | {t['medium']} | {t['hard']} |")

    # Any topics not in TOPIC_ORDER
    for topic, t in by_topic.items():
        if topic not in TOPIC_ORDER:
            name = topic.replace("-", " ").title()
            rows.append(f"| {name} | {t['total']} | {t['easy']} | {t['medium']} | {t['hard']} |")

    header = "| Topic | Solved | Easy | Medium | Hard |\n|-------|--------|------|--------|------|"
    return header + "\n" + "\n".join(rows) if rows else header


def make_recent_table(stats):
    rows = []
    for p in stats["recent"]:
        diff_emoji = DIFFICULTY_EMOJI.get(p["difficulty"], "🟡 Medium")
        topic_display = p["topic"].replace("-", " ").title()
        rows.append(
            f"| {p['num']} | {p['title']} | {diff_emoji} | {topic_display} | [View →]({p['path']}) |"
        )

    header = "| # | Problem | Difficulty | Topic | Solution |\n|---|---------|------------|-------|---------|"
    return header + "\n" + "\n".join(rows) if rows else header + "\n| — | No problems yet | — | — | — |"

# ─── Patch README ─────────────────────────────────────────────────────────────

def patch_section(content: str, marker: str, new_body: str) -> str:
    """Replace content between <!-- MARKER:START --> and <!-- MARKER:END -->."""
    pattern = rf'(<!-- {marker}:START -->)(.*?)(<!-- {marker}:END -->)'
    replacement = rf'\g<1>\n{new_body}\n\g<3>'
    new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
    if count == 0:
        print(f"⚠️  Marker '{marker}' not found in README.md")
    return new_content

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("🔍 Scanning problems...")
    index = load_index()
    stats = scan_problems(index)

    print(f"📊 Found: {stats['total']} total | {stats['easy']} easy | {stats['medium']} medium | {stats['hard']} hard")

    print("📝 Reading README.md...")
    with open(README_PATH, "r") as f:
        content = f.read()

    content = patch_section(content, "STATS", make_stats_table(stats))
    content = patch_section(content, "TOPICS", make_topics_table(stats))
    content = patch_section(content, "RECENT", make_recent_table(stats))

    with open(README_PATH, "w") as f:
        f.write(content)

    print("✅ README.md updated successfully!")
    print(f"   Last run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
