#!/usr/bin/env python3
"""
Fetch several public IP blocklists, extract IPv4 addresses, compare to
`badip_list.csv`, and write results to `data/fetched_ips.csv` and
`data/new_ips.csv`.
"""

import re
import csv
import ipaddress
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


SOURCES = [
    (
        "stamparm_ipsum",
        "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
    ),
    ("spamhaus_drop", "https://www.spamhaus.org/drop/drop.txt"),
    (
        "emerging_block_ips",
        "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt",
    ),
    (
        "ransomwaretracker_rw_ipbl",
        "https://ransomwaretracker.abuse.ch/downloads/RW_IPBL.txt",
    ),
    ("zeus_abusech", "https://zeustracker.abuse.ch/blocklist.php?download=ipblocklist"),
    (
        "hackernews_security",
        "https://hnrss.org/security?format=json",
    ),
]

IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def fetch_url(url: str, timeout: int = 20):
    """Fetch text content from `url` using `requests`.

    Raises RuntimeError if `requests` is not installed.
    Returns empty string on error.
    """
    if requests is None:
        raise RuntimeError("requests is required; run: pip install requests")
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text
    except requests.exceptions.RequestException as exc:  # network/HTTP errors
        print(f"Warning: failed to fetch {url}: {exc}")
        return ""


def extract_ips(text: str):
    """Return a set of valid IPv4 addresses found in `text`."""
    ips = set()
    for m in IPV4_RE.finditer(text or ""):
        ip = m.group(0)
        try:
            # ipaddress raises ValueError for invalid addresses
            ipaddress.ip_address(ip)
            ips.add(ip)
        except ValueError:
            continue
    return ips


def load_badip_csv(path: Path):
    """Load existing `badip_list.csv` (or similar) and return a set of IPs."""
    result = set()
    if not path.exists():
        return result
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # CSV may be ip or ip,score
                ip = line.split(",")[0].strip()
                try:
                    ipaddress.ip_address(ip)
                    result.add(ip)
                except ValueError:
                    continue
    except OSError as exc:  # unexpected I/O error
        print(f"Warning: failed to read {path}: {exc}")
    return result


def main():
    """Fetch configured blocklists, write per-source CSVs and summary files."""
    # pylint: disable=too-many-locals
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)

    badip_path = Path("badip_list.csv")
    badips = load_badip_csv(badip_path)
    print(f"Loaded {len(badips)} existing entries from {badip_path}")

    fetched = {}

    for name, url in SOURCES:
        print(f"Fetching {name} from {url}...")
        txt = fetch_url(url)
        ips = extract_ips(txt)
        print(f"  -> found {len(ips)} IPv4 candidates")
        # write per-source csv for records
        src_path = out_dir / f"{name}.csv"
        with src_path.open("w", newline="", encoding="utf-8") as sf:
            sw = csv.writer(sf)
            sw.writerow(["ip", "collected_at", "source"])
            for ip in sorted(ips):
                sw.writerow([ip, datetime.utcnow().isoformat() + "Z", name])
        for ip in ips:
            fetched.setdefault(ip, set()).add(name)

    all_fetched = set(fetched.keys())
    print(f"Total unique fetched IPs: {len(all_fetched)}")

    # Compare to existing
    new_ips = sorted(all_fetched - badips)
    common = sorted(all_fetched & badips)
    missing = sorted(badips - all_fetched)

    now = datetime.utcnow().isoformat() + "Z"

    fetched_path = out_dir / "fetched_ips.csv"
    new_path = out_dir / "new_ips.csv"

    # Write fetched (ip, sources)
    with fetched_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ip", "sources", "collected_at"])
        for ip in sorted(all_fetched):
            w.writerow([ip, ";".join(sorted(fetched.get(ip, []))), now])

    # Write new ips (not present in badip_list.csv)
    with new_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ip", "sources", "collected_at"])
        for ip in new_ips:
            w.writerow([ip, ";".join(sorted(fetched.get(ip, []))), now])

    print("")
    print(f"Wrote {fetched_path} and {new_path}")
    print(f"New IPs (not in badip_list.csv): {len(new_ips)}")
    print(f"IPs present in both fetched and badip_list.csv: {len(common)}")
    print(f"badip_list.csv entries not found in these sources: {len(missing)}")

    # Fetch-only mode: do not append to master CSV or write to the DB here.
    # The pipeline's `process_badips.py` will merge `data/new_ips.csv` and
    # other `data/*.csv` sources into `badip_list.csv` and update the DB.
    if new_ips:
        print(
            "Found "
            + str(len(new_ips))
            + " new IPs (not in badip_list.csv); leaving merge to process_badips.py"
        )
    else:
        print("No new IPs detected; nothing to merge")


if __name__ == "__main__":
    main()
