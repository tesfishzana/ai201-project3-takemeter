"""
Fetch r/nba posts and comments from Reddit's public JSON API.
Collects from hot, top, rising, and controversial listings to get variety.
Also dips into comment sections of debate posts for more analysis examples.
"""
import requests
import json
import time
import csv
import re
import sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
BASE = "https://www.reddit.com/r/nba"


def clean(text):
    text = text.strip()
    # collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # drop lines that are just URLs
    text = re.sub(r"https?://\S+", "", text)
    text = text.strip()
    return text


def fetch_listing(url, limit=100):
    params = {"limit": limit, "raw_json": 1}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}", file=sys.stderr)
        return None


def posts_from_listing(data):
    results = []
    if not data:
        return results
    for child in data.get("data", {}).get("children", []):
        p = child.get("data", {})
        selftext = clean(p.get("selftext", ""))
        title = clean(p.get("title", ""))
        if p.get("is_self") and selftext and selftext != "[removed]" and selftext != "[deleted]":
            text = selftext
        else:
            text = title
        text = clean(text)
        if len(text) < 20:
            continue
        results.append({
            "id": p.get("id", ""),
            "text": text,
            "score": p.get("score", 0),
            "source": "post",
        })
    return results


def comments_from_post(post_id, limit=40):
    url = f"{BASE}/comments/{post_id}.json"
    time.sleep(1.5)
    try:
        r = requests.get(url, headers=HEADERS, params={"limit": limit, "depth": 1, "raw_json": 1}, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ERROR fetching comments for {post_id}: {e}", file=sys.stderr)
        return []

    results = []
    if len(data) < 2:
        return results
    for child in data[1].get("data", {}).get("children", []):
        c = child.get("data", {})
        body = clean(c.get("body", ""))
        if not body or body in ("[removed]", "[deleted]") or len(body) < 25:
            continue
        results.append({
            "id": c.get("id", ""),
            "text": body,
            "score": c.get("score", 0),
            "source": "comment",
        })
    return results


def main():
    all_examples = {}

    endpoints = [
        (f"{BASE}/hot.json",           "hot"),
        (f"{BASE}/top.json?t=week",    "top_week"),
        (f"{BASE}/top.json?t=month",   "top_month"),
        (f"{BASE}/controversial.json?t=week", "controversial"),
        (f"{BASE}/rising.json",        "rising"),
    ]

    post_ids_for_comments = []

    for url, name in endpoints:
        print(f"Fetching {name}...")
        data = fetch_listing(url, limit=100)
        posts = posts_from_listing(data)
        print(f"  Got {len(posts)} posts")
        for p in posts:
            if p["id"] not in all_examples:
                all_examples[p["id"]] = p
            if p["source"] == "post" and p["score"] > 50:
                post_ids_for_comments.append(p["id"])
        time.sleep(2)

    # Fetch comments from a sample of high-score posts (for more analysis/hot_take variety)
    comment_post_ids = list(dict.fromkeys(post_ids_for_comments))[:25]
    print(f"\nFetching comments from {len(comment_post_ids)} posts...")
    for pid in comment_post_ids:
        comments = comments_from_post(pid, limit=30)
        added = 0
        for c in comments:
            if c["id"] not in all_examples:
                all_examples[c["id"]] = c
                added += 1
        print(f"  Post {pid}: +{added} comments")
        time.sleep(1.5)

    examples = list(all_examples.values())
    print(f"\nTotal unique examples collected: {len(examples)}")

    # Write raw (unlabeled) CSV for annotation
    out_path = "data/raw_unlabeled.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "score", "source", "label", "notes", "ai_assisted"])
        writer.writeheader()
        for ex in examples:
            writer.writerow({
                "id": ex["id"],
                "text": ex["text"],
                "score": ex["score"],
                "source": ex["source"],
                "label": "",
                "notes": "",
                "ai_assisted": "",
            })

    print(f"Saved {len(examples)} examples to {out_path}")
    return examples


if __name__ == "__main__":
    main()
