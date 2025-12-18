# API 

## Bad IP Database API

This document describes the SQLite database schema and how to query the bad IP information.

## Database Connection

```python
import sqlite3
from pathlib import Path

db_path = Path('data/badips.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
```

## Common Queries

### 1. Search for a Specific IP

```python
ip = '192.168.1.1'
cursor.execute('''
    SELECT bi.ip_address, bi.severity, bi.threat_count, 
           ig.country, ig.city, ig.latitude, ig.longitude
    FROM bad_ips bi
    LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
    WHERE bi.ip_address = ?
''', (ip,))

result = cursor.fetchone()
if result:
    print(f"Found: {result}")
```

### 2. Get All High-Severity IPs

```python
cursor.execute('''
    SELECT bi.ip_address, bi.severity, bi.threat_count,
           ig.country, ig.city
    FROM bad_ips bi
    LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
    WHERE bi.severity >= 4
    ORDER BY bi.threat_count DESC
    LIMIT 100
''')

high_severity_ips = cursor.fetchall()
```

### 3. Geographic Analysis

```python
# Top 20 countries by IP count
cursor.execute('''
    SELECT country, COUNT(*) as count
    FROM ip_geolocation
    WHERE country IS NOT NULL
    GROUP BY country
    ORDER BY count DESC
    LIMIT 20
''')

# Get all IPs from a specific country
cursor.execute('''
    SELECT ip_address, city, latitude, longitude
    FROM ip_geolocation
    WHERE country = ?
    ORDER BY ip_address
''', ('United States',))
```

### 4. Threat Statistics

```python
# Distribution by severity
cursor.execute('''
    SELECT severity, COUNT(*) as count
    FROM bad_ips
    GROUP BY severity
    ORDER BY severity
''')

# Most frequently detected threats
cursor.execute('''
    SELECT ip_address, threat_count, last_updated
    FROM bad_ips
    ORDER BY threat_count DESC
    LIMIT 20
''')
```

### 5. Time-based Analysis

```python
# Recently updated IPs
cursor.execute('''
    SELECT ip_address, severity, last_updated
    FROM bad_ips
    WHERE last_updated > datetime('now', '-7 days')
    ORDER BY last_updated DESC
    LIMIT 50
''')

# First detection dates
cursor.execute('''
    SELECT ip_address, first_seen, severity
    FROM bad_ips
    WHERE first_seen > datetime('now', '-30 days')
    ORDER BY first_seen DESC
''')
```

### 6. Export Data using Pandas

```python
import pandas as pd

# Export to CSV
query = '''
    SELECT bi.ip_address, bi.severity, bi.threat_count,
           ig.country, ig.city, ig.latitude, ig.longitude
    FROM bad_ips bi
    LEFT JOIN ip_geolocation ig ON bi.ip_address = ig.ip_address
'''

df = pd.read_sql_query(query, conn)
df.to_csv('bad_ips_export.csv', index=False)

# Export to JSON
import json
results = cursor.execute(query).fetchall()
columns = [description[0] for description in cursor.description]
data = [dict(zip(columns, row)) for row in results]
with open('bad_ips_export.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## Reference

### bad_ips Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-incrementing primary key |
| ip_address | TEXT | Unique IP address |
| severity | INTEGER | Threat level (1-5) |
| first_seen | TEXT | ISO 8601 timestamp |
| last_updated | TEXT | ISO 8601 timestamp |
| threat_count | INTEGER | Detection count |

### ip_geolocation Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-incrementing primary key |
| ip_address | TEXT | Unique IP address (FK) |
| country | TEXT | Country name |
| city | TEXT | City name |
| latitude | REAL | Geographic latitude |
| longitude | REAL | Geographic longitude |
| asn | TEXT | Autonomous System Number |
| isp | TEXT | Internet Service Provider |
| last_updated | TEXT | ISO 8601 timestamp |

### threat_categories Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-incrementing primary key |
| ip_address | TEXT | IP address (FK) |
| category | TEXT | Threat category |
| count | INTEGER | Detection count |

### database_stats Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-incrementing primary key |
| total_ips | INTEGER | Total IPs in database |
| update_time | TEXT | ISO 8601 timestamp |
| countries_affected | INTEGER | Unique countries |

## SECURITY

1. **Always use parameterized queries** to prevent SQL injection
2. **Close connections** after use: `conn.close()`
3. **Index frequently queried columns** for performance
4. **Batch operations** for better performance on large datasets
5. **Use transactions** for multiple related updates

## Example: Complete Analysis Script

```python
import sqlite3
import json
from datetime import datetime, timedelta

conn = sqlite3.connect('data/badips.db')
cursor = conn.cursor()

analysis = {
    'timestamp': datetime.now().isoformat(),
    'total_ips': cursor.execute('SELECT COUNT(*) FROM bad_ips').fetchone()[0],
    'unique_countries': cursor.execute('SELECT COUNT(DISTINCT country) FROM ip_geolocation WHERE country IS NOT NULL').fetchone()[0],
    'high_severity_ips': cursor.execute('SELECT COUNT(*) FROM bad_ips WHERE severity >= 4').fetchone()[0],
    'recently_added': cursor.execute(
        'SELECT COUNT(*) FROM bad_ips WHERE first_seen > datetime(?, \'days\')',
        ('-7',)
    ).fetchone()[0],
}

cursor.execute('''
    SELECT country, COUNT(*) as count
    FROM ip_geolocation
    WHERE country IS NOT NULL
    GROUP BY country
    ORDER BY count DESC
    LIMIT 10
''')
analysis['top_countries'] = [
    {'country': row[0], 'count': row[1]}
    for row in cursor.fetchall()
]

conn.close()

print(json.dumps(analysis, indent=2))
```

