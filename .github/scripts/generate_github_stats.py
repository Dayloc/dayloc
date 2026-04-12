from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


API_BASE = "https://api.github.com"
USERNAME = os.environ.get("GITHUB_USERNAME", "Dayloc")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_DIR = Path("profile")

CARD_BG = "#0d1117"
CARD_BORDER = "#30363d"
TEXT_MAIN = "#e6edf3"
TEXT_MUTED = "#8b949e"
ACCENT = "#58a6ff"
ACCENT_2 = "#a371f7"
LANG_COLORS = [
    "#58a6ff",
    "#a371f7",
    "#3fb950",
    "#f78166",
    "#d2a8ff",
    "#ff7b72",
]


def github_get(url: str):
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", "dayloc-github-stats-generator")
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8")), response.headers


def fetch_user(username: str):
    payload, _ = github_get(f"{API_BASE}/users/{urllib.parse.quote(username)}")
    return payload


def fetch_repos(username: str):
    repos = []
    page = 1
    while True:
        payload, _ = github_get(
            f"{API_BASE}/users/{urllib.parse.quote(username)}/repos?per_page=100&page={page}&sort=updated"
        )
        if not payload:
            break
        repos.extend(payload)
        if len(payload) < 100:
            break
        page += 1
    return repos


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_stats_svg(user: dict, repos: list[dict]) -> str:
    public_repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)
    following = user.get("following", 0)
    stars = sum(repo.get("stargazers_count", 0) for repo in repos if not repo.get("fork"))
    forks = sum(repo.get("forks_count", 0) for repo in repos if not repo.get("fork"))

    items = [
        ("Repos públicos", str(public_repos)),
        ("Seguidores", str(followers)),
        ("Siguiendo", str(following)),
        ("Estrellas", str(stars)),
        ("Forks", str(forks)),
    ]

    metric_blocks = []
    for index, (label, value) in enumerate(items):
        col = index % 3
        row = index // 3
        x = 40 + col * 180
        y = 122 + row * 108
        metric_blocks.append(
            f"""
            <g>
              <rect x="{x}" y="{y}" width="152" height="76" rx="16" fill="#111827" stroke="{CARD_BORDER}" />
              <text x="{x + 16}" y="{y + 28}" fill="{TEXT_MUTED}" font-size="14" font-family="Segoe UI, Arial, sans-serif">{xml_escape(label)}</text>
              <text x="{x + 16}" y="{y + 58}" fill="{TEXT_MAIN}" font-size="28" font-weight="700" font-family="Segoe UI, Arial, sans-serif">{xml_escape(value)}</text>
            </g>
            """
        )

    return f"""<svg width="620" height="340" viewBox="0 0 620 340" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Estadisticas de GitHub de {xml_escape(USERNAME)}">
  <rect width="620" height="340" rx="24" fill="{CARD_BG}" />
  <rect x="1" y="1" width="618" height="338" rx="23" stroke="{CARD_BORDER}" />
  <text x="40" y="58" fill="{TEXT_MAIN}" font-size="28" font-weight="700" font-family="Segoe UI, Arial, sans-serif">Estadisticas de GitHub</text>
  <text x="40" y="86" fill="{TEXT_MUTED}" font-size="15" font-family="Segoe UI, Arial, sans-serif">@{xml_escape(USERNAME)}</text>
  <rect x="40" y="98" width="540" height="1" fill="{CARD_BORDER}" />
  <circle cx="548" cy="58" r="8" fill="{ACCENT_2}" />
  <circle cx="572" cy="58" r="8" fill="{ACCENT}" />
  {''.join(metric_blocks)}
</svg>
"""


def build_top_langs_svg(language_totals: dict[str, int]) -> str:
    top_languages = sorted(language_totals.items(), key=lambda item: item[1], reverse=True)[:6]
    total_bytes = sum(amount for _, amount in top_languages) or 1

    rows = []
    bars = []
    current_x = 40.0

    for index, (language, amount) in enumerate(top_languages):
        pct = (amount / total_bytes) * 100
        color = LANG_COLORS[index % len(LANG_COLORS)]
        width = max((amount / total_bytes) * 540.0, 12.0)
        if current_x + width > 580:
            width = 580 - current_x
        bars.append(
            f'<rect x="{current_x:.2f}" y="108" width="{width:.2f}" height="14" rx="7" fill="{color}" />'
        )
        current_x += width

        row_y = 162 + index * 28
        rows.append(
            f"""
            <circle cx="48" cy="{row_y - 5}" r="6" fill="{color}" />
            <text x="64" y="{row_y}" fill="{TEXT_MAIN}" font-size="16" font-family="Segoe UI, Arial, sans-serif">{xml_escape(language)}</text>
            <text x="560" y="{row_y}" text-anchor="end" fill="{TEXT_MUTED}" font-size="15" font-family="Segoe UI, Arial, sans-serif">{pct:.1f}%</text>
            """
        )

    return f"""<svg width="620" height="360" viewBox="0 0 620 360" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Lenguajes mas usados por {xml_escape(USERNAME)}">
  <rect width="620" height="360" rx="24" fill="{CARD_BG}" />
  <rect x="1" y="1" width="618" height="358" rx="23" stroke="{CARD_BORDER}" />
  <text x="40" y="58" fill="{TEXT_MAIN}" font-size="28" font-weight="700" font-family="Segoe UI, Arial, sans-serif">Lenguajes mas usados</text>
  <text x="40" y="86" fill="{TEXT_MUTED}" font-size="15" font-family="Segoe UI, Arial, sans-serif">Calculado a partir del lenguaje principal y tamano de repositorios publicos</text>
  <rect x="40" y="108" width="540" height="14" rx="7" fill="#161b22" />
  {''.join(bars)}
  {''.join(rows)}
</svg>
"""


def build_error_svg(title: str, message: str) -> str:
    safe_title = xml_escape(title)
    safe_message = xml_escape(message[:140])
    return f"""<svg width="620" height="340" viewBox="0 0 620 340" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{safe_title}">
  <rect width="620" height="340" rx="24" fill="{CARD_BG}" />
  <rect x="1" y="1" width="618" height="338" rx="23" stroke="{CARD_BORDER}" />
  <text x="40" y="58" fill="{TEXT_MAIN}" font-size="28" font-weight="700" font-family="Segoe UI, Arial, sans-serif">{safe_title}</text>
  <text x="40" y="108" fill="{TEXT_MUTED}" font-size="16" font-family="Segoe UI, Arial, sans-serif">No se pudo actualizar en esta ejecucion.</text>
  <text x="40" y="148" fill="{TEXT_MAIN}" font-size="17" font-family="Segoe UI, Arial, sans-serif">Motivo:</text>
  <text x="40" y="178" fill="{TEXT_MUTED}" font-size="15" font-family="Segoe UI, Arial, sans-serif">{safe_message}</text>
  <text x="40" y="238" fill="{ACCENT}" font-size="15" font-family="Segoe UI, Arial, sans-serif">El workflow volvera a intentarlo automaticamente.</text>
</svg>
"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        user = fetch_user(USERNAME)
        repos = fetch_repos(USERNAME)
        source_repos = [repo for repo in repos if not repo.get("fork") and not repo.get("archived")]

        language_totals: dict[str, int] = {}
        for repo in source_repos:
            language = repo.get("language")
            size = max(repo.get("size", 0), 1)
            if not language:
                continue
            language_totals[language] = language_totals.get(language, 0) + size

        stats_svg = build_stats_svg(user, source_repos)
        top_langs_svg = build_top_langs_svg(language_totals)
    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        print(error_message)
        stats_svg = build_error_svg("Estadisticas de GitHub", error_message)
        top_langs_svg = build_error_svg("Lenguajes mas usados", error_message)

    (OUTPUT_DIR / "stats.svg").write_text(stats_svg, encoding="utf-8")
    (OUTPUT_DIR / "top-langs.svg").write_text(top_langs_svg, encoding="utf-8")


if __name__ == "__main__":
    main()
