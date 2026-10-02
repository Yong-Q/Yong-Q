#!/usr/bin/env python3
"""Generate the public profile; Python standard library only."""
import argparse
import html
import json
import math
import os
from pathlib import Path
import urllib.request

START, END = "<!-- PROFILE:START -->", "<!-- PROFILE:END -->"


def fetch_repos(username):
    headers = {"User-Agent": "Yong-Q-profile", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    repos = []
    for page in range(1, 101):
        request = urllib.request.Request(
            f"https://api.github.com/users/{username}/repos?per_page=100&page={page}", headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise RuntimeError("Invalid GitHub repository response")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
    raise RuntimeError("GitHub pagination limit exceeded")


def build_model(config, repos):
    username = config["username"]
    valid = []
    for repo in repos:
        if (repo.get("fork") or repo.get("private") or repo.get("archived")
                or repo["name"] in config.get("exclude", []) or repo.get("size", 0) == 0):
            continue
        item = {key: repo.get(key) for key in ["name", "description", "language", "pushed_at"]}
        item["html_url"] = f"https://github.com/{username}/{repo['name']}"
        valid.append(item)
    valid.sort(key=lambda item: (item.get("pushed_at") or "", item["name"]), reverse=True)
    by_name = {item["name"]: item for item in valid}
    featured = []
    for project in config["featured"]:
        if project["repo"] in by_name:
            item = dict(by_name[project["repo"]])
            item.update(project)
            item["summary"] = item.get("description") or project["summary"]
            featured.append(item)
    return {**config, "featured": featured, "recent": valid[:config.get("recent_limit", 4)],
            "activity_date": (valid[0].get("pushed_at") or "")[:10] if valid else ""}


def clean(value):
    return " ".join(str(value or "").split())


def escaped(value):
    return html.escape(clean(value), quote=True)


def markdown(value):
    return escaped(value).replace("|", "&#124;").replace("[", "&#91;").replace("]", "&#93;")


def render_svg(model, theme="auto"):
    count = len(model["featured"])
    height = 330 + count * 136 + 112
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Yong-Q — computational porous materials and classical DFT</title>',
             '<desc id="desc">Research profile featuring materials inverse design, scientific workflow automation and molecular transport.</desc>',
             '''<defs><linearGradient id="wash" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0e988d" stop-opacity=".09"/><stop offset="1" stop-color="#578ef5" stop-opacity=".025"/></linearGradient></defs>
<style>
svg{--bg:#fff;--fg:#122c35;--muted:#59717b;--line:#dce9eb;--card:#f6fafb;--accent:#087f78;--tag:#e9f5f3;--art:#128b8b}
.bg{fill:var(--bg)}.fg{fill:var(--fg)}.muted{fill:var(--muted)}.accent{fill:var(--accent)}.line{stroke:var(--line)}.card{fill:var(--card);stroke:var(--line)}.tag{fill:var(--tag)}.art{stroke:var(--art);fill:none}
text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}.mono{font-family:ui-monospace,Consolas,monospace}.label{font-size:11px;letter-spacing:2px;font-weight:600}.title{font-size:25px;font-weight:650}a{text-decoration:none}
''']
    dark = "svg{--bg:#0c1720;--fg:#e6f0f3;--muted:#9ab0bb;--line:#263b46;--card:#12222d;--accent:#66d8c7;--tag:#1b353e;--art:#59b9bd}"
    if theme == "auto":
        parts.append(f"@media(prefers-color-scheme:dark){{{dark}}}")
    elif theme == "dark":
        parts.append(dark)
    parts.extend(['</style>', f'<rect class="bg" width="960" height="{height}" rx="22"/>',
                  f'<rect x=".5" y=".5" width="959" height="{height-1}" rx="22" fill="none" class="line"/>',
                  '<rect x="1" y="1" width="958" height="303" rx="22" fill="url(#wash)"/>'])
    def text(x, y, value, cls="muted", size=15, extra=""):
        parts.append(f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" {extra}>{escaped(value)}</text>')
    text(40, 42, "COMPUTATIONAL MATERIALS / RESEARCH & CODE", "accent label")
    text(40, 105, model["username"], "fg", 54, 'font-weight="700" letter-spacing="-2"')
    text(42, 141, "From porous structures to molecular behavior.", "fg", 20)
    text(42, 179, "Classical density functional theory (cDFT)", "muted", 15)
    text(42, 203, "Molecular simulation · Machine learning · AI-assisted research", "muted", 15)
    x = 42
    for keyword in model["keywords"]:
        width = len(keyword) * 6.7 + 24
        parts.append(f'<rect x="{x}" y="239" width="{width}" height="29" rx="14.5" class="tag"/>')
        text(x + 12, 258, keyword, "accent", 12)
        x += width + 8
    # Decorative porous network: an illustration, not a scientific result.
    for cx, cy in [(766, 103), (822, 136), (766, 169), (878, 103), (878, 169)]:
        points = [(cx + 38 * math.cos(math.pi / 3 * i), cy + 38 * math.sin(math.pi / 3 * i)) for i in range(6)]
        pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
        parts.append(f'<polygon points="{pts}" class="art" stroke-width="1.2" opacity=".32"/>')
        for px, py in points:
            parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.1" fill="var(--art)" opacity=".6"/>')
    parts.append('<path d="M729 207 C758 210 771 142 806 157 S855 212 910 192" class="art" stroke-width="2" opacity=".6"/>')
    text(40, 319, "SELECTED PROJECTS", "muted label")
    for index, project in enumerate(model["featured"]):
        y = 338 + index * 136
        parts.append(f'<a href="{escaped(project["html_url"])}"><rect x="32" y="{y}" width="896" height="120" rx="13" class="card"/>')
        text(52, y + 28, f"0{index+1}", "accent mono", 12)
        text(89, y + 28, project["category"], "muted label")
        text(52, y + 58, project["title"], "fg title")
        text(888, y + 58, "↗", "accent", 25)
        summary = clean(project["summary"])
        if len(summary) > 112:
            summary = summary[:109].rsplit(" ", 1)[0] + "…"
        text(52, y + 83, summary, "muted", 14)
        text(52, y + 106, " / ".join(project["tags"]), "accent mono", 11)
        parts.append('</a>')
    y = 350 + count * 136
    text(40, y + 20, "RESEARCH RESOURCES", "muted label")
    for x, resource in zip([40, 533], model["resources"]):
        text(x, y + 53, resource["label"], "fg", 16)
    text(40, y + 79, "Code, models and data for computational materials research.", "muted", 12)
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def render_readme(model, original):
    rows = [START, f'## {markdown(model["username"])}', '', model["intro"], '', '### Projects', '']
    for project in model["featured"]:
        summary = project.get("profile_summary", project["summary"])
        rows.append(f'- **[{markdown(project["title"])}]({project["html_url"]})** — {markdown(summary)}')
    rows.extend(['', '### Paper & data', '',
                 ' · '.join(f'[{markdown(r["label"])}]({r["url"]})' for r in model["resources"]), '',
                 '<details>', '<summary>Recently updated</summary>', ''])
    for item in model["recent"]:
        focus = item.get("description") or next((p["summary"] for p in model["featured"] if p["name"] == item["name"]), None) or item.get("language") or "Research code"
        rows.append(f'- [{markdown(item["name"])}]({item["html_url"]}) · {(item.get("pushed_at") or "")[:10]} — {markdown(focus)}')
    rows.extend(['', '</details>', END])
    generated = "\n".join(rows)
    if START in original and END in original:
        before, rest = original.split(START, 1)
        _, after = rest.split(END, 1)
        return before + generated + after
    if START in original or END in original:
        raise ValueError("README generated-block markers are incomplete")
    return original.rstrip() + ("\n\n" if original.strip() else "") + generated + "\n"


def generate(root, repos=None):
    config = json.loads((root / "profile.json").read_text())
    fetched = fetch_repos(config["username"]) if repos is None else repos
    model = build_model(config, fetched)
    old = (root / "README.md").read_text() if (root / "README.md").exists() else ""
    # Build everything before any write so API/render failures retain last good outputs.
    snapshot = [{key: repo.get(key) for key in ["name", "description", "language", "pushed_at", "fork", "private", "archived", "size"]}
                for repo in fetched if repo["name"] not in config.get("exclude", [])]
    snapshot.sort(key=lambda repo: repo["name"])
    files = {"README.md": render_readme(model, old),
             "data/profile.json": json.dumps(model, ensure_ascii=False, indent=2) + "\n",
             "data/repositories.json": json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
             "assets/initial.js": "window.PROFILE_INITIAL = " + json.dumps(model, ensure_ascii=True).replace("<", "\\u003c") + ";\n"
                 + "window.PROFILE_CONFIG = " + json.dumps(config, ensure_ascii=True).replace("<", "\\u003c") + ";\n"}
    for theme in ["auto", "light", "dark"]:
        name = "panel.svg" if theme == "auto" else f"panel-{theme}.svg"
        files[f"assets/{name}"] = render_svg(model, theme)
    import xml.etree.ElementTree as ET
    for name, content in files.items():
        if name.endswith(".svg"):
            ET.fromstring(content)
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text() == content:
            continue
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content)
        temporary.replace(path)
    print(f"Generated {len(model['featured'])} featured and {len(model['recent'])} recent projects")
    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--offline", action="store_true", help="Use previously fetched repository snapshot")
    args = parser.parse_args()
    snapshot = json.loads((args.root / "data/repositories.json").read_text()) if args.offline else None
    generate(args.root, snapshot)
