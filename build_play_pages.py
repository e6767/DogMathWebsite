#!/usr/bin/env python3
"""Generate /play/<slug>/index.html per-game SEO pages from index.html.

Each generated page is a copy of the homepage with:
- <base href="/"> so relative paths still resolve
- Per-game title, description, canonical
- Per-game OpenGraph + Twitter cards
- VideoGame JSON-LD instead of WebSite JSON-LD

The body is identical to the homepage; the JS routing in index.html will
auto-open the game on load when window.location.pathname matches /play/<slug>/.
"""

import re, json, html, shutil
from pathlib import Path

ROOT = Path(__file__).parent
INDEX = ROOT / "index.html"
PLAY = ROOT / "play"

GAMES_BLOCK_RE = re.compile(r"const games = \[(.*?)\n\];", re.DOTALL)
ENTRY_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)
FIELD_RE = re.compile(r"(\w+)\s*:\s*('[^']*'|\"[^\"]*\")")


def unq(s):
    return s[1:-1] if s and len(s) >= 2 and s[0] in "'\"" and s[-1] in "'\"" else s


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_games(index_html):
    m = GAMES_BLOCK_RE.search(index_html)
    if not m:
        raise SystemExit("could not locate games[] block")
    block = m.group(1)
    games = []
    for entry in ENTRY_RE.finditer(block):
        fields = {k: unq(v) for k, v in FIELD_RE.findall(entry.group(0))}
        if "name" not in fields:
            continue
        name = fields["name"]
        path = fields.get("path")
        slug = path if path else slugify(name)
        games.append({
            "name": name,
            "genre": fields.get("genre", "Fun"),
            "src": fields.get("src"),
            "path": path,
            "slug": slug,
        })
    return games


# Tag-rewrite helpers — operate on the homepage HTML to produce a per-game variant
TITLE_RE = re.compile(r"<title>.*?</title>", re.DOTALL | re.IGNORECASE)
META_DESC_RE = re.compile(r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
CANON_RE = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
OG_TITLE_RE = re.compile(r'<meta\s+property=["\']og:title["\']\s+content=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
OG_DESC_RE = re.compile(r'<meta\s+property=["\']og:description["\']\s+content=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
OG_URL_RE = re.compile(r'<meta\s+property=["\']og:url["\']\s+content=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
TW_TITLE_RE = re.compile(r'<meta\s+name=["\']twitter:title["\']\s+content=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
TW_DESC_RE = re.compile(r'<meta\s+name=["\']twitter:description["\']\s+content=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
TW_URL_RE = re.compile(r'<meta\s+name=["\']twitter:url["\']\s+content=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
WEBSITE_JSONLD_RE = re.compile(r'<script\s+type=["\']application/ld\+json["\']\s*>\s*\{[^<]*?"@type":\s*"WebSite".*?</script>', re.DOTALL | re.IGNORECASE)


def render_for_game(homepage_html, game):
    name = game["name"]
    slug = game["slug"]
    canonical_url = f"https://dogmath.net/play/{slug}/"
    page_title = f"{name} - Play Free at Dogmath"
    page_desc = (
        f"Play {name} free online at Dogmath. {game['genre']} browser game — "
        f"no download, no signup, just instant play in any browser."
    )

    # Escape attribute values
    et = html.escape(page_title, quote=True)
    ed = html.escape(page_desc, quote=True)
    eu = html.escape(canonical_url, quote=True)
    en = html.escape(name, quote=True)

    h = homepage_html

    # Inject <base href="/"> right after <head> open
    h = re.sub(r"(<head[^>]*>)", r'\1\n<base href="/"/>', h, count=1, flags=re.IGNORECASE)

    h = TITLE_RE.sub(f"<title>{html.escape(page_title)}</title>", h, count=1)
    h = META_DESC_RE.sub(f'<meta name="description" content="{ed}"/>', h, count=1)
    h = CANON_RE.sub(f'<link rel="canonical" href="{eu}"/>', h, count=1)
    h = OG_TITLE_RE.sub(f'<meta property="og:title" content="{et}"/>', h, count=1)
    h = OG_DESC_RE.sub(f'<meta property="og:description" content="{ed}"/>', h, count=1)
    h = OG_URL_RE.sub(f'<meta property="og:url" content="{eu}"/>', h, count=1)
    h = TW_TITLE_RE.sub(f'<meta name="twitter:title" content="{et}"/>', h, count=1)
    h = TW_DESC_RE.sub(f'<meta name="twitter:description" content="{ed}"/>', h, count=1)
    h = TW_URL_RE.sub(f'<meta name="twitter:url" content="{eu}"/>', h, count=1)

    # Replace the WebSite JSON-LD with a VideoGame one
    videogame_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": name,
        "description": page_desc,
        "url": canonical_url,
        "image": f"https://dogmath.net/thumbs/{slug}.svg",
        "genre": game["genre"],
        "applicationCategory": "Game",
        "operatingSystem": "Any (Browser)",
        "isAccessibleForFree": True,
        "publisher": {"@type": "Organization", "name": "Dogmath", "url": "https://dogmath.net/"},
    }, indent=2)
    replacement = f'<script type="application/ld+json">\n{videogame_ld}\n</script>'
    h = WEBSITE_JSONLD_RE.sub(lambda m: replacement, h, count=1)

    return h


def main():
    homepage = INDEX.read_text()
    games = parse_games(homepage)
    print(f"parsed {len(games)} games from index.html")

    # Wipe + rebuild play/
    if PLAY.exists():
        shutil.rmtree(PLAY)
    PLAY.mkdir()

    for g in games:
        out_dir = PLAY / g["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "index.html"
        rendered = render_for_game(homepage, g)
        out_file.write_text(rendered)
    print(f"wrote {len(games)} pages under play/")

    # Also dump slugs for sitemap building
    slugs_file = ROOT / ".play-slugs.txt"
    slugs_file.write_text("\n".join(g["slug"] for g in games) + "\n")
    print(f"slug list -> {slugs_file}")


if __name__ == "__main__":
    main()
