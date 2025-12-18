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
    """Apply a cohesive, dark neon Matplotlib theme for all charts."""
    if plt is None:
        return
    assert plt is not None
    try:
        plt.rcParams.update(
            {
                "figure.facecolor": "#0a0a14",
                "axes.facecolor": "#1a1a2e",
                "axes.edgecolor": "#00d4ff",
                "axes.grid": True,
                "grid.color": "#2a2a4e",
                "grid.linestyle": "--",
                "grid.alpha": 0.25,
                "axes.titlesize": 16,
                "axes.labelsize": 13,
                "xtick.labelsize": 10,
                "ytick.labelsize": 10,
                "xtick.color": "#00d4ff",
                "ytick.color": "#00d4ff",
                "axes.labelcolor": "#00d4ff",
                "text.color": "#ffffff",
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
    """Return a list of n vibrant cyberattack colors: oranges, pinks, blues, yellows."""
    base = ["#ff6b35", "#ff1493", "#00d4ff", "#ffff00", "#ff00ff", "#ffa500", "#1e90ff", "#ff69b4", "#00ffff", "#ffd700"]
    if n <= len(base):
        return base[:n]
    colors = []
    for i in range(n):
        c = base[i % len(base)]
        colors.append(c)
    return colors


def apply_gradient_background(fig, ax):
    """Apply a deep blue gradient background (corner to corner) to the figure and axes."""
    # Create gradient from blue (top-left) to darker blue (bottom-right)
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    gradient = np.vstack([gradient] * 256)
    
    # Deep blue gradient: from #0066ff (top-left) to #000033 (bottom-right)
    ax.imshow(gradient, aspect='auto', cmap='Blues_r', alpha=0.8, extent=[ax.get_xlim()[0], ax.get_xlim()[1], 
                                                                            ax.get_ylim()[0], ax.get_ylim()[1]],
              zorder=-1)
    fig.patch.set_facecolor('#0a0a2e')
    ax.set_facecolor('#0a0a2e')


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

        # Build figure with 2x2 layout and deep blue gradient background
        fig = plt.figure(figsize=(16, 9), facecolor="#0a0a2e")
        gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.28)

        # Add gradient background from deep blue (top-left) to darker blue (bottom-right)
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        gradient = np.vstack((gradient, gradient))
        extent = [0, 1, 0, 1]
        
        # Create invisible axis for gradient
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(gradient, extent=extent, aspect="auto", cmap="Blues_r", alpha=0.4, zorder=0)
        ax_bg.set_xlim(0, 1)
        ax_bg.set_ylim(0, 1)
        ax_bg.axis("off")

        # A1: Donut chart for severity

        ax1 = fig.add_subplot(gs[0, 0])
        if sev_counts:
            level_names = ["Low", "Medium", "High", "Critical", "Extreme"]
            labels = [
                f"{level_names[s-1] if 1 <= s <= 5 else s}\n{sev_counts[i]:,}"
                for i, s in enumerate(severities)
            ]
            # Vibrant orange, pink, purple palette
            bright_palette = ["#ff6b35", "#ff1493", "#ff69b4", "#da70d6", "#ba55d3"]
            colors = bright_palette[: len(severities)] if len(severities) <= 5 else bright_palette
            _pie = ax1.pie(
                sev_counts,
                startangle=90,
                wedgeprops=dict(width=0.38, edgecolor="#00d4ff", linewidth=2),
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
                color="#00d4ff",
            )
            # Add labels outside with leader lines
            ang = 0
            total = sum(sev_counts)
            theta = np.cumsum([0] + [v / total * 360 for v in sev_counts])
            for i, w in enumerate(wedges):
                angle = np.deg2rad((theta[i] + theta[i + 1]) / 2)
                x = 1.1 * np.cos(angle)
                y = 1.1 * np.sin(angle)
                t = ax1.text(x, y, labels[i], ha="center", va="center", fontsize=9, color="#ffffff")
                t.set_path_effects([pe.withStroke(linewidth=2, foreground="#0a0a2e")])
            ax1.set_title("Threat Severity", color="#ffff00", fontweight="bold")
            ax1.set_facecolor("#0a0a2e")
        else:
            ax1.text(0.5, 0.5, "No severity data", ha="center", va="center")
            ax1.set_axis_off()

        # A2: Top countries bar
        ax2 = fig.add_subplot(gs[0, 1])
        if country_counts:
            x = np.arange(len(countries))
            max_c = max(country_counts)
            # Vibrant orange, pink, blue, yellow palette
            colors = ["#ff6b35", "#ff1493", "#1e90ff", "#ffff00", "#ffa500", "#ff69b4", "#00d4ff", "#da70d6"] * ((len(countries) // 8) + 1)
            colors = colors[: len(countries)]
            bars = ax2.bar(
                x, country_counts, color=colors, edgecolor="#00d4ff", linewidth=1.2
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
                    color="#ffffff",
                )
                tt.set_path_effects([pe.withStroke(linewidth=1.5, foreground="#0a0a2e")])
            ax2.set_xticks(x)
            ax2.set_xticklabels(countries, rotation=35, ha="right", color="#00d4ff")
            ax2.set_title("Top Countries", color="#ffff00", fontweight="bold")
            ax2.set_ylabel("IPs", color="#00d4ff")
            ax2.set_facecolor("#0a0a2e")
            ax2.tick_params(colors="#00d4ff")
        else:
            ax2.text(0.5, 0.5, "No country data", ha="center", va="center")
            ax2.set_axis_off()

        # B1: Top ASNs horizontal bars
        ax3 = fig.add_subplot(gs[1, 0])
        if asn_counts:
            y = np.arange(len(asns))
            # Vibrant orange, pink, blue, yellow palette
            colors = ["#ff6b35", "#ff1493", "#1e90ff", "#ffff00", "#ffa500", "#ff69b4", "#00d4ff", "#da70d6"] * ((len(asns) // 8) + 1)
            colors = colors[: len(asns)]
            bars = ax3.barh(
                y, asn_counts, color=colors, edgecolor="#00d4ff", linewidth=1.2
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
                    color="#ffffff",
                )
                tt.set_path_effects([pe.withStroke(linewidth=1.5, foreground="#0a0a2e")])
            ax3.set_yticks(y)
            ax3.set_yticklabels(asns, color="#00d4ff")
            ax3.set_title("Top ASNs", color="#ff1493", fontweight="bold")
            ax3.set_xlabel("IPs", color="#00d4ff")
            ax3.set_facecolor("#0a0a2e")
            ax3.tick_params(colors="#00d4ff")
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
            # Vibrant orange, pink, blue, yellow palette
            colors = ["#ff6b35", "#ff1493", "#1e90ff", "#ffff00", "#ffa500", "#ff69b4", "#00d4ff", "#da70d6"] * ((len(names) // 8) + 1)
            colors = colors[: len(names)]
            ax4.scatter(x, vals, s=sizes, c=colors, edgecolor="#00d4ff", linewidth=1.2)
            for i, v in enumerate(vals):
                tt = ax4.text(
                    x[i], v, f"{int(v):,}", ha="center", va="bottom", fontsize=8, color="#ffffff"
                )
                tt.set_path_effects([pe.withStroke(linewidth=1.5, foreground="#0a0a2e")])
            ax4.set_xticks(x)
            ax4.set_xticklabels(names, rotation=35, ha="right", color="#00d4ff")
            ax4.set_title("Top Cities (bubble size = IP count)", color="#ff1493", fontweight="bold")
            ax4.set_ylabel("IPs", color="#00d4ff")
            ax4.set_facecolor("#0a0a2e")
            ax4.tick_params(colors="#00d4ff")
        else:
            ax4.text(0.5, 0.5, "No city data", ha="center", va="center")
            ax4.set_axis_off()

        fig.suptitle(
            "Global Malicious IPs — Neon Dashboard",
            color="#ff1493",
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


def create_cyber_attack_origins_dashboard(stats):
    """Create a dashboard focused on cyber attack origins by country."""
    if not _plotting_ready():
        print("Matplotlib not available; skipping cyber attack origins dashboard")
        return False
    assert plt is not None and np is not None
    try:
        db_path = Path("data/badips.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Top 15 attacking countries
        cursor.execute(
            """
            SELECT country, COUNT(*) as attack_count
            FROM ip_geolocation
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY attack_count DESC
            LIMIT 15
        """
        )
        country_data = cursor.fetchall()
        countries = [r[0] for r in country_data]
        attack_counts = [int(r[1]) for r in country_data]

        # Get severity breakdown for top 5 countries
        cursor.execute(
            """
            SELECT g.country, b.severity, COUNT(*) as cnt
            FROM ip_geolocation g
            JOIN bad_ips b ON g.ip = b.ip
            WHERE g.country IN (
                SELECT country FROM ip_geolocation
                WHERE country IS NOT NULL
                GROUP BY country
                ORDER BY COUNT(*) DESC
                LIMIT 5
            )
            GROUP BY g.country, b.severity
            ORDER BY g.country, b.severity
        """
        )
        severity_by_country = cursor.fetchall()

        # Calculate total attacks and find #1 attacker
        cursor.execute(
            """
            SELECT COUNT(*) as total FROM ip_geolocation WHERE country IS NOT NULL
        """
        )
        total_attacks = cursor.fetchone()[0]
        
        top_country = countries[0] if countries else "Unknown"
        top_country_count = attack_counts[0] if attack_counts else 0
        top_country_pct = (top_country_count / total_attacks * 100) if total_attacks > 0 else 0

        conn.close()

        # Create figure with gradient background
        fig = plt.figure(figsize=(18, 10), facecolor="#0a0a2e")
        gs = fig.add_gridspec(2, 3, hspace=0.4, wspace=0.35)

        # Add gradient background
        ax_bg = fig.add_axes([0, 0, 1, 1])
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        gradient = np.vstack([gradient] * 256)
        ax_bg.imshow(gradient, extent=[0, 1, 0, 1], aspect="auto", cmap="cool", alpha=0.5, zorder=0)
        ax_bg.set_xlim(0, 1)
        ax_bg.set_ylim(0, 1)
        ax_bg.axis("off")

        # A1: Top 15 attacking countries (horizontal bar)
        ax1 = fig.add_subplot(gs[:, 0])
        y_pos = np.arange(len(countries))
        colors = ["#ff1493", "#ff6b35", "#1e90ff", "#ffff00", "#ff00ff", "#ffa500"] * 3
        colors = colors[:len(countries)]
        bars = ax1.barh(y_pos, attack_counts, color=colors, edgecolor="#00d4ff", linewidth=1.5)
        
        # Highlight #1 country
        if len(bars) > 0:
            bars[0].set_color("#ff0080")
            bars[0].set_linewidth(2.5)
        
        for i, (bar, count) in enumerate(zip(bars, attack_counts)):
            ax1.text(count, bar.get_y() + bar.get_height()/2, 
                    f" {count:,}", va="center", ha="left", 
                    color="#ffffff", fontsize=10, fontweight="bold")
        
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(countries, color="#00d4ff", fontsize=11)
        ax1.set_xlabel("Malicious IPs Originated", color="#00d4ff", fontsize=12)
        ax1.set_title("Top 15 Cyber Attack Origin Countries", color="#ff1493", fontsize=14, fontweight="bold", pad=15)
        ax1.invert_yaxis()
        ax1.set_facecolor("#0a0a2e")
        ax1.tick_params(colors="#00d4ff")
        ax1.grid(axis="x", color="#2a2a4e", alpha=0.3)

        # A2: #1 Attacker callout
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.text(0.5, 0.7, f"🔴 #1 Attack Origin", ha="center", va="center", 
                fontsize=16, color="#ff0080", fontweight="bold")
        ax2.text(0.5, 0.5, top_country, ha="center", va="center", 
                fontsize=32, color="#ffff00", fontweight="bold")
        ax2.text(0.5, 0.3, f"{top_country_count:,} Malicious IPs", ha="center", va="center", 
                fontsize=14, color="#00d4ff")
        ax2.text(0.5, 0.15, f"{top_country_pct:.1f}% of Global Attacks", ha="center", va="center", 
                fontsize=12, color="#ff69b4")
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.set_facecolor("#0a0a2e")
        ax2.axis("off")

        # A3: Attack concentration pie
        ax3 = fig.add_subplot(gs[0, 2])
        top5_total = sum(attack_counts[:5]) if len(attack_counts) >= 5 else sum(attack_counts)
        other_total = total_attacks - top5_total
        pie_data = attack_counts[:5] + ([other_total] if other_total > 0 else [])
        pie_labels = countries[:5] + (["Other"] if other_total > 0 else [])
        pie_colors = ["#ff1493", "#ff6b35", "#1e90ff", "#ffff00", "#ff00ff", "#888888"]
        
        wedges, texts, autotexts = ax3.pie(pie_data, labels=pie_labels, autopct="%1.1f%%",
                                            colors=pie_colors[:len(pie_data)],
                                            wedgeprops=dict(edgecolor="#00d4ff", linewidth=1.5),
                                            textprops=dict(color="#ffffff", fontsize=10))
        ax3.set_title("Attack Concentration\n(Top 5 + Others)", color="#00d4ff", fontsize=12, fontweight="bold")
        ax3.set_facecolor("#0a0a2e")

        # B: Severity breakdown for top 5 countries (stacked bar)
        ax4 = fig.add_subplot(gs[1, 1:])
        
        # Organize severity data
        top5_countries = countries[:5]
        severity_dict = {c: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0} for c in top5_countries}
        for country, severity, count in severity_by_country:
            if country in top5_countries and severity in severity_dict[country]:
                severity_dict[country][severity] = count
        
        x = np.arange(len(top5_countries))
        width = 0.6
        severity_colors = ["#00ff88", "#ffff00", "#ffa500", "#ff69b4", "#ff0080"]
        severity_labels = ["Low", "Medium", "High", "Critical", "Extreme"]
        
        bottom = np.zeros(len(top5_countries))
        for sev in range(1, 6):
            counts = [severity_dict[c][sev] for c in top5_countries]
            bars = ax4.bar(x, counts, width, bottom=bottom, label=severity_labels[sev-1],
                          color=severity_colors[sev-1], edgecolor="#00d4ff", linewidth=1)
            bottom += counts
        
        ax4.set_xticks(x)
        ax4.set_xticklabels(top5_countries, color="#00d4ff", fontsize=11)
        ax4.set_ylabel("Number of Malicious IPs", color="#00d4ff", fontsize=11)
        ax4.set_title("Threat Severity Distribution by Top 5 Attack Origins", 
                     color="#ff1493", fontsize=13, fontweight="bold", pad=10)
        ax4.legend(loc="upper right", framealpha=0.9, facecolor="#0a0a2e", edgecolor="#00d4ff")
        ax4.set_facecolor("#0a0a2e")
        ax4.tick_params(colors="#00d4ff")
        ax4.grid(axis="y", color="#2a2a4e", alpha=0.3)

        fig.suptitle(
            "Cyber Attack Origins — Global Threat Landscape",
            color="#ff1493",
            fontsize=20,
            fontweight="bold",
            y=0.98
        )

        charts_path = Path("data/charts")
        charts_path.mkdir(exist_ok=True)
        out_path = charts_path / "attack_origins.png"
        fig.savefig(str(out_path), bbox_inches="tight", facecolor="#0a0a2e")
        plt.close(fig)

        print("Cyber attack origins dashboard created")
        return True
    except Exception as e:
        print(f"Error creating cyber attack origins dashboard: {e}")
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
        # Use vibrant palette for better color separation
        palette_colors = steampunk_palette(len(countries))

        fig, ax = plt.subplots(figsize=(14, 7), facecolor="#0a0a2e")
        bars = ax.bar(x, counts, color=palette_colors, edgecolor="#00ffff", linewidth=1.5)

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
        ax.set_xticklabels(countries, rotation=35, ha="right", color="#00d4ff")
        ax.set_xlabel("Country", color="#00d4ff")
        ax.set_ylabel("Number of Malicious IPs", color="#00d4ff")
        ax.set_title("Top 15 Countries with Malicious IPs", pad=16, color="#ffff00", fontweight="bold")
        ax.grid(axis="y", color="#2a2a4e", alpha=0.3)
        ax.set_axisbelow(True)
        ax.set_facecolor("#0a0a2e")

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

        # Vibrant severity palette: green -> yellow -> orange -> pink -> red
        base_palette = ["#00ff88", "#ffff00", "#ffa500", "#ff1493", "#ff0000"]
        colors = base_palette[: len(severities)]

        fig, ax = plt.subplots(figsize=(12, 7), facecolor="#0a0a2e")
        bars = ax.bar(x, counts, color=colors, edgecolor="#00ffff", linewidth=1.5)

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
        ax.set_xticklabels(tick_labels, color="#00d4ff")

        ax.set_xlabel("Threat Severity Level", color="#00d4ff")
        ax.set_ylabel("Number of IPs", color="#00d4ff")
        ax.set_title("Malicious IP Threat Severity Distribution", pad=16, color="#ff1493", fontweight="bold")
        ax.grid(axis="y", color="#2a2a4e", alpha=0.3)
        ax.set_axisbelow(True)
        ax.set_facecolor("#0a0a2e")

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

        # Matplotlib horizontal bar chart for top 20 countries with vibrant colors
        fig, ax = plt.subplots(figsize=(14, 10), facecolor="#0a0a2e")

        counts = df["count"].to_numpy()
        labels = df["country"].tolist()
        y = np.arange(len(labels))
        max_count = counts.max() if len(counts) else 1
        palette_colors = steampunk_palette(len(labels))

        bars = ax.barh(y, counts, color=palette_colors, edgecolor="#00ffff", linewidth=1.5)

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
        ax.set_yticklabels(labels, color="#00d4ff")
        ax.set_xlabel("Number of Malicious IPs", color="#00d4ff")
        ax.set_ylabel("Country", color="#00d4ff")
        ax.set_title("Global Distribution of Malicious IPs (Top 20 Countries)", pad=16, color="#ffff00", fontweight="bold")
        ax.grid(axis="x", color="#2a2a4e", alpha=0.3)
        ax.invert_yaxis()
        ax.set_axisbelow(True)
        ax.set_facecolor("#0a0a2e")

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

        # Map IP counts to neon colors cyclically
        neon_colors = ["#ff6b35", "#00d4ff", "#ff00ff", "#00ff88", "#ffaa00", "#ff0080", "#00ffff", "#ffff00"]
        marker_colors = [neon_colors[i % len(neon_colors)] for i in range(len(df))]

        fig = go.Figure(
            go.Scattergeo(
                lon=df["lon"],
                lat=df["lat"],
                text=texts,
                mode="markers",
                marker=dict(
                    size=(counts / sizeref).clip(lower=6),
                    color=marker_colors,
                    line=dict(width=1.0, color="#00d4ff"),
                    opacity=0.95,
                ),
                hovertemplate="%{text}<extra></extra>",
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a14",
            plot_bgcolor="#0a0a14",
            margin=dict(l=20, r=20, t=40, b=20),
            geo=dict(
                showland=True,
                landcolor="#1a1a2e",
                showcountries=True,
                countrycolor="#3a3a5e",
                showocean=True,
                oceancolor="#0a0a14",
                coastlinecolor="#4a4a7e",
                projection_type="natural earth",
            ),
            title=dict(text="Global Malicious IPs — Country Pins", x=0.5, font=dict(color="#ffaa00", size=18)),
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


def create_hn_cyberattack_pie():
    """Create a pie chart from Hacker News cyber attack mentions by country"""
    if not _plotting_ready():
        print("Matplotlib not available; skipping HN pie chart")
        return False
    assert plt is not None and np is not None
    
    try:
        # Load HN mentions data
        hn_data_path = Path("data/hn_country_mentions.json")
        if not hn_data_path.exists():
            print("HN data not found. Run scripts/hacker_news.py first.")
            return False
        
        import json
        with open(hn_data_path, 'r', encoding='utf-8') as f:
            hn_data = json.load(f)
        
        countries_data = hn_data.get("countries", {})
        if not countries_data:
            print("No HN country data available")
            return False
        
        # Extract top 10 countries by mentions
        sorted_countries = sorted(
            countries_data.items(), 
            key=lambda x: x[1]["mentions"], 
            reverse=True
        )[:10]
        
        labels = [f"{data['country']}\n{data['mentions']}" for code, data in sorted_countries]
        values = [data["mentions"] for code, data in sorted_countries]
        
        # Apply theme and create figure with gradient background
        apply_viz_theme()
        fig = plt.figure(figsize=(12, 8), facecolor="#0a0a2e")
        
        # Add gradient background
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack([gradient] * 256)
        
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.imshow(gradient, aspect='auto', cmap='Blues_r', alpha=0.6, extent=[0, 1, 0, 1], zorder=0)
        ax_bg.set_xlim(0, 1)
        ax_bg.set_ylim(0, 1)
        ax_bg.axis('off')
        
        # Create pie chart
        ax = fig.add_subplot(111)
        ax.set_facecolor('none')
        
        # Vibrant color palette
        colors = steampunk_palette(len(values))
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops=dict(edgecolor='#00d4ff', linewidth=2),
            textprops=dict(color="#ffffff", fontsize=11, weight='bold')
        )
        
        # Add white stroke to percentage text for readability
        for autotext in autotexts:
            autotext.set_path_effects([pe.withStroke(linewidth=2, foreground="#0a0a2e")])
        
        # Add white stroke to label text
        for text in texts:
            text.set_path_effects([pe.withStroke(linewidth=2, foreground="#0a0a2e")])
        
        ax.set_title(
            "Distribution of Cyberattack Traffic by Nation\n% of hacking activity originating in each state",
            color="#ffff00",
            fontsize=16,
            fontweight="bold",
            pad=20
        )
        
        # Add source attribution
        last_updated = hn_data.get("last_updated", "Unknown")
        update_date = last_updated.split('T')[0] if 'T' in last_updated else last_updated
        fig.text(
            0.5, 0.02,
            f"Source: Hacker News Search API (Last 180 days) | Generated: {update_date}",
            ha='center',
            fontsize=10,
            color='#00d4ff'
        )
        
        charts_path = Path("data/charts")
        charts_path.mkdir(exist_ok=True)
        plt.savefig(str(charts_path / "hn_cyberattack_pie.png"), bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close()
        
        print("HN cyber attack pie chart created")
        return True
    except Exception as e:
        print(f"Error creating HN pie chart: {e}")
        return False


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
    create_cyber_attack_origins_dashboard(stats)
    create_hn_cyberattack_pie()
    print("\nUpdating README statistics (safe update)...")
    # Use the lightweight updater that patches only the Database Statistics block
    try:
        subprocess.run([sys.executable, "scripts/update_readme.py"], check=False)
    except Exception as e:
        print(f"Failed to run update_readme_stats.py: {e}")

    print("\nVisualization generation completed!")


if __name__ == "__main__":
    main()
