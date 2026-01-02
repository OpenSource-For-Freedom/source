# Contributing to SOURCE

Thank you for your interest in improving the SOURCE malicious IP intelligence feed! We welcome contributions from security researchers, developers, and data enthusiasts.

## Table of Contents

- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Running Locally](#running-locally)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Testing](#testing)

---

## How to Contribute

### Reporting Issues

**Data Quality Issues**
- Found false positives or outdated IPs? Open an issue with IP address, source, and evidence
- Include severity level and any DNS/WHOIS data that supports your claim

**Bugs**
- Check existing issues to avoid duplicates
- Provide Python version, OS, and error logs
- Include minimal reproduction steps

**Feature Requests**
- Describe the use case and expected behavior
- Explain how it improves threat intelligence value
- Consider submitting a draft implementation

### Contributing Code

We accept pull requests for:

- Bug fixes and error handling improvements
- New threat intelligence sources (must be reputable and open)
- Visualization enhancements
- Performance optimizations
- Documentation improvements
- Test coverage expansion  

---

## Development Setup

### Prerequisites

- **Python 3.10+** (3.14 recommended)
- **Git**
- **SQLite3** (usually pre-installed)
- **Virtual environment tool** (venv, conda, or poetry)

### Clone the Repository

```bash
git clone https://github.com/OpenSource-For-Freedom/SOURCE.git
cd SOURCE
```

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Required Python Packages

```
requests>=2.31.0
geoip2>=4.7.0
matplotlib>=3.8.0
pandas>=2.1.0
plotly>=5.18.0
```

### Download GeoIP Databases

GeoLite2 databases are required for geolocation enrichment:

1. Create a free account at [MaxMind](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)
2. Download `GeoLite2-City.mmdb` and `GeoLite2-ASN.mmdb`
3. Place them in the `data/` directory

---

## Running Locally

### Fetch Threat Feeds

```bash
python scripts/fetch_blacklists.py
```

This downloads fresh IP lists from configured sources and writes them to `data/fetched_ips.csv`.

### Process and Enrich Data

```bash
python scripts/process_badips.py
```

This script:
- Deduplicates IPs
- Enriches with geolocation and ASN data
- Calculates severity scores
- Updates `badip_list.csv` and `data/badips.db`

### Generate Visualizations

```bash
python scripts/generate_visualizations.py
```

Creates charts in `data/charts/`.

### Update README Stats

```bash
python scripts/update_readme.py
```

Refreshes statistics in [README.md](README.md).

---

## Submitting Changes

### Pull Request Process

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit with clear messages
   ```bash
   git commit -m "Add support for new threat feed: Example Feed"
   ```

3. **Test your changes** locally
   ```bash
   python scripts/process_badips.py
   python scripts/generate_visualizations.py
   ```

4. **Push to your fork** and open a pull request
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Describe your changes** in the PR description:
   - What problem does it solve?
   - How did you test it?
   - Any breaking changes?

### Pull Request Guidelines

- Keep changes focused — one feature per PR
- Update documentation if behavior changes
- Add tests for new functionality
- Ensure all scripts run without errors
- Follow existing code style
- Sign commits (optional but encouraged)  

---

## Code Style

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use meaningful variable names (`ip_address`, not `x`)
- Add docstrings to functions and classes
- Limit lines to 88 characters (Black formatter standard)
- Use type hints where appropriate

### Example Function

```python
def enrich_ip_with_geolocation(ip_address: str) -> dict:
    """
    Catch an IP address with geolocation data.
    
    Args:
        ip_address: IPv4 or IPv6 address string
        
    Returns:
        Dictionary containing country, city, latitude, longitude
    """
    # Implementation
    pass
```

### Formatting

We recommend using `black` for consistent formatting as the workflow does this:

```bash
pip install black
black scripts/
```

---

## Testing

### Manual Testing

Before submitting a PR, verify:

1. **Data Integrity**
   ```bash
   # Check CSV format
   head -n 10 badip_list.csv
   
   # Verify database
   sqlite3 data/badips.db "SELECT COUNT(*) FROM bad_ips;"
   ```

2. **Visualization Generation**
   ```bash
   python scripts/generate_visualizations.py
   # Check that images are created in data/charts/
   ```

3. **Script Execution**
   ```bash
   # All scripts should run without errors
   python scripts/fetch_blacklists.py
   python scripts/process_badips.py
   python scripts/generate_visualizations.py
   ```

### Automated Tests

We welcome contributions that add test coverage:

```python
# Example test structure (future)
def test_severity_calculation():
    assert map_score_to_severity(3) == 1
    assert map_score_to_severity(15) == 3
    assert map_score_to_severity(60) == 5
```

---

## Adding New Threat Feeds

To add a new data source:

1. **Verify Feed Quality**
   - Must be reputable and actively maintained
   - Should provide IP addresses with context (malware, botnet, scanner, etc.)
   - Prefer open-source or freely accessible feeds

2. **Update `fetch_blacklists.py`**
   ```python
   FEED_URLS = [
       # ... existing feeds
       "https://example.com/threat-feed.txt",  # Add new feed
   ]
   ```

3. **Handle Feed Format**
   - Parse CSV, plain text, or JSON formats
   - Extract IP addresses and any metadata (severity, category)

4. **Update Documentation**
   - Add feed to "Data Sources" section in [README.md](README.md)
   - Credit the source provider

5. **Test End-to-End**
   ```bash
   python scripts/fetch_blacklists.py
   python scripts/process_badips.py
   ```

---

## Questions?

- **General Questions:** Open a [Discussion](https://github.com/OpenSource-For-Freedom/SOURCE/discussions)
- **Bug Reports:** Open an [Issue](https://github.com/OpenSource-For-Freedom/SOURCE/issues)
- **Security Issues:** See [SECURITY.md](SECURITY.md)

---

**K E E P --- H U N T I N G**
