#!/usr/bin/env python3
"""
update_readme.py
────────────────
Scans the topics/ directory, counts problems by difficulty and topic,
then rewrites the stats sections in README.md between special markers.

KEY FIX: Fetches real difficulty from LeetCode's GraphQL API for any
problem not already cached in problem_index.json. Auto-saves new
entries back to the index so each problem is only fetched once.

Markers used:
  <!-- STATS:START --> ... <!-- STATS:END -->
  <!-- TOPICS:START --> ... <!-- TOPICS:END -->
  <!-- RECENT:START --> ... <!-- RECENT:END -->
"""

import os
import re
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ─── Config ───────────────────────────────────────────────────────────────────

REPO_ROOT   = Path(__file__).parent.parent
TOPICS_DIR  = REPO_ROOT / "topics"
README_PATH = REPO_ROOT / "README.md"
INDEX_FILE  = REPO_ROOT / "scripts" / "problem_index.json"

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

# LeetCode GraphQL endpoint (public, no auth needed)
LEETCODE_API = "https://leetcode.com/graphql"

GRAPHQL_QUERY = """
query getProblem($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    title
    difficulty
    topicTags {
      slug
    }
  }
}
"""

# ─── LeetCode API ─────────────────────────────────────────────────────────────

def fetch_difficulty_from_leetcode(problem_slug: str) -> dict:
    """
    Calls LeetCode's GraphQL API to get real difficulty + title for a problem.
    Returns dict with 'title' and 'difficulty', or empty dict on failure.
    """
    try:
        response = requests.post(
            LEETCODE_API,
            json={"query": GRAPHQL_QUERY, "variables": {"titleSlug": problem_slug}},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://leetcode.com",
            },
            timeout=10,
        )
        if response.status_code != 200:
            print(f"   ⚠️  API returned {response.status_code} for '{problem_slug}'")
            return {}

        data = response.json()
        question = data.get("data", {}).get("question")

        if not question:
            print(f"   ⚠️  No data returned for '{problem_slug}'")
            return {}

        return {
            "title":      question["title"],
            "difficulty": question["difficulty"].lower(),  # "Easy" -> "easy"
        }

    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Network error fetching '{problem_slug}': {e}")
        return {}

# ─── Index Management ─────────────────────────────────────────────────────────

def load_index() -> dict:
    """Load the problem index JSON. Returns empty dict if not found."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            raw = json.load(f)
        # Strip comment keys that start with "_"
        return {k: v for k, v in raw.items() if not k.startswith("_")}
    return {}

def save_index(index: dict):
    """Save updated index back to disk."""
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)
    print(f"   💾 Saved {len(index)} entries to problem_index.json")

def get_problem_meta(index: dict, problem_key: str, problem_slug: str) -> dict:
    """
    Returns metadata for a problem. Priority order:
      1. Already in index with valid difficulty -> return cached (no API call)
      2. Not in index -> fetch from LeetCode API -> cache it -> return it
      3. API fails -> fallback to slug-derived title + 'medium'
    """
    if problem_key in index:
        entry = index[problem_key]
        if entry.get("difficulty") and entry["difficulty"] in ("easy", "medium", "hard"):
            return entry

    # Not cached or malformed — fetch from LeetCode
    print(f"   🌐 Fetching from LeetCode API: {problem_slug}")
    api_data = fetch_difficulty_from_leetcode(problem_slug)
    time.sleep(0.3)  # Be polite to LeetCode's servers

    if api_data:
        existing = index.get(problem_key, {})
        existing.update({
            "title":      api_data["title"],
            "difficulty": api_data["difficulty"],
        })
        index[problem_key] = existing
        print(f"   ✅ {api_data['title']} -> {api_data['difficulty'].upper()}")
        return existing

    # API failed — safe fallback
    print(f"   ❌ Could not fetch difficulty for '{problem_slug}', defaulting to medium")
    fallback = {
        "title":      problem_slug.replace("-", " ").title(),
        "difficulty": "medium",
    }
    index[problem_key] = fallback
    return fallback

# ─── Scan Problems ────────────────────────────────────────────────────────────

def scan_problems(index: dict) -> dict:
    """Walk topics/ dir, resolve difficulty via API if needed, build stats."""
    stats = {
        "total":    0,
        "easy":     0,
        "medium":   0,
        "hard":     0,
        "by_topic": defaultdict(lambda: {"total": 0, "easy": 0, "medium": 0, "hard": 0}),
        "recent":   [],
    }

    if not TOPICS_DIR.exists():
        print(f"⚠️  topics/ directory not found at {TOPICS_DIR}")
        return stats

    index_updated = False

    for topic_dir in sorted(TOPICS_DIR.iterdir()):
        if not topic_dir.is_dir():
            continue
        topic = topic_dir.name

        for problem_dir in sorted(topic_dir.iterdir(), reverse=True):
            if not problem_dir.is_dir():
                continue

            # Parse: "1-two-sum" -> num="1", slug="two-sum"
            match = re.match(r'^(\d+)-(.+)$', problem_dir.name)
            if not match:
                continue

            problem_num  = match.group(1)
            problem_slug = match.group(2)
            problem_key  = f"{problem_num}-{problem_slug}"

            # THE FIX: resolve from API if not already cached
            before_count = len(index)
            meta = get_problem_meta(index, problem_key, problem_slug)
            if len(index) != before_count:
                index_updated = True

            difficulty   = meta.get("difficulty", "medium")
            display_name = meta.get("title", problem_slug.replace("-", " ").title())

            java_files = list(problem_dir.glob("*.java"))
            mtime = max(f.stat().st_mtime for f in java_files) if java_files else 0

            stats["total"] += 1
            stats[difficulty] += 1
            stats["by_topic"][topic]["total"]    += 1
            stats["by_topic"][topic][difficulty] += 1

            stats["recent"].append({
                "num":        problem_num,
                "title":      display_name,
                "difficulty": difficulty,
                "topic":      topic,
                "path":       f"./topics/{topic}/{problem_dir.name}/",
                "mtime":      mtime,
            })

    if index_updated:
        save_index(index)

    stats["recent"].sort(key=lambda x: x["mtime"], reverse=True)
    stats["recent"] = stats["recent"][:10]

    return stats

# ─── Generate Markdown Sections ───────────────────────────────────────────────

def make_stats_table(stats: dict) -> str:
    return f"""| Metric | Count |
|--------|-------|
| 🟢 Easy | {stats['easy']} |
| 🟡 Medium | {stats['medium']} |
| 🔴 Hard | {stats['hard']} |
| 📦 **Total Solved** | **{stats['total']}** |"""


def make_topics_table(stats: dict) -> str:
    rows     = []
    by_topic = stats["by_topic"]

    for topic in TOPIC_ORDER:
        if topic not in by_topic:
            continue
        t    = by_topic[topic]
        name = topic.replace("-", " ").title()
        rows.append(f"| {name} | {t['total']} | {t['easy']} | {t['medium']} | {t['hard']} |")

    for topic, t in by_topic.items():
        if topic not in TOPIC_ORDER:
            name = topic.replace("-", " ").title()
            rows.append(f"| {name} | {t['total']} | {t['easy']} | {t['medium']} | {t['hard']} |")

    header = "| Topic | Solved | Easy | Medium | Hard |\n|-------|--------|------|--------|------|"
    return header + "\n" + "\n".join(rows) if rows else header


def make_recent_table(stats: dict) -> str:
    rows = []
    for p in stats["recent"]:
        diff_emoji    = DIFFICULTY_EMOJI.get(p["difficulty"], "🟡 Medium")
        topic_display = p["topic"].replace("-", " ").title()
        rows.append(
            f"| {p['num']} | {p['title']} | {diff_emoji} | {topic_display} | [View →]({p['path']}) |"
        )

    header = "| # | Problem | Difficulty | Topic | Solution |\n|---|---------|------------|-------|---------|"
    return header + "\n" + "\n".join(rows) if rows else header + "\n| — | No problems yet | — | — | — |"

# ─── Patch README ─────────────────────────────────────────────────────────────

def patch_section(content: str, marker: str, new_body: str) -> str:
    pattern     = rf'(<!-- {marker}:START -->)(.*?)(<!-- {marker}:END -->)'
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

    print(f"\n📊 Results: {stats['total']} total | {stats['easy']} easy | {stats['medium']} medium | {stats['hard']} hard")

    print("\n📝 Patching README.md...")
    with open(README_PATH, "r") as f:
        content = f.read()

    content = patch_section(content, "STATS",  make_stats_table(stats))
    content = patch_section(content, "TOPICS", make_topics_table(stats))
    content = patch_section(content, "RECENT", make_recent_table(stats))

    with open(README_PATH, "w") as f:
        f.write(content)

    print(f"✅ README.md updated successfully!")
    print(f"   Last run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
