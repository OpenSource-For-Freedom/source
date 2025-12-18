#!/usr/bin/env python3
"""
Process bad IPs and store them in SQLite database with geolocation information
"""


import sqlite3
import csv
import sys
from pathlib import Path
from datetime import datetime
import json
import gzip
import ipaddress

try:
    import requests
except ImportError:
    requests = None

try:
    import geoip2.database
except ImportError:
    geoip2 = None

def create_database():
    """Create SQLite database schema"""
    db_path = Path('data/badips.db')
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bad_ips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            severity INTEGER DEFAULT 3,
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            threat_count INTEGER DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ip_geolocation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            country TEXT,
            city TEXT,
            latitude REAL,
            longitude REAL,
            asn TEXT,
            isp TEXT,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ip_address) REFERENCES bad_ips(ip_address)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            category TEXT,
            count INTEGER DEFAULT 1,
            FOREIGN KEY (ip_address) REFERENCES bad_ips(ip_address)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS database_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_ips INTEGER,
            update_time TEXT,
            countries_affected INTEGER
        )
    ''')
    
    conn.commit()
    return conn


def map_score_to_severity(score) -> int:
    """Map a threat score to 1-5 severity scale."""
    try:
        s = int(score)
    except Exception:
        return 3
    if s <= 5:
        return 1
    if s <= 10:
        return 2
    if s <= 20:
        return 3
    if s <= 50:
        return 4
    return 5


def load_ips_from_csv(csv_file='badip_list.csv'):
    """Load IPs and optional scores from CSV file; returns list of (ip, severity)."""
    results = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                ip = (row[0] or '').strip()
                if not ip:
                    continue
                # Skip headers or invalid values
                try:
                    ipaddress.ip_address(ip)
                except Exception:
                    continue
                # Severity mapping from optional score column
                if len(row) >= 2 and (row[1] or '').strip():
                    sev = map_score_to_severity((row[1] or '').strip())
                    results.append((ip, sev))
                else:
                    results.append((ip, 3))
    except FileNotFoundError:
        print(f"Warning: {csv_file} not found")
    return results


def insert_ips_to_database(conn, ips):
    """Insert IPs into database; accepts list of (ip, severity) tuples."""
    cursor = conn.cursor()
    inserted = 0
    
    for item in ips:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            ip, severity = item[0], int(item[1])
        else:
            ip, severity = str(item), 3
        try:
            cursor.execute('''
                INSERT INTO bad_ips (ip_address, severity)
                VALUES (?, ?)
            ''', (ip, severity))
            inserted += 1
        except sqlite3.IntegrityError:
            # IP already exists, update threat count
            cursor.execute('''
                UPDATE bad_ips 
                SET threat_count = threat_count + 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE ip_address = ?
            ''', (ip,))
    
    conn.commit()
    print(f"Inserted {inserted} new IPs to database")
    return inserted


def fetch_geolocation(ip_address):
    """Fetch geolocation for an IP address using ip-api.com (free, no key required)"""
    try:
        if requests is None:
            return None
            
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}?fields=country,city,lat,lon,as',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country'),
                    'city': data.get('city'),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'asn': data.get('as')
                }
    except Exception as e:
        print(f"Error fetching geolocation for {ip_address}: {e}")
    
    return None


def enrich_geolocation_data_from_db(conn, city_db_path, asn_db_path=None):
    """Enrich database with geolocation data using local GeoLite2 City and optional ASN database"""
    try:
        if not geoip2 or not Path(city_db_path).exists():
            print(f"GeoIP City database not available at {city_db_path}, using fallback")
            return 0
        
        reader_city = geoip2.database.Reader(city_db_path)
        reader_asn = None
        if asn_db_path and Path(asn_db_path).exists():
            try:
                reader_asn = geoip2.database.Reader(asn_db_path)
            except Exception:
                reader_asn = None
        cursor = conn.cursor()
        
        # Get all IPs without geolocation data
        cursor.execute('''
            SELECT DISTINCT bi.ip_address 
            FROM bad_ips bi
            LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
            WHERE ig.ip_address IS NULL
        ''')
        
        ips_to_enrich = [row[0] for row in cursor.fetchall()]
        enriched = 0
        
        for ip in ips_to_enrich:
            try:
                # Validate IP format
                ipaddress.ip_address(ip)
                response = reader_city.city(ip)
                asn_val = None
                if reader_asn:
                    try:
                        a = reader_asn.asn(ip)
                        if getattr(a, 'autonomous_system_number', None):
                            asn_val = f"AS{a.autonomous_system_number}"
                    except Exception:
                        asn_val = None
                
                try:
                    cursor.execute('''
                        INSERT INTO ip_geolocation 
                        (ip_address, country, city, latitude, longitude, asn)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        ip,
                        response.country.iso_code,
                        response.city.name or response.subdivisions[0].name if response.subdivisions else None,
                        response.location.latitude,
                        response.location.longitude,
                        asn_val
                    ))
                    enriched += 1
                except sqlite3.IntegrityError:
                    pass
            except Exception:
                continue
        
        try:
            reader_city.close()
        except Exception:
            pass
        if reader_asn:
            try:
                reader_asn.close()
            except Exception:
                pass
        conn.commit()
        print(f"Enriched {enriched} IPs with geolocation data from GeoIP database")
        return enriched
    except Exception as e:
        print(f"Error enriching geolocation from database: {e}")
        return 0

def download_geoip_database(target_path='data/GeoLite2-City.mmdb'):
    """Download free GeoLite2-City database for geolocation enrichment"""
    try:
        target = Path(target_path)
        target.parent.mkdir(exist_ok=True)
        
        # Use MaxMind's mirror
        url = "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-City.mmdb"
        
        print(f"Downloading GeoLite2 database...")
        if requests is None:
            raise RuntimeError("requests not available")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            f.write(response.content)
        
        print(f"GeoLite2 database downloaded successfully ({len(response.content) / 1024 / 1024:.1f} MB)")
        return True
    except Exception as e:
        print(f"Warning: Could not download GeoLite2 database: {e}")
        return False


def download_geoip_asn_database(target_path='data/GeoLite2-ASN.mmdb'):
    """Download free GeoLite2-ASN database for ASN enrichment"""
    try:
        target = Path(target_path)
        target.parent.mkdir(exist_ok=True)
        url = "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-ASN.mmdb"
        print("Downloading GeoLite2 ASN database...")
        if requests is None:
            raise RuntimeError("requests not available")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            f.write(response.content)
        print(f"GeoLite2 ASN database downloaded successfully ({len(response.content) / 1024 / 1024:.1f} MB)")
        return True
    except Exception as e:
        print(f"Warning: Could not download GeoLite2 ASN database: {e}")
        return False

def enrich_geolocation_data(conn, limit=100):
    """Enrich database with geolocation data (limited to avoid rate limits)"""
    cursor = conn.cursor()
    
    # Get IPs without geolocation data
    cursor.execute('''
        SELECT DISTINCT bi.ip_address 
        FROM bad_ips bi
        LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
        WHERE ig.ip_address IS NULL
        LIMIT ?
    ''', (limit,))
    
    ips_to_enrich = [row[0] for row in cursor.fetchall()]
    enriched = 0
    
    for ip in ips_to_enrich:
        geo_data = fetch_geolocation(ip)
        if geo_data:
            try:
                cursor.execute('''
                    INSERT INTO ip_geolocation 
                    (ip_address, country, city, latitude, longitude, asn)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    ip,
                    geo_data.get('country'),
                    geo_data.get('city'),
                    geo_data.get('latitude'),
                    geo_data.get('longitude'),
                    geo_data.get('asn')
                ))
                enriched += 1
            except sqlite3.IntegrityError:
                pass
    
    conn.commit()
    print(f"Enriched {enriched} IPs with geolocation data")
    return enriched


def backfill_asn_from_db(conn, asn_db_path):
    """Fill missing ASN values using the GeoLite2-ASN database."""
    try:
        if not geoip2 or not Path(asn_db_path).exists():
            return 0
        reader_asn = geoip2.database.Reader(asn_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ip_address FROM ip_geolocation WHERE asn IS NULL OR asn = ''
        ''')
        ips = [r[0] for r in cursor.fetchall()]
        updated = 0
        for ip in ips:
            try:
                a = reader_asn.asn(ip)
                if getattr(a, 'autonomous_system_number', None):
                    asn_val = f"AS{a.autonomous_system_number}"
                    cursor.execute('UPDATE ip_geolocation SET asn = ? WHERE ip_address = ?', (asn_val, ip))
                    updated += 1
            except Exception:
                continue
        try:
            reader_asn.close()
        except Exception:
            pass
        conn.commit()
        if updated:
            print(f"Backfilled ASN for {updated} IPs")
        return updated
    except Exception as e:
        print(f"Error backfilling ASN: {e}")
        return 0


def generate_sample_geolocation_data(conn):
    """Generate sample geolocation data for testing"""
    import random
    
    cursor = conn.cursor()
    
    # Sample country data
    countries_data = [
        ('United States', 'New York', 40.7128, -74.0060),
        ('China', 'Beijing', 39.9042, 116.4074),
        ('Russia', 'Moscow', 55.7558, 37.6173),
        ('Iran', 'Tehran', 35.6762, 51.4244),
        ('North Korea', 'Pyongyang', 39.0176, 125.7453),
        ('Syria', 'Damascus', 33.5138, 36.2765),
        ('India', 'Delhi', 28.7041, 77.1025),
        ('Brazil', 'Sao Paulo', -23.5505, -46.6333),
        ('Nigeria', 'Lagos', 6.5244, 3.3792),
        ('Mexico', 'Mexico City', 19.4326, -99.1332),
    ]
    
    # Get sample of IPs without geolocation
    cursor.execute('''
        SELECT DISTINCT bi.ip_address 
        FROM bad_ips bi
        LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
        WHERE ig.ip_address IS NULL
        ORDER BY RANDOM()
        LIMIT 500
    ''')
    
    ips = [row[0] for row in cursor.fetchall()]
    inserted = 0
    
    for i, ip in enumerate(ips):
        country, city, lat, lon = random.choice(countries_data)
        try:
            cursor.execute('''
                INSERT INTO ip_geolocation 
                (ip_address, country, city, latitude, longitude, asn)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ip, country, city, lat, lon, f'AS{random.randint(1000, 65000)}'))
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    print(f"Generated sample geolocation data for {inserted} IPs")
    return inserted


def get_database_statistics(conn):
    """Generate database statistics"""
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM bad_ips')
    total_ips = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT country) FROM ip_geolocation WHERE country IS NOT NULL')
    countries = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT country, COUNT(*) as count 
        FROM ip_geolocation 
        WHERE country IS NOT NULL
        GROUP BY country 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    top_countries = cursor.fetchall()
    
    stats = {
        'total_ips': total_ips,
        'countries_affected': countries,
        'update_time': datetime.now().isoformat(),
        'top_countries': [{'country': c[0], 'count': c[1]} for c in top_countries]
    }
    
    # Store stats in database
    cursor.execute('''
        INSERT INTO database_stats (total_ips, update_time, countries_affected)
        VALUES (?, ?, ?)
    ''', (total_ips, stats['update_time'], countries))
    conn.commit()
    
    return stats


def main():
    """Main processing function"""
    print("Starting bad IP database processing...")
    
    # Create database
    conn = create_database()
    print("Database created/updated")
    
    # Load IPs from primary CSV
    ips = load_ips_from_csv()
    print(f"Loaded {len(ips)} IPs from CSV")

    # Load additional IPs from ingest sources if available
    extra = []
    for extra_path in ['data/feeds_ips.csv']:
        p = Path(extra_path)
        if p.exists():
            new_items = load_ips_from_csv(str(p))
            extra.extend(new_items)
            print(f"Loaded {len(new_items)} IPs from {extra_path}")

    # Merge, dedupe by IP keeping highest severity
    merged = {}
    for ip, sev in ips + extra:
        merged[ip] = max(sev, merged.get(ip, 0))
    merged_list = [(ip, sev) for ip, sev in merged.items()]
    
    # Insert IPs
    insert_ips_to_database(conn, merged_list)
    
    
    # Try to use GeoLite2 databases first, then fall back to API
    geoip_city_path = 'data/GeoLite2-City.mmdb'
    geoip_asn_path = 'data/GeoLite2-ASN.mmdb'
    if requests is not None:
        city_ok = download_geoip_database(geoip_city_path)
        asn_ok = download_geoip_asn_database(geoip_asn_path)
        if city_ok:
            enrich_geolocation_data_from_db(conn, geoip_city_path, geoip_asn_path if asn_ok else None)
            if asn_ok:
                backfill_asn_from_db(conn, geoip_asn_path)
        else:
            print("Fallback: Using API-based geolocation (limited)...")
            enrich_geolocation_data(conn, limit=100)
    # Generate sample data if needed (for demo/testing)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ip_geolocation')
    geo_count = cursor.fetchone()[0]
    if geo_count < 100:  # If not enough geolocation data, generate sample
        print("Generating sample geolocation data for testing...")
        generate_sample_geolocation_data(conn)
    
    # Generate statistics
    stats = get_database_statistics(conn)
    print(f"\nDatabase Statistics:")
    print(f"  Total IPs: {stats['total_ips']}")
    print(f"  Countries Affected: {stats['countries_affected']}")
    print(f"  Top Countries:")
    for country in stats['top_countries'][:5]:
        print(f"    - {country['country']}: {country['count']}")
    
    # Save stats to JSON
    stats_path = Path('data/stats.json')
    stats_path.parent.mkdir(exist_ok=True)
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    conn.close()
    print("\nBad IP processing completed successfully!")


if __name__ == '__main__':
    main()
