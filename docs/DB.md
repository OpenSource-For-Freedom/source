## Pipeline

- **Fetch script:** [scripts/fetch_blacklists.py](scripts/fetch_blacklists.py) — fetch-only; writes per-source CSVs into the `data/` folder (produces `data/fetched_ips.csv` and `data/new_ips.csv`) and does NOT modify `badip_list.csv` or the database.
- **Processor:** [scripts/process_badips.py](scripts/process_badips.py) — ingests all CSVs under `data/`, deduplicates and normalizes records, updates the canonical [badip_list.csv](badip_list.csv), and writes `data/badips.db`; also performs geolocation/ASN enrichment and generates charts.
- **CI orchestration:** [.github/workflows/update-badip.yml](.github/workflows/update-badip.yml) — runs the fetcher, then the processor, then `scripts/generate_visualizations.py`, and commits the updated artifacts back to the repo (uses GitHub Actions secrets where needed).

## Database overview

### How database files feed badips.db and .mmdb

- badip_list.csv (source-of-truth)
    - Master CSV containing rows for each malicious IP (ip, first_seen, last_seen, severity, source_feed, asn, asn_org, country_code, city, latitude, longitude, notes).
    - Updated weekly by CI; used as the single canonical input for all downstream artifacts.

- Enrichment/cache files (intermediate)
    - Temporary JSON/Parquet/CSV files produced during enrichment (geo lookups, ASN resolution, reverse DNS, threat scoring).
    - Persisted to avoid repeated external lookups and to provide reproducible builds.

- badips.db (SQLite)
    - Built from badip_list.csv + enrichment data.
    - Normalized tables (ips, asns, sources) and indexes on ip, last_seen, severity for fast analytic queries and joins.
    - Primary runtime store for dashboards, CI checks, exports, and programmatic queries.

- badips.mmdb (MaxMind DB)
    - Generated from badip_list.csv + geolocation fields via an mmdb writer (e.g., libmaxminddb/mmdbwriter).
    - Schema maps IP -> {is_malicious: true, severity, first_seen, last_seen, source, asn, asn_org, country, city, latitude, longitude}.
    - Optimized for low-latency binary lookups by services (GeoIP2-compatible consumers, edge proxies, appliances).

- Exports and consumers
    - Blocklists (plain IP/CIDR), JSON/GeoJSON, CSV exports and the .mmdb are produced from badips.db or directly from the canonical CSV.
    - SIEM enrichment jobs and automation read badips.db for joins; network appliances read the .mmdb for fast IP tagging.

- CI pipeline
    - CI: ingest feeds -> normalize -> enrich -> write badip_list.csv -> build badips.db -> build badips.mmdb -> generate charts/exports -> publish artifacts.
    - Each step adds structure (DB tables, MMDB keys) tailored to consumer performance and query patterns.

### Dependancies
```
requests>=
geoip2>=
matplotlib>=
pandas>=
plotly>=
pygeoip>=
```

## Database Statistics
- **Total Malicious IPs**: 212,137
- **Countries Affected**: 213
- **Average Threat Severity**: 3.00/5
- **Last Updated**: 2025-12-17 22:32:11 UTC