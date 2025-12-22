#!/usr/bin/env python3
import sqlite3
import sys
from pathlib import Path
import json

try:
    import pandas as pd
except ImportError:
    pd = None


def show_stats():
    db_path = Path("data/badips.db")

    if not db_path.exists():
        print("ERROR: Database not found. Run process_badips.py first.")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\nBad IP Database Statistics")
    print("=" * 50)

    cursor.execute("SELECT COUNT(*) FROM bad_ips")
    total_ips = cursor.fetchone()[0]
    print(f"Total Malicious IPs: {total_ips:,}")

    cursor.execute(
        "SELECT COUNT(DISTINCT country) FROM ip_geolocation WHERE country IS NOT NULL"
    )
    countries = cursor.fetchone()[0]
    print(f"Countries Affected: {countries}")

    cursor.execute("SELECT AVG(severity) FROM bad_ips")
    avg_severity = cursor.fetchone()[0] or 0
    print(f"Average Severity: {avg_severity:.2f}/5")

    cursor.execute("SELECT COUNT(*) FROM ip_geolocation")
    geo_enriched = cursor.fetchone()[0]
    print(f"IPs with Geolocation: {geo_enriched:,}")

    print("\nTop 5 Countries:")
    print("-" * 50)
    cursor.execute(
        """
        SELECT country, COUNT(*) as count 
        FROM ip_geolocation 
        WHERE country IS NOT NULL
        GROUP BY country 
        ORDER BY count DESC 
        LIMIT 5
    """
    )
    for country, count in cursor.fetchall():
        print(f"  {country}: {count:,} IPs")

    print("\nThreat Severity Distribution:")
    print("-" * 50)
    cursor.execute(
        """
        SELECT severity, COUNT(*) as count
        FROM bad_ips
        GROUP BY severity
        ORDER BY severity
    """
    )
    for severity, count in cursor.fetchall():
        bar_str = "#" * (count // max(1, total_ips // 20))
        print(f"  Level {severity}: {count:,} IPs {bar_str}")

    conn.close()


def search_ip(ip_address):
    db_path = Path("data/badips.db")

    if not db_path.exists():
        print("ERROR: Database not found.")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT bi.ip_address, bi.severity, bi.threat_count, 
               bi.first_seen, bi.last_updated,
               ig.country, ig.city, ig.latitude, ig.longitude, ig.asn
        FROM bad_ips bi
        LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
        WHERE bi.ip_address = ?
    """,
        (ip_address,),
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"\nFound Malicious IP: {ip_address}")
        print("=" * 50)
        print(f"Threat Severity: {result[1]}/5")
        print(f"Detection Count: {result[2]}")
        print(f"First Seen: {result[3]}")
        print(f"Last Updated: {result[4]}")
        if result[5]:
            print(f"Country: {result[5]}")
        if result[6]:
            print(f"City: {result[6]}")
        if result[7] and result[8]:
            print(f"Coordinates: {result[7]:.4f}, {result[8]:.4f}")
        if result[9]:
            print(f"ASN: {result[9]}")
    else:
        print(f"IP {ip_address} not found in malicious database.")

    print()


def export_data(format_type="csv"):
    """Export database to CSV/ JSON"""
    db_path = Path("data/badips.db")

    if not db_path.exists():
        print("ERROR: Database not found.")
        return

    conn = sqlite3.connect(str(db_path))

    query = """
        SELECT bi.ip_address, bi.severity, bi.threat_count,
               bi.first_seen, bi.last_updated,
               ig.country, ig.city, ig.latitude, ig.longitude, ig.asn
        FROM bad_ips bi
        LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
        ORDER BY bi.threat_count DESC
    """

    if format_type.lower() == "csv":
        if pd is None:
            print("ERROR: pandas not installed. Install with: pip install pandas")
        else:
            df = pd.read_sql_query(query, conn)
            output_file = "bad_ips_export.csv"
            df.to_csv(output_file, index=False)
            print(f"Exported to {output_file}")

    elif format_type.lower() == "json":
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        output_file = "bad_ips_export.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Exported to {output_file}")

    conn.close()


def reset_database():
    db_path = Path("data/badips.db")

    if db_path.exists():
        confirm = input(f"WARNING: This will delete {db_path}. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            db_path.unlink()
            print("Database deleted.")
        else:
            print("Cancelled.")
    else:
        print("Database not found.")


def main():
    if len(sys.argv) < 2:
        print("Bad IP Database Utility")
        print("=" * 50)
        print("\nUsage:")
        print("  python utils.py stats              - Show database statistics")
        print("  python utils.py search <IP>        - Search for an IP address")
        print("  python utils.py export [csv|json]  - Export database")
        print("  python utils.py reset              - Reset database")
        return

    command = sys.argv[1].lower()

    if command == "stats":
        show_stats()
    elif command == "search":
        if len(sys.argv) < 3:
            print("Please provide an IP address to search.")
        else:
            search_ip(sys.argv[2])
    elif command == "export":
        format_type = sys.argv[2] if len(sys.argv) > 2 else "csv"
        export_data(format_type)
    elif command == "reset":
        reset_database()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
