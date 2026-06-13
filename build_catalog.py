import json
import re
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "stars_raw.json"
CATALOG_JSON_PATH = ROOT / "stars_catalog.json"
CATALOG_MD_PATH = ROOT / "stars_catalog.md"
CATALOG_HTML_PATH = ROOT / "stars_dashboard.html"


CATEGORIES = [
    {
        "name": "AI Agent 与 Coding Agent",
        "keywords": [
            "agent", "agents", "agentic", "claude", "codex", "mcp", "openclaw",
            "qclaw", "coding agent", "code assistant", "multi-agent", "swarm",
            "llm tool", "skill", "skills", "prompt", "prompts",
            "manus", "openmanus", "clawdbot", "fuclaude", "cc-notebook",
            "assistant", "rawchat",
        ],
    },
    {
        "name": "AI 模型、LLM、RAG 与机器学习",
        "keywords": [
            "llm", "rag", "transformer", "deepseek", "qwen", "gemini", "openai",
            "machine learning", "ml", "model", "models", "embedding", "embeddings",
            "pytorch", "tensorflow", "cuda", "inference", "fine-tuning",
            "chat", "z-image", "fabubu",
        ],
    },
    {
        "name": "视频、音频与生成式创作",
        "keywords": [
            "video", "audio", "voice", "tts", "image generation", "ai-image",
            "ai-video", "render", "ffmpeg", "caption", "subtitle", "animation",
            "generative", "sora", "veo", "kling", "flux", "midjourney",
            "capcut", "opencut", "fooocus", "stable-diffusion", "comfyui",
            "webui", "screenshot", "demo", "demos", "sniffer", "downloader",
            "wechatvideo", "wechatvideosniffer", "mywechatvideodownloader",
            "kohya", "视频号",
        ],
    },
    {
        "name": "内容运营、社媒与增长工具",
        "keywords": [
            "xiaohongshu", "rednote", "wechat", "twitter", "x articles",
            "social", "social-media", "blogger", "blog", "publishing",
            "marketing", "growth", "content", "douyin", "tiktok",
        ],
    },
    {
        "name": "前端、设计系统与动画",
        "keywords": [
            "frontend", "front-end", "react", "vue", "svelte", "nextjs",
            "design", "design system", "css", "html", "tailwind", "ui",
            "component", "components", "gsap", "webgl", "threejs", "browser",
            "mvvm", "avalon",
        ],
    },
    {
        "name": "开发工具、CLI 与工程效率",
        "keywords": [
            "cli", "terminal", "devtool", "developer", "productivity",
            "workflow", "tooling", "automation", "script", "extension",
            "plugin", "vscode", "ide", "shell", "rust", "git",
            "tabs", "tab-out",
        ],
    },
    {
        "name": "数据、搜索与知识管理",
        "keywords": [
            "search", "database", "db", "data", "dataset", "knowledge",
            "notion", "obsidian", "docs", "document", "markdown", "export",
            "crawler", "scraper", "spider", "index",
            "location", "locations", "latitude", "longitude", "geographical",
        ],
    },
    {
        "name": "后端、基础设施与云原生",
        "keywords": [
            "backend", "server", "api", "docker", "kubernetes", "cloud",
            "infra", "infrastructure", "serverless", "proxy", "gateway",
            "microservice", "distributed", "go", "java",
        ],
    },
    {
        "name": "\u79fb\u52a8\u7aef\u3001\u684c\u9762\u7aef\u4e0e\u8de8\u5e73\u53f0\u5e94\u7528",
        "keywords": [
            "mobile", "desktop", "cross-platform", "ios", "macos", "android",
            "flutter", "dart", "swift", "objective-c", "airdrop", "file-sharing",
            "cocoapods", "sdk",
        ],
    },
    {
        "name": "商业产品、电商与业务应用",
        "keywords": [
            "commerce", "ecommerce", "crm", "erp", "saas", "business",
            "payment", "shop", "store", "dashboard", "admin", "faka",
            "12306", "订票", "刷票",
        ],
    },
    {
        "name": "学习资源、Awesome 与模板",
        "keywords": [
            "awesome", "course", "tutorial", "learning", "guide", "book",
            "template", "boilerplate", "example", "examples", "collection",
            "list", "roadmap",
        ],
    },
    {
        "name": "安全、隐私与逆向",
        "keywords": [
            "security", "privacy", "auth", "authentication", "vpn", "proxy",
            "reverse", "malware", "pentest", "hacking", "crypto", "cryptography",
            "shadowsocks",
        ],
    },
    {
        "name": "\u5206\u6790\u7edf\u8ba1\u3001\u76d1\u63a7\u4e0e\u53ef\u89c2\u6d4b\u6027",
        "keywords": [
            "analytics", "tracking", "tracker", "matomo", "monitor", "monitoring",
            "observability", "metrics", "nginx",
        ],
    },
]


def normalize_items(raw_items):
    repos = []
    for item in raw_items:
        repo = item.get("repo") or item
        if not repo:
            continue
        owner = repo.get("owner") or {}
        repos.append(
            {
                "full_name": repo.get("full_name") or "",
                "name": repo.get("name") or "",
                "owner_login": owner.get("login") or (repo.get("full_name") or "/").split("/", 1)[0],
                "owner_avatar_url": owner.get("avatar_url") or "",
                "html_url": repo.get("html_url") or "",
                "homepage": repo.get("homepage") or "",
                "description": repo.get("description") or "",
                "language": repo.get("language") or "Unknown",
                "topics": repo.get("topics") or [],
                "stars": repo.get("stargazers_count") or 0,
                "forks": repo.get("forks_count") or repo.get("forks") or 0,
                "open_issues": repo.get("open_issues_count") or repo.get("open_issues") or 0,
                "updated_at": repo.get("updated_at") or "",
                "pushed_at": repo.get("pushed_at") or "",
                "starred_at": item.get("starred_at") or "",
                "archived": bool(repo.get("archived")),
                "fork": bool(repo.get("fork")),
                "license": (repo.get("license") or {}).get("spdx_id") or "",
            }
        )
    return repos


def text_blob(repo):
    pieces = [
        repo["full_name"],
        repo["name"],
        repo["description"],
        repo["language"],
        " ".join(repo["topics"]),
    ]
    return " ".join(pieces).lower()


def keyword_matches(blob, keyword):
    keyword = keyword.lower()
    if any(ch in keyword for ch in " -_./"):
        return keyword in blob
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", blob) is not None


PROJECT_NOTES = {
    "shizhilya/yuan": "统一的命运解读 Agent Skill，给 Codex、Claude Code 等运行时使用；支持八字、称骨、数字命理、西洋占星、吠陀占星、紫微斗数等多种方法。",
    "miounet11/life-kline": "人生运势可视化工具，把 AI 大模型和传统八字命理结合起来，把人生走势画成类似股票 K 线的图，支持自托管。",
}


CATEGORY_NOTES = {
    "AI Agent 与 Coding Agent": "面向 AI Agent 或 Coding Agent 的工具、技能、提示词、运行框架或协作系统。",
    "AI 模型、LLM、RAG 与机器学习": "和大模型、机器学习、RAG、模型推理、训练或 AI 应用能力相关。",
    "视频、音频与生成式创作": "用于视频、音频、图像生成、剪辑、字幕、配音、渲染或创意生产。",
    "内容运营、社媒与增长工具": "服务于内容生产、社媒运营、微信/小红书/抖音/X 等平台或增长工作流。",
    "前端、设计系统与动画": "和前端开发、UI、设计系统、CSS、网页动画或浏览器体验相关。",
    "开发工具、CLI 与工程效率": "提升开发效率的命令行工具、插件、脚本、工作流或工程辅助工具。",
    "数据、搜索与知识管理": "用于数据采集、搜索、文档转换、知识库、索引、地理数据或信息管理。",
    "后端、基础设施与云原生": "后端服务、API、Docker、云原生、代理、网关、服务端或基础设施相关。",
    "商业产品、电商与业务应用": "电商、支付、业务系统、管理后台、票务或商业产品应用。",
    "学习资源、Awesome 与模板": "教程、指南、awesome 清单、模板、样例或学习资料集合。",
    "安全、隐私与逆向": "安全、隐私、代理、加密、逆向或网络访问相关。",
    "移动端、桌面端与跨平台应用": "移动端、桌面端、Flutter、iOS、macOS、Android 或跨平台应用相关。",
    "分析统计、监控与可观测性": "统计分析、埋点、监控、指标、Nginx 配置或可观测性相关。",
}


TOPIC_LABELS = {
    "agent": "AI Agent",
    "agents": "AI Agent",
    "ai": "AI",
    "ai-agent": "AI Agent",
    "ai-agents": "AI Agent",
    "llm": "大模型",
    "llms": "大模型",
    "rag": "RAG 检索增强生成",
    "mcp": "MCP 工具/服务",
    "claude": "Claude",
    "claude-code": "Claude Code",
    "codex": "Codex",
    "openai": "OpenAI",
    "deepseek": "DeepSeek",
    "gemini": "Gemini",
    "python": "Python",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "rust": "Rust",
    "go": "Go",
    "react": "React",
    "nodejs": "Node.js",
    "frontend": "前端",
    "browser": "浏览器",
    "browser-automation": "浏览器自动化",
    "automation": "自动化",
    "cli": "命令行",
    "developer-tools": "开发者工具",
    "productivity": "效率工具",
    "video": "视频",
    "video-generation": "视频生成",
    "audio": "音频",
    "tts": "文本转语音",
    "voice": "语音",
    "voice-cloning": "声音克隆",
    "ffmpeg": "FFmpeg",
    "subtitle": "字幕",
    "image-generation": "图像生成",
    "animation": "动画",
    "design": "设计",
    "design-system": "设计系统",
    "css": "CSS",
    "html": "HTML",
    "data": "数据",
    "search": "搜索",
    "crawler": "爬虫",
    "scraper": "网页抓取",
    "markdown": "Markdown",
    "document": "文档",
    "docs": "文档",
    "docker": "Docker",
    "api": "API",
    "server": "服务端",
    "proxy": "代理",
    "security": "安全",
    "privacy": "隐私",
    "wechat": "微信",
    "xiaohongshu": "小红书",
    "rednote": "小红书",
    "social-media": "社媒",
    "publishing": "发布",
    "commerce": "电商",
    "ecommerce": "电商",
    "template": "模板",
    "awesome": "awesome 清单",
    "astrology": "占星/命理",
    "bazi": "八字",
    "destiny": "命运解读",
    "fortune-telling": "算命/运势",
    "chinese-astrology": "中国命理",
    "self-hosted": "自托管",
    "visualization": "可视化",
}


DESC_HINTS = [
    ("destiny-reading", "命运解读"),
    ("fortune", "运势/算命"),
    ("astrology", "占星"),
    ("bazi", "八字"),
    ("zi wei", "紫微斗数"),
    ("agent", "AI Agent"),
    ("coding agent", "编程 Agent"),
    ("skill", "Agent Skill"),
    ("prompt", "提示词"),
    ("llm", "大模型"),
    ("rag", "RAG 检索增强生成"),
    ("voice", "语音"),
    ("tts", "文本转语音"),
    ("video", "视频"),
    ("audio", "音频"),
    ("image", "图像"),
    ("animation", "动画"),
    ("browser", "浏览器"),
    ("automation", "自动化"),
    ("search", "搜索"),
    ("scraping", "网页抓取"),
    ("crawler", "爬虫"),
    ("markdown", "Markdown"),
    ("document", "文档"),
    ("design", "设计"),
    ("frontend", "前端"),
    ("commerce", "电商"),
    ("workflow", "工作流"),
    ("cli", "命令行"),
    ("extension", "扩展插件"),
    ("plugin", "插件"),
    ("self-hosted", "自托管"),
]


def has_cjk(text):
    return re.search(r"[\u4e00-\u9fff]", text or "") is not None


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def chinese_explanation(repo, primary):
    full_name = repo["full_name"]
    if full_name in PROJECT_NOTES:
        return PROJECT_NOTES[full_name]

    desc = clean_text(repo["description"])
    if desc and has_cjk(desc):
        return desc

    blob = text_blob(repo)
    hints = []
    for topic in repo["topics"]:
        label = TOPIC_LABELS.get(topic.lower())
        if label and label not in hints:
            hints.append(label)
    for keyword, label in DESC_HINTS:
        if keyword in blob and label not in hints:
            hints.append(label)

    if hints:
        focus = "、".join(hints[:5])
        return f"{CATEGORY_NOTES.get(primary, primary)}重点涉及：{focus}。"

    if repo["language"] != "Unknown":
        return f"{CATEGORY_NOTES.get(primary, primary)}主要语言是 {repo['language']}。"
    return CATEGORY_NOTES.get(primary, "这个项目需要结合 README 进一步判断具体用途。")


def classify(repo):
    blob = text_blob(repo)
    scored = []
    for category in CATEGORIES:
        matches = []
        score = 0
        for keyword in category["keywords"]:
            if keyword_matches(blob, keyword):
                matches.append(keyword)
                score += 3 if " " in keyword else 1
        if score:
            scored.append((score, category["name"], sorted(set(matches))))

    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored:
        return "待复核/未归类", [], []

    primary = scored[0][1]
    secondary = [name for _, name, _ in scored[1:4]]
    matched = sorted({kw for _, _, kws in scored for kw in kws})[:12]
    return primary, secondary, matched


def iso_to_date(value):
    if not value:
        return ""
    return value.split("T", 1)[0]


def build_catalog(raw_path=RAW_PATH):
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8-sig"))
    if isinstance(raw, dict):
        raw = [raw]
    repos = normalize_items(raw)

    catalog = []
    for repo in repos:
        primary, secondary, matched = classify(repo)
        note = chinese_explanation(repo, primary)
        catalog.append(
            {
                **repo,
                "primary_category": primary,
                "secondary_categories": secondary,
                "matched_keywords": matched,
                "chinese_note": note,
            }
        )

    catalog.sort(key=lambda repo: (repo["primary_category"], -repo["stars"], repo["full_name"].lower()))
    return catalog


def repo_line(repo):
    note = clean_text(repo.get("chinese_note") or "")
    if len(note) > 180:
        note = note[:177].rstrip() + "..."
    meta = [
        repo["language"],
        f"{repo['stars']:,} stars",
        f"updated {iso_to_date(repo['updated_at'])}",
    ]
    if repo["starred_at"]:
        meta.append(f"starred {iso_to_date(repo['starred_at'])}")
    if repo["archived"]:
        meta.append("archived")
    return f"- [{repo['full_name']}]({repo['html_url']}) - 中文解释：{note} ({'; '.join(meta)})"


def write_markdown(catalog, output_path=CATALOG_MD_PATH, owner_label="BoscoCJ"):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    by_category = defaultdict(list)
    for repo in catalog:
        by_category[repo["primary_category"]].append(repo)

    language_counts = Counter(repo["language"] for repo in catalog)
    category_counts = Counter(repo["primary_category"] for repo in catalog)
    recent = sorted(catalog, key=lambda repo: repo["starred_at"] or "", reverse=True)[:20]
    hot = sorted(catalog, key=lambda repo: repo["stars"], reverse=True)[:20]

    lines = [
        f"# {owner_label} GitHub Stars 分类目录",
        "",
        f"- 生成时间: {generated_at}",
        f"- 项目总数: {len(catalog)}",
        f"- 数据来源: GitHub public starred repositories",
        "",
        "## 分类概览",
        "",
    ]
    for name, count in category_counts.most_common():
        lines.append(f"- {name}: {count}")

    lines.extend(["", "## 主要语言", ""])
    for language, count in language_counts.most_common(20):
        lines.append(f"- {language}: {count}")

    lines.extend(["", "## 最近收藏 Top 20", ""])
    for repo in recent:
        lines.append(repo_line(repo))

    lines.extend(["", "## 高星项目 Top 20", ""])
    for repo in hot:
        lines.append(repo_line(repo))

    lines.extend(["", "## 全量分类", ""])
    for category in sorted(by_category):
        repos = sorted(by_category[category], key=lambda repo: (-repo["stars"], repo["full_name"].lower()))
        lines.extend([f"### {category}", ""])
        for repo in repos:
            lines.append(repo_line(repo))
        lines.append("")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_html(catalog, output_path=CATALOG_HTML_PATH, owner_name="BoscoCJ", owner_label=None, site_title="GitHub Stars Dashboard", all_users=None):
    owner_label = owner_label or owner_name
    all_users = all_users or []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    category_counts = Counter(repo["primary_category"] for repo in catalog)
    language_counts = Counter(repo["language"] for repo in catalog)
    category_order = [name for name, _ in category_counts.most_common()]
    total_stars = sum(repo["stars"] for repo in catalog)
    recent_count = sum(1 for repo in catalog if (repo["starred_at"] or "") >= "2026-01-01")
    data_json = json.dumps(catalog, ensure_ascii=False).replace("</", "<\\/")
    category_json = json.dumps(category_order, ensure_ascii=False)
    user_switcher = ""
    if all_users:
        links = []
        for user in all_users:
            username = user.get("username") or ""
            active = " active" if username.lower() == owner_name.lower() else ""
            href = user.get("href") or "#"
            label = user.get("label") or username or "User"
            links.append(f'<a class="user-link{active}" href="{escape(href, quote=True)}">{escape(label)}</a>')
        user_switcher = f'<nav class="user-switcher" aria-label="用户切换">{"".join(links)}</nav>'

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(owner_label)} · {escape(site_title)}</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --ink: #171717;
      --muted: #6d6a63;
      --line: rgba(23, 23, 23, .12);
      --panel: rgba(255, 252, 246, .76);
      --panel-strong: #fffaf0;
      --shadow: 0 22px 60px rgba(24, 22, 18, .12);
      --radius: 8px;
      --font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: var(--font);
      background:
        linear-gradient(135deg, rgba(26, 85, 92, .14), transparent 30%),
        linear-gradient(315deg, rgba(190, 74, 58, .13), transparent 28%),
        var(--bg);
    }}

    a {{ color: inherit; text-decoration: none; }}
    button, input, select {{ font: inherit; }}

    .shell {{
      width: min(1440px, calc(100% - 40px));
      margin: 0 auto;
      padding: 28px 0 64px;
    }}

    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 22px;
      align-items: stretch;
      margin-bottom: 22px;
    }}

    .hero-main {{
      min-height: 260px;
      padding: 34px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background:
        linear-gradient(135deg, rgba(17, 17, 17, .92), rgba(41, 38, 32, .88)),
        #171717;
      color: #fffaf0;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }}

    .hero-main::after {{
      content: "";
      position: absolute;
      inset: auto -12% -32% 42%;
      height: 220px;
      background: radial-gradient(circle at 50% 50%, rgba(238, 198, 112, .30), transparent 62%);
      transform: rotate(-8deg);
      pointer-events: none;
    }}

    .eyebrow {{
      margin: 0 0 22px;
      color: rgba(255, 250, 240, .64);
      font-size: 13px;
      letter-spacing: 0;
    }}

    h1 {{
      margin: 0;
      max-width: 820px;
      font-size: clamp(38px, 5.6vw, 78px);
      line-height: .96;
      letter-spacing: 0;
      font-weight: 760;
    }}

    .hero-copy {{
      max-width: 760px;
      margin: 22px 0 0;
      color: rgba(255, 250, 240, .76);
      font-size: 16px;
      line-height: 1.75;
    }}

    .hero-side {{
      display: grid;
      gap: 12px;
    }}

    .stat {{
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel);
      backdrop-filter: blur(18px);
      box-shadow: 0 16px 42px rgba(24, 22, 18, .08);
    }}

    .stat-value {{
      display: block;
      font-size: 34px;
      line-height: 1;
      font-weight: 760;
    }}

    .stat-label {{
      display: block;
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }}

    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 5;
      display: grid;
      grid-template-columns: minmax(260px, 1fr) 180px;
      gap: 12px;
      margin: 0 0 18px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255, 252, 246, .86);
      backdrop-filter: blur(18px);
      box-shadow: 0 18px 42px rgba(24, 22, 18, .08);
    }}

    .user-switcher {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: -4px 0 18px;
    }}

    .user-link {{
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 250, 240, .82);
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
    }}

    .user-link.active {{
      background: #171717;
      color: #fffaf0;
      border-color: #171717;
    }}

    .search-panel {{
      display: grid;
      gap: 9px;
      min-width: 0;
    }}

    .search-box {{
      position: relative;
      height: 46px;
      min-width: 0;
    }}

    .search, .sort {{
      width: 100%;
      height: 46px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fffaf0;
      color: var(--ink);
      outline: none;
    }}

    .search {{ padding: 0 46px 0 16px; }}
    .sort {{ padding: 0 12px; }}

    .clear-search {{
      position: absolute;
      top: 50%;
      right: 8px;
      transform: translateY(-50%);
      width: 30px;
      height: 30px;
      display: none;
      place-items: center;
      border: 0;
      border-radius: 999px;
      background: rgba(23, 23, 23, .08);
      color: var(--muted);
      cursor: pointer;
      font-size: 18px;
      line-height: 1;
    }}

    .clear-search.visible {{ display: grid; }}
    .clear-search:hover {{
      background: rgba(23, 23, 23, .14);
      color: var(--ink);
    }}

    .search-meta {{
      min-height: 18px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }}

    .quick-searches {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }}

    .quick-chip {{
      height: 30px;
      padding: 0 10px;
      border: 1px solid rgba(23, 23, 23, .1);
      border-radius: 999px;
      background: rgba(255, 250, 240, .7);
      color: #3a3732;
      cursor: pointer;
      font-size: 12px;
      line-height: 1;
      transition: background .16s ease, border-color .16s ease, color .16s ease;
    }}

    .quick-chip:hover, .quick-chip.active {{
      border-color: rgba(23, 23, 23, .28);
      background: #171717;
      color: #fffaf0;
    }}

    .category-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      margin-bottom: 20px;
    }}

    .category-pill {{
      position: relative;
      min-height: 54px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 11px 14px 11px 18px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255, 250, 240, .82);
      color: var(--ink);
      cursor: pointer;
      overflow: hidden;
      text-align: left;
      box-shadow: 0 12px 28px rgba(24, 22, 18, .06);
      transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease;
    }}

    .category-pill::before {{
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 5px;
      background: linear-gradient(180deg, var(--pill-a), var(--pill-b));
    }}

    .category-pill:hover {{ transform: translateY(-1px); }}
    .category-pill.active {{
      background: #171717;
      color: #fffaf0;
      border-color: #171717;
      box-shadow: 0 18px 40px rgba(24, 22, 18, .18);
    }}

    .category-label {{
      min-width: 0;
      font-size: 14px;
      line-height: 1.35;
      font-weight: 680;
      overflow-wrap: anywhere;
    }}

    .category-count {{
      min-width: 42px;
      padding: 6px 9px;
      border-radius: 999px;
      background: rgba(23, 23, 23, .08);
      color: var(--muted);
      text-align: center;
      font-size: 12px;
      font-variant-numeric: tabular-nums;
    }}

    .category-pill.active .category-count {{
      color: rgba(255, 250, 240, .92);
      background: rgba(255, 250, 240, .16);
    }}

    .section {{
      margin-top: 22px;
      border-radius: var(--radius);
      overflow: hidden;
      border: 1px solid var(--line);
      background: rgba(255, 252, 246, .62);
      box-shadow: 0 18px 48px rgba(24, 22, 18, .08);
    }}

    .section-head {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      align-items: end;
      padding: 22px 24px;
      color: #fffaf0;
      background: linear-gradient(135deg, var(--cat-a), var(--cat-b));
    }}

    .section-title {{
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
      font-weight: 720;
    }}

    .section-meta {{
      margin: 8px 0 0;
      color: rgba(255, 250, 240, .78);
      font-size: 13px;
    }}

    .section-count {{
      font-size: 38px;
      line-height: 1;
      font-weight: 760;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
      gap: 14px;
      padding: 14px;
    }}

    .repo-card {{
      min-height: 232px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: 16px;
      padding: 18px;
      border: 1px solid rgba(23, 23, 23, .11);
      border-radius: var(--radius);
      background: rgba(255, 250, 240, .9);
      transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
    }}

    .repo-card:hover {{
      transform: translateY(-3px);
      border-color: rgba(23, 23, 23, .28);
      box-shadow: 0 18px 40px rgba(24, 22, 18, .12);
    }}

    .repo-top {{
      display: grid;
      grid-template-columns: 42px 1fr;
      gap: 12px;
      align-items: center;
      min-width: 0;
    }}

    .avatar {{
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: 1px solid rgba(23, 23, 23, .12);
      background: #e7dfcf;
      object-fit: cover;
    }}

    .repo-name {{
      display: block;
      overflow-wrap: anywhere;
      font-weight: 740;
      line-height: 1.25;
    }}

    .owner {{
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}

    .note {{
      margin: 0;
      color: #34312c;
      font-size: 14px;
      line-height: 1.72;
    }}

    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      align-items: center;
    }}

    .tag {{
      max-width: 100%;
      padding: 5px 8px;
      border-radius: 999px;
      background: rgba(23, 23, 23, .07);
      color: #3a3732;
      font-size: 12px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }}

    .metric {{
      color: var(--muted);
      font-variant-numeric: tabular-nums;
    }}

    .empty {{
      display: none;
      padding: 54px 18px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: var(--radius);
      background: rgba(255, 252, 246, .74);
    }}

    .footer {{
      margin-top: 34px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.7;
    }}

    @media (max-width: 900px) {{
      .shell {{ width: min(100% - 24px, 1440px); padding-top: 14px; }}
      .hero {{ grid-template-columns: 1fr; }}
      .hero-main {{ min-height: 240px; padding: 26px; }}
      .hero-side {{ grid-template-columns: repeat(2, 1fr); }}
      .toolbar {{ grid-template-columns: 1fr; }}
      .section-head {{ grid-template-columns: 1fr; }}
    }}

    @media (max-width: 560px) {{
      .hero-side {{ grid-template-columns: 1fr; }}
      .grid {{ grid-template-columns: 1fr; }}
      .category-strip {{ grid-template-columns: 1fr 1fr; gap: 8px; }}
      .category-pill {{ min-height: 48px; padding: 10px 10px 10px 14px; }}
      .category-label {{ font-size: 12px; }}
      .category-count {{ min-width: 34px; padding: 5px 7px; }}
      .section-head {{ padding: 18px; }}
      .repo-card {{ min-height: 0; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="hero-main">
        <p class="eyebrow">@{escape(owner_name)} GitHub Stars · {escape(generated_at)}</p>
        <h1>把收藏夹变成项目雷达</h1>
        <p class="hero-copy">正在浏览 {escape(owner_label)} 的公开 GitHub stars。每张卡片都有中文解释、技术标签、热度和更新时间，点击项目名即可跳转到 GitHub。</p>
      </div>
      <aside class="hero-side" aria-label="统计概览">
        <div class="stat"><span class="stat-value">{len(catalog)}</span><span class="stat-label">已分类项目</span></div>
        <div class="stat"><span class="stat-value">{len(category_counts)}</span><span class="stat-label">用途分类</span></div>
        <div class="stat"><span class="stat-value">{total_stars:,}</span><span class="stat-label">累计 GitHub stars</span></div>
        <div class="stat"><span class="stat-value">{recent_count}</span><span class="stat-label">2026 年收藏</span></div>
      </aside>
    </section>

    {user_switcher}

    <section class="toolbar" aria-label="筛选工具">
      <div class="search-panel">
        <div class="search-box">
          <input class="search" id="search" type="search" placeholder="搜索项目、作者、中文解释、技术栈、分类" autocomplete="off">
          <button class="clear-search" id="clearSearch" type="button" aria-label="清空搜索">×</button>
        </div>
        <div class="quick-searches" id="quickSearches" aria-label="常用搜索">
          <button class="quick-chip" type="button" data-query="命理">命理</button>
          <button class="quick-chip" type="button" data-query="八卦算命">八卦算命</button>
          <button class="quick-chip" type="button" data-query="Agent">Agent</button>
          <button class="quick-chip" type="button" data-query="RAG">RAG</button>
          <button class="quick-chip" type="button" data-query="视频">视频</button>
          <button class="quick-chip" type="button" data-query="剪辑">剪辑</button>
          <button class="quick-chip" type="button" data-query="前端">前端</button>
          <button class="quick-chip" type="button" data-query="安全">安全</button>
        </div>
        <div class="search-meta" id="searchMeta"></div>
      </div>
      <select class="sort" id="sort" aria-label="排序">
        <option value="stars">按热度排序</option>
        <option value="recent">按收藏时间</option>
        <option value="updated">按更新时间</option>
        <option value="name">按名称排序</option>
      </select>
    </section>

    <nav class="category-strip" id="categoryStrip" aria-label="分类筛选"></nav>
    <div class="empty" id="empty">没有找到匹配项目。换个关键词试试。</div>
    <div id="sections"></div>
    <p class="footer">数据来自 @{escape(owner_name)} 的 GitHub public starred repositories。头像图片直接使用 GitHub owner avatar；页面为静态 HTML，可由 GitHub Actions 自动刷新。</p>
  </main>

  <script type="application/json" id="catalog-data">{data_json}</script>
  <script type="application/json" id="category-data">{category_json}</script>
  <script>
    const catalog = JSON.parse(document.getElementById('catalog-data').textContent);
    const categoryOrder = JSON.parse(document.getElementById('category-data').textContent);
    const palette = [
      ['#111827', '#0f766e'],
      ['#7f1d1d', '#c2410c'],
      ['#312e81', '#7c3aed'],
      ['#064e3b', '#65a30d'],
      ['#1e3a8a', '#0891b2'],
      ['#701a75', '#db2777'],
      ['#3f3f46', '#71717a'],
      ['#78350f', '#ca8a04'],
      ['#164e63', '#2563eb'],
      ['#4c1d95', '#9333ea'],
      ['#14532d', '#16a34a'],
      ['#581c87', '#be185d'],
      ['#292524', '#a16207']
    ];

    const state = {{ category: '全部', query: '', sort: 'stars' }};
    const categoryStrip = document.getElementById('categoryStrip');
    const sectionsEl = document.getElementById('sections');
    const emptyEl = document.getElementById('empty');
    const searchEl = document.getElementById('search');
    const clearSearchEl = document.getElementById('clearSearch');
    const searchMetaEl = document.getElementById('searchMeta');
    const quickSearchesEl = document.getElementById('quickSearches');
    const sortEl = document.getElementById('sort');

    const searchAliases = {{
      '命理': ['命理', '算命', '八字', '八卦', '占卜', '占星', '星盘', '紫微', '风水', '易经', '玄学', '命运'],
      '算命': ['命理', '算命', '八字', '八卦', '占卜', '占星', '星盘', '紫微', '风水', '易经', '玄学', '命运'],
      '八卦': ['命理', '算命', '八字', '八卦', '占卜', '占星', '星盘', '紫微', '风水', '易经', '玄学', '命运'],
      'agent': ['agent', 'agents', 'assistant', 'coding agent', 'ai agent', '智能体', '助手', '自动化'],
      'rag': ['rag', 'retrieval', 'embedding', 'vector', '向量', '检索', '知识库', '召回'],
      '视频': ['视频', 'video', 'audio', '音频', '剪辑', '字幕', 'transcribe', 'ffmpeg', '生成式创作'],
      '剪辑': ['视频', 'video', '剪辑', '字幕', 'transcribe', 'ffmpeg', 'cut'],
      '前端': ['前端', 'frontend', 'react', 'vue', 'css', 'ui', 'design', 'animation', '动画'],
      '安全': ['安全', 'security', 'privacy', '隐私', 'reverse', '逆向']
    }};

    function formatNumber(value) {{
      return new Intl.NumberFormat('en-US').format(value || 0);
    }}

    function compactDate(value) {{
      return value ? value.slice(0, 10) : 'unknown';
    }}

    function categoryColors(category) {{
      const index = Math.max(0, categoryOrder.indexOf(category));
      return palette[index % palette.length];
    }}

    function normalizeText(value) {{
      return String(value || '')
        .normalize('NFKD')
        .replace(/[\\u0300-\\u036f]/g, '')
        .toLowerCase()
        .replace(/[\\\\/_:|.,;()[\\]{{}}<>#"'`~!?+=*-]+/g, ' ')
        .replace(/\\s+/g, ' ')
        .trim();
    }}

    function repoSearchFields(repo) {{
      if (!repo.__searchFields) {{
        const name = normalizeText([repo.full_name, repo.name, repo.owner_login].join(' '));
        const note = normalizeText([repo.chinese_note, repo.description].join(' '));
        const meta = normalizeText([
          repo.primary_category,
          ...(repo.secondary_categories || []),
          repo.language,
          repo.license,
          repo.homepage,
          ...(repo.topics || []),
          ...(repo.matched_keywords || [])
        ].join(' '));
        repo.__searchFields = {{
          name,
          note,
          meta,
          all: [name, note, meta].join(' ')
        }};
      }}
      return repo.__searchFields;
    }}

    function expandToken(token) {{
      const expanded = new Set([token]);
      for (const [key, values] of Object.entries(searchAliases)) {{
        const normalizedKey = normalizeText(key);
        if (token.includes(normalizedKey) || normalizedKey.includes(token) || values.some(value => token.includes(normalizeText(value)))) {{
          values.forEach(value => expanded.add(normalizeText(value)));
        }}
      }}
      return [...expanded].filter(Boolean);
    }}

    function queryGroups(query) {{
      const normalized = normalizeText(query);
      if (!normalized) return [];
      return normalized.split(' ').filter(Boolean).map(expandToken);
    }}

    function scoreTerm(fields, term) {{
      let score = 0;
      if (fields.name === term) score += 180;
      if (fields.name.includes(term)) score += 90;
      if (fields.meta.includes(term)) score += 48;
      if (fields.note.includes(term)) score += 36;
      if (fields.all.includes(term)) score += 12;
      return score;
    }}

    function repoSearchScore(repo) {{
      if (!state.query) return 0;
      const fields = repoSearchFields(repo);
      const groups = queryGroups(state.query);
      if (!groups.length) return 0;
      let score = 0;
      const raw = normalizeText(state.query);
      if (fields.all.includes(raw)) score += 120;
      for (const group of groups) {{
        const groupScore = Math.max(...group.map(term => scoreTerm(fields, term)));
        if (groupScore <= 0) return -1;
        score += groupScore;
      }}
      return score;
    }}

    function repoMatchesSearch(repo) {{
      return repoSearchScore(repo) >= 0;
    }}

    function repoMatches(repo) {{
      if (state.category !== '全部' && repo.primary_category !== state.category) return false;
      const score = repoSearchScore(repo);
      repo.__score = score;
      return score >= 0;
    }}

    function legacySearchBlob(repo) {{
      return [
        repo.full_name,
        repo.description,
        repo.chinese_note,
        repo.primary_category,
        repo.language,
        ...(repo.topics || [])
      ].join(' ').toLowerCase();
    }}

    function sortRepos(repos) {{
      const sorted = [...repos];
      const byText = (repo) => repo.full_name.toLowerCase();
      if (state.query) {{
        sorted.sort((a, b) => (b.__score || 0) - (a.__score || 0) || (b.stars || 0) - (a.stars || 0) || byText(a).localeCompare(byText(b)));
      }} else if (state.sort === 'recent') {{
        sorted.sort((a, b) => (b.starred_at || '').localeCompare(a.starred_at || '') || byText(a).localeCompare(byText(b)));
      }} else if (state.sort === 'updated') {{
        sorted.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || '') || byText(a).localeCompare(byText(b)));
      }} else if (state.sort === 'name') {{
        sorted.sort((a, b) => byText(a).localeCompare(byText(b)));
      }} else {{
        sorted.sort((a, b) => (b.stars || 0) - (a.stars || 0) || byText(a).localeCompare(byText(b)));
      }}
      return sorted;
    }}

    function renderCategoryStrip() {{
      const searchableCatalog = state.query ? catalog.filter(repoMatchesSearch) : catalog;
      const counts = searchableCatalog.reduce((acc, repo) => {{
        acc[repo.primary_category] = (acc[repo.primary_category] || 0) + 1;
        return acc;
      }}, {{}});
      const labels = ['全部', ...categoryOrder];
      categoryStrip.innerHTML = labels.map(label => {{
        const active = state.category === label ? ' active' : '';
        const count = label === '全部' ? searchableCatalog.length : counts[label] || 0;
        const colors = label === '全部' ? ['#171717', '#525252'] : categoryColors(label);
        return `<button class="category-pill${{active}}" style="--pill-a: ${{colors[0]}}; --pill-b: ${{colors[1]}};" data-category="${{escapeAttr(label)}}"><span class="category-label">${{escapeHtml(label)}}</span><span class="category-count">${{count}}</span></button>`;
      }}).join('');
      categoryStrip.querySelectorAll('button').forEach(button => {{
        button.addEventListener('click', () => {{
          state.category = button.dataset.category;
          render();
        }});
      }});
    }}

    function renderCard(repo) {{
      const topics = (repo.topics || []).slice(0, 4).map(topic => `<span class="tag">${{escapeHtml(topic)}}</span>`).join('');
      const homepage = repo.homepage ? `<span class="tag">homepage</span>` : '';
      return `
        <a class="repo-card" href="${{escapeAttr(repo.html_url)}}" target="_blank" rel="noreferrer">
          <div class="repo-top">
            <img class="avatar" src="${{escapeAttr(repo.owner_avatar_url)}}" alt="" loading="lazy">
            <span>
              <span class="repo-name">${{escapeHtml(repo.full_name)}}</span>
              <span class="owner">${{escapeHtml(repo.owner_login || '')}} · ${{escapeHtml(repo.language || 'Unknown')}}</span>
            </span>
          </div>
          <p class="note">${{escapeHtml(repo.chinese_note || repo.description || '暂无说明')}}</p>
          <div class="tags">
            <span class="tag metric">${{formatNumber(repo.stars)}} stars</span>
            <span class="tag metric">updated ${{compactDate(repo.updated_at)}}</span>
            ${{topics}}
            ${{homepage}}
          </div>
        </a>
      `;
    }}

    function renderSections(repos) {{
      const groups = new Map();
      for (const category of categoryOrder) groups.set(category, []);
      for (const repo of repos) {{
        if (!groups.has(repo.primary_category)) groups.set(repo.primary_category, []);
        groups.get(repo.primary_category).push(repo);
      }}

      sectionsEl.innerHTML = [...groups.entries()]
        .filter(([, items]) => items.length)
        .map(([category, items]) => {{
          const colors = categoryColors(category);
          const sortedItems = sortRepos(items);
          return `
            <section class="section" style="--cat-a: ${{colors[0]}}; --cat-b: ${{colors[1]}};">
              <header class="section-head">
                <div>
                  <h2 class="section-title">${{escapeHtml(category)}}</h2>
                  <p class="section-meta">按当前排序展示，可直接点击卡片进入 GitHub 项目页</p>
                </div>
                <div class="section-count">${{items.length}}</div>
              </header>
              <div class="grid">${{sortedItems.map(renderCard).join('')}}</div>
            </section>
          `;
        }}).join('');
    }}

    function render() {{
      const filtered = catalog.filter(repoMatches);
      emptyEl.style.display = filtered.length ? 'none' : 'block';
      clearSearchEl.classList.toggle('visible', Boolean(state.query));
      searchMetaEl.textContent = state.query
        ? `找到 ${{filtered.length}} 个匹配项目${{state.category === '全部' ? '' : ' · ' + state.category}}`
        : `当前显示 ${{filtered.length}} 个项目`;
      quickSearchesEl.querySelectorAll('button').forEach(button => {{
        button.classList.toggle('active', normalizeText(button.dataset.query) === normalizeText(state.query));
      }});
      renderCategoryStrip();
      renderSections(filtered);
    }}

    function escapeHtml(value) {{
      return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }}

    function escapeAttr(value) {{
      return escapeHtml(value);
    }}

    searchEl.addEventListener('input', event => {{
      state.query = event.target.value.trim();
      render();
    }});

    clearSearchEl.addEventListener('click', () => {{
      state.query = '';
      searchEl.value = '';
      searchEl.focus();
      render();
    }});

    quickSearchesEl.addEventListener('click', event => {{
      const button = event.target.closest('button[data-query]');
      if (!button) return;
      state.query = button.dataset.query;
      searchEl.value = state.query;
      render();
    }});

    sortEl.addEventListener('change', event => {{
      state.sort = event.target.value;
      render();
    }});

    render();
  </script>
</body>
</html>
"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build a GitHub Stars dashboard from a raw starred repositories JSON file.")
    parser.add_argument("--raw", default=str(RAW_PATH))
    parser.add_argument("--json", default=str(CATALOG_JSON_PATH))
    parser.add_argument("--markdown", default=str(CATALOG_MD_PATH))
    parser.add_argument("--html", default=str(CATALOG_HTML_PATH))
    parser.add_argument("--owner", default="BoscoCJ")
    parser.add_argument("--label", default=None)
    parser.add_argument("--title", default="GitHub Stars Dashboard")
    args = parser.parse_args()

    catalog = build_catalog(args.raw)
    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(catalog, args.markdown, args.label or args.owner)
    write_html(catalog, args.html, owner_name=args.owner, owner_label=args.label, site_title=args.title)
    print(f"repos={len(catalog)}")
    print(f"json={json_path}")
    print(f"markdown={args.markdown}")
    print(f"html={args.html}")


if __name__ == "__main__":
    main()
