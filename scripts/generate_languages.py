#!/usr/bin/env python3
"""Generate a compact SVG of language usage across the user's public repositories."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "bojanzdelar")
TOKEN = os.environ.get("GITHUB_TOKEN")
EXCLUDED_LANGUAGES = {"Jupyter Notebook"}
COLORS = [
    "#88c0d0", "#81a1c1", "#5e81ac", "#a3be8c",
    "#b48ead", "#ebcb8b", "#d08770", "#8fbcbb",
]
WIDTH = 640
LEFT = 155
RIGHT = 70
BAR_WIDTH = WIDTH - LEFT - RIGHT


def github_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "top-languages-readme-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_languages():
    totals = Counter()
    page = 1
    while True:
        query = urllib.parse.urlencode({
            "type": "owner", "per_page": 100, "page": page
        })
        repos = github_json(
            f"https://api.github.com/users/{USERNAME}/repos?{query}"
        )
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            if repo.get("name", "").lower() == USERNAME.lower():
                continue
            languages = github_json(repo["languages_url"])
            for language, byte_count in languages.items():
                if language not in EXCLUDED_LANGUAGES:
                    totals[language] += byte_count
        if len(repos) < 100:
            break
        page += 1
    return totals


def render_svg(totals):
    ranked = totals.most_common(8)
    total_bytes = sum(totals.values())
    rows = []
    y = 55

    if not ranked or not total_bytes:
        rows.append(
            '<text x="320" y="125" text-anchor="middle" '
            'fill="#d8dee9" font-size="15">No language data available</text>'
        )
        height = 180
    else:
        for index, (language, byte_count) in enumerate(ranked):
            percentage = byte_count / total_bytes * 100
            bar_length = BAR_WIDTH * percentage / 100
            color = COLORS[index % len(COLORS)]
            rows.append(
                f'<text x="{LEFT - 14}" y="{y + 4}" text-anchor="end" '
                f'fill="#d8dee9" font-size="13">{escape(language)}</text>'
            )
            rows.append(
                f'<rect x="{LEFT}" y="{y - 10}" width="{BAR_WIDTH}" '
                f'height="10" rx="5" fill="#3b4252"/>'
            )
            rows.append(
                f'<rect x="{LEFT}" y="{y - 10}" width="{bar_length:.1f}" '
                f'height="10" rx="5" fill="{color}"/>'
            )
            rows.append(
                f'<text x="{LEFT + BAR_WIDTH + 12}" y="{y + 4}" '
                f'fill="#d8dee9" font-size="12">{percentage:.1f}%</text>'
            )
            y += 30
        height = y + 15

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Top programming languages across public GitHub repositories">
  <rect width="100%" height="100%" rx="12" fill="#2e3440"/>
  <text x="24" y="28" fill="#eceff4" font-family="Arial, sans-serif" font-size="15" font-weight="600">Top languages</text>
  <g font-family="Arial, sans-serif">
    {"".join(rows)}
  </g>
</svg>
'''


def main():
    svg = render_svg(collect_languages())
    output = Path("assets/top-languages.svg")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
