# dogmath.net

A static, dependency-free website serving 60+ mirrored browser games. Vanilla HTML/CSS/JS — no framework, no bundler, no build step for the site itself. Python scripts mirror games from upstream hosts and generate SEO landing pages; the static files are then synced to S3 behind CloudFront.

**Live site:** [www.dogmath.net](https://www.dogmath.net)

## How it works

The site is a single `index.html` containing the homepage, a client-side router, and the canonical list of games. Games play inside a modal iframe from their local mirror under `games/<slug>/`. Each game also gets a per-slug SEO landing page under `play/<slug>/` so search engines see unique URLs, while users land on the homepage with the game pre-opened.

### Source of truth

The `const games = [...]` array in `index.html` is the canonical list of games. **Every other artifact is derived from it** — `play/<slug>/index.html`, `.play-slugs.txt`, and `sitemap.xml`. To add or remove a game, edit this array and re-run the build script; do not hand-edit the generated files.

## Repository layout

| Path | Purpose |
|------|---------|
| `index.html` | Homepage, `games[]` array, and client-side router |
| `games/<slug>/` | Local, ad-stripped mirror of each game |
| `play/<slug>/` | Generated per-game SEO landing pages |
| `thumbs/` | Game thumbnail images (`.png` / `.svg`) |
| `sitemap.xml`, `robots.txt` | SEO / crawler files (sitemap is generated) |
| `build_play_pages.py` | Regenerates all `play/` pages, `.play-slugs.txt`, and `sitemap.xml` |
| `download_hubpro.py` | Mirrors a `hub-pro.github.io` game into `games/<slug>/` |
| `download_games.py` | Mirrors the UBG77 game set (handles Unity WebGL builds) |
| `download_unity.py` | Mirrors Unity-based hub-pro games needing special handling |
| `cf-function-rewrite.js` | CloudFront Function that appends `index.html` to directory paths |
| `apps-script.gs` | Google Apps Script backing the per-game thumbs-up / play counters (reference copy) |
| `CLAUDE.md` | Detailed contributor/automation guide |

## How a game flows to production

```
Source (hub-pro.github.io | ubg77.github.io | other)
    │  download_hubpro.py | download_games.py | download_unity.py
    ▼
games/<slug>/          ← local mirror, ad-stripped, paths relativized
    │  edit index.html: append entry to games[]; add thumbs/<slug>
    ▼
index.html             ← homepage + games[] + client-side router
    │  python3 build_play_pages.py
    ▼
play/<slug>/index.html ← generated per-game SEO landing pages
    │  aws s3 sync + cloudfront invalidate
    ▼
www.dogmath.net
```

## Common commands

```bash
# Regenerate all play/ pages, .play-slugs.txt, and sitemap.xml after editing games[]
# (lastmod defaults to today; pass YYYY-MM-DD to override)
python3 build_play_pages.py [lastmod-date]

# Mirror a new game from its upstream host into games/<slug>/
python3 download_hubpro.py [slug]
python3 download_games.py
python3 download_unity.py
```

## Deployment

Static files are hosted on **S3** behind a **CloudFront** distribution. A typical single-game deploy syncs the changed files to S3 and invalidates the affected CloudFront paths. See [`CLAUDE.md`](./CLAUDE.md) for the exact bucket, distribution ID, and step-by-step deploy/invalidation commands.

> **Note:** This working copy is not necessarily a live `git` clone. Deploys go straight to S3, so the GitHub repo can drift from what's in production — treat the deployed site as the source of truth for what's live.

## License

All game content is mirrored from third-party upstream sources and remains the property of its respective creators. This repository contains the site scaffolding and mirroring tooling only.
