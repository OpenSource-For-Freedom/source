#!/usr/bin/env python3
"""
Generate visualizations and update README with bad IP statistics
"""

# Many functions here are visualization-heavy and intentionally large.
# pylint: disable=too-many-lines,too-many-statements,too-many-branches,too-many-locals,broad-exception-caught,use-dict-literal,import-outside-toplevel,invalid-name,line-too-long,unused-argument,unused-variable,maybe-no-member,no-member

import sqlite3
from pathlib import Path
from datetime import datetime
import subprocess
import sys

from typing import Any

# plachold for plot errors
plt: Any = None
np: Any = None
pe: Any = None
pd: Any = None
go: Any = None

try:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import patheffects as pe
    import pandas as pd
    import plotly.graph_objects as go
except ImportError:
    print("Warning: Some visualization libraries not available")
    # keep the Any-typed placeholders as None at runtime mark and stage


def _plotting_ready():
    return plt is not None and np is not None


def apply_viz_theme():
    """Apply a cohesive, modern Matplotlib theme for all charts."""
    if plt is None:
        return
    assert plt is not None
    try:
        plt.rcParams.update(
            {
                "figure.facecolor": "white",
                "axes.facecolor": "#f7f7f9",
                "axes.edgecolor": "#2e2e2e",
                "axes.grid": True,
                "grid.color": "#b0b8c0",
                "grid.linestyle": "--",
                "grid.alpha": 0.35,
                "axes.titlesize": 16,
                "axes.labelsize": 13,
                "xtick.labelsize": 10,
                "ytick.labelsize": 10,
                "savefig.dpi": 200,
            }
        )
    except Exception:
        pass


def apply_steampunk_theme():
    """Steampunk-inspired dark theme with brass/copper accents."""
    if plt is None:
        return
    assert plt is not None
    try:
        plt.rcParams.update(
            {
                "figure.facecolor": "#0b0b0f",
                "axes.facecolor": "#111118",
                "axes.edgecolor": "#76ff7a",  # lime edge
                "axes.labelcolor": "#ff9be0",
                "text.color": "#d8ffd8",
                "axes.grid": True,
                "grid.color": "#2a2a33",
                "grid.linestyle": ":",
                "grid.alpha": 0.35,
                "xtick.color": "#d8ffd8",
                "ytick.color": "#d8ffd8",
                "axes.titlesize": 16,
                "axes.labelsize": 12,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
                "savefig.dpi": 180,
            }
        )
    except Exception:
        pass


def steampunk_palette(n):
    """Return a list of n steampunk-like copper/brass colors."""
    base = ["#ff66c4", "#76ff7a", "#ff9be0", "#64f58d", "#ff5fbf"]
    if n <= len(base):
        return base[:n]
    colors = []
    for i in range(n):
        c = base[i % len(base)]
        colors.append(c)
    return colors


def create_steampunk_dashboard(stats):
    """Create a single PNG dashboard with multiple charts in a steampunk theme."""
    if not _plotting_ready():
        print("Matplotlib not available; skipping dashboard")
        return False
    assert plt is not None and np is not None
    try:
        db_path = Path("data/badips.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Severity distribution
        cursor.execute(
            """
            SELECT severity, COUNT(*)
            FROM bad_ips
            GROUP BY severity
            ORDER BY severity
        """
        )
        sev_rows = cursor.fetchall()
        severities = [int(r[0]) for r in sev_rows]
        sev_counts = [int(r[1]) for r in sev_rows]

        # Top countries (limit 12 for compactness)
        cursor.execute(
            """
            SELECT country, COUNT(*) as count
            FROM ip_geolocation
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 12
        """
        )
        country_rows = cursor.fetchall()
        countries = [r[0] for r in country_rows]
        country_counts = [int(r[1]) for r in country_rows]

        # Top ASNs (limit 10)
        cursor.execute(
            """
            SELECT COALESCE(asn, 'AS-Unknown') AS asn, COUNT(*) as cnt
            FROM ip_geolocation
            GROUP BY asn
            ORDER BY cnt DESC
            LIMIT 10
        """
        )
        asn_rows = cursor.fetchall()
        asns = [str(r[0]) for r in asn_rows]
        asn_counts = [int(r[1]) for r in asn_rows]

        # Top cities bubble data (limit 15)
        cursor.execute(
            """
            SELECT city, country, COUNT(*) as cnt
            FROM ip_geolocation
            WHERE city IS NOT NULL AND country IS NOT NULL
            GROUP BY city, country
            ORDER BY cnt DESC
            LIMIT 15
        """
        )
        city_rows = cursor.fetchall()
        conn.close()

        # Apply theme
        apply_steampunk_theme()

        # Build figure with 2x2 layout
        fig = plt.figure(figsize=(16, 9))
        gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.28)

        # A1: Donut chart for severityfor Liam
        ax1 = fig.add_subplot(gs[0, 0])
        if sev_counts:
            level_names = ["Low", "Medium", "High", "Critical", "Extreme"]
            labels = [
                f"{level_names[s-1] if 1 <= s <= 5 else s}\n{sev_counts[i]:,}"
                for i, s in enumerate(severities)
            ]
            colors = steampunk_palette(len(severities))
            _pie = ax1.pie(
                sev_counts,
                startangle=90,
                wedgeprops=dict(width=0.38, edgecolor="#2b1e16", linewidth=1.5),
                colors=colors,
                labels=None,
            )
            if len(_pie) == 3:
                wedges, texts, _autotexts = _pie
            else:
                wedges, texts = _pie
            # Center text
            ax1.text(
                0,
                0,
                "Severity",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )
            # Add labels outside with leader lines
            ang = 0
            total = sum(sev_counts)
            theta = np.cumsum([0] + [v / total * 360 for v in sev_counts])
            for i, w in enumerate(wedges):
                angle = np.deg2rad((theta[i] + theta[i + 1]) / 2)
                x = 1.1 * np.cos(angle)
                y = 1.1 * np.sin(angle)
                t = ax1.text(x, y, labels[i], ha="center", va="center", fontsize=9)
                t.set_path_effects([pe.withStroke(linewidth=2, foreground="#12100e")])
            ax1.set_title("Threat Severity")
        else:
            ax1.text(0.5, 0.5, "No severity data", ha="center", va="center")
            ax1.set_axis_off()

        # A2: Top countries bar
        ax2 = fig.add_subplot(gs[0, 1])
        if country_counts:
            x = np.arange(len(countries))
            max_c = max(country_counts)
            # Copper gradient based on value
            base = np.array(country_counts) / (max_c or 1)
            cmap_orange = plt.cm.get_cmap("Oranges")
            colors = cmap_orange(0.35 + 0.6 * base)
            bars = ax2.bar(
                x, country_counts, color=colors, edgecolor="#8a5a2b", linewidth=1.1
            )
            for b in bars:
                h = b.get_height()
                tt = ax2.text(
                    b.get_x() + b.get_width() / 2.0,
                    h,
                    f"{int(h):,}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )
                tt.set_path_effects([pe.withStroke(linewidth=2, foreground="#12100e")])
            ax2.set_xticks(x)
            ax2.set_xticklabels(countries, rotation=35, ha="right")
            ax2.set_title("Top Countries")
            ax2.set_ylabel("IPs")
        else:
            ax2.text(0.5, 0.5, "No country data", ha="center", va="center")
            ax2.set_axis_off()

        # B1: Top ASNs horizontal bars
        ax3 = fig.add_subplot(gs[1, 0])
        if asn_counts:
            y = np.arange(len(asns))
            max_a = max(asn_counts)
            cmap_copper = plt.cm.get_cmap("copper")
            colors = cmap_copper(0.35 + 0.6 * (np.array(asn_counts) / (max_a or 1)))
            bars = ax3.barh(
                y, asn_counts, color=colors, edgecolor="#714c2a", linewidth=1.1
            )
            for i, b in enumerate(bars):
                w = b.get_width()
                tt = ax3.text(
                    w,
                    b.get_y() + b.get_height() / 2.0,
                    f" {int(w):,}",
                    ha="left",
                    va="center",
                    fontsize=9,
                )
                tt.set_path_effects([pe.withStroke(linewidth=2, foreground="#12100e")])
            ax3.set_yticks(y)
            ax3.set_yticklabels(asns)
            ax3.set_title("Top ASNs")
            ax3.set_xlabel("IPs")
            ax3.invert_yaxis()
        else:
            ax3.text(0.5, 0.5, "No ASN data", ha="center", va="center")
            ax3.set_axis_off()

        # B2: Top cities bubble chart
        ax4 = fig.add_subplot(gs[1, 1])
        if city_rows:
            names = [f"{r[0]} ({r[1]})" for r in city_rows]
            vals = np.array([int(r[2]) for r in city_rows])
            x = np.arange(len(names))
            sizes = 150 * (vals / (vals.max() or 1)) + 30
            cmap_ybor = plt.cm.get_cmap("YlOrBr")
            colors = cmap_ybor(0.35 + 0.6 * (vals / (vals.max() or 1)))
            ax4.scatter(x, vals, s=sizes, c=colors, edgecolor="#5a3b1a", linewidth=0.8)
            for i, v in enumerate(vals):
                tt = ax4.text(
                    x[i], v, f"{int(v):,}", ha="center", va="bottom", fontsize=8
                )
                tt.set_path_effects([pe.withStroke(linewidth=2, foreground="#12100e")])
            ax4.set_xticks(x)
            ax4.set_xticklabels(names, rotation=35, ha="right")
            ax4.set_title("Top Cities (bubble size = IP count)")
            ax4.set_ylabel("IPs")
        else:
            ax4.text(0.5, 0.5, "No city data", ha="center", va="center")
            ax4.set_axis_off()

        fig.suptitle(
            "Global Malicious IPs — Steampunk Dashboard",
            color="#d7b377",
            fontsize=18,
            fontweight="bold",
        )

        charts_path = Path("data/charts")
        charts_path.mkdir(exist_ok=True)
        out_path = charts_path / "dashboard.png"
        fig.savefig(str(out_path), bbox_inches="tight")
        plt.close(fig)

        print("Steampunk dashboard created")
        return True
    except Exception as e:
        print(f"Error creating dashboard: {e}")
        return False


def get_statistics():
    """Get statistics from database"""
    db_path = Path("data/badips.db")

    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Total IPs
    cursor.execute("SELECT COUNT(*) FROM bad_ips")
    total_ips = cursor.fetchone()[0]

    # Countries affected
    cursor.execute(
        "SELECT COUNT(DISTINCT country) FROM ip_geolocation WHERE country IS NOT NULL"
    )
    countries = cursor.fetchone()[0]

    # Top countries
    cursor.execute(
        """
        SELECT country, COUNT(*) as count 
        FROM ip_geolocation 
        WHERE country IS NOT NULL
        GROUP BY country 
        ORDER BY count DESC 
        LIMIT 15
    """
    )
    top_countries = cursor.fetchall()

    # Top cities
    cursor.execute(
        """
        SELECT city, country, COUNT(*) as count 
        FROM ip_geolocation 
        WHERE city IS NOT NULL AND country IS NOT NULL
        GROUP BY city, country
        ORDER BY count DESC 
        LIMIT 10
    """
    )
    top_cities = cursor.fetchall()

    # Average threat level
    cursor.execute("SELECT AVG(severity), MAX(severity), MIN(severity) FROM bad_ips")
    severity_stats = cursor.fetchone()

    conn.close()

    return {
        "total_ips": total_ips,
        "countries": countries,
        "top_countries": top_countries,
        "top_cities": top_cities,
        "severity_avg": severity_stats[0],
        "severity_max": severity_stats[1],
        "severity_min": severity_stats[2],
        "update_time": datetime.now().isoformat(),
    }


def create_country_chart(stats):
    """Create country distribution chart as PNG image with polished styling"""
    if not stats or not stats["top_countries"]:
        return False
    if not _plotting_ready():
        print("Matplotlib not available; skipping country chart")
        return False
    assert plt is not None and np is not None
    try:
        countries = [c[0] for c in stats["top_countries"]]
        counts = [c[1] for c in stats["top_countries"]]

        x = np.arange(len(countries))
        max_count = max(counts) if counts else 1
        # Smooth gradient from light to deep crimson based on relative height
        cmap_pinklime = (
            plt.cm.get_cmap("PiYG") if hasattr(plt.cm, "get_cmap") else plt.cm.RdYlGn
        )
        colors = cmap_pinklime(0.3 + 0.7 * (np.array(counts) / max_count))

        fig, ax = plt.subplots(figsize=(14, 7))
        bars = ax.bar(x, counts, color=colors, edgecolor="#7a0c0c", linewidth=1.2)

        # Value labels with subtle outline for readability
        for i, bar_obj in enumerate(bars):
            h = bar_obj.get_height()
            txt = ax.text(
                bar_obj.get_x() + bar_obj.get_width() / 2.0,
                h,
                f"{int(h):,}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                color="#1f1f1f",
            )
            txt.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])

        ax.set_xticks(x)
        ax.set_xticklabels(countries, rotation=35, ha="right")
        ax.set_xlabel("Country")
        ax.set_ylabel("Number of Malicious IPs")
        ax.set_title("Top 15 Countries with Malicious IPs", pad=16)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.set_facecolor("#f7f7f9")

        plt.tight_layout()
        charts_path = Path("data/charts")
        charts_path.mkdir(exist_ok=True)
        plt.savefig(str(charts_path / "countries.png"), bbox_inches="tight")
        plt.close()

        print("Country chart created")
        return True
    except Exception as e:
        print(f"Error creating country chart: {e}")
        return False


def create_severity_chart(stats):
    """Create severity distribution chart as PNG image with polished styling"""
    if not _plotting_ready():
        print("Matplotlib not available; skipping severity chart")
        return False
    assert plt is not None and np is not None
    try:
        db_path = Path("data/badips.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM bad_ips
            GROUP BY severity
            ORDER BY severity
        """
        )
        severity_data = cursor.fetchall()
        conn.close()

        if not severity_data:
            return False

        severities = [int(s[0]) for s in severity_data]
        counts = [int(s[1]) for s in severity_data]
        x = np.arange(len(severities))

        # Semantic palette from low->extreme
        base_palette = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#8e0000"]
        colors = base_palette[: len(severities)]

        fig, ax = plt.subplots(figsize=(12, 7))
        bars = ax.bar(x, counts, color=colors, edgecolor="#333", linewidth=1.0)

        # Labels with outline
        for bar_obj in bars:
            h = bar_obj.get_height()
            t = ax.text(
                bar_obj.get_x() + bar_obj.get_width() / 2.0,
                h,
                f"{int(h):,}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
                color="#1f1f1f",
            )
            t.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])

        level_names = ["Low", "Medium", "High", "Critical", "Extreme"]
        tick_labels = [
            (
                f"Level {s}\n({level_names[s-1]})"
                if 1 <= s <= len(level_names)
                else f"Level {s}"
            )
            for s in severities
        ]
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels)

        ax.set_xlabel("Threat Severity Level")
        ax.set_ylabel("Number of IPs")
        ax.set_title("Malicious IP Threat Severity Distribution", pad=16)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.set_facecolor("#f7f7f9")

        plt.tight_layout()
        charts_path = Path("data/charts")
        charts_path.mkdir(exist_ok=True)
        plt.savefig(str(charts_path / "severity.png"), bbox_inches="tight")
        plt.close()

        print("Severity chart created")
        return True
    except Exception as e:
        print(f"Error creating severity chart: {e}")
        return False


def create_geo_map(stats):
    """Create geographic distribution chart as PNG image with polished styling"""
    try:
        db_path = Path("data/badips.db")
        conn = sqlite3.connect(str(db_path))

        query = """
            SELECT country, COUNT(*) as count
            FROM ip_geolocation
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 20
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return False

        # Matplotlib horizontal bar chart for top 20 countries with gradient and labels
        fig, ax = plt.subplots(figsize=(14, 10))

        counts = df["count"].to_numpy()
        labels = df["country"].tolist()
        y = np.arange(len(labels))
        max_count = counts.max() if len(counts) else 1
        colors = plt.cm.Reds(0.35 + 0.65 * (counts / max_count))

        bars = ax.barh(y, counts, color=colors, edgecolor="#7a0c0c", linewidth=1.2)

        # Labels at bar end with outline
        for i, bar_obj in enumerate(bars):
            width = bar_obj.get_width()
            txt = ax.text(
                width,
                bar_obj.get_y() + bar_obj.get_height() / 2.0,
                f" {int(width):,}",
                ha="left",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="#1f1f1f",
            )
            txt.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])

        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Number of Malicious IPs")
        ax.set_ylabel("Country")
        ax.set_title("Global Distribution of Malicious IPs (Top 20 Countries)", pad=16)
        ax.grid(axis="x")
        ax.invert_yaxis()
        ax.set_axisbelow(True)
        ax.set_facecolor("#f7f7f9")

        plt.tight_layout()

        charts_path = Path("data/charts")
        charts_path.mkdir(exist_ok=True)
        plt.savefig(str(charts_path / "worldmap.png"), bbox_inches="tight")
        plt.close()

        print("Geographic map created")
        return True
    except Exception as e:
        print(f"Error creating geographic map: {e}")
        return False


def create_world_pins_map(stats):
    """Create a world map with colored pins per country using Plotly scattergeo."""
    try:
        db_path = Path("data/badips.db")
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT country, AVG(latitude) AS lat, AVG(longitude) AS lon, COUNT(*) AS cnt
            FROM ip_geolocation
            WHERE country IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY country
            ORDER BY cnt DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            return False

        # Size scaling (area-based): improve legibility across counts
        counts = df["cnt"]
        sizeref = (counts.max() / 40.0) if counts.max() else 1
        texts = [
            f"{row['country']}: {int(row['cnt']):,} IPs" for _, row in df.iterrows()
        ]

        fig = go.Figure(
            go.Scattergeo(
                lon=df["lon"],
                lat=df["lat"],
                text=texts,
                mode="markers",
                marker=dict(
                    size=(counts / sizeref).clip(lower=6),
                    color=counts,
                    colorscale="Inferno",
                    reversescale=False,
                    colorbar=dict(title="IPs"),
                    line=dict(width=0.6, color="#2b1e16"),
                    opacity=0.9,
                ),
                hovertemplate="%{text}<extra></extra>",
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#12100e",
            plot_bgcolor="#12100e",
            margin=dict(l=20, r=20, t=40, b=20),
            geo=dict(
                showland=True,
                landcolor="#1e1a16",
                showcountries=True,
                countrycolor="#6b4e2e",
                showocean=True,
                oceancolor="#0d0b0a",
                coastlinecolor="#6b4e2e",
                projection_type="natural earth",
            ),
            title=dict(text="Global Malicious IPs — Country Pins", x=0.5),
        )

        charts_path = Path("data/charts")
        charts_path.mkdir(exist_ok=True)
        out_png = charts_path / "map_pins.png"
        try:
            fig.write_image(str(out_png), width=1400, height=800, scale=2)
            print("World pins map created (PNG)")
        except Exception as e:
            # Fallback to HTML if kaleido is unavailable
            out_html = charts_path / "map_pins.html"
            fig.write_html(str(out_html), include_plotlyjs="cdn")
            print(f"World pins map created (HTML fallback): {e}")
        return True
    except Exception as e:
        print(f"Error creating world pins map: {e}")
        return False


def update_readme(stats):
    """Update README with embedded chart images and statistics"""
    if not stats:
        print("No statistics available for README update")
        return

    readme_path = Path("README.md")

    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    def _get_repo_slug():
        try:
            git_config = Path(".git/config")
            if not git_config.exists():
                return None
            content = git_config.read_text(encoding="utf-8", errors="ignore")
            import re

            m = re.search(r"\[remote \"origin\"\][^\]]*url\s*=\s*(.+)", content)
            if not m:
                return None
            url = m.group(1).strip()
            if "github.com" not in url:
                return None
            url = url.replace("\n", "")
            if url.startswith("git@github.com:"):
                slug = url.split(":", 1)[1]
            else:
                slug = url.split("github.com/", 1)[1]
            slug = slug.replace(".git", "")
            return slug.strip()
        except Exception:
            return None

    repo_slug = _get_repo_slug()
    actions_badge = (
        f"https://github.com/{repo_slug}/actions/workflows/update-badip.yml/badge.svg"
        if repo_slug
        else None
    )
    views_badge = (
        f"https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2F{repo_slug}&title=Views&edge_flat=false&count_bg=%238A5A2B&title_bg=%2312100E&color=%23D7B377"
        if repo_slug
        else None
    )
    python_badge = (
        "https://img.shields.io/badge/Python-3.14-%233776AB?logo=python&logoColor=white"
    )
    gh_badge = "https://img.shields.io/badge/GitHub-Repo-%2312100E?logo=github&logoColor=white&labelColor=%23A67C52&color=%2312100E"

    readme_content = f"""
<div align="center">

    <img alt="GitHub" src="https://raw.githubusercontent.com/edent/SuperTinyIcons/master/images/svg/github.svg" width="64" height="64" />

    <h1>Bad IP Database</h1>

    <p>
        <img alt="Python" src="{python_badge}" />
        <img alt="GitHub Repo" src="{gh_badge}" />
        {f'<img alt="Actions" src="{actions_badge}" />' if actions_badge else ''}
        {f'<img alt="Views" src="{views_badge}" />' if views_badge else ''}
    </p>

    <em>Automatically updated malicious IP database with geolocation mapping and threat analysis.</em>

    <p><strong>Data updated every Sunday at midnight UTC.</strong></p>

</div>

---

## Database Statistics

- **Total Malicious IPs**: {stats['total_ips']:,}
- **Countries Affected**: {stats['countries']}
- **Average Threat Severity**: {stats['severity_avg']:.2f}/5
- **Last Updated**: {update_time}

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

**Data Source**: [Stamparm/Ipsum](https://github.com/stamparm/ipsum) | **Last Generated**: {update_time}
"""

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("README updated with embedded chart images")


def main():
    """Main visualization generation function"""
    print("Generating visualizations and updating documentation...")

    # Apply consistent theme
    apply_viz_theme()
    apply_steampunk_theme()

    stats = get_statistics()

    if not stats:
        print("No database found. Run process_badips.py first.")
        return

    print("\nDatabase Statistics:")
    print(f"  Total IPs: {stats['total_ips']:,}")
    print(f"  Countries: {stats['countries']}")
    print(f"  Avg Severity: {stats['severity_avg']:.2f}/5")

    print("\nCreating visualizations...")
    create_country_chart(stats)
    create_geo_map(stats)
    create_world_pins_map(stats)
    create_steampunk_dashboard(stats)
    print("\nUpdating README statistics (safe update)...")
    # Use the lightweight updater that patches only the Database Statistics block
    try:
        subprocess.run([sys.executable, "scripts/update_readme.py"], check=False)
    except Exception as e:
        print(f"Failed to run update_readme_stats.py: {e}")

    print("\nVisualization generation completed!")


if __name__ == "__main__":
    main()
