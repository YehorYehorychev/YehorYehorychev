#!/usr/bin/env python3
"""Generate a self-hosted GitHub activity graph for the profile README."""
import json
import math
import os
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "YehorYehorychev"
DAYS = 31
today = date.today()
start = today - timedelta(days=DAYS - 1)
query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""
payload = json.dumps({
    "query": query,
    "variables": {
        "login": USERNAME,
        "from": start.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z",
    },
}).encode()
req = Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Content-Type": "application/json",
        "User-Agent": "profile-activity-graph",
    },
)
with urlopen(req, timeout=30) as response:
    data = json.load(response)
if data.get("errors"):
    raise RuntimeError(str(data["errors"]))
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
counts = {
    day["date"]: day["contributionCount"]
    for week in weeks
    for day in week["contributionDays"]
}
dates = [start + timedelta(days=i) for i in range(DAYS)]
values = [counts.get(d.isoformat(), 0) for d in dates]
width, height = 860, 270
left, right, top, bottom = 54, 24, 45, 50
plot_w, plot_h = width - left - right, height - top - bottom
max_value = max(max(values), 4)
y_max = max(4, math.ceil(max_value / 4) * 4)
coordinates = [
    (left + i * plot_w / (DAYS - 1), top + plot_h * (1 - v / y_max))
    for i, v in enumerate(values)
]
points = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
area = f"{left},{top + plot_h} " + points + f" {left + plot_w},{top + plot_h}"
svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contributions over the last {DAYS} days">',
    '<rect width="100%" height="100%" rx="12" fill="#1a1b27"/>',
    '<text x="24" y="27" font-size="17" font-family="Arial,sans-serif" font-weight="600" fill="#70a5fd">GitHub Activity · Last 31 Days</text>',
]
for i in range(5):
    value = y_max * i / 4
    y = top + plot_h * (1 - i / 4)
    svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#34364b" stroke-width="1"/>')
    svg.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" fill="#a9b1d6" font-size="11" font-family="Arial,sans-serif">{value:g}</text>')
for i in range(0, DAYS, 5):
    x = coordinates[i][0]
    svg.append(f'<text x="{x:.1f}" y="{top + plot_h + 22}" text-anchor="middle" fill="#a9b1d6" font-size="11" font-family="Arial,sans-serif">{dates[i].strftime("%b %d")}</text>')
svg.extend([
    f'<polygon points="{area}" fill="#70a5fd" fill-opacity=".15"/>',
    f'<polyline points="{points}" fill="none" stroke="#70a5fd" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>',
])
for x, y in coordinates:
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#70a5fd"/>')
svg.extend([
    f'<text x="{left}" y="{height - 10}" fill="#a9b1d6" font-size="11" font-family="Arial,sans-serif">Daily public contributions · Updated {today.isoformat()} UTC</text>',
    '</svg>',
])
Path("assets").mkdir(parents=True, exist_ok=True)
Path("assets/contribution-graph.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")
