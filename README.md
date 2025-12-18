<div align="center">

<img alt="Source" src="assets/source.png" width="400" style="border: 4px solid #000; border-radius: 8px; display: block; margin: 0 auto 30px;" />

<img alt="GitHub" src="https://raw.githubusercontent.com/edent/SuperTinyIcons/master/images/svg/github.svg" width="64" height="64" />

<h1>Bad IP Database</h1>

<p>
<img alt="Python" src="https://img.shields.io/badge/Python-3.11-%233776AB?logo=python&logoColor=white" />
<img alt="GitHub Repo" src="https://img.shields.io/badge/GitHub-Repo-%2312100E?logo=github&logoColor=white&labelColor=%23A67C52&color=%2312100E" />
<img alt="Actions" src="https://github.com/OpenSource-For-Freedom/source/actions/workflows/update-badip.yml/badge.svg" />
<img alt="Views" src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FOpenSource-For-Freedom/source&title=Views&edge_flat=false&count_bg=%238A5A2B&title_bg=%2312100E&color=%23D7B377" />
</p>

<em>Automatically updated malicious IP database with geolocation mapping and threat analysis.</em>

<p><strong>Data updated every Sunday at midnight UTC.</strong></p>

</div>

# Overview
- This is an "API-Less" Database of known malicious IP's. We are capturing using the CI process with Google RSS and [Stamparm/Ipsum](https://github.com/stamparm/ipsum) as key ingestion. 
- You can clone this repository, and it will produce the same series of graphs and constant CI updates as it does here. 

---

## Database Statistics

- **Total Malicious IPs**: 192,605
- **Countries Affected**: 213
- **Average Threat Severity**: 3.00/5
- **Last Updated**: 2025-12-17 19:54:01 UTC

---

## Global Threat Distribution

<div align="center">

<img alt="Pin Map" src="data/charts/map_pins.png" width="920" />

<img alt="Dashboard" src="data/charts/dashboard.png" width="920" />

</div>

---

## Detailed Views

![Countries Chart](data/charts/countries.png)

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Getting started guide
- **[API.md](API.md)** - Database schema and query examples
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines

---
**Data Sources**: [Stamparm/Ipsum](https://github.com/stamparm/ipsum) | [Google Safe Browsing](https://developers.google.com/safe-browsing) | Google RSS feeds (via CI) | **Last Generated**: 2025-12-17 19:54:01 UTC
