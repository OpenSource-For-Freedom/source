#!/usr/bin/env python3
"""Update README `## Database Statistics` block from data/stats.json."""
import json
import re
from pathlib import Path
from datetime import datetime


def load_stats(path="data/stats.json"):
    """Load statistics JSON from `path` and return parsed dict or None."""
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def format_time(iso_str):
    """Convert ISO timestamp to human-readable UTC string when possible."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, TypeError):
        return iso_str


def build_block(stats):
    """Build the markdown stats block from a `stats` dict as a table."""
    update_time = format_time(
        stats.get("update_time") or stats.get("update_time_iso") or ""
    )
    total = stats.get("total_ips", 0)
    countries = stats.get("countries_affected") or stats.get("countries") or 0
    severity = stats.get("severity_avg") or stats.get("average_severity") or 0.0

    # Render as a compact Markdown table
    block = (
        "## Database Statistics\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Total Malicious IPs | {int(total):,} |\n"
        f"| Countries Affected | {int(countries)} |\n"
        f"| Average Threat Severity | {float(severity):.2f}/5 |\n"
        f"| Last Updated | {update_time} |\n\n"
    )
    # Optional: Top Countries table (from stats['top_countries'])
    top_countries = stats.get("top_countries") or []
    if top_countries:
        block += (
            "## Top Countries\n\n"
            "| Country | IPs |\n"
            "|---|---|\n"
        )
        for entry in top_countries[:10]:
            try:
                c = str(entry.get("country", "Unknown"))
                cnt = int(entry.get("count", 0))
            except Exception:
                c, cnt = str(entry), 0
            block += f"| {c} | {cnt} |\n"
        block += "\n"
    return block


def load_wall_of_shame(db_path="data/badips.db", limit=20):
    """Load top offenders for Wall of Shame from SQLite database.
    Returns list of dicts: {ip, domain, severity, threats}
    """
    p = Path(db_path)
    if not p.exists():
        return []
    import sqlite3

    try:
        conn = sqlite3.connect(str(p))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bi.ip_address,
                   COALESCE(ig.asn, ig.isp, 'N/A') AS domain,
                   bi.severity,
                   bi.threat_count
            FROM bad_ips bi
            LEFT JOIN ip_geolocation ig ON ig.ip_address = bi.ip_address
            ORDER BY bi.severity DESC, bi.threat_count DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        rows = cursor.fetchall()
        conn.close()
        results = [
            {
                "ip": str(r[0] or ""),
                "domain": str(r[1] or "N/A"),
                "severity": int(r[2] or 0),
                "threats": int(r[3] or 0),
            }
            for r in rows
        ]
        return results
    except Exception:
        return []


def build_wall_block(items):
    """Render Wall of Shame section as a Markdown table."""
    header = (
        "## Wall of Shame\n"
        "| IP | Domain/Host | Severity | Threats |\n"
        "|---|---|---|---|\n"
    )
    rows = [
        f"| {i['ip']} | {i['domain']} | {i['severity']}/5 | {i['threats']} |"
        for i in items
    ]
    return header + "\n".join(rows) + "\n\n"


def load_resolved_domains(path="data/resolved_domains.csv"):
    """Load IP -> hostname mappings produced by workflow dig step."""
    p = Path(path)
    if not p.exists():
        return {}
    import csv
    mapping = {}
    try:
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                ip = (row[0] or "").strip()
                dom = (row[1] or "N/A").strip()
                # Skip noisy dig errors or empty
                if dom.startswith(";;") or "communications error" in dom.lower():
                    dom = "N/A"
                if ip:
                    mapping[ip] = dom or "N/A"
    except Exception:
        return {}
    return mapping


def replace_block(readme_path="README.md", stats_path="data/stats.json"):
    """Replace the `## Database Statistics` block and update Last Generated timestamp in `README.md`."""
    stats = load_stats(stats_path)
    if not stats:
        print("No stats available; skipping README update")
        return 1

    readme = Path(readme_path)
    content = readme.read_text(encoding="utf-8")
    pattern = re.compile(r"## Database Statistics.*?\n---", re.S)
    new_block = build_block(stats) + "---"

    if not pattern.search(content):
        content = new_block + "\n\n" + content
    else:
        content = pattern.sub(new_block, content, count=1)

    # Also update the "Last Generated" timestamp at the bottom
    update_time = format_time(stats.get("update_time") or "")
    timestamp_pattern = re.compile(r"(\*\*Last Generated\*\*:) [^\n]+")
    if timestamp_pattern.search(content):
        content = timestamp_pattern.sub(rf"\1 {update_time}", content)
    else:
        # If pattern doesn't exist, add it at the end before closing div
        content = re.sub(
            r"(Data Sources.*?)\n</div>",
            rf"\1 | **Last Generated**: {update_time}\n</div>",
            content,
            flags=re.S,
        )

    # Update Wall of Shame with live table
    wall_items = load_wall_of_shame()
    # Apply hostname overrides if available
    resolved_map = load_resolved_domains()
    if wall_items and resolved_map:
        for i in wall_items:
            ip = i.get("ip")
            host = resolved_map.get(ip)
            if ip and host and host != "N/A" and not host.startswith(";;") and "communications error" not in host.lower():
                i["domain"] = host
    if wall_items:
        wall_block = build_wall_block(wall_items)
        wall_pat = re.compile(r"## Wall of Shame.*?(?=\n# Overview|\n## Overview|\Z)", re.S)
        if wall_pat.search(content):
            content = wall_pat.sub(wall_block, content, count=1)
        else:
            # If section doesn't exist, append before Overview
            content = re.sub(
                r"(\n# Overview|\n## Overview)",
                "\n" + wall_block + r"\1",
                content,
                count=1,
            )

    readme.write_text(content, encoding="utf-8")
    print("README Database Statistics updated")
    return 0


def ensure_cyber_origins_section(readme_path="README.md"):
    """Ensure the Cyber Attack Origins chart is present in README."""
    readme = Path(readme_path)
    content = readme.read_text(encoding="utf-8")

    section = (
        "## Cyber Attack Origins\n\n"
        "![Cyber Attack Origins](data/charts/attack_origins.png)\n\n"
    )

    pattern = re.compile(r"## Cyber Attack Origins.*?(?=\n## |\n# |\Z)", re.S)
    if pattern.search(content):
        content = pattern.sub(section, content, count=1)
    else:
        if "## Wall of Shame" in content:
            content = content.replace("## Wall of Shame", section + "## Wall of Shame", 1)
        elif "# Overview" in content or "## Overview" in content:
            content = re.sub(r"(\n# Overview|\n## Overview)", "\n" + section + r"\1", content, count=1)
        else:
            content += "\n" + section

    readme.write_text(content, encoding="utf-8")
    print("README Cyber Attack Origins section updated")


if __name__ == "__main__":
    rc = replace_block()
    ensure_cyber_origins_section()
    raise SystemExit(rc)
