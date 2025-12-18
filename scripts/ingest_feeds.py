#!/usr/bin/env python3
"""
Ingest RSS/Atom feeds, extract IPv4 addresses mentioned in entries, and
store them in data/feeds_ips.csv to be merged into the main database.
"""

import re
import csv
from pathlib import Path
from datetime import datetime

try:
    import feedparser
    import requests
except ImportError:
    feedparser = None
    requests = None

IPV4_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def is_valid_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except Exception:
        return False


def get_default_feeds():
    return [
        # Google security-related feeds
        "https://feeds.feedburner.com/GoogleOnlineSecurityBlog",  # Google Security Blog
        "https://cloud.google.com/blog/topics/security/rss.xml",  # Google Cloud Security
        # Additional reputable security blogs (often include indicators)
        "https://blog.google/threat-analysis-group/rss/",  # Google TAG
        "https://feeds.feedburner.com/KrebsOnSecurity",  # Krebs
        "https://blog.talosintelligence.com/feeds/posts/default",  # Cisco Talos
        "https://securelist.com/feed/",  # Kaspersky Securelist
        "https://www.bleepingcomputer.com/feed/",  # BleepingComputer
        "https://www.sans.org/newsletters/at-risk/rss/",  # SANS At-Risk
    ]


def load_feeds_list():
    cfg = Path("data/feeds.txt")
    if cfg.exists():
        lines = [l.strip() for l in cfg.read_text(encoding="utf-8").splitlines()]
        return [l for l in lines if l and not l.startswith("#")]
    return get_default_feeds()


def extract_ips_from_text(text: str):
    ips = set()
    for m in IPV4_REGEX.finditer(text or ""):
        ip = m.group(0)
        if is_valid_ipv4(ip):
            ips.add(ip)
    return ips


def ingest():
    if feedparser is None:
        print("feedparser not available; skipping RSS ingest")
        return 0

    feeds = load_feeds_list()
    seen_ips = set()
    rows = []
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            if getattr(feed, "bozo", 0):
                continue
            for entry in feed.entries:
                text = " ".join(
                    [
                        str(entry.get("title", "")),
                        str(entry.get("summary", "")),
                    ]
                )
                ips = extract_ips_from_text(text)
                for ip in ips:
                    if ip in seen_ips:
                        continue
                    seen_ips.add(ip)
                    rows.append([ip, 15, url, now])
        except Exception as e:
            print(f"Warning: failed to parse {url}: {e}")

    out = Path("data/feeds_ips.csv")
    out.parent.mkdir(exist_ok=True)
    header = ["ip", "score", "source", "first_seen"]
    if not out.exists():
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
    else:
        with open(out, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    print(f"RSS ingest complete: {len(rows)} new IPs from {len(feeds)} feeds")
    return len(rows)


def main():
    ingest()


if __name__ == "__main__":
    main()
