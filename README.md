<div align="center">
<img alt="SOURCE" src="assets/source.png" width="800" />


<h1>S-O-U-R-C-E</h1>

<p align="center">
  <a href="https://github.com/OpenSource-For-Freedom/source/actions/workflows/update-badip.yml">
  <img alt="Workflow Status" src="https://github.com/OpenSource-For-Freedom/source/actions/workflows/update-badip.yml/badge.svg" />
</a>
<a href="https://github.com/OpenSource-For-Freedom/source/actions">
  <img alt="GitHub Actions" src="https://img.shields.io/badge/GitHub-Actions-%23000000?logo=github&logoColor=white" />
</a>
<a href="https://www.python.org/downloads/release/python-3140/">
  <img alt="Python 3.14" src="https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white" />
</a>
<a href="https://hits.dwyl.com/OpenSource-For-Freedom/source">
  <img alt="Views" src="https://hits.dwyl.com/OpenSource-For-Freedom/source.svg?style=flat-square" />
</a>
</p>

<em>Automatically updated malicious IP database with geolocation mapping and threat analysis.</em>

<p><strong>Data updated every Sunday at midnight UTC.</strong></p>


---

## Database Statistics

- **Total Malicious IPs**: 230,701
- **Countries Affected**: 216
- **Average Threat Severity**: 0.00/5
- **Last Updated**: 2025-12-19 04:17:39 UTC

---

## Global Threat Distribution

<div align="center">

<img alt="Pin Map" src="data/charts/map_pins.png" width="920" />

<img alt="Dashboard" src="data/charts/dashboard.png" width="920" />

</div>

<img alt="Countries Chart" src="data/charts/countries.png" width="920" />

<img alt="World Map" src="data/charts/worldmap.png" width="920" />

---

## Cyber Attack Attribution (Hacker News)

<div align="center">

<img alt="HN Cyber Attack Mentions by Country" src="data/charts/hn_cyberattack_pie.png" width="920" />

</div>

</div>

## Wall of Shame
```bash
| IP              | Domain                              | Score |
|-----------------|-------------------------------------|-------|
| 114.111.54.188  | N/A                                 | 10    |
| 179.43.184.242  | hostedby.privatelayer.com           | 10    |
| 193.221.201.95  | N/A                                 | 10    |
| 45.148.10.121   | N/A                                 | 9     |
| 80.82.77.139    | dojo.census.shodan.io               | 9     |
| 129.45.84.93    | host-93.84.45.129.djezzycloud.dz    | 9     |
| 2.57.121.25     | hosting25.tronicsat.com             | 8     |
| 2.57.121.112    | dns112.personaliseplus.com          | 8     |
| 3.137.73.221    | scan.cypex.ai                       | 8     |
| 43.252.231.122  | N/A                                 | 8     |
| 61.245.11.87    | N/A                                 | 8     |
| 64.227.97.118   | N/A                                 | 8     |
| 66.240.192.138  | census8.shodan.io                   | 8     |
| 71.6.199.23     | einstein.census.shodan.io           | 8     |
| 80.82.77.33     | sky.census.shodan.io                | 8     |
| 80.94.92.164    | N/A                                 | 8     |
| 80.94.92.182    | N/A                                 | 8     |
| 80.94.92.186    | N/A                                 | 8     |
| 94.102.49.193   | cloud.census.shodan.io              | 8     |
| 103.224.243.145 | server.creativesense.co.in          | 8     |
```
# Overview
- This is an "API-KEY-LESS" repo.
- Uses open-source data to collect known malicious IPs and geolocate them with Python.
- Clone this repo to obtain actively updated data to help secure your infrastructure.
- Source of truth: [Bad IP List](/badip_list.csv) is updated weekly; images and charts are regenerated on the same cadence.

## Documentation

- **[Overview.md](docs/OVERVIEW.md)** - General Overview of repository function
- **[API.md](docs/API.md)** - Database schema and query examples
- **[Database.md](docs/DB.md)** - Database design, included files and pipeline


![batman](assets/IMG_4295.jpeg)
---
**Data Sources**: [Stamparm/Ipsum](https://github.com/stamparm/ipsum) |[Hacker News](https://thehackernews.com/) | [Google Safe Browsing](https://developers.google.com/safe-browsing) | [Google Transparency Report](https://transparencyreport.google.com/) | **Last Generated**: 2025-12-19 04:17:39 UTC
</div>

