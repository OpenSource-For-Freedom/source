#!/usr/bin/env python3
"""
Fetch Hacker News mentions of cyber attacks by country
Uses HN Algolia Search API to find discussions about cyber attacks attributed to countries
"""

import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# Top countries to search for (matching our IP data)
COUNTRIES = [
    ("China", "CN"),
    ("United States", "US"),
    ("Russia", "RU"),
    ("India", "IN"),
    ("Netherlands", "NL"),
    ("Brazil", "BR"),
    ("Thailand", "TH"),
    ("Germany", "DE"),
    ("Singapore", "SG"),
    ("South Korea", "KR"),
    ("North Korea", "NK"),
    ("Iran", "IR"),
    ("Ukraine", "UA"),
    ("United Kingdom", "UK"),
    ("France", "FR"),
]

# Cyber attack related keywords
CYBER_KEYWORDS = [
    "cyber attack",
    "hacking",
    "hack",
    "ransomware",
    "data breach",
    "cyberattack",
    "malware",
    "APT",
    "threat actor",
]


def search_hn(query, days_back=180):
    """Search HN Algolia API for a query in the last N days"""
    # HN Algolia API endpoint
    url = "http://hn.algolia.com/api/v1/search"
    
    # Calculate timestamp for N days ago
    since_ts = int((datetime.now() - timedelta(days=days_back)).timestamp())
    
    params = {
        "query": query,
        "tags": "story",
        "numericFilters": f"created_at_i>{since_ts}",
        "hitsPerPage": 100,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("nbHits", 0)
    except Exception as e:
        print(f"Error searching HN for '{query}': {e}")
        return 0


def fetch_country_mentions():
    """Fetch HN mentions of cyber attacks by country"""
    print("Searching Hacker News for cyber attack mentions by country...")
    print("(This searches the last 180 days of HN stories)")
    
    results = {}
    
    for country_name, country_code in COUNTRIES:
        total_mentions = 0
        
        # Search for country + each cyber keyword
        for keyword in CYBER_KEYWORDS[:3]:  # Limit to top 3 keywords to avoid rate limiting
            query = f"{country_name} {keyword}"
            count = search_hn(query, days_back=180)
            total_mentions += count
            
            if count > 0:
                print(f"  '{query}': {count} stories")
        
        results[country_code] = {
            "country": country_name,
            "mentions": total_mentions,
        }
        
        print(f"Total for {country_name}: {total_mentions} mentions\n")
    
    return results


def save_results(results):
    """Save results to JSON file"""
    output_path = Path("data/hn_country_mentions.json")
    
    # Sort by mentions
    sorted_results = dict(
        sorted(results.items(), key=lambda x: x[1]["mentions"], reverse=True)
    )
    
    data = {
        "last_updated": datetime.now().isoformat(),
        "search_period_days": 180,
        "countries": sorted_results,
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"\nSaved results to {output_path}")
    
    # Print summary
    print("\nTop 10 Countries by HN Cyber Attack Mentions:")
    for i, (code, info) in enumerate(list(sorted_results.items())[:10], 1):
        print(f"{i}. {info['country']} ({code}): {info['mentions']} mentions")


def main():
    """Main function"""
    results = fetch_country_mentions()
    save_results(results)
    print("\nHacker News cyber attack mention analysis complete!")


if __name__ == "__main__":
    main()
