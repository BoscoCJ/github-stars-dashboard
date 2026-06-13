import json
import os
import shutil
import time
import urllib.parse
import urllib.request
from urllib.error import URLError
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from build_catalog import build_catalog, write_html, write_markdown


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yml"
GENERATED = ROOT / ".generated"
MANIFEST_PATH = ROOT / ".stars-pages.json"
PER_PAGE = 100


def parse_scalar(value):
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def load_config():
    config = {
        "site_title": "GitHub Stars Dashboard",
        "local_fallback_user": "BoscoCJ",
        "users": [{"username": "auto", "label": "我的收藏"}],
    }
    if not CONFIG_PATH.exists():
        return config

    users = []
    current_user = None
    in_users = False
    for raw_line in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if not raw_line.startswith(" ") and stripped == "users:":
            in_users = True
            continue
        if not raw_line.startswith(" ") and ":" in stripped:
            in_users = False
            key, value = stripped.split(":", 1)
            config[key.strip()] = parse_scalar(value)
            continue
        if in_users and stripped.startswith("- "):
            if current_user:
                users.append(current_user)
            current_user = {}
            item = stripped[2:].strip()
            if item and ":" in item:
                key, value = item.split(":", 1)
                current_user[key.strip()] = parse_scalar(value)
            continue
        if in_users and current_user is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_user[key.strip()] = parse_scalar(value)

    if current_user:
        users.append(current_user)
    if users:
        config["users"] = users
    return config


def resolve_username(username, config):
    if not username or username == "auto":
        return os.environ.get("GITHUB_REPOSITORY_OWNER") or config.get("local_fallback_user") or "BoscoCJ"
    return username


def user_slug(username):
    return urllib.parse.quote(username, safe="")


def safe_page_dir(slug):
    path = (ROOT / slug).resolve()
    root = ROOT.resolve()
    if path.parent != root or not slug or slug in {".", ".."}:
        raise ValueError(f"Unsafe generated page slug: {slug}")
    return path


def cleanup_previous_pages():
    legacy_u = ROOT / "u"
    if legacy_u.exists():
        shutil.rmtree(legacy_u)

    if not MANIFEST_PATH.exists():
        return
    try:
        previous_slugs = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("slugs", [])
    except json.JSONDecodeError:
        previous_slugs = []
    for slug in previous_slugs:
        path = safe_page_dir(str(slug))
        if path.exists() and path.is_dir():
            shutil.rmtree(path)


def fetch_page(username, page):
    url = f"https://api.github.com/users/{urllib.parse.quote(username)}/starred?per_page={PER_PAGE}&page={page}"
    headers = {
        "User-Agent": "GitHubStarsDashboard",
        "Accept": "application/vnd.github.star+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except (TimeoutError, URLError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 + attempt * 3)
    raise last_error


def fetch_all_stars(username):
    all_items = []
    page = 1
    while True:
        items = fetch_page(username, page)
        if not items:
            break
        all_items.extend(items)
        if len(items) < PER_PAGE:
            break
        page += 1
        time.sleep(0.2)
    return all_items


def write_landing_page(site_title, users, generated_at):
    total_repos = sum(user["repo_count"] for user in users)
    cards = "\n".join(
        f"""
        <a class="user-card" href="{escape(user['href'], quote=True)}">
          <span class="avatar-wrap"><img src="{escape(user['avatar_url'], quote=True)}" alt="" loading="lazy"></span>
          <span>
            <strong>{escape(user['label'])}</strong>
            <small>@{escape(user['username'])}</small>
          </span>
          <span class="count">{user['repo_count']}</span>
        </a>
        """
        for user in users
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(site_title)}</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --ink: #171717;
      --muted: #6d6a63;
      --line: rgba(23, 23, 23, .12);
      --panel: rgba(255, 252, 246, .8);
      --radius: 8px;
      --font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 12% 10%, rgba(15, 118, 110, .13), transparent 28%),
        linear-gradient(135deg, #f5f1e8 0%, #ebe4d6 48%, #f7f3ea 100%);
      color: var(--ink);
      font-family: var(--font);
    }}
    a {{ color: inherit; text-decoration: none; }}
    .shell {{ width: min(100% - 32px, 1040px); margin: 0 auto; padding: 42px 0; }}
    .hero {{
      min-height: 280px;
      display: grid;
      align-content: end;
      padding: 34px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: linear-gradient(135deg, #171717, #243b38 60%, #7f1d1d);
      color: #fffaf0;
      box-shadow: 0 22px 60px rgba(24, 22, 18, .12);
    }}
    .eyebrow {{ margin: 0 0 14px; color: rgba(255, 250, 240, .7); font-size: 13px; }}
    h1 {{ max-width: 760px; margin: 0; font-size: clamp(38px, 7vw, 74px); line-height: .96; letter-spacing: 0; }}
    .hero p:last-child {{ max-width: 720px; margin: 22px 0 0; color: rgba(255, 250, 240, .78); line-height: 1.8; }}
    .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0; }}
    .stat, .user-card {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel);
      box-shadow: 0 16px 42px rgba(24, 22, 18, .08);
    }}
    .stat {{ padding: 18px; }}
    .stat strong {{ display: block; font-size: 30px; line-height: 1; }}
    .stat span {{ display: block; margin-top: 8px; color: var(--muted); font-size: 13px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    .user-card {{
      min-height: 96px;
      display: grid;
      grid-template-columns: 52px minmax(0, 1fr) auto;
      gap: 14px;
      align-items: center;
      padding: 18px;
      transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
    }}
    .user-card:hover {{ transform: translateY(-2px); border-color: rgba(23, 23, 23, .28); box-shadow: 0 18px 40px rgba(24, 22, 18, .12); }}
    .avatar-wrap img {{ width: 52px; height: 52px; border-radius: 50%; object-fit: cover; }}
    .user-card strong {{ display: block; overflow-wrap: anywhere; }}
    .user-card small {{ display: block; margin-top: 4px; color: var(--muted); overflow-wrap: anywhere; }}
    .count {{ min-width: 46px; padding: 7px 10px; border-radius: 999px; background: rgba(23, 23, 23, .08); color: var(--muted); text-align: center; font-variant-numeric: tabular-nums; }}
    .footer {{ margin-top: 28px; color: var(--muted); font-size: 13px; line-height: 1.7; }}
    @media (max-width: 680px) {{
      .shell {{ width: min(100% - 24px, 1040px); padding-top: 20px; }}
      .hero {{ min-height: 240px; padding: 24px; }}
      .stats {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">GitHub Stars Observatory · {escape(generated_at)}</p>
      <h1>{escape(site_title)}</h1>
      <p>默认整理自己的公开 Stars，也可以观察任意 GitHub 用户的公开收藏。选择一个用户，进入独立的分类、搜索和项目雷达页面。</p>
    </section>
    <section class="stats" aria-label="站点统计">
      <div class="stat"><strong>{len(users)}</strong><span>已配置用户</span></div>
      <div class="stat"><strong>{total_repos}</strong><span>公开 Stars 项目</span></div>
      <div class="stat"><strong>Daily</strong><span>GitHub Actions 自动刷新</span></div>
    </section>
    <section class="grid" aria-label="用户列表">
      {cards}
    </section>
    <p class="footer">本项目只读取 GitHub 公开 starred repositories，不读取私有仓库，不需要个人 GitHub Token。</p>
  </main>
</body>
</html>
"""
    (ROOT / "index.html").write_text(html, encoding="utf-8")


def main():
    config = load_config()
    site_title = str(config.get("site_title") or "GitHub Stars Dashboard")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cleanup_previous_pages()
    GENERATED.mkdir(exist_ok=True)
    (ROOT / ".nojekyll").touch()

    resolved_users = []
    seen = set()
    for entry in config.get("users", []):
        username = resolve_username(str(entry.get("username") or "auto"), config)
        key = username.lower()
        if key in seen:
            continue
        seen.add(key)
        label = str(entry.get("label") or username)
        slug = user_slug(username)
        resolved_users.append(
            {
                "username": username,
                "label": label,
                "slug": slug,
                "href": f"{slug}/",
            }
        )

    single_user = len(resolved_users) == 1
    if single_user:
        nav_users = [{"username": user["username"], "label": user["label"], "href": "./"} for user in resolved_users]
    else:
        nav_users = [{"username": user["username"], "label": user["label"], "href": f"../{user['slug']}/"} for user in resolved_users]

    summaries = []
    generated_slugs = []
    for user in resolved_users:
        stars = fetch_all_stars(user["username"])
        user_dir = GENERATED / user["slug"]
        page_dir = safe_page_dir(user["slug"])
        raw_path = user_dir / "stars_raw.json"
        catalog_json = user_dir / "stars_catalog.json"
        catalog_md = user_dir / "stars_catalog.md"
        page_path = ROOT / "index.html" if single_user else page_dir / "index.html"
        user_dir.mkdir(parents=True, exist_ok=True)
        if not single_user:
            page_dir.mkdir(parents=True, exist_ok=True)
            generated_slugs.append(user["slug"])

        raw_path.write_text(json.dumps(stars, ensure_ascii=False, indent=2), encoding="utf-8")
        catalog = build_catalog(raw_path)
        catalog_json.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        write_markdown(catalog, catalog_md, user["label"])
        write_html(
            catalog,
            page_path,
            owner_name=user["username"],
            owner_label=user["label"],
            site_title=site_title,
            all_users=nav_users,
        )

        avatar_url = f"https://github.com/{urllib.parse.quote(user['username'])}.png"
        summaries.append({**user, "repo_count": len(catalog), "avatar_url": avatar_url})
        print(f"refreshed @{user['username']} repos={len(catalog)} page={page_path}")

    if not single_user:
        write_landing_page(site_title, summaries, generated_at)
    MANIFEST_PATH.write_text(json.dumps({"slugs": generated_slugs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"users={len(summaries)}")
    print(f"index={ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
