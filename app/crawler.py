"""Polite, robots.txt-aware, same-domain crawler."""
from __future__ import annotations

import time
import urllib.robotparser
from collections import deque
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "SEOBrain200Bot/0.2 (+site audit; respects robots.txt)"
SKIP_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf", ".zip", ".mp4", ".mp3",
            ".css", ".js", ".ico", ".woff", ".woff2", ".xml", ".json")


def normalize(url: str) -> str:
    url, _ = urldefrag(url.strip())
    p = urlparse(url)
    path = p.path or "/"
    return f"{p.scheme.lower()}://{p.netloc.lower()}{path}" + (f"?{p.query}" if p.query else "")


def host_key(netloc: str) -> str:
    netloc = netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


@dataclass
class PageResult:
    url: str
    final_url: str
    status_code: int | None
    response_ms: int
    bytes: int
    content_type: str = ""
    title: str = ""
    meta_description: str = ""
    h1: list[str] = field(default_factory=list)
    h2_count: int = 0
    canonical: str = ""
    robots_meta: str = ""
    lang: str = ""
    viewport: bool = False
    word_count: int = 0
    images_total: int = 0
    images_missing_alt: int = 0
    internal_links: list[str] = field(default_factory=list)
    external_links: int = 0
    schema_types: list[str] = field(default_factory=list)
    og_title: bool = False
    https: bool = False
    redirected: bool = False
    error: str = ""


@dataclass
class CrawlResult:
    start_url: str
    pages: list[PageResult]
    robots_found: bool
    sitemap_urls: list[str]
    blocked_by_robots: list[str]
    broken_links: list[dict]


def parse_page(url: str, resp: httpx.Response, ms: int, domain: str) -> PageResult:
    ctype = resp.headers.get("content-type", "")
    pr = PageResult(url=url, final_url=str(resp.url), status_code=resp.status_code, response_ms=ms,
                    bytes=len(resp.content), content_type=ctype,
                    https=str(resp.url).startswith("https://"),
                    redirected=normalize(str(resp.url)) != normalize(url))
    if "html" not in ctype.lower():
        return pr
    soup = BeautifulSoup(resp.text, "html.parser")
    if soup.title and soup.title.string:
        pr.title = soup.title.string.strip()
    md = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    pr.meta_description = (md.get("content") or "").strip() if md else ""
    rm = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "robots"})
    pr.robots_meta = (rm.get("content") or "").lower() if rm else ""
    pr.viewport = bool(soup.find("meta", attrs={"name": lambda v: v and v.lower() == "viewport"}))
    pr.og_title = bool(soup.find("meta", attrs={"property": "og:title"}))
    can = soup.find("link", rel=lambda v: v and "canonical" in (v if isinstance(v, list) else [v]))
    pr.canonical = urljoin(str(resp.url), can.get("href", "")) if can and can.get("href") else ""
    html = soup.find("html")
    pr.lang = (html.get("lang") or "") if html else ""
    pr.h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    pr.h2_count = len(soup.find_all("h2"))
    for s in soup.find_all("script", type="application/ld+json"):
        txt = s.string or ""
        for t in ("Organization", "LocalBusiness", "Product", "Article", "BreadcrumbList", "FAQPage",
                  "WebSite", "Service", "Person", "Event", "Review"):
            if f'"{t}"' in txt and t not in pr.schema_types:
                pr.schema_types.append(t)
    imgs = soup.find_all("img")
    pr.images_total = len(imgs)
    pr.images_missing_alt = sum(1 for i in imgs if not (i.get("alt") or "").strip())
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    pr.word_count = len(soup.get_text(" ", strip=True).split())
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absu = normalize(urljoin(str(resp.url), href))
        p = urlparse(absu)
        if p.scheme not in ("http", "https"):
            continue
        if host_key(p.netloc) == domain:
            if absu not in seen:
                seen.add(absu)
                pr.internal_links.append(absu)
        else:
            pr.external_links += 1
    return pr


def crawl(start_url: str, max_pages: int = 25, delay: float = 0.4, timeout: float = 12.0,
          progress: Callable[[str], None] | None = None,
          client: httpx.Client | None = None) -> CrawlResult:
    if not start_url.startswith(("http://", "https://")):
        start_url = "https://" + start_url
    start_url = normalize(start_url)
    parsed = urlparse(start_url)
    domain = host_key(parsed.netloc)
    own = client is None
    client = client or httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=timeout)

    rp = urllib.robotparser.RobotFileParser()
    robots_found, sitemaps = False, []
    try:
        r = client.get(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
        if r.status_code == 200 and "html" not in r.headers.get("content-type", ""):
            robots_found = True
            rp.parse(r.text.splitlines())
            sitemaps = [l.split(":", 1)[1].strip() for l in r.text.splitlines() if l.lower().startswith("sitemap:")]
        else:
            rp.parse([])
    except httpx.HTTPError:
        rp.parse([])

    queue, queued = deque([start_url]), {start_url}
    pages: list[PageResult] = []
    blocked: list[str] = []
    status_by_url: dict[str, int | None] = {}
    linked_from: dict[str, str] = {}
    try:
        while queue and len(pages) < max_pages:
            url = queue.popleft()
            if not rp.can_fetch(USER_AGENT, url):
                blocked.append(url)
                continue
            if url.lower().endswith(SKIP_EXT):
                continue
            if progress:
                progress(f"Crawling {len(pages) + 1}/{max_pages}: {url}")
            t0 = time.perf_counter()
            try:
                resp = client.get(url)
                ms = int((time.perf_counter() - t0) * 1000)
                pr = parse_page(url, resp, ms, domain)
            except httpx.HTTPError as e:
                pr = PageResult(url=url, final_url=url, status_code=None,
                                response_ms=int((time.perf_counter() - t0) * 1000), bytes=0, error=type(e).__name__)
            pages.append(pr)
            status_by_url[url] = pr.status_code
            for link in pr.internal_links:
                if link not in queued and not link.lower().endswith(SKIP_EXT):
                    queued.add(link)
                    linked_from.setdefault(link, url)
                    queue.append(link)
            time.sleep(delay)
    finally:
        if own:
            client.close()

    broken = [{"url": u, "status": s, "linked_from": linked_from.get(u, "")}
              for u, s in status_by_url.items() if s is None or s >= 400]
    return CrawlResult(start_url, pages, robots_found, sitemaps, blocked, broken)
