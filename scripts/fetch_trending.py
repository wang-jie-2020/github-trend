import argparse
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.request import Request, urlopen

from dotenv import load_dotenv

TRENDING_URL = "https://github.com/trending?since=weekly"


@dataclass
class RepoItem:
    repo: str = ""
    description: str = ""
    language: str = ""
    stars: int = 0
    forks: int = 0


class TrendingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self._in_article = False
        self._in_h2 = False
        self._in_description = False
        self._in_language = False
        self._capture_stars = False
        self._capture_forks = False
        self._current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "Box-row" in attrs.get("class", ""):
            self._in_article = True
            self._current = RepoItem()
        if not self._in_article:
            return
        if tag == "h2":
            self._in_h2 = True
        elif tag == "p":
            self._in_description = True
        elif tag == "span" and attrs.get("itemprop") == "programmingLanguage":
            self._in_language = True
        elif tag == "a":
            href = attrs.get("href", "")
            if self._in_h2 and href.count("/") >= 2:
                self._current.repo = href.strip("/")
            elif href.endswith("/stargazers"):
                self._capture_stars = True
            elif href.endswith("/forks"):
                self._capture_forks = True

    def handle_endtag(self, tag):
        if tag == "article" and self._in_article:
            self._in_article = False
            self._in_h2 = False
            self._in_description = False
            self._in_language = False
            self._capture_stars = False
            self._capture_forks = False
            self.items.append(self._current)
            self._current = None
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "p":
            self._in_description = False
        elif tag == "span":
            self._in_language = False
        elif tag == "a":
            self._capture_stars = False
            self._capture_forks = False

    def handle_data(self, data):
        if not self._in_article or self._current is None:
            return
        text = data.strip()
        if not text:
            return
        if self._in_description:
            self._current.description = text
        elif self._in_language:
            self._current.language = text
        elif self._capture_stars:
            self._current.stars = int(re.sub(r"[^0-9]", "", text) or 0)
        elif self._capture_forks:
            self._current.forks = int(re.sub(r"[^0-9]", "", text) or 0)


def parse_trending_html(html: str):
    parser = TrendingParser()
    parser.feed(html)
    return [
        {
            "repo": item.repo,
            "description": item.description,
            "language": item.language,
            "stars": item.stars,
            "forks": item.forks,
        }
        for item in parser.items
        if item.repo
    ]


def normalize_items(items):
    normalized = []
    for idx, item in enumerate(items, start=1):
        normalized.append(
            {
                "source": "trending",
                "rank": idx,
                "repo": item["repo"],
                "url": f"https://github.com/{item['repo']}",
                "summary": item.get("description", ""),
                "language": item.get("language", ""),
                "stars": int(item.get("stars", 0)),
                "forks": int(item.get("forks", 0)),
            }
        )
    return normalized


def fetch_html():
    request = Request(TRENDING_URL, headers={"User-Agent": "weekly-trending-bot"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    html = fetch_html()
    parsed = parse_trending_html(html)
    normalized = normalize_items(parsed)[: args.top]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
