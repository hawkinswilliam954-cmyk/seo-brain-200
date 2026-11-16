"""Operational agents. Each one maps to a role in agents/registry.json and returns
evidence-backed findings. All are recommend-only: none of them changes a website."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from typing import Callable

from .crawler import CrawlResult, PageResult


@dataclass
class Finding:
    agent_id: str
    severity: str  # critical | high | medium | low
    issue: str
    url: str
    evidence: str
    recommendation: str


AgentFn = Callable[[CrawlResult], list[Finding]]
OPERATIONAL: dict[str, AgentFn] = {}


def agent(agent_id: str):
    def wrap(fn: AgentFn) -> AgentFn:
        OPERATIONAL[agent_id] = fn
        return fn
    return wrap


def html_pages(c: CrawlResult) -> list[PageResult]:
    return [p for p in c.pages if p.status_code and p.status_code < 400 and "html" in p.content_type.lower()]


@agent("TECH_002")  # Crawl analyzer
def crawl_analyzer(c: CrawlResult) -> list[Finding]:
    out = []
    if not c.robots_found:
        out.append(Finding("TECH_002", "low", "No robots.txt file", c.start_url, "robots.txt returned no file",
                           "Add a robots.txt that points to your XML sitemap."))
    if not c.sitemap_urls:
        out.append(Finding("TECH_002", "medium", "No XML sitemap declared", c.start_url,
                           "robots.txt has no Sitemap: line", "Publish an XML sitemap and reference it in robots.txt."))
    for p in c.pages:
        if p.redirected:
            out.append(Finding("TECH_002", "low", "Internal link redirects", p.url, f"Redirects to {p.final_url}",
                               "Link straight to the final URL to save crawl budget."))
    return out


@agent("TECH_004")  # Broken-link detector
def broken_links(c: CrawlResult) -> list[Finding]:
    return [Finding("TECH_004", "high", "Broken internal link", b["url"],
                    f"Status {b['status'] or 'no response'}; linked from {b['linked_from'] or 'start'}",
                    "Fix the link or add a 301 redirect to the right page.") for b in c.broken_links]


@agent("TECH_003")  # Indexation monitor
def indexation(c: CrawlResult) -> list[Finding]:
    out = []
    for p in html_pages(c):
        if "noindex" in p.robots_meta:
            out.append(Finding("TECH_003", "critical" if p.url == c.start_url else "high",
                               "Page is set to noindex", p.url, f"meta robots: {p.robots_meta}",
                               "Remove noindex if this page should appear in Google."))
    for u in c.blocked_by_robots[:20]:
        out.append(Finding("TECH_003", "medium", "Blocked by robots.txt", u, "Disallowed for crawlers",
                           "Confirm this block is intended."))
    return out


@agent("TECH_001")  # Technical SEO auditor
def technical(c: CrawlResult) -> list[Finding]:
    out = []
    for p in c.pages:
        if p.status_code and not p.https:
            out.append(Finding("TECH_001", "high", "Page not served over HTTPS", p.url, p.final_url,
                               "Force HTTPS with a site-wide 301 redirect."))
    for p in html_pages(c):
        if not p.lang:
            out.append(Finding("TECH_001", "low", "Missing html lang attribute", p.url, "<html> has no lang",
                               'Add lang="en" (or the right language) to the <html> tag.'))
    return out


@agent("CONT_006")  # Title and meta writer
def titles_meta(c: CrawlResult) -> list[Finding]:
    out = []
    pages = html_pages(c)
    for p in pages:
        if not p.title:
            out.append(Finding("CONT_006", "high", "Missing page title", p.url, "<title> empty or absent",
                               "Write a unique 50-60 character title with the page's main keyword."))
        elif len(p.title) > 60:
            out.append(Finding("CONT_006", "low", "Title too long", p.url, f"{len(p.title)} chars: {p.title[:80]}",
                               "Trim to about 60 characters so Google doesn't cut it off."))
        elif len(p.title) < 20:
            out.append(Finding("CONT_006", "medium", "Title too short", p.url, f"{len(p.title)} chars: {p.title}",
                               "Expand the title to describe the page and include a keyword."))
        if not p.meta_description:
            out.append(Finding("CONT_006", "medium", "Missing meta description", p.url, "No meta description",
                               "Add a 140-160 character description that sells the click."))
        elif len(p.meta_description) > 165:
            out.append(Finding("CONT_006", "low", "Meta description too long", p.url,
                               f"{len(p.meta_description)} chars", "Trim to about 155 characters."))
    for title, n in Counter(p.title for p in pages if p.title).items():
        if n > 1:
            urls = [p.url for p in pages if p.title == title]
            out.append(Finding("CONT_006", "medium", "Duplicate title tag", urls[0],
                               f'"{title[:70]}" used on {n} pages', "Give every page its own title."))
    return out


@agent("CONT_005")  # Content optimizer
def content(c: CrawlResult) -> list[Finding]:
    out = []
    for p in html_pages(c):
        if len(p.h1) == 0:
            out.append(Finding("CONT_005", "medium", "Missing H1 heading", p.url, "No <h1>",
                               "Add one H1 that states what the page is about."))
        elif len(p.h1) > 1:
            out.append(Finding("CONT_005", "low", "Multiple H1 headings", p.url, f"{len(p.h1)} H1 tags",
                               "Keep one H1 and make the rest H2s."))
        if p.word_count < 250:
            out.append(Finding("CONT_005", "medium", "Thin content", p.url, f"{p.word_count} words",
                               "Expand to 500+ useful words answering what searchers ask."))
    return out


@agent("TECH_006")  # Schema generator
def schema(c: CrawlResult) -> list[Finding]:
    pages = html_pages(c)
    if pages and not any(p.schema_types for p in pages):
        return [Finding("TECH_006", "medium", "No structured data found", c.start_url, "No JSON-LD on crawled pages",
                        "Add Organization or LocalBusiness schema to the homepage.")]
    return []


@agent("TECH_009")  # Mobile SEO auditor
def mobile(c: CrawlResult) -> list[Finding]:
    return [Finding("TECH_009", "high", "No mobile viewport tag", p.url, "meta viewport missing",
                    'Add <meta name="viewport" content="width=device-width, initial-scale=1">.')
            for p in html_pages(c) if not p.viewport]


@agent("TECH_011")  # Canonical manager
def canonical(c: CrawlResult) -> list[Finding]:
    out = []
    for p in html_pages(c):
        if not p.canonical:
            out.append(Finding("TECH_011", "low", "Missing canonical tag", p.url, "No rel=canonical",
                               "Add a self-referencing canonical tag."))
    return out


@agent("TECH_018")  # Image optimization
def images(c: CrawlResult) -> list[Finding]:
    return [Finding("TECH_018", "medium" if p.images_missing_alt > 3 else "low", "Images missing alt text", p.url,
                    f"{p.images_missing_alt} of {p.images_total} images", "Describe each image in its alt attribute.")
            for p in html_pages(c) if p.images_missing_alt]


@agent("TECH_007")  # Core Web Vitals analyst (server-side proxy signals)
def speed(c: CrawlResult) -> list[Finding]:
    out = []
    for p in html_pages(c):
        if p.response_ms > 1500:
            out.append(Finding("TECH_007", "medium", "Slow server response", p.url, f"{p.response_ms} ms",
                               "Add caching or a CDN; aim for under 800 ms."))
        if p.bytes > 1_500_000:
            out.append(Finding("TECH_007", "medium", "Heavy HTML page", p.url, f"{p.bytes // 1024} KB",
                               "Cut inline scripts and page weight."))
    return out


@agent("TECH_014")  # Duplicate content detector
def duplicates(c: CrawlResult) -> list[Finding]:
    by_desc = defaultdict(list)
    for p in html_pages(c):
        if p.meta_description:
            by_desc[p.meta_description].append(p.url)
    return [Finding("TECH_014", "low", "Duplicate meta description", urls[0], f"Shared by {len(urls)} pages",
                    "Write a unique description for each page.") for urls in by_desc.values() if len(urls) > 1]


SEV_WEIGHT = {"critical": 15, "high": 6, "medium": 3, "low": 1}


def score(severities: list[str], page_count: int) -> int:
    """0-100 health score. Penalty is normalised by site size so big sites aren't punished for size alone."""
    if page_count == 0:
        return 0
    penalty = sum(SEV_WEIGHT[s] for s in severities)
    per_page = penalty / max(page_count, 1)
    return max(0, min(100, round(100 - per_page * 6)))


def run_all(c: CrawlResult) -> list[Finding]:
    out: list[Finding] = []
    for fn in OPERATIONAL.values():
        out.extend(fn(c))
    return out


def as_dict(f: Finding) -> dict:
    return asdict(f)
