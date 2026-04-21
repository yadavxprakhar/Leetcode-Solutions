#!/usr/bin/env python3
"""
update_recent_activity.py
══════════════════════════════════════════════════════════════════
Scans the DSA-Solutions repo for the most recently added problems
from BOTH LeetCode (topics/ + root {num}-{slug}/) and GeeksForGeeks
(Difficulty: {level}/{Name}/) and rewrites the README Recent Activity
section.

Sort strategy (most reliable in CI):
  PRIMARY   → git commit timestamp of the problem folder
  FALLBACK  → file mtime (if git history unavailable)

README marker targeted:
  <!-- RECENT:START --> ... <!-- RECENT:END -->

Usage:
  python scripts/update_recent_activity.py          # normal run
  python scripts/update_recent_activity.py --dry-run # preview only
"""

import re
import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from urllib.parse import quote

# ══════════════════════════════════════════════════════════════════
# CONFIG  — edit these if your folder layout changes
# ══════════════════════════════════════════════════════════════════

REPO_ROOT    = Path(__file__).parent.parent
README_PATH  = REPO_ROOT / "README.md"
CACHE_FILE   = REPO_ROOT / "scripts" / "recent_cache.json"

RECENT_LIMIT = 12   # rows shown in the table
DRY_RUN      = "--dry-run" in sys.argv

# GitHub repo info — used for building absolute clickable URLs
GITHUB_REPO  = "yadavxprakhar/DSA-Solutions"
GITHUB_BASE  = f"https://github.com/{GITHUB_REPO}/tree/main"

# ── Regex patterns ──────────────────────────────────────────────
LC_FOLDER_RE  = re.compile(r'^(\d+)-([a-z0-9-]+)$')           # 812-rotate-string
GFG_DIFF_RE   = re.compile(r'^Difficulty:\s*(Basic|Easy|Medium|Hard)$', re.I)
README_MARKER = "RECENT"

# ── Difficulty display ───────────────────────────────────────────
DIFF_EMOJI = {
    "basic":  "🔵 Basic",
    "easy":   "🟢 Easy",
    "medium": "🟡 Medium",
    "hard":   "🔴 Hard",
}

# ── Platform display ─────────────────────────────────────────────
PLATFORM_TAG = {
    "leetcode": "🟠 LC",
    "gfg":      "🔵 GFG",
}

# ── Topic inference from slug keywords ──────────────────────────
TOPIC_KEYWORDS = {
    "linked-list":           ["linked", "list", "node", "cycle", "loop", "lru",
                              "flatten", "merge", "reverse-nodes"],
    "trees":                 ["tree", "bst", "binary", "inorder", "preorder",
                              "postorder", "height", "diameter", "lca", "trie",
                              "serialize", "zigzag"],
    "graphs":                ["graph", "bfs", "dfs", "island", "path", "connected",
                              "topological", "course", "clone", "walls", "pacific"],
    "dynamic-programming":   ["dp", "knapsack", "subsequence", "partition", "coin",
                              "jump", "climb", "rob", "edit-distance", "unique-paths",
                              "decode", "maximum-product"],
    "sliding-window":        ["window", "maximum-sliding", "permutation-in-string",
                              "minimum-window", "fruit-into-baskets"],
    "two-pointers":          ["two-sum", "three-sum", "four-sum", "container-with",
                              "trapping-rain", "remove-duplicates", "sort-colors"],
    "binary-search":         ["binary-search", "search-in-rotated", "find-minimum",
                              "peak-element", "median", "koko", "sqrt"],
    "stack-queue":           ["stack", "queue", "monotonic", "bracket", "parenthes",
                              "daily-temperatures", "next-greater", "valid-parentheses",
                              "implement-queue", "largest-rectangle"],
    "backtracking":          ["subset", "permutation", "combination", "n-queen",
                              "sudoku", "word-search", "palindrome-partitioning"],
    "heap":                  ["heap", "priority", "kth-largest", "kth-smallest",
                              "merge-k", "top-k", "find-k"],
    "greedy":                ["greedy", "activity", "job-schedule", "minimum-cost",
                              "assign-cookies", "jump-game", "gas-station"],
    "arrays":                ["array", "subarray", "rotate", "maximum-subarray",
                              "matrix", "spiral", "kadane", "product-except",
                              "majority-element", "missing-number", "move-zeroes"],
    "strings":               ["string", "palindrome", "anagram", "prefix", "suffix",
                              "character", "reverse-words", "longest-common",
                              "isomorphic", "atoi", "beauty", "roman"],
    "math":                  ["prime", "gcd", "lcm", "factorial", "fibonacci",
                              "power", "sqrt", "excel-sheet", "count-primes"],
}

def build_github_url(folder_path: Path) -> str:
    """
    Convert an absolute local folder path to a clickable GitHub tree URL.

    Strategy:
      1. Make the path relative to REPO_ROOT
      2. URL-encode EACH segment individually (preserves / separators)
      3. If a Solution.java or .java file exists inside, link to the
         file directly (blob URL); otherwise link to the folder (tree URL).

    Examples:
      REPO_ROOT/topics/strings/812-rotate-string/
        → https://github.com/yadavxprakhar/DSA-Solutions/tree/main/topics/strings/812-rotate-string

      REPO_ROOT/Difficulty: Medium/Find length of Loop/
        → https://github.com/yadavxprakhar/DSA-Solutions/tree/main/Difficulty%3A%20Medium/Find%20length%20of%20Loop
    """
    try:
        rel = folder_path.relative_to(REPO_ROOT)
    except ValueError:
        # path is already relative — make it absolute first
        rel = Path(str(folder_path).lstrip("./"))

    # Encode each path segment separately so slashes stay as literal /
    encoded_parts = [quote(part, safe="") for part in rel.parts]
    encoded_path  = "/".join(encoded_parts)

    # Prefer linking to the solution file if it exists
    link_type = "tree"
    if folder_path.exists():
        java_files = list(folder_path.glob("*.java"))
        if java_files:
            # Pick Solution.java first, else the first .java file found
            target = next((f for f in java_files if f.name == "Solution.java"), java_files[0])
            file_parts   = [quote(part, safe="") for part in target.relative_to(REPO_ROOT).parts]
            encoded_path = "/".join(file_parts)
            link_type    = "blob"

    return f"https://github.com/{GITHUB_REPO}/{link_type}/main/{encoded_path}"


def infer_topic(slug: str) -> str:
    s = slug.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in s for kw in keywords):
            return topic
    return "general"

# ══════════════════════════════════════════════════════════════════
# GIT TIMESTAMP  — most reliable sort key in CI
# ══════════════════════════════════════════════════════════════════

def git_commit_time(path: Path) -> float:
    """
    Returns the Unix timestamp of the most recent git commit that
    touched anything inside `path`. Falls back to file mtime.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(path)],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        ts = result.stdout.strip()
        if ts:
            return float(ts)
    except Exception:
        pass

    # Fallback: most recent mtime inside the folder
    mtimes = [f.stat().st_mtime for f in path.rglob("*") if f.is_file()]
    return max(mtimes) if mtimes else 0.0


def git_commit_date(path: Path) -> str:
    """Human-readable date string for display (YYYY-MM-DD)."""
    ts = git_commit_time(path)
    if ts:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    return "—"

# ══════════════════════════════════════════════════════════════════
# SCANNERS
# ══════════════════════════════════════════════════════════════════

def scan_leetcode() -> list[dict]:
    """
    Scans two locations for LC problems:
      1. topics/{topic}/{num}-{slug}/   (organized by you)
      2. {num}-{slug}/                  (raw LeetSync root dumps)
    De-duplicates by problem number — topics/ wins.
    """
    problems: dict[str, dict] = {}   # num → entry

    # ── Pass 1: topics/ (authoritative) ──────────────────────────
    topics_dir = REPO_ROOT / "topics"
    if topics_dir.exists():
        for topic_dir in sorted(topics_dir.iterdir()):
            if not topic_dir.is_dir():
                continue
            topic = topic_dir.name
            for prob_dir in topic_dir.iterdir():
                if not prob_dir.is_dir():
                    continue
                m = LC_FOLDER_RE.match(prob_dir.name)
                if not m:
                    continue
                num, slug = m.group(1), m.group(2)
                ts = git_commit_time(prob_dir)
                problems[num] = {
                    "platform":   "leetcode",
                    "num":        num,
                    "title":      slug.replace("-", " ").title(),
                    "difficulty": "unknown",   # filled by cache later
                    "topic":      topic,
                    "path":       build_github_url(prob_dir),
                    "ts":         ts,
                    "date":       datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else "—",
                    "_slug":      slug,
                    "_source":    "topics",
                }

    # ── Pass 2: root LeetSync dumps (only if not in topics/) ─────
    for item in REPO_ROOT.iterdir():
        if not item.is_dir():
            continue
        m = LC_FOLDER_RE.match(item.name)
        if not m:
            continue
        num, slug = m.group(1), m.group(2)
        if num in problems:
            continue   # already have it from topics/
        ts = git_commit_time(item)
        problems[num] = {
            "platform":   "leetcode",
            "num":        num,
            "title":      slug.replace("-", " ").title(),
            "difficulty": "unknown",
            "topic":      infer_topic(slug),
            "path":       build_github_url(item),
            "ts":         ts,
            "date":       datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else "—",
            "_slug":      slug,
            "_source":    "root",
        }

    return list(problems.values())


def scan_gfg() -> list[dict]:
    """
    Scans for GFG-to-GitHub extension folders:
      Difficulty: Basic/{Problem Name}/
      Difficulty: Easy/{Problem Name}/
      Difficulty: Medium/{Problem Name}/
      Difficulty: Hard/{Problem Name}/
    """
    problems = []
    seen     = set()

    for diff_dir in REPO_ROOT.iterdir():
        if not diff_dir.is_dir():
            continue
        m = GFG_DIFF_RE.match(diff_dir.name)
        if not m:
            continue
        difficulty = m.group(1).lower()   # basic / easy / medium / hard

        for prob_dir in diff_dir.iterdir():
            if not prob_dir.is_dir():
                continue
            name = prob_dir.name           # "Find length of Loop"
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            uid  = f"gfg-{difficulty}-{slug}"
            if uid in seen:
                continue
            seen.add(uid)

            ts = git_commit_time(prob_dir)
            problems.append({
                "platform":   "gfg",
                "num":        None,
                "title":      name,
                "difficulty": difficulty,
                "topic":      infer_topic(slug),
                "path":       build_github_url(prob_dir),
                "ts":         ts,
                "date":       datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else "—",
                "_slug":      slug,
            })

    return problems

# ══════════════════════════════════════════════════════════════════
# DIFFICULTY CACHE  (reads from problem_index.json if present)
# ══════════════════════════════════════════════════════════════════

def load_difficulty_cache() -> dict:
    """
    Load LC difficulties from problem_index.json (written by update_readme.py).
    Keys in that file are like  "lc-812-rotate-string" → {"difficulty": "easy", ...}
    """
    index_file = REPO_ROOT / "scripts" / "problem_index.json"
    if not index_file.exists():
        return {}
    try:
        with open(index_file) as f:
            raw = json.load(f)
        cache = {}
        for k, v in raw.items():
            if k.startswith("_"):
                continue
            # Strip "lc-" prefix → "812-rotate-string"
            plain_key = re.sub(r'^lc-', '', k)
            cache[plain_key] = v.get("difficulty", "unknown")
        return cache
    except Exception:
        return {}


def enrich_difficulties(problems: list[dict]) -> list[dict]:
    """
    Fills in LC difficulty from the cached index.
    GFG difficulty is already known from folder name.
    """
    cache = load_difficulty_cache()
    for p in problems:
        if p["platform"] == "leetcode" and p["difficulty"] == "unknown":
            slug_key = f"{p['num']}-{p['_slug']}"
            p["difficulty"] = cache.get(slug_key, "unknown")
    return problems

# ══════════════════════════════════════════════════════════════════
# TABLE GENERATOR
# ══════════════════════════════════════════════════════════════════

def make_recent_table(problems: list[dict]) -> str:
    """
    Builds the markdown table rows for RECENT:START section.
    Format:
      | # | Problem | Difficulty | Topic | Date | Solution |
    """
    rows = []
    for p in problems:
        num_cell   = p["num"] if p["num"] else "—"
        plat_tag   = PLATFORM_TAG.get(p["platform"], "")
        diff_label = DIFF_EMOJI.get(p["difficulty"], "⚪ Unknown")
        topic_disp = p["topic"].replace("-", " ").title()
        title_cell = f"{plat_tag} {p['title']}"
        date_cell  = p.get("date", "—")
        link       = p["path"]

        rows.append(
            f"| {num_cell} | {title_cell} | {diff_label} | {topic_disp} | {date_cell} | [View →]({link}) |"
        )

    header = (
        "| # | Problem | Difficulty | Topic | Date | Solution |\n"
        "|---|---------|------------|-------|------|----------|"
    )

    if not rows:
        return header + "\n| — | No problems yet | — | — | — | — |"

    return header + "\n" + "\n".join(rows)

# ══════════════════════════════════════════════════════════════════
# README PATCHER
# ══════════════════════════════════════════════════════════════════

def patch_readme(new_table: str) -> bool:
    """
    Replaces content between <!-- RECENT:START --> and <!-- RECENT:END -->.
    Returns True if the file was changed.
    """
    if not README_PATH.exists():
        print(f"❌  README not found at {README_PATH}")
        return False

    with open(README_PATH, "r", encoding="utf-8") as f:
        original = f.read()

    pattern     = r'(<!-- RECENT:START -->)(.*?)(<!-- RECENT:END -->)'
    replacement = rf'\1\n{new_table}\n\3'
    updated, n  = re.subn(pattern, replacement, original, flags=re.DOTALL)

    if n == 0:
        print("⚠️   <!-- RECENT:START --> marker not found in README.md")
        print("     Add this to your README where you want Recent Activity:")
        print("     <!-- RECENT:START -->")
        print("     <!-- RECENT:END -->")
        return False

    if updated == original:
        print("✅  Recent Activity is already up-to-date. No changes needed.")
        return False

    if DRY_RUN:
        print("🔍  DRY RUN — would write:")
        print(new_table)
        return False

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    return True

# ══════════════════════════════════════════════════════════════════
# CACHE  (skip re-scanning unchanged folders)
# ══════════════════════════════════════════════════════════════════

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(data: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save cache: {e}")

# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    print("═" * 60)
    print("  Recent Activity Updater  —  LeetCode + GFG")
    print("═" * 60)

    # 1. Scan both platforms
    print("\n📂  Scanning LeetCode problems...")
    lc_problems = scan_leetcode()
    print(f"    Found {len(lc_problems)} LC problems")

    print("📂  Scanning GFG problems...")
    gfg_problems = scan_gfg()
    print(f"    Found {len(gfg_problems)} GFG problems")

    # 2. Merge + enrich difficulties from cached index
    all_problems = lc_problems + gfg_problems
    all_problems = enrich_difficulties(all_problems)

    # 3. Sort by git commit timestamp (newest first)
    all_problems.sort(key=lambda p: p["ts"], reverse=True)

    # 4. Deduplicate by (platform, num/title)
    seen_keys = set()
    deduped   = []
    for p in all_problems:
        uid = f"{p['platform']}-{p['num'] or p['title']}"
        if uid in seen_keys:
            continue
        seen_keys.add(uid)
        deduped.append(p)

    # 5. Take top N
    recent = deduped[:RECENT_LIMIT]

    print(f"\n🔥  Top {len(recent)} recent problems:")
    for i, p in enumerate(recent, 1):
        plat = p["platform"].upper()
        diff = p["difficulty"]
        print(f"    {i:2}. [{plat}] {p['title']:<40} {diff:<8}  {p['date']}")

    # 6. Build table
    table = make_recent_table(recent)

    # 7. Patch README
    print(f"\n📝  Patching README.md...")
    changed = patch_readme(table)

    if changed:
        print(f"✅  README updated with {len(recent)} recent problems.")
        # Save cache for next run
        save_cache({
            "last_run": datetime.now(tz=timezone.utc).isoformat(),
            "count":    len(recent),
        })
    else:
        print("    No README changes committed.")

    print("═" * 60)


if __name__ == "__main__":
    main()
