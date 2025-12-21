<div align="center">
<img alt="SOURCE" src="assets/source.png" width="800" />


<h1>S-O-U-R-C-E</h1>

<p align="center">
  <a href="https://github.com/OpenSource-For-Freedom/SOURCE/actions/workflows/update-badip.yml">
    <img alt="source" src="https://github.com/OpenSource-For-Freedom/SOURCE/actions/workflows/update-badip.yml/badge.svg" />
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

## Resources
- Curl this to capture the bad ip file
```
curl -sS https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv
```

## Database Statistics

| Metric | Value |
|---|---|
| Total Malicious IPs | 247,069 |
| Countries Affected | 217 |
| Average Threat Severity | 3.00/5 |
| Last Updated | 2025-12-21 02:09:41 UTC |

## Top Countries

| Country | IPs |
|---|---|
| CN | 48244 |
| US | 39616 |
| IN | 12924 |
| RU | 9768 |
| NL | 8972 |
| TH | 7718 |
| BR | 7550 |
| DE | 6818 |
| SG | 5798 |
| KR | 5491 |

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
| IP | ASN/ISP | Severity | Threats |
|---|---|---|---|
| 83.219.248.37 | AS41745 | 3/5 | 27 |
| 179.43.184.242 | AS51852 | 3/5 | 25 |
| 114.111.54.188 | AS54994 | 3/5 | 25 |
| 45.148.10.121 | AS48090 | 3/5 | 25 |
| 80.94.92.182 | AS47890 | 3/5 | 25 |
| 80.94.92.186 | AS47890 | 3/5 | 25 |
| 129.45.84.93 | AS327931 | 3/5 | 25 |
| 143.20.185.79 | AS214209 | 3/5 | 25 |
| 45.93.168.13 | AS48011 | 3/5 | 25 |
| 61.245.11.87 | AS19970 | 3/5 | 25 |
| 62.60.131.157 | AS208137 | 3/5 | 25 |
| 64.227.97.118 | AS14061 | 3/5 | 25 |
| 66.132.153.113 | AS398324 | 3/5 | 25 |
| 66.132.153.115 | AS398324 | 3/5 | 25 |
| 66.132.153.123 | AS398324 | 3/5 | 25 |
| 66.132.153.127 | AS398324 | 3/5 | 25 |
| 66.240.192.138 | AS10439 | 3/5 | 25 |
| 71.6.165.200 | AS10439 | 3/5 | 25 |
| 71.6.199.23 | AS10439 | 3/5 | 25 |
| 80.82.77.33 | AS202425 | 3/5 | 25 |


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
**Data Sources**: [Stamparm/Ipsum](https://github.com/stamparm/ipsum) |[Hacker News](https://thehackernews.com/) | [Google Safe Browsing](https://developers.google.com/safe-browsing) | [Google Transparency Report](https://transparencyreport.google.com/) | **Last Generated**: 2025-12-21 02:09:41 UTC
</div>

